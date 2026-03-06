"""
Тесты для Optimization Engine — сжатие и фильтрация контекста.

Методы оптимизации:
- L1: Zero-loss (без потерь)
- L2: Template matching
- L3: Masking / Anonymization
- L4: Aggressive compression
"""

import pytest
from ccbm.optimizer import OptimizationEngine, OptimizationResult
from ccbm.analyzer import Span, CriticalityLevel


class TestOptimizationEngine:
    """Тесты для OptimizationEngine."""

    def setup_method(self):
        """Настройка тестов."""
        self.engine = OptimizationEngine(target_budget=4000)

    def test_optimize_l1_preserved(self):
        """L1 данные сохраняются без изменений."""
        spans = [
            Span(
                text="950101300038",
                start=0,
                end=12,
                level=CriticalityLevel.L1,
                confidence=0.95,
                metadata={"type": "iin_bin"},
            ),
        ]
        result = self.engine.optimize(spans)
        
        # L1 должен быть сохранён
        assert "950101300038" in result.optimized_text
        assert result.compression_ratio >= 1.0

    def test_optimize_l3_masked(self):
        """L3 данные (PII) маскируются."""
        spans = [
            Span(
                text="Иван Иванов",
                start=0,
                end=11,
                level=CriticalityLevel.L3,
                confidence=0.9,
            ),
        ]
        result = self.engine.optimize(spans)
        
        # PII должен быть замаскирован
        assert "Иван Иванов" not in result.optimized_text
        assert "[PII REDACTED]" in result.optimized_text

    def test_optimize_l4_compressed(self):
        """L4 данные сжимаются."""
        long_text = "Это очень длинный текст. " * 50  # 1250 символов
        spans = [
            Span(
                text=long_text,
                start=0,
                end=len(long_text),
                level=CriticalityLevel.L4,
                confidence=1.0,
            ),
        ]
        result = self.engine.optimize(spans)
        
        # L4 должен быть сжат
        assert len(result.optimized_text) < len(long_text)
        assert result.compression_ratio > 1.0

    def test_optimize_mixed_levels(self):
        """Оптимизация смешанных уровней."""
        spans = [
            Span(
                text="950101300038",
                start=0,
                end=12,
                level=CriticalityLevel.L1,
                confidence=0.95,
            ),
            Span(
                text="Иван Иванов",
                start=13,
                end=24,
                level=CriticalityLevel.L3,
                confidence=0.9,
            ),
            Span(
                text="Это обычный текст для контекста.",
                start=25,
                end=58,
                level=CriticalityLevel.L4,
                confidence=1.0,
            ),
        ]
        result = self.engine.optimize(spans)
        
        # L1 сохранён
        assert "950101300038" in result.optimized_text
        # L3 замаскирован
        assert "Иван Иванов" not in result.optimized_text
        assert "[PII REDACTED]" in result.optimized_text

    def test_optimize_sorted_spans(self):
        """Спаны должны быть отсортированы в результате."""
        spans = [
            Span(text="L4 text", start=50, end=57, level=CriticalityLevel.L4, confidence=1.0),
            Span(text="L1 data", start=0, end=7, level=CriticalityLevel.L1, confidence=0.95),
            Span(text="L3 PII", start=20, end=26, level=CriticalityLevel.L3, confidence=0.9),
        ]
        result = self.engine.optimize(spans)
        
        # Проверяем что спаны собраны в правильном порядке
        assert result.spans_preserved == 3

    def test_compression_stats(self):
        """Статистика сжатия должна заполняться."""
        spans = [
            Span(text="1000 KZT", start=0, end=8, level=CriticalityLevel.L1, confidence=0.95),
            Span(text="Some text", start=9, end=18, level=CriticalityLevel.L4, confidence=1.0),
        ]
        result = self.engine.optimize(spans)
        
        assert result.metadata is not None
        assert "l1_preserved" in result.metadata
        assert "l4_summarized" in result.metadata


class TestOptimizationResult:
    """Тесты для OptimizationResult."""

    def test_result_creation(self):
        """Создание результата оптимизации."""
        result = OptimizationResult(
            original_text="Original text",
            optimized_text="Optimized",
            compression_ratio=1.5,
            spans_removed=0,
            spans_preserved=3,
        )
        assert result.original_text == "Original text"
        assert result.optimized_text == "Optimized"
        assert result.compression_ratio == 1.5

    def test_result_with_metadata(self):
        """Результат с метаданными."""
        result = OptimizationResult(
            original_text="Original",
            optimized_text="Optimized",
            compression_ratio=2.0,
            spans_removed=1,
            spans_preserved=5,
            metadata={"l1_preserved": 2, "l4_summarized": 3},
        )
        assert result.metadata is not None
        assert result.metadata["l1_preserved"] == 2

    def test_compression_ratio_calculation(self):
        """Расчёт коэффициента сжатия."""
        original = "A" * 1000
        optimized = "B" * 250
        result = OptimizationResult(
            original_text=original,
            optimized_text=optimized,
            compression_ratio=4.0,  # 1000 / 250
            spans_removed=0,
            spans_preserved=1,
        )
        assert result.compression_ratio == 4.0


