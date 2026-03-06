"""
LLMLingua Integration — production сжатие контекста для CCBM.

Интеграция с Microsoft LLMLingua для умного сжатия промптов.
https://github.com/microsoft/LLMLingua

Поддерживаемые методы:
- LLMLingua-2: Token-level compression
- LongLLMLingua: Document-level compression
- LoPace: Lossless compression
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, cast

try:
    from llmlingua import PromptCompressor
    LLMLINGUA_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    PromptCompressor = Any
    LLMLINGUA_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class CompressionResult:
    """Результат сжатия через LLMLingua."""
    original_text: str
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    method: str
    metadata: dict[str, Any] | None = None

    @property
    def tokens_saved(self) -> int:
        """Количество сохранённых токенов."""
        return self.original_tokens - self.compressed_tokens

    @property
    def savings_percent(self) -> float:
        """Процент сэкономленных токенов."""
        if self.original_tokens == 0:
            return 0.0
        return (self.tokens_saved / self.original_tokens) * 100

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "original_text": self.original_text,
            "compressed_text": self.compressed_text,
            "original_tokens": self.original_tokens,
            "compressed_tokens": self.compressed_tokens,
            "compression_ratio": self.compression_ratio,
            "method": self.method,
            "tokens_saved": self.tokens_saved,
            "savings_percent": self.savings_percent,
            "metadata": self.metadata or {},
        }


class LLMLinguaCompressor:
    """
    Обёртка для LLMLingua PromptCompressor.

    Поддерживает:
    - LLMLingua-2 (быстрое сжатие)
    - LongLLMLingua (для длинных документов)
    - Кастомные настройки сжатия
    """

    def __init__(
        self,
        model_name: str = "microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
        device: str = "cpu",
    ):
        """
        Инициализация компрессора.

        Args:
            model_name: Модель для сжатия
            device: Устройство (cpu/cuda)
        """
        self.model_name = model_name
        self.device = device
        self._compressor: PromptCompressor | None = None

    @property
    def compressor(self) -> PromptCompressor:
        """Ленивая инициализация компрессора."""
        if self._compressor is None:
            if not LLMLINGUA_AVAILABLE:
                raise RuntimeError(
                    "llmlingua is not installed. Install with: pip install 'ccbm[compression]'"
                )
            logger.info(f"Инициализация LLMLingua: {self.model_name}")
            self._compressor = PromptCompressor(
                model_name=self.model_name,
                model_device=self.device,
            )
        return self._compressor

    def compress(
        self,
        text: str,
        target_token: int = 300,
        instruction: str = "",
        context: str = "",
        rank_method: str = "llmlingua2",
        additional_compress_kwargs: dict | None = None,
    ) -> CompressionResult:
        """
        Сжатие текста через LLMLingua.

        Args:
            text: Текст для сжатия
            target_token: Целевое количество токенов
            instruction: Инструкция для модели
            context: Дополнительный контекст
            rank_method: Метод ранжирования (llmlingua2/longllmlingua)
            additional_compress_kwargs: Дополнительные параметры

        Returns:
            CompressionResult с результатами
        """
        try:
            # Сжатие
            compressed = self.compress_prompt(
                texts=[text],
                target_token=target_token,
                instruction=instruction,
                context=context,
                rank_method=rank_method,
                **(additional_compress_kwargs or {}),
            )

            compressed_text = compressed.get("compressed_prompt", "")

            # Оценка токенов (приблизительно)
            original_tokens = self._estimate_tokens(text)
            compressed_tokens = self._estimate_tokens(compressed_text)

            return CompressionResult(
                original_text=text,
                compressed_text=compressed_text,
                original_tokens=original_tokens,
                compressed_tokens=compressed_tokens,
                compression_ratio=original_tokens / compressed_tokens if compressed_tokens > 0 else 1.0,
                method=rank_method,
                metadata={
                    "model": self.model_name,
                    "target_token": target_token,
                    "instruction": instruction,
                },
            )

        except Exception as e:
            logger.error(f"Ошибка сжатия LLMLingua: {e}")
            # Fallback на базовое сжатие
            return self._fallback_compress(text)

    def compress_prompt(
        self,
        texts: list[str],
        target_token: int = 300,
        instruction: str = "",
        context: str = "",
        rank_method: str = "llmlingua2",
        **kwargs,
    ) -> dict[str, Any]:
        """
        Сжатие промпта через LLMLingua.

        Args:
            texts: Список текстов для сжатия
            target_token: Целевое количество токенов
            instruction: Инструкция
            context: Контекст
            rank_method: Метод ранжирования

        Returns:
            Dict с compressed_prompt и другой информацией
        """
        return cast(dict[str, Any], self.compressor.compress_prompt(
            texts,
            instruction=instruction,
            context=context,
            ratio=target_token / sum(self._estimate_tokens(t) for t in texts) if texts else 0.5,
            **kwargs,
        ))

    def compress_long(
        self,
        text: str,
        question: str = "",
        instruction: str = "",
    ) -> CompressionResult:
        """
        Сжатие длинного документа через LongLLMLingua.

        Args:
            text: Длинный текст
            question: Вопрос для контекста
            instruction: Инструкция

        Returns:
            CompressionResult
        """
        try:
            compressed = self.compressor.compress_long(
                context=text,
                question=question,
                instruction=instruction,
            )

            compressed_text = compressed.get("compressed_prompt", "")

            original_tokens = self._estimate_tokens(text)
            compressed_tokens = self._estimate_tokens(compressed_text)

            return CompressionResult(
                original_text=text,
                compressed_text=compressed_text,
                original_tokens=original_tokens,
                compressed_tokens=compressed_tokens,
                compression_ratio=original_tokens / compressed_tokens if compressed_tokens > 0 else 1.0,
                method="longllmlingua",
                metadata={
                    "model": self.model_name,
                    "question": question,
                    "instruction": instruction,
                },
            )

        except Exception as e:
            logger.error(f"Ошибка LongLLMLingua: {e}")
            return self._fallback_compress(text)

    def _fallback_compress(self, text: str) -> CompressionResult:
        """
        Базовое сжатие при ошибке LLMLingua.

        Args:
            text: Текст для сжатия

        Returns:
            CompressionResult
        """
        # Простая эвристика: удаление лишних пробелов, сокращение
        compressed = " ".join(text.split())

        if len(compressed) > 500:
            sentences = compressed.split('.')
            compressed = '. '.join(sentences[:5]) + '.'

        original_tokens = self._estimate_tokens(text)
        compressed_tokens = self._estimate_tokens(compressed)

        return CompressionResult(
            original_text=text,
            compressed_text=compressed,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=original_tokens / compressed_tokens if compressed_tokens > 0 else 1.0,
            method="fallback",
            metadata={"reason": "LLMLingua unavailable"},
        )

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """
        Приблизительная оценка количества токенов.

        Для русского/казахского: ~1.5 токена на слово

        Args:
            text: Текст

        Returns:
            Примерное количество токенов
        """
        words = len(text.split())
        # Для кириллицы коэффициент больше
        return int(words * 1.5)


@dataclass
class LLMLinguaConfig:
    """Конфигурация для LLMLingua."""
    model_name: str = "microsoft/llmlingua-2-xlm-roberta-large-meetingbank"
    device: str = "cpu"
    target_token: int = 300
    rank_method: str = "llmlingua2"
    instruction: str = ""
    context: str = ""

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "target_token": self.target_token,
            "rank_method": self.rank_method,
            "instruction": self.instruction,
            "context": self.context,
        }


def create_compressor(config: LLMLinguaConfig | None = None) -> LLMLinguaCompressor:
    """
    Создание компрессора с конфигурацией.

    Args:
        config: Конфигурация

    Returns:
        LLMLinguaCompressor
    """
    if config is None:
        config = LLMLinguaConfig()

    return LLMLinguaCompressor(
        model_name=config.model_name,
        device=config.device,
    )
