"""
Agentic Compression Metrics — метрики из ACBench (ICML 2025).

Метрики для оценки влияния сжатия на агентские способности:
- ERank (Energy Rank) — "энергия" сжатия
- Context Retention Score — сохранение контекста для задач
- Workflow Retention — сохранение workflow generation
- Tool Use Preservation — сохранение function calling

Применение для CCBM:
- Extended validation suite для Quality Gates
- Тесты на workflow generation (LangChain-совместимые)
- Task-specific retention metrics
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class AgenticMetrics:
    """Метрики агентского сжатия."""
    # Основные метрики
    compression_ratio: float
    bert_score: float

    # ACBench метрики
    erank_score: float  # Energy Rank (0-1)
    retention_score: float  # Context Retention (0-1)
    workflow_retention: float  # Workflow preservation (0-1)
    tool_use_preservation: float  # Function calling preservation (0-1)

    # Итоговая оценка
    overall_score: float

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "compression_ratio": self.compression_ratio,
            "bert_score": self.bert_score,
            "erank_score": self.erank_score,
            "retention_score": self.retention_score,
            "workflow_retention": self.workflow_retention,
            "tool_use_preservation": self.tool_use_preservation,
            "overall_score": self.overall_score,
        }


class AgenticCompressionEvaluator:
    """
    Оценщик агентского сжатия (ACBench-inspired).

    Методы:
    - compute_erank: Energy Rank метрика
    - compute_retention: Context Retention Score
    - evaluate_workflow: Workflow Retention
    - evaluate_tool_use: Tool Use Preservation
    """

    def __init__(self):
        """Инициализация оценщика."""
        pass

    def evaluate(
        self,
        original_text: str,
        compressed_text: str,
        task_output_original: str,
        task_output_compressed: str,
        task_type: str = "qa",
    ) -> AgenticMetrics:
        """
        Полная оценка агентского сжатия.

        Args:
            original_text: Исходный контекст
            compressed_text: Сжатый контекст
            task_output_original: Результат задачи с оригинальным контекстом
            task_output_compressed: Результат задачи со сжатым контекстом
            task_type: Тип задачи (qa/code/rag/workflow)

        Returns:
            AgenticMetrics
        """
        compression_ratio = len(original_text) / max(1, len(compressed_text))

        # BERT Score (семантическое сходство)
        bert_score = self._compute_bert_score(original_text, compressed_text)

        # ERank Score
        erank_score = self._compute_erank(original_text, compressed_text)

        # Context Retention Score
        retention_score = self._compute_retention(
            task_output_original,
            task_output_compressed,
            task_type,
        )

        # Workflow Retention (для workflow задач)
        workflow_retention = self._evaluate_workflow(
            task_output_original,
            task_output_compressed,
        ) if task_type == "workflow" else 1.0

        # Tool Use Preservation (для tool use задач)
        tool_use_preservation = self._evaluate_tool_use(
            task_output_original,
            task_output_compressed,
        ) if task_type in ["tool_use", "code"] else 1.0

        # Итоговая оценка (взвешенная средняя)
        overall_score = (
            bert_score * 0.3 +
            retention_score * 0.4 +
            erank_score * 0.1 +
            workflow_retention * 0.1 +
            tool_use_preservation * 0.1
        )

        return AgenticMetrics(
            compression_ratio=compression_ratio,
            bert_score=bert_score,
            erank_score=erank_score,
            retention_score=retention_score,
            workflow_retention=workflow_retention,
            tool_use_preservation=tool_use_preservation,
            overall_score=overall_score,
        )

    def _compute_bert_score(self, text1: str, text2: str) -> float:
        """
        Вычисление BERT Score (F1).

        Args:
            text1: Текст 1
            text2: Текст 2

        Returns:
            BERT Score (0-1)
        """
        try:
            from bert_score import score

            P, R, F1 = score(
                [text1],
                [text2],
                lang="en",
                verbose=False,
            )

            return float(F1.mean())

        except ImportError:
            logger.warning("bert_score не установлен. Используем fallback.")
            return self._simple_similarity(text1, text2)

    def _compute_erank(self, original: str, compressed: str) -> float:
        """
        Energy Rank метрика.

        Идея: "энергия" информации в сжатом тексте.
        Вычисляется через распределение важности токенов.

        Args:
            original: Исходный текст
            compressed: Сжатый текст

        Returns:
            ERank Score (0-1)
        """
        # Упрощённая версия: через TF-IDF важность
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer

            vectorizer = TfidfVectorizer()
            tfidf = vectorizer.fit_transform([original, compressed])

            # Сравниваем распределение важности
            original_tfidf = tfidf[0].toarray().flatten()
            compressed_tfidf = tfidf[1].toarray().flatten()

            # Cosine similarity между распределениями
            similarity = np.dot(original_tfidf, compressed_tfidf) / (
                np.linalg.norm(original_tfidf) * np.linalg.norm(compressed_tfidf) + 1e-8
            )

            return float(similarity)

        except ImportError:
            logger.warning("scikit-learn не установлен. Используем fallback.")
            return 0.5  # Neutral score

    def _compute_retention(
        self,
        output_original: str,
        output_compressed: str,
        task_type: str,
    ) -> float:
        """
        Context Retention Score.

        Для разных задач:
        - QA: Exact Match / F1
        - Code: Pass@k
        - RAG: Recall@k

        Args:
            output_original: Вывод с оригинальным контекстом
            output_compressed: Вывод со сжатым контекстом
            task_type: Тип задачи

        Returns:
            Retention Score (0-1)
        """
        if task_type == "qa":
            return self._qa_retention(output_original, output_compressed)
        elif task_type == "code":
            return self._code_retention(output_original, output_compressed)
        elif task_type == "rag":
            return self._rag_retention(output_original, output_compressed)
        else:
            return self._simple_similarity(output_original, output_compressed)

    def _qa_retention(self, original: str, compressed: str) -> float:
        """
        QA Retention через Exact Match.

        Args:
            original: Оригинальный ответ
            compressed: Сжатый ответ

        Returns:
            Retention Score (0-1)
        """
        # Exact Match
        if original.strip().lower() == compressed.strip().lower():
            return 1.0

        # Partial Match (F1-like)
        original_words = set(original.lower().split())
        compressed_words = set(compressed.lower().split())

        intersection = original_words & compressed_words
        union = original_words | compressed_words

        return len(intersection) / max(1, len(union))

    def _code_retention(self, original: str, compressed: str) -> float:
        """
        Code Retention через синтаксическую эквивалентность.

        Args:
            original: Оригинальный код
            compressed: Сжатый код

        Returns:
            Retention Score (0-1)
        """
        # Простая эвристика: сравнение ключевых элементов
        import re

        # Извлекаем функции/классы
        original_funcs = set(re.findall(r'def\s+(\w+)', original))
        compressed_funcs = set(re.findall(r'def\s+(\w+)', compressed))

        if not original_funcs:
            return self._simple_similarity(original, compressed)

        return len(original_funcs & compressed_funcs) / max(1, len(original_funcs))

    def _rag_retention(self, original: str, compressed: str) -> float:
        """
        RAG Retention через Recall.

        Args:
            original: Оригинальные retrieved документы
            compressed: Сжатые retrieved документы

        Returns:
            Recall@k (0-1)
        """
        # Упрощённо: через overlap ключевых сущностей
        original_entities = set(self._extract_entities(original))
        compressed_entities = set(self._extract_entities(compressed))

        if not original_entities:
            return 1.0

        return len(original_entities & compressed_entities) / max(1, len(original_entities))

    def _evaluate_workflow(self, original: str, compressed: str) -> float:
        """
        Workflow Retention для workflow generation задач.

        Args:
            original: Оригинальный workflow
            compressed: Сжатый workflow

        Returns:
            Retention Score (0-1)
        """
        # Сравниваем ключевые шаги workflow
        original_steps = self._extract_workflow_steps(original)
        compressed_steps = self._extract_workflow_steps(compressed)

        if not original_steps:
            return 1.0

        matches = sum(1 for step in compressed_steps if step in original_steps)
        return matches / max(1, len(original_steps))

    def _evaluate_tool_use(self, original: str, compressed: str) -> float:
        """
        Tool Use Preservation для function calling.

        Args:
            original: Оригинальный вызов функции
            compressed: Сжатый вызов функции

        Returns:
            Preservation Score (0-1)
        """
        # Сравниваем имена функций и аргументы
        import re

        original_funcs = re.findall(r'(\w+)\((.*?)\)', original, re.DOTALL)
        compressed_funcs = re.findall(r'(\w+)\((.*?)\)', compressed, re.DOTALL)

        if not original_funcs:
            return 1.0

        # Сравниваем имена функций
        original_names = {f[0] for f in original_funcs}
        compressed_names = {f[0] for f in compressed_funcs}

        return len(original_names & compressed_names) / max(1, len(original_names))

    @staticmethod
    def _simple_similarity(text1: str, text2: str) -> float:
        """Простая similarity через Jaccard."""
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())

        intersection = set1 & set2
        union = set1 | set2

        return len(intersection) / max(1, len(union))

    @staticmethod
    def _extract_entities(text: str) -> list[str]:
        """Извлечение сущностей (упрощённо)."""
        import re

        # Имена, даты, числа
        patterns = [
            r'\b[A-Z][a-z]+\b',  # Имена
            r'\b\d{1,2}\.\d{1,2}\.\d{4}\b',  # Даты
            r'\b\d+[.,]?\d*\b',  # Числа
        ]

        entities = []
        for pattern in patterns:
            entities.extend(re.findall(pattern, text))

        return entities

    @staticmethod
    def _extract_workflow_steps(text: str) -> list[str]:
        """Извлечение шагов workflow."""
        import re

        # Нумерованные списки, bullet points
        patterns = [
            r'\d+\.\s*(.+?)(?:\n|$)',
            r'[-*]\s*(.+?)(?:\n|$)',
        ]

        steps = []
        for pattern in patterns:
            steps.extend(re.findall(pattern, text))

        return steps


def evaluate_agentic_compression(
    original: str,
    compressed: str,
    task_output_original: str,
    task_output_compressed: str,
    task_type: str = "qa",
) -> AgenticMetrics:
    """
    Оценка агентского сжатия.

    Args:
        original: Исходный контекст
        compressed: Сжатый контекст
        task_output_original: Результат задачи с оригиналом
        task_output_compressed: Результат задачи со сжатым
        task_type: Тип задачи

    Returns:
        AgenticMetrics
    """
    evaluator = AgenticCompressionEvaluator()

    return evaluator.evaluate(
        original,
        compressed,
        task_output_original,
        task_output_compressed,
        task_type,
    )
