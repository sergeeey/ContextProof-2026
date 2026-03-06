"""
QA Faithfulness Golden Set — тесты на сохранение ответов при сжатии.

Содержит:
- 20-30 QA пар вопрос-ответ
- NLI entailment тесты
- Числовые инварианты
- Фактовые инварианты
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class QACategory(Enum):
    """Категории QA тестов."""
    IIN_EXTRACTION = "iin_extraction"
    DATE_EXTRACTION = "date_extraction"
    MONEY_EXTRACTION = "money_extraction"
    COMPANY_NAME = "company_name"
    CONTRACT_DETAILS = "contract_details"
    LEGAL_CLAUSE = "legal_clause"
    PII_DETECTION = "pii_detection"
    NUMERIC_INVARIANT = "numeric_invariant"
    FACTUAL_INVARIANT = "factual_invariant"
    MULTI_HOP = "multi_hop"


class AnswerType(Enum):
    """Типы ответов."""
    EXACT = "exact"  # Точное совпадение
    CONTAINS = "contains"  # Содержит ответ
    ENTAILMENT = "entailment"  # Логическое следование
    NUMERIC = "numeric"  # Числовой ответ (с допуском)


@dataclass
class QAPair:
    """Пара вопрос-ответ для Golden Set."""
    id: str
    category: QACategory
    context: str
    question: str
    expected_answer: str
    answer_type: AnswerType
    tolerance: float = 0.0  # Для числовых ответов
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        """Сериализация в словарь."""
        return {
            "id": self.id,
            "category": self.category.value,
            "context": self.context,
            "question": self.question,
            "expected_answer": self.expected_answer,
            "answer_type": self.answer_type.value,
            "tolerance": self.tolerance,
            "metadata": self.metadata or {},
        }


@dataclass
class AdversarialTest:
    """Adversarial тест для long-context."""
    id: str
    test_type: str  # lost_in_the_middle, permutation, hard_negative
    context: str
    question: str
    expected_answer: str
    difficulty: str  # EASY, MEDIUM, HARD
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        """Сериализация в словарь."""
        return {
            "id": self.id,
            "test_type": self.test_type,
            "context": self.context,
            "question": self.question,
            "expected_answer": self.expected_answer,
            "difficulty": self.difficulty,
            "metadata": self.metadata or {},
        }


class QAGoldenSet:
    """
    Golden Set для QA Faithfulness тестирования.
    
    Содержит:
    - 30 QA пар
    - 10 Adversarial тестов
    """
    
    def __init__(self):
        """Инициализация Golden Set."""
        self.qa_pairs: List[QAPair] = []
        self.adversarial_tests: List[AdversarialTest] = []
        self._load_default()
    
    def _load_default(self):
        """Загрузка стандартного набора."""
        # ==================== QA PAIRS ====================
        
        # IIN Extraction (5 тестов)
        self.qa_pairs.extend([
            QAPair(
                id="QA-001",
                category=QACategory.IIN_EXTRACTION,
                context="ИИН сотрудника 950101300038 указан в договоре.",
                question="Какой ИИН указан в договоре?",
                expected_answer="950101300038",
                answer_type=AnswerType.EXACT,
            ),
            QAPair(
                id="QA-002",
                category=QACategory.IIN_EXTRACTION,
                context="Физическое лицо имеет ИИН 850315400123.",
                question="Назовите ИИН физического лица.",
                expected_answer="850315400123",
                answer_type=AnswerType.EXACT,
            ),
            QAPair(
                id="QA-003",
                category=QACategory.IIN_EXTRACTION,
                context="В базе данных: Иванов И.И. (ИИН: 750101300038), Петров П.П. (ИИН: 650202400047).",
                question="Какой ИИН у Иванова И.И.?",
                expected_answer="750101300038",
                answer_type=AnswerType.EXACT,
            ),
            QAPair(
                id="QA-004",
                category=QACategory.IIN_EXTRACTION,
                context="Договор заключен между ТОО Альфа (БИН 010140000012) и физическим лицом (ИИН 900101500056).",
                question="Какой ИИН у физического лица?",
                expected_answer="900101500056",
                answer_type=AnswerType.EXACT,
            ),
            QAPair(
                id="QA-005",
                category=QACategory.IIN_EXTRACTION,
                context="Сотрудники: 1) Ахметов А.А. ИИН 880101600067, 2) Смирнов С.С. ИИН 770202700078.",
                question="Назовите ИИН Ахметова А.А.",
                expected_answer="880101600067",
                answer_type=AnswerType.EXACT,
            ),
        ])
        
        # Money Extraction (5 тестов)
        self.qa_pairs.extend([
            QAPair(
                id="QA-006",
                category=QACategory.MONEY_EXTRACTION,
                context="Договор на сумму 100000 KZT заключен 15.03.2026.",
                question="Какая сумма указана в договоре?",
                expected_answer="100000",
                answer_type=AnswerType.NUMERIC,
                tolerance=0.0,
            ),
            QAPair(
                id="QA-007",
                category=QACategory.MONEY_EXTRACTION,
                context="Заработная плата составляет 500000 тенге в месяц.",
                question="Какова заработная плата?",
                expected_answer="500000",
                answer_type=AnswerType.NUMERIC,
            ),
            QAPair(
                id="QA-008",
                category=QACategory.MONEY_EXTRACTION,
                context="Кредит выдан на сумму 5000000 KZT под 15% годовых.",
                question="Какова сумма кредита?",
                expected_answer="5000000",
                answer_type=AnswerType.NUMERIC,
            ),
            QAPair(
                id="QA-009",
                category=QACategory.MONEY_EXTRACTION,
                context="Штраф в размере 250000 тенге наложен на компанию.",
                question="Каков размер штрафа?",
                expected_answer="250000",
                answer_type=AnswerType.NUMERIC,
            ),
            QAPair(
                id="QA-010",
                category=QACategory.MONEY_EXTRACTION,
                context="Инвестиции составили $1000000 (один миллион долларов).",
                question="Какова сумма инвестиций в долларах?",
                expected_answer="1000000",
                answer_type=AnswerType.NUMERIC,
            ),
        ])
        
        # Date Extraction (5 тестов)
        self.qa_pairs.extend([
            QAPair(
                id="QA-011",
                category=QACategory.DATE_EXTRACTION,
                context="Договор заключен 15.03.2026 и действует до 31.12.2026.",
                question="Когда заключен договор?",
                expected_answer="15.03.2026",
                answer_type=AnswerType.EXACT,
            ),
            QAPair(
                id="QA-012",
                category=QACategory.DATE_EXTRACTION,
                context="Сотрудник принят на работу 01.02.2025.",
                question="Когда сотрудник принят на работу?",
                expected_answer="01.02.2025",
                answer_type=AnswerType.EXACT,
            ),
            QAPair(
                id="QA-013",
                category=QACategory.DATE_EXTRACTION,
                context="Дата рождения: 20.05.1990, место рождения: г. Алматы.",
                question="Когда родился сотрудник?",
                expected_answer="20.05.1990",
                answer_type=AnswerType.EXACT,
            ),
            QAPair(
                id="QA-014",
                category=QACategory.DATE_EXTRACTION,
                context="Платеж должен быть произведен не позднее 30.06.2026.",
                question="До какой даты должен быть произведен платеж?",
                expected_answer="30.06.2026",
                answer_type=AnswerType.EXACT,
            ),
            QAPair(
                id="QA-015",
                category=QACategory.DATE_EXTRACTION,
                context="Отпуск предоставлен с 01.07.2026 по 14.07.2026.",
                question="Когда начинается отпуск?",
                expected_answer="01.07.2026",
                answer_type=AnswerType.EXACT,
            ),
        ])
        
        # Company Name (5 тестов)
        self.qa_pairs.extend([
            QAPair(
                id="QA-016",
                category=QACategory.COMPANY_NAME,
                context="Договор заключен между ТОО Альфа и ТОО Бета.",
                question="Назовите первую компанию в договоре.",
                expected_answer="ТОО Альфа",
                answer_type=AnswerType.EXACT,
            ),
            QAPair(
                id="QA-017",
                category=QACategory.COMPANY_NAME,
                context="Заказчик: АО Казахтелеком, Исполнитель: ТОО Казатомпром.",
                question="Кто является заказчиком?",
                expected_answer="АО Казахтелеком",
                answer_type=AnswerType.EXACT,
            ),
            QAPair(
                id="QA-018",
                category=QACategory.COMPANY_NAME,
                context="Банк-эмитент: АО Народный Банк Казахстана.",
                question="Назовите банк-эмитент.",
                expected_answer="АО Народный Банк Казахстана",
                answer_type=AnswerType.EXACT,
            ),
            QAPair(
                id="QA-019",
                category=QACategory.COMPANY_NAME,
                context="Компания-работодатель: ТОО КазМунайГаз.",
                question="Кто является работодателем?",
                expected_answer="ТОО КазМунайГаз",
                answer_type=AnswerType.EXACT,
            ),
            QAPair(
                id="QA-020",
                category=QACategory.COMPANY_NAME,
                context="Поставщик: ИП Иванов И.И., Покупатель: ТОО Сатурн.",
                question="Кто является поставщиком?",
                expected_answer="ИП Иванов И.И.",
                answer_type=AnswerType.EXACT,
            ),
        ])
        
        # Numeric Invariant (5 тестов)
        self.qa_pairs.extend([
            QAPair(
                id="QA-021",
                category=QACategory.NUMERIC_INVARIANT,
                context="Сумма договора: 100000 KZT, НДС 12%: 12000 KZT, Итого: 112000 KZT.",
                question="Какова итоговая сумма с НДС?",
                expected_answer="112000",
                answer_type=AnswerType.NUMERIC,
            ),
            QAPair(
                id="QA-022",
                category=QACategory.NUMERIC_INVARIANT,
                context="Количество сотрудников: 150 человек, из них инженеры: 50 человек.",
                question="Сколько всего сотрудников?",
                expected_answer="150",
                answer_type=AnswerType.NUMERIC,
            ),
            QAPair(
                id="QA-023",
                category=QACategory.NUMERIC_INVARIANT,
                context="Площадь помещения: 200 кв.м, арендная ставка: 5000 тенге/кв.м, итого: 1000000 тенге.",
                question="Какова итоговая арендная плата?",
                expected_answer="1000000",
                answer_type=AnswerType.NUMERIC,
            ),
            QAPair(
                id="QA-024",
                category=QACategory.NUMERIC_INVARIANT,
                context="Кредит 10000000 тенге на 5 лет под 15% годовых.",
                question="На какой срок выдан кредит (в годах)?",
                expected_answer="5",
                answer_type=AnswerType.NUMERIC,
            ),
            QAPair(
                id="QA-025",
                category=QACategory.NUMERIC_INVARIANT,
                context="Температура: +25°C, влажность: 60%, давление: 760 мм рт.ст.",
                question="Какова температура?",
                expected_answer="25",
                answer_type=AnswerType.NUMERIC,
            ),
        ])
        
        # Multi-hop reasoning (5 тестов)
        self.qa_pairs.extend([
            QAPair(
                id="QA-026",
                category=QACategory.MULTI_HOP,
                context="Иванов И.И. (ИИН 750101300038) работает в ТОО Альфа с 01.02.2025. Зарплата: 500000 тенге.",
                question="Где работает Иванов И.И.?",
                expected_answer="ТОО Альфа",
                answer_type=AnswerType.EXACT,
            ),
            QAPair(
                id="QA-027",
                category=QACategory.MULTI_HOP,
                context="ТОО Бета (БИН 010140000012) заключило договор с ТОО Альфа на сумму 1000000 KZT 15.03.2026.",
                question="Какова сумма договора с ТОО Бета?",
                expected_answer="1000000",
                answer_type=AnswerType.NUMERIC,
            ),
            QAPair(
                id="QA-028",
                category=QACategory.MULTI_HOP,
                context="Сотрудник Ахметов А.А. (ИИН 880101600067) принят 01.07.2025 на должность инженера.",
                question="Когда принят Ахметов А.А.?",
                expected_answer="01.07.2025",
                answer_type=AnswerType.EXACT,
            ),
            QAPair(
                id="QA-029",
                category=QACategory.MULTI_HOP,
                context="Компания ТОО Сатурн (БИН 020250000023) получила кредит 50000000 тенге 01.01.2026.",
                question="Какую сумму получила компания ТОО Сатурн?",
                expected_answer="50000000",
                answer_type=AnswerType.NUMERIC,
            ),
            QAPair(
                id="QA-030",
                category=QACategory.MULTI_HOP,
                context="Договор №123 от 15.03.2026 между ТОО Альфа и ТОО Бета на сумму 100000 KZT.",
                question="Когда заключен договор №123?",
                expected_answer="15.03.2026",
                answer_type=AnswerType.EXACT,
            ),
        ])
        
        # ==================== ADVERSARIAL TESTS ====================
        
        # Lost in the middle (3 теста)
        self.adversarial_tests.extend([
            AdversarialTest(
                id="ADV-001",
                test_type="lost_in_the_middle",
                context="Начало документа. ИИН первого сотрудника 950101300038. " + " ".join([f"Служебная информация {i}." for i in range(50)]) + " Конец документа.",
                question="Какой ИИН у первого сотрудника?",
                expected_answer="950101300038",
                difficulty="HARD",
            ),
            AdversarialTest(
                id="ADV-002",
                test_type="lost_in_the_middle",
                context="Договор от 15.03.2026. " + " ".join([f"Параграф {i}." for i in range(100)]) + " Сумма договора: 5000000 KZT. Конец.",
                question="Какова сумма договора?",
                expected_answer="5000000",
                difficulty="HARD",
            ),
            AdversarialTest(
                id="ADV-003",
                test_type="lost_in_the_middle",
                context="Список сотрудников: " + " ".join([f"Сотрудник {i}." for i in range(200)]) + " ИИН ключевого сотрудника: 850315400123. Конец списка.",
                question="Какой ИИН у ключевого сотрудника?",
                expected_answer="850315400123",
                difficulty="HARD",
            ),
        ])
        
        # Permutation (3 теста)
        self.adversarial_tests.extend([
            AdversarialTest(
                id="ADV-004",
                test_type="permutation",
                context="Иванов И.И. имеет ИИН 750101300038 и зарплату 500000 тенге. Петров П.П. имеет ИИН 650202400047 и зарплату 600000 тенге.",
                question="Какой ИИН у Иванова И.И.?",
                expected_answer="750101300038",
                difficulty="MEDIUM",
                metadata={"permutation_risk": "high"},
            ),
            AdversarialTest(
                id="ADV-005",
                test_type="permutation",
                context="ТОО Альфа (БИН 010140000012) и ТОО Бета (БИН 020250000023) заключили договор. Альфа платит 1000000, Бета платит 2000000.",
                question="Какой БИН у ТОО Альфа?",
                expected_answer="010140000012",
                difficulty="MEDIUM",
            ),
            AdversarialTest(
                id="ADV-006",
                test_type="permutation",
                context="Договор №123 от 15.03.2026, Договор №456 от 20.04.2026, Договор №789 от 25.05.2026.",
                question="Когда заключен Договор №456?",
                expected_answer="20.04.2026",
                difficulty="MEDIUM",
            ),
        ])
        
        # Hard negative (4 теста)
        self.adversarial_tests.extend([
            AdversarialTest(
                id="ADV-007",
                test_type="hard_negative",
                context="ИИН 950101300038 принадлежит Иванову И.И. (не 950101300039!). БИН 010140000012 принадлежит ТОО Альфа.",
                question="Какой ИИН у Иванова И.И.?",
                expected_answer="950101300038",
                difficulty="HARD",
                metadata={"distractor": "950101300039"},
            ),
            AdversarialTest(
                id="ADV-008",
                test_type="hard_negative",
                context="Сумма договора 100000 KZT (не 1000000 KZT!). НДС 12000 KZT.",
                question="Какова сумма договора?",
                expected_answer="100000",
                difficulty="HARD",
                metadata={"distractor": "1000000"},
            ),
            AdversarialTest(
                id="ADV-009",
                test_type="hard_negative",
                context="Дата заключения 15.03.2026 (не 15.03.2025 и не 15.03.2027!).",
                question="Когда заключен договор?",
                expected_answer="15.03.2026",
                difficulty="HARD",
                metadata={"distractors": ["15.03.2025", "15.03.2027"]},
            ),
            AdversarialTest(
                id="ADV-010",
                test_type="hard_negative",
                context="Иванов (ИИН 750101300038) и Петров (ИИН 750101300038 - ошибка, правильно 650202400047).",
                question="Какой ИИН у Петрова?",
                expected_answer="650202400047",
                difficulty="HARD",
                metadata={"distractor": "750101300038", "correction": "650202400047"},
            ),
        ])
    
    def get_qa_pairs(self, category: Optional[QACategory] = None) -> List[QAPair]:
        """
        Получение QA пар с фильтрацией.
        
        Args:
            category: Фильтр по категории
            
        Returns:
            Список QA пар
        """
        if category:
            return [qa for qa in self.qa_pairs if qa.category == category]
        return self.qa_pairs
    
    def get_adversarial_tests(self, test_type: Optional[str] = None) -> List[AdversarialTest]:
        """
        Получение adversarial тестов с фильтрацией.
        
        Args:
            test_type: Фильтр по типу теста
            
        Returns:
            Список adversarial тестов
        """
        if test_type:
            return [t for t in self.adversarial_tests if t.test_type == test_type]
        return self.adversarial_tests
    
    def export_to_json(self, path: str = "golden_set_qa.json"):
        """
        Экспорт в JSON.
        
        Args:
            path: Путь к файлу
        """
        data = {
            "version": "1.3.0",
            "total_qa_pairs": len(self.qa_pairs),
            "total_adversarial_tests": len(self.adversarial_tests),
            "qa_pairs": [qa.to_dict() for qa in self.qa_pairs],
            "adversarial_tests": [t.to_dict() for t in self.adversarial_tests],
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики Golden Set.
        
        Returns:
            Словарь со статистикой
        """
        by_category = {}
        for qa in self.qa_pairs:
            cat = qa.category.value
            by_category[cat] = by_category.get(cat, 0) + 1
        
        by_type = {}
        for test in self.adversarial_tests:
            t = test.test_type
            by_type[t] = by_type.get(t, 0) + 1
        
        return {
            "total_qa_pairs": len(self.qa_pairs),
            "total_adversarial_tests": len(self.adversarial_tests),
            "qa_by_category": by_category,
            "adversarial_by_type": by_type,
            "difficulty_distribution": {
                "EASY": sum(1 for t in self.adversarial_tests if t.difficulty == "EASY"),
                "MEDIUM": sum(1 for t in self.adversarial_tests if t.difficulty == "MEDIUM"),
                "HARD": sum(1 for t in self.adversarial_tests if t.difficulty == "HARD"),
            },
        }


# Global instance
_golden_set: Optional[QAGoldenSet] = None


def get_golden_set() -> QAGoldenSet:
    """Получение глобального Golden Set."""
    global _golden_set
    if _golden_set is None:
        _golden_set = QAGoldenSet()
    return _golden_set
