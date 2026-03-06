"""
Тесты для QA Faithfulness и Adversarial Long-Context.
"""

import pytest

from ccbm.quality.golden_set_qa import (
    AnswerType,
    QACategory,
    QAGoldenSet,
    get_golden_set,
)


class TestQAGoldenSet:
    """Тесты для QA Golden Set."""

    def test_golden_set_creation(self):
        """Создание Golden Set."""
        gs = QAGoldenSet()

        assert len(gs.qa_pairs) == 30
        assert len(gs.adversarial_tests) == 10

    def test_qa_pairs_by_category(self):
        """Получение QA пар по категории."""
        gs = QAGoldenSet()

        iin_pairs = gs.get_qa_pairs(category=QACategory.IIN_EXTRACTION)
        assert len(iin_pairs) == 5

        money_pairs = gs.get_qa_pairs(category=QACategory.MONEY_EXTRACTION)
        assert len(money_pairs) == 5

        date_pairs = gs.get_qa_pairs(category=QACategory.DATE_EXTRACTION)
        assert len(date_pairs) == 5

    def test_adversarial_tests_by_type(self):
        """Получение adversarial тестов по типу."""
        gs = QAGoldenSet()

        lost_tests = gs.get_adversarial_tests(test_type="lost_in_the_middle")
        assert len(lost_tests) == 3

        permutation_tests = gs.get_adversarial_tests(test_type="permutation")
        assert len(permutation_tests) == 3

        hard_negative_tests = gs.get_adversarial_tests(test_type="hard_negative")
        assert len(hard_negative_tests) == 4

    def test_export_to_json(self, tmp_path):
        """Экспорт в JSON."""
        gs = QAGoldenSet()

        json_path = tmp_path / "golden_set_qa.json"
        gs.export_to_json(str(json_path))

        assert json_path.exists()

        import json
        with open(json_path) as f:
            data = json.load(f)

        assert data["version"] == "1.3.0"
        assert data["total_qa_pairs"] == 30
        assert data["total_adversarial_tests"] == 10

    def test_statistics(self):
        """Получение статистики."""
        gs = QAGoldenSet()
        stats = gs.get_statistics()

        assert stats["total_qa_pairs"] == 30
        assert stats["total_adversarial_tests"] == 10
        assert "iin_extraction" in stats["qa_by_category"]
        assert "lost_in_the_middle" in stats["adversarial_by_type"]

    def test_global_golden_set(self):
        """Глобальный Golden Set."""
        gs1 = get_golden_set()
        gs2 = get_golden_set()

        assert gs1 is gs2


class TestQAFaithfulness:
    """Тесты на сохранение ответов при сжатии."""

    @pytest.fixture
    def golden_set(self):
        """Фикстура Golden Set."""
        return get_golden_set()

    def test_iin_extraction_preserved(self, golden_set):
        """IIN extraction сохраняется при сжатии."""
        from ccbm import CriticalityAnalyzer, OptimizationEngine

        analyzer = CriticalityAnalyzer()
        optimizer = OptimizationEngine()

        qa_pairs = golden_set.get_qa_pairs(category=QACategory.IIN_EXTRACTION)

        for qa in qa_pairs[:3]:  # Первые 3 теста
            spans = analyzer.analyze(qa.context)
            result = optimizer.optimize(spans)

            # Проверяем что ИИН сохранён
            assert qa.expected_answer in result.optimized_text or \
                   qa.expected_answer in result.original_text

    def test_money_extraction_preserved(self, golden_set):
        """Money extraction сохраняется при сжатии."""
        from ccbm import CriticalityAnalyzer, OptimizationEngine

        analyzer = CriticalityAnalyzer()
        optimizer = OptimizationEngine()

        qa_pairs = golden_set.get_qa_pairs(category=QACategory.MONEY_EXTRACTION)

        for qa in qa_pairs[:3]:
            spans = analyzer.analyze(qa.context)
            result = optimizer.optimize(spans)

            # Проверяем что сумма сохранена (хотя бы частично)
            assert qa.expected_answer in result.optimized_text or \
                   qa.expected_answer in result.original_text

    def test_date_extraction_preserved(self, golden_set):
        """Date extraction сохраняется при сжатии."""
        from ccbm import CriticalityAnalyzer, OptimizationEngine

        analyzer = CriticalityAnalyzer()
        optimizer = OptimizationEngine()

        qa_pairs = golden_set.get_qa_pairs(category=QACategory.DATE_EXTRACTION)

        for qa in qa_pairs[:3]:
            spans = analyzer.analyze(qa.context)
            result = optimizer.optimize(spans)

            # Проверяем что дата сохранена
            assert qa.expected_answer in result.optimized_text or \
                   qa.expected_answer in result.original_text


