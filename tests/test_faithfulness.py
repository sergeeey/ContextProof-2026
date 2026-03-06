"""
Тесты для Faithfulness Analyzer и Optimized Compression.
"""

import pytest
from ccbm.quality.faithfulness_analyzer import (
    FaithfulnessAnalyzer,
    ErrorType,
    analyze_faithfulness,
)
from ccbm.optimizer.faithfulness_optimized import (
    FaithfulnessOptimizedCompressor,
    compress_with_faithfulness,
)


class TestFaithfulnessAnalyzer:
    """Тесты для Faithfulness Analyzer."""

    def test_analyzer_creation(self):
        """Создание анализатора."""
        analyzer = FaithfulnessAnalyzer()
        
        assert len(analyzer.errors) == 0
        assert analyzer.golden_set is not None

    def test_analyze_qa_pair_no_error(self):
        """Анализ QA пары без ошибок."""
        analyzer = FaithfulnessAnalyzer()
        golden_set = analyzer.golden_set
        
        # Берём первую QA пару
        qa_pair = golden_set.qa_pairs[0]
        
        # "Сжимаем" без потерь (просто копируем)
        compressed_context = qa_pair.context
        compressed_answer = qa_pair.expected_answer
        
        error = analyzer.analyze_qa_pair(qa_pair, compressed_context, compressed_answer)
        
        assert error is None  # Ошибок нет

    def test_analyze_qa_pair_with_error(self):
        """Анализ QA пары с ошибкой."""
        analyzer = FaithfulnessAnalyzer()
        golden_set = analyzer.golden_set
        
        qa_pair = golden_set.qa_pairs[0]
        
        # "Сжимаем" с потерей данных
        compressed_context = "Удалено всё"
        compressed_answer = "Неизвестно"
        
        error = analyzer.analyze_qa_pair(qa_pair, compressed_context, compressed_answer)
        
        assert error is not None
        assert error.qa_pair_id == qa_pair.id
        assert error.severity in ["CRITICAL", "HIGH", "MEDIUM"]

    def test_get_statistics(self):
        """Получение статистики."""
        analyzer = FaithfulnessAnalyzer()
        golden_set = analyzer.golden_set
        
        # Прогоняем несколько QA пар с ошибками
        for qa_pair in golden_set.qa_pairs[:5]:
            analyzer.analyze_qa_pair(
                qa_pair,
                "Удалено",
                "Неизвестно",
            )
        
        stats = analyzer.get_statistics()
        
        assert stats["total_errors"] == 5
        assert "errors_by_type" in stats
        assert "errors_by_severity" in stats
        assert "faithfulness_score" in stats
        assert stats["faithfulness_score"] < 1.0

    def test_get_recommendations(self):
        """Получение рекомендаций."""
        analyzer = FaithfulnessAnalyzer()
        golden_set = analyzer.golden_set
        
        # Создаём ошибки разных типов
        for qa_pair in golden_set.qa_pairs[:10]:
            analyzer.analyze_qa_pair(
                qa_pair,
                "Удалено",
                "Неизвестно",
            )
        
        recommendations = analyzer.get_recommendations()
        
        assert len(recommendations) > 0
        
        # Проверяем что рекомендации отсортированы по приоритету
        if len(recommendations) > 1:
            priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            for i in range(len(recommendations) - 1):
                assert priority_order[recommendations[i]["priority"]] <= \
                       priority_order[recommendations[i + 1]["priority"]]

    def test_export_report(self, tmp_path):
        """Экспорт отчёта."""
        analyzer = FaithfulnessAnalyzer()
        golden_set = analyzer.golden_set
        
        # Создаём ошибки
        for qa_pair in golden_set.qa_pairs[:3]:
            analyzer.analyze_qa_pair(
                qa_pair,
                "Удалено",
                "Неизвестно",
            )
        
        report_path = tmp_path / "faithfulness_report.json"
        analyzer.export_report(str(report_path))
        
        assert report_path.exists()
        
        import json
        with open(report_path) as f:
            report = json.load(f)
        
        assert report["version"] == "1.3.0"
        assert report["total_errors"] == 3
        assert "statistics" in report
        assert "recommendations" in report


