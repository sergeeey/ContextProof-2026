"""
Тесты для Question-Aware и Two-Stage Compression.
"""

import pytest
from ccbm.analyzer import Span, CriticalityLevel
from ccbm.optimizer.question_aware import (
    QuestionAwareCompressor,
    RankedSpan,
    compress_with_question,
    CompressionConfig,
)
from ccbm.optimizer.two_stage import (
    TwoStageCompressor,
    TwoStageResult,
    compress_two_stage,
    TwoStageConfig,
)
from ccbm.quality.agentic_metrics import (
    AgenticCompressionEvaluator,
    AgenticMetrics,
    evaluate_agentic_compression,
)


class TestQuestionAwareCompressor:
    """Тесты для Question-Aware Compression."""

    def test_compressor_creation(self):
        """Создание компрессора."""
        compressor = QuestionAwareCompressor()
        
        assert compressor.model_name == "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        assert compressor._model is None  # Ленивая загрузка

    def test_rank_spans_by_question(self):
        """Ранжирование спанов по вопросу."""
        compressor = QuestionAwareCompressor()
        
        spans = [
            Span(text="ИИН 950101300038", start=0, end=15, level=CriticalityLevel.L1, confidence=0.95),
            Span(text="Договор заключён 15.03.2026", start=16, end=45, level=CriticalityLevel.L4, confidence=1.0),
        ]
        
        question = "Какой ИИН указан?"
        ranked = compressor.rank_spans_by_question(spans, question)
        
        assert len(ranked) == 2
        assert isinstance(ranked[0], RankedSpan)
        
        # Первый спан должен быть более релевантен (ИИН в вопросе)
        assert ranked[0].span.text == "ИИН 950101300038"

    def test_reorder_and_compress(self):
        """Переупорядочивание и сжатие."""
        compressor = QuestionAwareCompressor()
        
        spans = [
            Span(text="ИИН 950101300038", start=0, end=15, level=CriticalityLevel.L1, confidence=0.95),
            Span(text="Контекстный текст", start=16, end=35, level=CriticalityLevel.L4, confidence=1.0),
        ]
        
        ranked = [
            RankedSpan(span=s, relevance_score=0.9, position_bonus=0.8)
            for s in spans
        ]
        
        compressed, metadata = compressor.reorder_and_compress(ranked, target_budget=100)
        
        assert "ИИН 950101300038" in compressed
        assert metadata["l1_preserved"] == 1

    def test_compress_with_question(self):
        """Сжатие с учётом вопроса."""
        spans = [
            Span(text="ИИН 950101300038", start=0, end=15, level=CriticalityLevel.L1, confidence=0.95),
            Span(text="Договор на сумму 100000 KZT", start=16, end=45, level=CriticalityLevel.L4, confidence=1.0),
        ]
        
        question = "Какой ИИН?"
        compressed, metadata = compress_with_question(spans, question)
        
        assert len(compressed) > 0
        assert metadata["question_aware"] is True

    def test_keyword_relevance(self):
        """Keyword-based релевантность."""
        relevance = QuestionAwareCompressor._keyword_relevance(
            "ИИН сотрудника 950101300038",
            "ИИН номер",
        )
        
        assert 0.0 <= relevance <= 1.0
        assert relevance > 0.0  # Должно быть совпадение (ИИН)


class TestTwoStageCompressor:
    """Тесты для Two-Stage Compression."""

    def test_compressor_creation(self):
        """Создание компрессора."""
        compressor = TwoStageCompressor()
        
        assert compressor.aggressive is False
        assert compressor._optimizer is not None

    def test_compress(self):
        """Двухэтапное сжатие."""
        compressor = TwoStageCompressor()
        
        text = "ИИН 950101300038.   Договор    заключён 15.03.2026."
        result = compressor.compress(text)
        
        assert isinstance(result, TwoStageResult)
        assert result.original_text == text
        assert result.stage1_reduction >= 0  # Может быть 0 если нет дубликатов
        assert result.compression_ratio >= 1.0

    def test_coarse_filter(self):
        """Coarse-grain filter."""
        compressor = TwoStageCompressor()
        
        text = "ИИН   950101300038.    Множественные     пробелы."
        filtered = compressor._coarse_filter(text)
        
        # Должно удалить множественные пробелы
        assert "  " not in filtered or filtered.count("  ") < text.count("  ")

    def test_remove_stop_words(self):
        """Удаление stop words."""
        compressor = TwoStageCompressor(aggressive=True)
        
        text = "И это был очень важный документ и договор"
        filtered = compressor._remove_stop_words(text)
        
        # Stop words должны быть удалены
        assert len(filtered.split()) < len(text.split())

    def test_aggressive_mode(self):
        """Агрессивный режим."""
        compressor = TwoStageCompressor(aggressive=True)
        
        text = "Email: user@example.com, URL: https://example.com"
        result = compressor.compress(text)
        
        # В агрессивном режиме email/url должны быть заменены
        assert "[EMAIL]" in result.compressed_text or "[URL]" in result.compressed_text

    def test_compress_with_config(self):
        """Сжатие с конфигурацией."""
        config = TwoStageConfig(
            aggressive=True,
            target_budget=100,
        )
        
        text = "Длинный текст " * 20
        result = compress_two_stage(text, config=config)
        
        assert isinstance(result, TwoStageResult)
        assert result.metadata["aggressive_mode"] is True


