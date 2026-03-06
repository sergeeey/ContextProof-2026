"""
Тесты для ChernoffVerifier — верификация через границы Чернова.

Адаптировано из ChernoffPy (E:\\MarkovChains\\ChernoffPy\tests\test_certified.py)
"""

import numpy as np
import pytest
from ccbm.verifier.chernoff_bound import (
    ChernoffOrder,
    ChernoffVerifier,
    DataRegularity,
    compute_certified_bound,
    effective_order,
    n_steps_for_tolerance,
    verify_convergence_order,
)


class TestChernoffOrder:
    """Тесты для класса ChernoffOrder."""

    def test_linear_method_order_1(self):
        """Линейный метод должен иметь порядок 1."""
        order = ChernoffOrder.from_method("linear")
        assert order.k == 1

    def test_crank_nicolson_order_2(self):
        """Crank-Nicolson должен иметь порядок 2."""
        order = ChernoffOrder.from_method("crank-nicolson")
        assert order.k == 2

    def test_pade22_order_4(self):
        """Padé [2/2] должен иметь порядок 4."""
        order = ChernoffOrder.from_method("pade22")
        assert order.k == 4

    def test_pade33_order_6(self):
        """Padé [3/3] должен иметь порядок 6."""
        order = ChernoffOrder.from_method("pade33")
        assert order.k == 6

    def test_quadratic_order_2(self):
        """Quadratic должен иметь порядок 2."""
        order = ChernoffOrder.from_method("quadratic")
        assert order.k == 2

    def test_unknown_defaults_to_2(self):
        """Неизвестный метод должен иметь порядок 2 по умолчанию."""
        order = ChernoffOrder.from_method("unknown_method")
        assert order.k == 2


class TestDataRegularity:
    """Тесты для класса DataRegularity."""

    def test_smooth_kf_large(self):
        """Гладкие данные должны иметь высокую регулярность."""
        reg = DataRegularity.smooth()
        assert reg.k_f >= 100

    def test_financial_kf_2(self):
        """Финансовые данные должны иметь регулярность 2."""
        reg = DataRegularity.financial()
        assert reg.k_f == 2

    def test_discontinuous_kf_0(self):
        """Разрывные данные должны иметь регулярность 0."""
        reg = DataRegularity.discontinuous()
        assert reg.k_f == 0

    def test_piecewise_kf_2(self):
        """Кусочно-гладкие данные должны иметь регулярность 2."""
        reg = DataRegularity.piecewise()
        assert reg.k_f == 2


class TestEffectiveOrder:
    """Тесты для функции effective_order."""

    def test_cn_financial_gives_2(self):
        """CN + financial = 2."""
        assert effective_order(ChernoffOrder(2, "CN"), DataRegularity.financial()) == 2

    def test_pade_financial_gives_2(self):
        """Padé + financial = 2 (ограничено регулярностью данных)."""
        assert effective_order(ChernoffOrder(4, "Padé"), DataRegularity.financial()) == 2

    def test_linear_smooth_gives_1(self):
        """Linear + smooth = 1 (ограничено методом)."""
        assert effective_order(ChernoffOrder(1, "Linear"), DataRegularity.smooth()) == 1

    def test_cn_discontinuous_gives_0(self):
        """CN + discontinuous = 0 (данные ограничивают)."""
        assert effective_order(ChernoffOrder(2, "CN"), DataRegularity.discontinuous()) == 0


class TestCertifiedBound:
    """Тесты для compute_certified_bound."""

    def test_bound_with_exact(self):
        """Граница с известным точным значением."""
        exact = 100.0
        prices = {20: 100.5, 40: 100.125, 80: 100.03125}
        bound = compute_certified_bound(
            prices=prices,
            chernoff_order=ChernoffOrder(2, "CN"),
            payoff_reg=DataRegularity.financial(),
            n_target=20,
            safety_factor=2.0,
            exact_price=exact,
        )
        assert bound.bound >= abs(prices[20] - exact)
        assert bound.is_certified is True

    def test_bound_without_exact(self):
        """Граница без точного значения (Richardson)."""
        prices = {20: 100.5, 40: 100.125, 80: 100.03125}
        bound = compute_certified_bound(
            prices=prices,
            chernoff_order=ChernoffOrder(2, "CN"),
            payoff_reg=DataRegularity.financial(),
            n_target=20,
            safety_factor=2.0,
            exact_price=None,
        )
        assert bound.bound > 0
        assert bound.is_certified is False

    def test_bound_decreases_with_n(self):
        """Граница должна уменьшаться с ростом n."""
        exact = 100.0
        prices = {20: 100.4, 40: 100.1, 80: 100.025}
        bound_20 = compute_certified_bound(prices, ChernoffOrder(2, "CN"), DataRegularity.financial(), 20, 2.0, exact)
        bound_40 = compute_certified_bound(prices, ChernoffOrder(2, "CN"), DataRegularity.financial(), 40, 2.0, exact)
        assert bound_40.bound < bound_20.bound

    def test_safety_factor(self):
        """Больший safety_factor даёт большую границу."""
        exact = 100.0
        prices = {20: 100.4, 40: 100.1, 80: 100.025}
        bound_1 = compute_certified_bound(prices, ChernoffOrder(2, "CN"), DataRegularity.financial(), 20, 1.0, exact)
        bound_3 = compute_certified_bound(prices, ChernoffOrder(2, "CN"), DataRegularity.financial(), 20, 3.0, exact)
        assert bound_3.bound > bound_1.bound


