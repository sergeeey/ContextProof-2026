"""
Question-Aware Compression — умное сжатие с учётом вопроса пользователя.

Inspired by LongLLMLingua (Microsoft, 2024):
- Question-aware hierarchical compression
- Reorder mechanism (решение "lost in the middle")
- Multi-level compression (document → paragraph → sentence)

Применение для CCBM:
- L0.5: Question relevance scoring для L4 спанов
- Reorder: Критичные данные (L1) всегда в начало
- Budget-aware: Приоритет релевантным вопросу спанам
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import cast

from ccbm.analyzer import CriticalityLevel, Span

logger = logging.getLogger(__name__)


@dataclass
class RankedSpan:
    """Спан с рангом релевантности."""
    span: Span
    relevance_score: float  # 0.0 - 1.0
    position_bonus: float   # Бонус за позицию (начало текста важнее)
    final_score: float = 0.0

    def __post_init__(self):
        self.final_score = self.relevance_score * 0.7 + self.position_bonus * 0.3


class QuestionAwareCompressor:
    """
    Question-aware компрессор для CCBM.

    Алгоритм:
    1. Ранжирование спанов по релевантности к вопросу
    2. Переупорядочивание (L1 → начало, релевантные → выше)
    3. Сжатие с учётом бюджета и приоритетов
    """

    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Инициализация.

        Args:
            model_name: Модель для semantic similarity
        """
        self.model_name = model_name
        self._model = None
        self._tokenizer = None

    @property
    def model(self):
        """Ленивая загрузка модели."""
        if self._model is None:
            if os.getenv("CCBM_ENABLE_SEMANTIC_MODEL", "0") != "1":
                self._model = "fallback"
                return self._model
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Загружена модель для question-aware: {self.model_name}")
            except Exception as e:
                logger.warning(
                    f"Sentence-transformers недоступен ({e}). Используем fallback (keyword matching)"
                )
                self._model = "fallback"
        return self._model

    def rank_spans_by_question(
        self,
        spans: list[Span],
        question: str,
    ) -> list[RankedSpan]:
        """
        Ранжирование спанов по релевантности к вопросу.

        Args:
            spans: Список спанов от CriticalityAnalyzer
            question: Вопрос пользователя

        Returns:
            Отсортированный список RankedSpan
        """
        if not spans:
            return []

        ranked = []

        # Вычисляем релевантность для каждого спана
        for i, span in enumerate(spans):
            relevance = self._compute_relevance(span.text, question)
            position_bonus = 1.0 / (1.0 + i * 0.1)  # Чем ближе к началу, тем выше бонус

            ranked_span = RankedSpan(
                span=span,
                relevance_score=relevance,
                position_bonus=position_bonus,
            )
            ranked.append(ranked_span)

        # Сортировка по final_score (убывание)
        ranked.sort(key=lambda r: r.final_score, reverse=True)

        return ranked

    def reorder_and_compress(
        self,
        ranked_spans: list[RankedSpan],
        target_budget: int = 4000,
    ) -> tuple[str, dict]:
        """
        Переупорядочивание и сжатие.

        Алгоритм:
        1. L1 спаны (критичные) → всегда в начало
        2. Релевантные вопросу → выше в приоритете
        3. Сжатие L4 с учётом бюджета

        Args:
            ranked_spans: Ранжированные спаны
            target_budget: Целевой бюджет токенов

        Returns:
            (сжатый текст, метаданные)
        """
        # Разделение по уровням
        l1_spans = [r for r in ranked_spans if r.span.level == CriticalityLevel.L1]
        l2_spans = [r for r in ranked_spans if r.span.level == CriticalityLevel.L2]
        l3_spans = [r for r in ranked_spans if r.span.level == CriticalityLevel.L3]
        l4_spans = [r for r in ranked_spans if r.span.level == CriticalityLevel.L4]

        # 1. L1 всегда в начало (критичные данные)
        result_spans: list[Span | str] = [r.span for r in l1_spans]

        # 2. L2 (юридические) → следующие
        result_spans.extend([r.span for r in l2_spans])

        # 3. L3 (PII) → маскируем или сохраняем
        result_spans.extend([r.span for r in l3_spans])

        # 4. L4 (контекст) → с учётом релевантности и бюджета
        current_length = 0
        for item in result_spans:
            current_length += len(item.text) if isinstance(item, Span) else len(item)

        # Сортируем L4 по релевантности
        l4_spans.sort(key=lambda r: r.final_score, reverse=True)

        for ranked in l4_spans:
            if current_length >= target_budget:
                break

            span_text = ranked.span.text

            # Если спан не влезает полностью → сжимаем
            if current_length + len(span_text) > target_budget:
                # Сжимаем пропорционально релевантности
                keep_ratio = min(1.0, ranked.relevance_score)
                truncated = span_text[:int(len(span_text) * keep_ratio)]
                result_spans.append(truncated)
                current_length += len(truncated)
            else:
                result_spans.append(span_text)
                current_length += len(span_text)

        # Сборка итогового текста
        compressed_text = " ".join(
            s if isinstance(s, str) else s.text
            for s in result_spans
        )

        metadata = {
            "question_aware": True,
            "l1_preserved": len(l1_spans),
            "l2_preserved": len(l2_spans),
            "l3_preserved": len(l3_spans),
            "l4_compressed": len(l4_spans),
            "total_spans": len(result_spans),
            "compression_ratio": len("".join(r.span.text for r in ranked_spans)) / max(1, len(compressed_text)),
        }

        return compressed_text, metadata

    def _compute_relevance(self, text: str, question: str) -> float:
        """
        Вычисление релевантности текста к вопросу.

        Args:
            text: Текст спана
            question: Вопрос

        Returns:
            Релевантность (0.0 - 1.0)
        """
        if not text or not question:
            return 0.0

        # Fallback: keyword matching
        if self.model == "fallback":
            return self._keyword_relevance(text, question)

        # Semantic similarity
        try:
            from sentence_transformers import util

            embeddings = self.model.encode([text, question], convert_to_tensor=True)
            similarity = util.cos_sim(embeddings[0], embeddings[1]).item()

            return max(0.0, min(1.0, cast(float, similarity)))

        except Exception as e:
            logger.warning(f"Ошибка semantic similarity: {e}")
            return self._keyword_relevance(text, question)

    @staticmethod
    def _keyword_relevance(text: str, question: str) -> float:
        """
        Keyword-based релевантность (fallback).

        Args:
            text: Текст спана
            question: Вопрос

        Returns:
            Релевантность (0.0 - 1.0)
        """
        text_lower = text.lower()
        question_words = set(question.lower().split())

        matches = sum(1 for word in question_words if word in text_lower)
        return matches / max(1, len(question_words))


@dataclass
class CompressionConfig:
    """Конфигурация question-aware сжатия."""
    target_budget: int = 4000
    preserve_l1: bool = True
    reorder_enabled: bool = True
    relevance_threshold: float = 0.3  # Минимальная релевантность для сохранения
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "target_budget": self.target_budget,
            "preserve_l1": self.preserve_l1,
            "reorder_enabled": self.reorder_enabled,
            "relevance_threshold": self.relevance_threshold,
            "model_name": self.model_name,
        }


def compress_with_question(
    spans: list[Span],
    question: str,
    config: CompressionConfig | None = None,
) -> tuple[str, dict]:
    """
    Сжатие с учётом вопроса.

    Args:
        spans: Список спанов от CriticalityAnalyzer
        question: Вопрос пользователя
        config: Конфигурация

    Returns:
        (сжатый текст, метаданные)
    """
    if config is None:
        config = CompressionConfig()

    compressor = QuestionAwareCompressor(model_name=config.model_name)

    # Ранжирование
    ranked = compressor.rank_spans_by_question(spans, question)

    # Переупорядочивание и сжатие
    return compressor.reorder_and_compress(ranked, config.target_budget)
