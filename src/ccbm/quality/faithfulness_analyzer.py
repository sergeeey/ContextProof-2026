"""
Faithfulness Error Analyzer — анализ ошибок faithfulness.

Определяет:
- Какие типы вопросов теряются при сжатии
- Какие категории данных страдают больше
- Где именно происходит потеря информации
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from ccbm.quality.golden_set_qa import QAGoldenSet, QACategory, QAPair


class ErrorType(Enum):
    """Типы ошибок faithfulness."""
    L1_DATA_LOST = "l1_data_lost"  # Критичные данные удалены
    NUMERIC_DRIFT = "numeric_drift"  # Число изменилось
    ENTITY_SWAPPED = "entity_swapped"  # Сущность перепутана
    CONTEXT_LOST = "context_lost"  # Контекст утерян
    SEMANTIC_DRIFT = "semantic_drift"  # Смысл изменился
    HALLUCINATION = "hallucination"  # Выдуманная информация


@dataclass
class FaithfulnessError:
    """Запись об ошибке faithfulness."""
    error_id: str
    qa_pair_id: str
    error_type: ErrorType
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    original_answer: str
    compressed_answer: str
    expected_answer: str
    description: str
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        """Сериализация в словарь."""
        return {
            "error_id": self.error_id,
            "qa_pair_id": self.qa_pair_id,
            "error_type": self.error_type.value,
            "severity": self.severity,
            "original_answer": self.original_answer,
            "compressed_answer": self.compressed_answer,
            "expected_answer": self.expected_answer,
            "description": self.description,
            "metadata": self.metadata or {},
        }


class FaithfulnessAnalyzer:
    """
    Анализатор ошибок faithfulness.
    
    Использование:
    1. Прогнать QA тесты на сжатом контексте
    2. Сравнить ответы с оригиналом
    3. Классифицировать ошибки
    4. Получить рекомендации по улучшению
    """
    
    def __init__(self):
        """Инициализация анализатора."""
        self.golden_set = QAGoldenSet()
        self.errors: List[FaithfulnessError] = []
        self._error_counter = 0
    
    def analyze_qa_pair(
        self,
        qa_pair: QAPair,
        compressed_context: str,
        compressed_answer: str,
    ) -> Optional[FaithfulnessError]:
        """
        Анализ одной QA пары.
        
        Args:
            qa_pair: QA пара
            compressed_context: Сжатый контекст
            compressed_answer: Ответ на сжатом контексте
            
        Returns:
            FaithfulnessError если есть ошибка, иначе None
        """
        # Проверка: содержится ли ожидаемый ответ в сжатом
        expected_in_compressed = qa_pair.expected_answer in compressed_context
        
        # Проверка: совпадает ли ответ
        answer_match = qa_pair.expected_answer == compressed_answer
        
        # Проверка: содержится ли ответ в сжатом
        answer_in_compressed = qa_pair.expected_answer in compressed_answer
        
        if answer_match or answer_in_compressed:
            return None  # Ошибки нет
        
        # Классификация ошибки
        if not expected_in_compressed:
            if qa_pair.category in [QACategory.IIN_EXTRACTION, QACategory.MONEY_EXTRACTION, QACategory.DATE_EXTRACTION]:
                error_type = ErrorType.L1_DATA_LOST
                severity = "CRITICAL"
            else:
                error_type = ErrorType.CONTEXT_LOST
                severity = "HIGH"
        elif self._is_numeric_drift(qa_pair, compressed_answer):
            error_type = ErrorType.NUMERIC_DRIFT
            severity = "CRITICAL"
        elif self._is_entity_swap(qa_pair, compressed_answer):
            error_type = ErrorType.ENTITY_SWAPPED
            severity = "HIGH"
        else:
            error_type = ErrorType.SEMANTIC_DRIFT
            severity = "MEDIUM"
        
        self._error_counter += 1
        error = FaithfulnessError(
            error_id=f"FAITH-{self._error_counter:04d}",
            qa_pair_id=qa_pair.id,
            error_type=error_type,
            severity=severity,
            original_answer=qa_pair.expected_answer,
            compressed_answer=compressed_answer,
            expected_answer=qa_pair.expected_answer,
            description=f"Answer mismatch for {qa_pair.category.value}",
            metadata={
                "question": qa_pair.question,
                "category": qa_pair.category.value,
                "answer_type": qa_pair.answer_type.value,
            },
        )
        
        self.errors.append(error)
        return error
    
    def _is_numeric_drift(self, qa_pair: QAPair, compressed_answer: str) -> bool:
        """Проверка на numeric drift."""
        if qa_pair.answer_type.value != "numeric":
            return False
        
        try:
            expected = float(qa_pair.expected_answer)
            actual = float(compressed_answer)
            
            # Допуск 5%
            tolerance = expected * 0.05
            return abs(expected - actual) > tolerance
            
        except (ValueError, TypeError):
            return False
    
    def _is_entity_swap(self, qa_pair: QAPair, compressed_answer: str) -> bool:
        """Проверка на swap сущностей."""
        # Проверяем есть ли в ответе другая сущность того же типа
        if qa_pair.category == QACategory.IIN_EXTRACTION:
            return len(compressed_answer) == 12 and compressed_answer.isdigit()
        elif qa_pair.category == QACategory.DATE_EXTRACTION:
            return "." in compressed_answer and len(compressed_answer) == 10
        elif qa_pair.category == QACategory.MONEY_EXTRACTION:
            return any(c.isdigit() for c in compressed_answer)
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики ошибок.
        
        Returns:
            Словарь со статистикой
        """
        if not self.errors:
            return {
                "total_errors": 0,
                "errors_by_type": {},
                "errors_by_severity": {},
                "errors_by_category": {},
                "faithfulness_score": 1.0,
            }
        
        # По типам
        by_type = {}
        for error in self.errors:
            etype = error.error_type.value
            by_type[etype] = by_type.get(etype, 0) + 1
        
        # По критичности
        by_severity = {}
        for error in self.errors:
            sev = error.severity
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        # По категориям
        by_category = {}
        for error in self.errors:
            cat = error.metadata.get("category", "unknown") if error.metadata else "unknown"
            by_category[cat] = by_category.get(cat, 0) + 1
        
        # Faithfulness score
        total_qa = len(self.golden_set.qa_pairs)
        faithfulness = 1.0 - (len(self.errors) / total_qa)
        
        return {
            "total_errors": len(self.errors),
            "errors_by_type": by_type,
            "errors_by_severity": by_severity,
            "errors_by_category": by_category,
            "faithfulness_score": round(faithfulness, 3),
            "critical_errors": by_severity.get("CRITICAL", 0),
            "high_errors": by_severity.get("HIGH", 0),
        }
    
    def get_recommendations(self) -> List[Dict[str, str]]:
        """
        Получение рекомендаций по улучшению.
        
        Returns:
            Список рекомендаций
        """
        stats = self.get_statistics()
        recommendations = []
        
        # L1 Data Lost
        if stats["errors_by_type"].get("l1_data_lost", 0) > 0:
            recommendations.append({
                "priority": "CRITICAL",
                "area": "L1 Retention",
                "issue": f"{stats['errors_by_type']['l1_data_lost']} критичных данных потеряно",
                "fix": "Усилить L1 retention в OptimizationEngine. Проверить что ИИН/БИН/даты/суммы всегда сохраняются.",
                "estimated_impact": "+2-3% faithfulness",
            })
        
        # Numeric Drift
        if stats["errors_by_type"].get("numeric_drift", 0) > 0:
            recommendations.append({
                "priority": "CRITICAL",
                "area": "Numeric Invariants",
                "issue": f"{stats['errors_by_type']['numeric_drift']} чисел изменилось",
                "fix": "Добавить Chernoff верификацию для всех числовых данных. Использовать exact match для L1 чисел.",
                "estimated_impact": "+1-2% faithfulness",
            })
        
        # Entity Swapped
        if stats["errors_by_type"].get("entity_swapped", 0) > 0:
            recommendations.append({
                "priority": "HIGH",
                "area": "Entity Resolution",
                "issue": f"{stats['errors_by_type']['entity_swapped']} сущностей перепутано",
                "fix": "Улучшить NER для различения сущностей. Добавить entity linking в Question-Aware.",
                "estimated_impact": "+1% faithfulness",
            })
        
        # Context Lost
        if stats["errors_by_type"].get("context_lost", 0) > 0:
            recommendations.append({
                "priority": "HIGH",
                "area": "Context Preservation",
                "issue": f"{stats['errors_by_type']['context_lost']} контекстов утеряно",
                "fix": "Увеличить target_budget для Question-Aware compression. Добавить context-aware ranking.",
                "estimated_impact": "+1-2% faithfulness",
            })
        
        # Semantic Drift
        if stats["errors_by_type"].get("semantic_drift", 0) > 0:
            recommendations.append({
                "priority": "MEDIUM",
                "area": "Semantic Preservation",
                "issue": f"{stats['errors_by_type']['semantic_drift']} смысловых изменений",
                "fix": "Использовать BERTScore для валидации сжатия. Добавить NLI entailment check.",
                "estimated_impact": "+0.5-1% faithfulness",
            })
        
        # Сортировка по приоритету
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        recommendations.sort(key=lambda r: priority_order.get(r["priority"], 99))
        
        return recommendations
    
    def export_report(self, path: str = "faithfulness_error_report.json"):
        """
        Экспорт отчёта об ошибках.
        
        Args:
            path: Путь к файлу
        """
        report = {
            "version": "1.3.0",
            "total_errors": len(self.errors),
            "statistics": self.get_statistics(),
            "recommendations": self.get_recommendations(),
            "errors": [e.to_dict() for e in self.errors],
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)


def analyze_faithfulness(
    compression_func,
    qa_func,
) -> Dict[str, Any]:
    """
    Полный анализ faithfulness.
    
    Args:
        compression_func: Функция сжатия (context) -> compressed_context
        qa_func: Функция QA (context, question) -> answer
        
    Returns:
        Отчёт с метриками и рекомендациями
    """
    analyzer = FaithfulnessAnalyzer()
    golden_set = analyzer.golden_set
    
    # Прогон всех QA пар
    for qa_pair in golden_set.qa_pairs:
        compressed = compression_func(qa_pair.context)
        answer = qa_func(compressed, qa_pair.question)
        
        analyzer.analyze_qa_pair(qa_pair, compressed, answer)
    
    # Отчёт
    stats = analyzer.get_statistics()
    recommendations = analyzer.get_recommendations()
    
    return {
        "faithfulness_score": stats["faithfulness_score"],
        "total_errors": stats["total_errors"],
        "critical_errors": stats["critical_errors"],
        "recommendations": recommendations,
    }