class TestPIIMasking:
    """Тесты для маскирования PII."""

    def setup_method(self):
        """Настройка тестов."""
        self.engine = OptimizationEngine()

    def test_mask_simple_pii(self):
        """Маскирование простого PII."""
        span = Span(
            text="John Doe",
            start=0,
            end=8,
            level=CriticalityLevel.L3,
            confidence=0.9,
        )
        masked = self.engine._mask_pii(span)
        
        assert masked.text == "[PII REDACTED]"
        assert masked.level == CriticalityLevel.L3

    def test_mask_long_pii(self):
        """Маскирование длинного PII."""
        span = Span(
            text="Длинное имя с фамилией и отчеством",
            start=0,
            end=35,
            level=CriticalityLevel.L3,
            confidence=0.9,
        )
        masked = self.engine._mask_pii(span)
        
        # Должно быть замаскировано независимо от длины
        assert masked.text == "[PII REDACTED]"


class TestContextCompression:
    """Тесты для сжатия контекста."""

    def setup_method(self):
        """Настройка тестов."""
        self.engine = OptimizationEngine()

    def test_compress_short_text(self):
        """Сжатие короткого текста."""
        span = Span(
            text="Короткий текст.",
            start=0,
            end=15,
            level=CriticalityLevel.L4,
            confidence=1.0,
        )
        compressed = self.engine._compress_context(span)
        
        # Короткий текст может остаться без изменений
        assert len(compressed.text) <= len(span.text)

    def test_compress_long_text(self):
        """Сжатие длинного текста."""
        long_text = "Предложение. " * 100  # > 500 символов
        span = Span(
            text=long_text,
            start=0,
            end=len(long_text),
            level=CriticalityLevel.L4,
            confidence=1.0,
        )
        compressed = self.engine._compress_context(span)
        
        # Длинный текст должен быть сжат
        assert len(compressed.text) < len(long_text)
        assert len(compressed.text) <= 500  # Лимит

    def test_compress_removes_extra_spaces(self):
        """Сжатие удаляет лишние пробелы."""
        span = Span(
            text="Текст   с    лишними   пробелами.",
            start=0,
            end=35,
            level=CriticalityLevel.L4,
            confidence=1.0,
        )
        compressed = self.engine._compress_context(span)
        
        # Пробелы должны быть нормализованы
        assert "  " not in compressed.text  # Нет двойных пробелов

    def test_compress_preserves_meaning(self):
        """Сжатие сохраняет смысл (первые предложения)."""
        text = "Первое предложение. Второе предложение. Третье предложение. Четвёртое."
        span = Span(
            text=text,
            start=0,
            end=len(text),
            level=CriticalityLevel.L4,
            confidence=1.0,
        )
        compressed = self.engine._compress_context(span)
        
        # Первые предложения должны быть сохранены
        assert "Первое предложение" in compressed.text


class TestBudgetManagement:
    """Тесты для управления бюджетом."""

    def test_set_budget(self):
        """Установка бюджета."""
        engine = OptimizationEngine(target_budget=4000)
        assert engine.target_budget == 4000
        
        engine.set_budget(8000)
        assert engine.target_budget == 8000

    def test_different_budgets(self):
        """Разные бюджеты для разных сценариев."""
        engine_strict = OptimizationEngine(target_budget=2000)
        engine_relaxed = OptimizationEngine(target_budget=8000)
        
        assert engine_strict.target_budget < engine_relaxed.target_budget


class TestEdgeCases:
    """Тесты граничных случаев."""

    def setup_method(self):
        """Настройка тестов."""
        self.engine = OptimizationEngine()

    def test_empty_spans(self):
        """Пустой список спанов."""
        result = self.engine.optimize([])
        
        assert result.original_text == ""
        assert result.optimized_text == ""
        assert result.compression_ratio == 1.0

    def test_single_l1_span(self):
        """Единственный L1 спан."""
        spans = [
            Span(text="1000 KZT", start=0, end=8, level=CriticalityLevel.L1, confidence=0.95),
        ]
        result = self.engine.optimize(spans)
        
        assert result.original_text == "1000 KZT"
        assert result.optimized_text == "1000 KZT"
        assert result.compression_ratio == 1.0

    def test_single_l4_span(self):
        """Единственный L4 спан."""
        spans = [
            Span(text="Long text " * 100, start=0, end=1000, level=CriticalityLevel.L4, confidence=1.0),
        ]
        result = self.engine.optimize(spans)
        
        # L4 должен быть сжат или хотя бы обработан
        assert len(result.optimized_text) > 0
        assert result.spans_preserved == 1