class TestAgenticMetrics:
    """Тесты для Agentic Compression Metrics."""

    def test_evaluator_creation(self):
        """Создание оценщика."""
        evaluator = AgenticCompressionEvaluator()
        assert evaluator is not None

    def test_evaluate_qa(self):
        """Оценка QA задачи."""
        evaluator = AgenticCompressionEvaluator()
        
        metrics = evaluator.evaluate(
            original_text="Контекст для вопроса",
            compressed_text="Контекст",
            task_output_original="Ответ: 42",
            task_output_compressed="Ответ: 42",
            task_type="qa",
        )
        
        assert isinstance(metrics, AgenticMetrics)
        assert 0.0 <= metrics.overall_score <= 1.0
        assert metrics.compression_ratio >= 1.0

    def test_qa_retention_exact_match(self):
        """QA Retention через Exact Match."""
        evaluator = AgenticCompressionEvaluator()
        
        score = evaluator._qa_retention("Ответ 42", "Ответ 42")
        assert score == 1.0
        
        score = evaluator._qa_retention("Ответ 42", "Ответ 43")
        assert score < 1.0

    def test_code_retention(self):
        """Code Retention."""
        evaluator = AgenticCompressionEvaluator()
        
        original = "def hello():\n    return 'world'"
        compressed = "def hello():\n    return 'world'"
        
        score = evaluator._code_retention(original, compressed)
        assert score == 1.0

    def test_erank_computation(self):
        """ERank Score."""
        evaluator = AgenticCompressionEvaluator()
        
        original = "Важный текст с информацией"
        compressed = "Важный текст"
        
        score = evaluator._compute_erank(original, compressed)
        assert 0.0 <= score <= 1.0

    def test_evaluate_agentic_compression(self):
        """Полная оценка."""
        metrics = evaluate_agentic_compression(
            original="Длинный контекст для задачи",
            compressed="Короткий контекст",
            task_output_original="Правильный ответ",
            task_output_compressed="Правильный ответ",
            task_type="qa",
        )
        
        assert isinstance(metrics, AgenticMetrics)
        assert metrics.overall_score >= 0.0


class TestIntegration:
    """Интеграционные тесты."""

    def test_question_aware_workflow(self):
        """Question-aware workflow."""
        spans = [
            Span(text="ИИН 950101300038", start=0, end=15, level=CriticalityLevel.L1, confidence=0.95),
            Span(text="Договор на сумму 100000 KZT от 15.03.2026", start=16, end=55, level=CriticalityLevel.L4, confidence=1.0),
        ]
        
        question = "Какой ИИН указан в договоре?"
        
        # Question-aware сжатие
        compressed, metadata = compress_with_question(spans, question)
        
        # ИИН должен быть сохранён
        assert "950101300038" in compressed
        assert metadata["question_aware"] is True

    def test_two_stage_workflow(self):
        """Two-stage workflow."""
        text = "ИИН   950101300038.    Договор    от 15.03.2026."
        
        # Two-stage сжатие
        result = compress_two_stage(text)
        
        assert result.compression_ratio >= 1.0
        assert result.stage1_reduction >= 0

    def test_combined_compression(self):
        """Комбинированное сжатие (Question-aware + Two-stage)."""
        spans = [
            Span(text="ИИН 950101300038", start=0, end=15, level=CriticalityLevel.L1, confidence=0.95),
            Span(text="Договор на сумму 100000 KZT", start=16, end=45, level=CriticalityLevel.L4, confidence=1.0),
        ]
        
        question = "Какой ИИН?"
        
        # 1. Question-aware ранжирование
        compressor = QuestionAwareCompressor()
        ranked = compressor.rank_spans_by_question(spans, question)
        
        # 2. Two-stage сжатие
        text = " ".join(s.span.text for s in ranked)
        result = compress_two_stage(text)
        
        assert result.compression_ratio >= 1.0