class TestFaithfulnessOptimizedCompressor:
    """Тесты для Faithfulness Optimized Compressor."""

    def test_compressor_creation(self):
        """Создание компрессора."""
        compressor = FaithfulnessOptimizedCompressor()
        
        assert compressor.l1_retention_target == 1.0
        assert compressor.numeric_tolerance == 0.0
        assert compressor.enable_nli is False
        assert compressor.enable_bertscore is False

    def test_compress_basic(self):
        """Базовое сжатие."""
        compressor = FaithfulnessOptimizedCompressor()
        
        text = "ИИН 950101300038, договор на 100000 KZT от 15.03.2026."
        
        compressed, metadata = compressor.compress(text, target_budget=100)
        
        assert len(compressed) > 0
        assert "faithfulness_score" in metadata
        assert "l1_retention_rate" in metadata
        assert "numeric_drift_rate" in metadata

    def test_l1_retention(self):
        """L1 retention."""
        compressor = FaithfulnessOptimizedCompressor(l1_retention_target=1.0)
        
        text = "ИИН 950101300038, сумма 100000 KZT."
        
        compressed, metadata = compressor.compress(text)
        
        # L1 данные должны быть сохранены
        assert "950101300038" in compressed or metadata["l1_retention_rate"] == 1.0
        assert metadata["l1_retention_rate"] >= 0.9  # Минимум 90%

    def test_numeric_drift_check(self):
        """Numeric drift check."""
        compressor = FaithfulnessOptimizedCompressor(numeric_tolerance=0.0)
        
        text = "Сумма 100000 KZT, НДС 12000 KZT."
        
        compressed, metadata = compressor.compress(text)
        
        assert "numeric_drift_rate" in metadata
        assert 0.0 <= metadata["numeric_drift_rate"] <= 1.0

    def test_faithfulness_score_computation(self):
        """Faithfulness score computation."""
        compressor = FaithfulnessOptimizedCompressor()
        
        # Проверяем формулу
        faithfulness = compressor._compute_faithfulness(
            l1_retention=1.0,
            numeric_drift=0.0,
            nli_score=0.9,
            bert_score=0.85,
        )
        
        # 0.4*1.0 + 0.3*1.0 + 0.2*0.9 + 0.1*0.85 = 0.4 + 0.3 + 0.18 + 0.085 = 0.965
        assert 0.95 <= faithfulness <= 1.0

    def test_enforce_l1_retention(self):
        """L1 retention enforcement."""
        compressor = FaithfulnessOptimizedCompressor()
        
        from ccbm.analyzer import Span, CriticalityLevel
        from ccbm.optimizer import OptimizationResult
        
        original_text = "ИИН 950101300038, текст."
        
        # Создаём результат с потерей L1
        result = OptimizationResult(
            original_text=original_text,
            optimized_text="текст",  # ИИН потерян
            compression_ratio=2.0,
            spans_removed=0,
            spans_preserved=1,
        )
        
        l1_spans = [
            Span(text="950101300038", start=0, end=12, level=CriticalityLevel.L1, confidence=0.95),
        ]
        
        improved = compressor._enforce_l1_retention(original_text, result, l1_spans)
        
        # L1 данные должны быть добавлены
        assert "950101300038" in improved.optimized_text

    def test_get_stats(self):
        """Получение статистики."""
        compressor = FaithfulnessOptimizedCompressor()
        
        # Несколько сжатий
        for i in range(5):
            compressor.compress(f"Тест {i}. ИИН 95010130003{i}.")
        
        stats = compressor.get_stats()
        
        assert stats["total_compressions"] == 5
        assert "avg_l1_retention" in stats
        assert "avg_faithfulness" in stats


class TestCompressWithFaithfulness:
    """Тесты для compress_with_faithfulness."""

    def test_quick_compress(self):
        """Быстрое сжатие."""
        text = "ИИН 950101300038, договор на 100000 KZT."
        
        compressed, metadata = compress_with_faithfulness(text)
        
        assert len(compressed) > 0
        assert "faithfulness_score" in metadata

    def test_compress_with_nli(self):
        """Сжатие с NLI."""
        text = "ИИН 950101300038."
        
        compressed, metadata = compress_with_faithfulness(
            text,
            enable_nli=True,
        )
        
        assert "nli_entailment_score" in metadata

    def test_compress_with_bertscore(self):
        """Сжатие с BERTScore."""
        text = "ИИН 950101300038."
        
        compressed, metadata = compress_with_faithfulness(
            text,
            enable_bertscore=True,
        )
        
        assert "bert_score" in metadata


class TestIntegration:
    """Интеграционные тесты."""

    def test_full_faithfulness_pipeline(self):
        """Полный pipeline faithfulness."""
        # 1. Compress
        compressor = FaithfulnessOptimizedCompressor()
        text = "ИИН 950101300038, сумма 100000 KZT, дата 15.03.2026."
        
        compressed, metadata = compressor.compress(text)
        
        # 2. Analyze
        analyzer = FaithfulnessAnalyzer()
        
        # Имитируем QA ответ
        from ccbm.quality.golden_set_qa import QAPair, QACategory, AnswerType
        
        qa_pair = QAPair(
            id="TEST-001",
            category=QACategory.IIN_EXTRACTION,
            context=text,
            question="Какой ИИН?",
            expected_answer="950101300038",
            answer_type=AnswerType.EXACT,
        )
        
        error = analyzer.analyze_qa_pair(
            qa_pair,
            compressed,
            "950101300038",  # Правильный ответ
        )
        
        # Ошибки не должно быть если L1 сохранён
        if metadata["l1_retention_rate"] == 1.0:
            assert error is None
        
        # 3. Statistics
        stats = analyzer.get_statistics()
        assert "faithfulness_score" in stats