class TestChernoffVerifier:
    """Тесты для ChernoffVerifier."""

    def test_verify_perfect_data(self):
        """Верификация идеальных данных (без ошибок)."""
        verifier = ChernoffVerifier(domain="financial")
        original = np.array([100.0, 200.0, 300.0, 400.0])
        compressed = original.copy()

        bound = verifier.verify(original, compressed, "test_data")
        assert bound.bound == 0.0
        assert verifier.is_valid(bound) is True

    def test_verify_small_error(self):
        """Верификация с маленькой ошибкой."""
        verifier = ChernoffVerifier(domain="financial", safety_factor=2.0)
        original = np.array([100.0, 200.0, 300.0, 400.0])
        compressed = original + np.array([0.001, 0.001, 0.001, 0.001])

        bound = verifier.verify(original, compressed, "test_data")
        # Ошибка должна быть в пределах границы
        assert bound.bound >= 0.001

    def test_verify_large_error(self):
        """Верификация с большой ошибкой (должна быть COMPROMISED)."""
        verifier = ChernoffVerifier(domain="financial", safety_factor=2.0)
        original = np.array([100.0, 200.0, 300.0, 400.0])
        compressed = original + np.array([10.0, 10.0, 10.0, 10.0])

        bound = verifier.verify(original, compressed, "test_data")
        status = verifier.get_status(bound)
        # Большая ошибка должна быть COMPROMISED или UNVERIFIED
        assert status in ["COMPROMISED", "UNVERIFIED"]

    def test_verify_invariants(self):
        """Верификация инвариантов."""
        verifier = ChernoffVerifier(domain="financial")
        original = {"sum": 1000.0, "mean": 250.0, "count": 4.0}
        compressed = {"sum": 1000.1, "mean": 250.02, "count": 4.0}

        bounds = verifier.verify_invariants(original, compressed)

        assert "sum" in bounds
        assert "mean" in bounds
        assert "count" in bounds

        # Count должен быть идеальным
        assert bounds["count"].bound == 0.0

    def test_verify_invariants_missing(self):
        """Верификация с потерянным инвариантом."""
        verifier = ChernoffVerifier(domain="financial")
        original = {"sum": 1000.0, "mean": 250.0}
        compressed = {"sum": 1000.1}  # mean потерян

        bounds = verifier.verify_invariants(original, compressed)

        assert bounds["mean"].bound == float('inf')
        assert verifier.is_valid(bounds["mean"]) is False


class TestVerifyConvergenceOrder:
    """Тесты для verify_convergence_order."""

    def test_cn_order_2(self):
        """Проверка сходимости порядка 2."""
        exact = 1.0
        prices = {20: exact + 2 / 20**2, 40: exact + 2 / 40**2, 80: exact + 2 / 80**2}
        result = verify_convergence_order(prices, expected_order=2, exact_price=exact, tolerance=0.2)
        assert result["is_consistent"] is True
        assert result["empirical_order"] == pytest.approx(2.0, rel=0.1)

    def test_linear_order_1(self):
        """Проверка сходимости порядка 1."""
        exact = 1.0
        prices = {20: exact + 1 / 20, 40: exact + 1 / 40, 80: exact + 1 / 80}
        result = verify_convergence_order(prices, expected_order=1, exact_price=exact, tolerance=0.2)
        assert result["is_consistent"] is True
        assert result["empirical_order"] == pytest.approx(1.0, rel=0.1)

    def test_mismatch_detected(self):
        """Обнаружение несоответствия порядка."""
        exact = 1.0
        prices = {20: exact + 1 / 20, 40: exact + 1 / 40, 80: exact + 1 / 80}
        result = verify_convergence_order(prices, expected_order=2, exact_price=exact, tolerance=0.2)
        assert result["is_consistent"] is False


class TestNStepsForTolerance:
    """Тесты для n_steps_for_tolerance."""

    def test_cn_0001_gives_reasonable_n(self):
        """CN: разумное n для ошибки 0.001."""
        n = n_steps_for_tolerance(target_error=1e-3, constant_B=1.0, effective_order=2, safety_factor=2.0)
        assert 10 <= n <= 100

    def test_linear_needs_more_steps(self):
        """Linear требует больше шагов чем CN."""
        n_cn = n_steps_for_tolerance(target_error=1e-3, constant_B=1.0, effective_order=2, safety_factor=2.0)
        n_linear = n_steps_for_tolerance(target_error=1e-3, constant_B=1.0, effective_order=1, safety_factor=2.0)
        assert n_linear > n_cn

    def test_zero_order_raises(self):
        """Нулевой порядок должен вызывать ошибку."""
        with pytest.raises(ValueError):
            n_steps_for_tolerance(target_error=1e-3, constant_B=1.0, effective_order=0)