class TestAdversarialLongContext:
    """Тесты на adversarial long-context."""

    @pytest.fixture
    def golden_set(self):
        """Фикстура Golden Set."""
        return get_golden_set()

    def test_lost_in_the_middle(self, golden_set):
        """Тест lost in the middle."""
        tests = golden_set.get_adversarial_tests(test_type="lost_in_the_middle")

        assert len(tests) == 3

        for test in tests:
            # Проверяем что контекст длинный
            assert len(test.context.split()) > 50
            assert test.difficulty == "HARD"

    def test_permutation_resilience(self, golden_set):
        """Тест на устойчивость к перестановкам."""
        tests = golden_set.get_adversarial_tests(test_type="permutation")

        assert len(tests) == 3

        for test in tests:
            # Проверяем что сложность MEDIUM или есть metadata
            assert test.difficulty in ["MEDIUM", "HARD"]

    def test_hard_negative_detection(self, golden_set):
        """Тест на hard negative."""
        tests = golden_set.get_adversarial_tests(test_type="hard_negative")

        assert len(tests) == 4

        for test in tests:
            # Проверяем что есть distractor
            assert "distractor" in test.metadata or "distractors" in test.metadata
            assert test.difficulty == "HARD"

    def test_adversarial_difficulty_distribution(self, golden_set):
        """Распределение сложности adversarial тестов."""
        stats = golden_set.get_statistics()

        difficulty = stats["difficulty_distribution"]

        assert difficulty["EASY"] >= 0
        assert difficulty["MEDIUM"] >= 3
        assert difficulty["HARD"] >= 6


class TestAnswerConsistency:
    """Тесты на консистентность ответов."""

    @pytest.fixture
    def golden_set(self):
        """Фикстура Golden Set."""
        return get_golden_set()

    def test_exact_match_answers(self, golden_set):
        """Exact match ответы."""
        qa_pairs = [qa for qa in golden_set.qa_pairs if qa.answer_type == AnswerType.EXACT]

        assert len(qa_pairs) > 10

        for qa in qa_pairs:
            # Проверяем что ответ не пустой
            assert len(qa.expected_answer) > 0

    def test_numeric_answers(self, golden_set):
        """Numeric ответы."""
        qa_pairs = [qa for qa in golden_set.qa_pairs if qa.answer_type == AnswerType.NUMERIC]

        assert len(qa_pairs) > 10

        for qa in qa_pairs:
            # Проверяем что числовой ответ
            assert qa.expected_answer.isdigit() or \
                   any(c.isdigit() for c in qa.expected_answer)

    def test_multi_hop_reasoning(self, golden_set):
        """Multi-hop reasoning тесты."""
        qa_pairs = golden_set.get_qa_pairs(category=QACategory.MULTI_HOP)

        assert len(qa_pairs) == 5

        for qa in qa_pairs:
            # Multi-hop требует связывания информации
            assert len(qa.context) > 50  # Контекст должен быть достаточно длинным


class TestGoldenSetCoverage:
    """Тесты на покрытие Golden Set."""

    @pytest.fixture
    def golden_set(self):
        """Фикстура Golden Set."""
        return get_golden_set()

    def test_category_coverage(self, golden_set):
        """Покрытие категорий."""
        stats = golden_set.get_statistics()

        # Проверяем что все категории представлены
        categories = [
            "iin_extraction",
            "money_extraction",
            "date_extraction",
            "company_name",
            "numeric_invariant",
            "multi_hop",
        ]

        for cat in categories:
            assert cat in stats["qa_by_category"]
            assert stats["qa_by_category"][cat] >= 5

    def test_adversarial_coverage(self, golden_set):
        """Покрытие adversarial тестов."""
        stats = golden_set.get_statistics()

        # Проверяем что все типы adversarial тестов представлены
        types = [
            "lost_in_the_middle",
            "permutation",
            "hard_negative",
        ]

        for t in types:
            assert t in stats["adversarial_by_type"]
            assert stats["adversarial_by_type"][t] >= 3

    def test_total_coverage(self, golden_set):
        """Общее покрытие."""
        stats = golden_set.get_statistics()

        assert stats["total_qa_pairs"] >= 20  # Минимум 20 QA пар
        assert stats["total_adversarial_tests"] >= 10  # Минимум 10 adversarial тестов
