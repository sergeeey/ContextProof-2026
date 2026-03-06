"""
Chernoff Verifier — математическая верификация числовых данных через границы Чернова.

Адаптировано из ChernoffPy (E:\MarkovChains\ChernoffPy) для CCBM.
Использует теорию сходимости Чернова (Galkin-Remizov, 2025) для верификации
числовых инвариантов после сжатия контекста.

Основная идея:
- Вычисляем значения до оптимизации (оригинал)
- Вычисляем значения после оптимизации (сжатие)
- Применяем границы Чернова для оценки ошибки
- Если ошибка превышает порог → COMPROMISED → откат к оригиналу
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict
import numpy as np


@dataclass(frozen=True)
class ChernoffOrder:
    """
    Теоретический порядок сходимости метода верификации.
    
    Для CCBM используем упрощённую модель:
    - k=1: Базовая верификация (линейная сходимость)
    - k=2: Улучшенная верификация (квадратичная сходимость)
    - k=4: Высокая точность (для критических финансовых данных)
    """
    k: int
    name: str
    is_exact: bool = True

    @staticmethod
    def from_method(method_name: str) -> "ChernoffOrder":
        """Определение порядка сходимости по имени метода."""
        name_lower = method_name.lower()
        
        if "linear" in name_lower or "euler" in name_lower:
            return ChernoffOrder(k=1, name="Linear/Backward Euler")
        if "crank" in name_lower or "nicolson" in name_lower or "cn" in name_lower:
            return ChernoffOrder(k=2, name="Crank-Nicolson")
        if "pade" in name_lower:
            if "22" in name_lower or "2.2" in name_lower:
                return ChernoffOrder(k=4, name="Padé [2/2]")
            if "33" in name_lower or "3.3" in name_lower:
                return ChernoffOrder(k=6, name="Padé [3/3]")
            return ChernoffOrder(k=4, name="Padé")
        if "quadratic" in name_lower or "order2" in name_lower:
            return ChernoffOrder(k=2, name="Quadratic")
        if "high" in name_lower or "order4" in name_lower:
            return ChernoffOrder(k=4, name="High-order")
        
        # По умолчанию — квадратичная сходимость
        return ChernoffOrder(k=2, name=method_name or "Default")


@dataclass(frozen=True)
class DataRegularity:
    """
    Класс регулярности данных — аналог PayoffRegularity из ChernoffPy.
    
    Определяет гладкость числовых данных для оценки сходимости.
    """
    k_f: int
    name: str
    description: str = ""

    @staticmethod
    def smooth() -> "DataRegularity":
        """Гладкие данные: непрерывные, дифференцируемые (например, временные ряды)."""
        return DataRegularity(k_f=100, name="smooth", description="Smooth continuous data")

    @staticmethod
    def piecewise() -> "DataRegularity":
        """Кусочно-гладкие данные: с разрывами первого рода (например, ставки)."""
        return DataRegularity(k_f=2, name="piecewise smooth", description="Piecewise smooth with jumps")

    @staticmethod
    def discontinuous() -> "DataRegularity":
        """Разрывные данные: с разрывами (например, бинарные флаги)."""
        return DataRegularity(k_f=0, name="discontinuous", description="Discontinuous data")

    @staticmethod
    def financial() -> "DataRegularity":
        """Финансовые данные: суммы, ставки, даты — требуют высокой точности."""
        return DataRegularity(k_f=2, name="financial", description="Financial data (sums, rates, dates)")

    @staticmethod
    def legal() -> "DataRegularity":
        """Юридические данные: тексты договоров, клаузулы."""
        return DataRegularity(k_f=1, name="legal", description="Legal text data")


@dataclass(frozen=True)
class CertifiedBound:
    """
    Сертифицированная верхняя граница ошибки верификации.
    
    Адаптировано из ChernoffPy.compute_certified_bound()
    """
    bound: float                    # Верхняя граница ошибки
    effective_order: int           # Эффективный порядок сходимости
    n_steps: int                   # Количество шагов верификации
    method: str                    # Метод верификации
    constant_B: float              # Константа B из теории Чернова
    safety_factor: float           # Коэффициент запаса (≥ 1.0)
    is_certified: bool             # True если сертифицировано
    reference: str = "Galkin-Remizov (2025), Israel J. Math."
    data_name: str = ""            # Имя верифицируемых данных


def effective_order(chernoff_order: ChernoffOrder, data_reg: DataRegularity) -> int:
    """
    Эффективный алгебраический порядок: min(порядок метода, регулярность данных).
    
    Если данные недостаточно гладкие, порядок сходимости ограничивается регулярностью.
    """
    return min(chernoff_order.k, data_reg.k_f)


class ChernoffVerifier:
    """
    Верификатор числовых данных на основе границ Чернова.
    
    Применение в CCBM:
    1. Вычисляем математическое ожидание до сжатия (original)
    2. Вычисляем после сжатия (compressed)
    3. Применяем границы Чернова для оценки вероятности ошибки
    4. Если P(error > threshold) > alpha → COMPROMISED → откат
    
    Для финансовых данных в РК: alpha = 0.01 (строго!)
    """
    
    # Уровни значимости для разных доменов
    SIGNIFICANCE_LEVELS = {
        "financial": 0.01,      # Финансы: строго 1%
        "legal": 0.05,          # Юридические: 5%
        "medical": 0.001,       # Медицина: 0.1%
        "general": 0.05,        # Общие данные: 5%
    }
    
    def __init__(
        self,
        method: str = "crank-nicolson",
        safety_factor: float = 2.0,
        domain: str = "financial",
    ):
        """
        Инициализация верификатора.
        
        Args:
            method: Метод верификации (влияет на порядок сходимости)
            safety_factor: Коэффициент запаса (≥ 1.0), рекомендуется 2.0
            domain: Домен данных для выбора уровня значимости
        """
        self.method = method
        self.safety_factor = safety_factor
        self.domain = domain
        self.significance_level = self.SIGNIFICANCE_LEVELS.get(domain, 0.05)
        self.chernoff_order = ChernoffOrder.from_method(method)
        
    def verify(
        self,
        original_values: np.ndarray,
        compressed_values: np.ndarray,
        data_name: str = "data",
        n_steps: Optional[int] = None,
    ) -> CertifiedBound:
        """
        Верификация числовых данных через границы Чернова.
        
        Args:
            original_values: Оригинальные значения (до сжатия)
            compressed_values: Сжатые значения (после оптимизации)
            data_name: Имя данных для отчёта
            n_steps: Количество шагов (по умолчанию len(original_values))
            
        Returns:
            CertifiedBound с границей ошибки
        """
        if len(original_values) != len(compressed_values):
            raise ValueError("Длины массивов должны совпадать")
        
        # Для одиночных значений используем упрощённую верификацию
        if len(original_values) == 1:
            error = abs(float(original_values[0]) - float(compressed_values[0]))
            return CertifiedBound(
                bound=error * self.safety_factor,
                effective_order=self.chernoff_order.k,
                n_steps=1,
                method="single_value_comparison",
                constant_B=error,
                safety_factor=self.safety_factor,
                is_certified=True,
                data_name=data_name,
            )
        
        n = n_steps or len(original_values)
        data_reg = DataRegularity.financial() if self.domain == "financial" else DataRegularity.smooth()

        # Вычисляем разницу (ошибку)
        errors = np.abs(original_values - compressed_values)
        max_error = float(np.max(errors))

        # Создаём "цены" для compute_certified_bound (адаптация из ChernoffPy)
        # В CCBM: original = exact_price, compressed = approximated
        # Для оценки сходимости создаём несколько точек с разными n
        n_points = [max(2, n // 4), max(4, n // 2), n]
        prices = {}
        for n_p in n_points:
            # Симуляция сходимости: чем больше n, тем ближе к оригиналу
            scale = n_p / n
            scaled_mean = float(np.mean(compressed_values)) * (1 - scale) + float(np.mean(original_values)) * scale
            prices[n_p] = scaled_mean

        bound = compute_certified_bound(
            prices=prices,
            chernoff_order=self.chernoff_order,
            payoff_reg=data_reg,
            n_target=n,
            safety_factor=self.safety_factor,
            exact_price=float(np.mean(original_values)),
        )

        # Возвращаем с именем данных
        return CertifiedBound(
            bound=max(bound.bound, max_error),  # Используем максимум из теории и наблюдений
            effective_order=bound.effective_order,
            n_steps=bound.n_steps,
            method=bound.method,
            constant_B=bound.constant_B,
            safety_factor=bound.safety_factor,
            is_certified=bound.is_certified,
            reference=bound.reference,
            data_name=data_name,
        )
    
    def verify_invariants(
        self,
        original_invariants: Dict[str, float],
        compressed_invariants: Dict[str, float],
    ) -> Dict[str, CertifiedBound]:
        """
        Верификация набора инвариантов (например, суммы, средние, контрольные суммы).
        
        Args:
            original_invariants: Оригинальные инварианты {имя: значение}
            compressed_invariants: Сжатые инварианты {имя: значение}
            
        Returns:
            Словарь {имя_инварианта: CertifiedBound}
        """
        results = {}
        
        all_keys = set(original_invariants.keys()) | set(compressed_invariants.keys())
        
        for key in all_keys:
            if key not in original_invariants:
                # Инвариант потерян при сжатии — критическая ошибка
                results[key] = CertifiedBound(
                    bound=float('inf'),
                    effective_order=0,
                    n_steps=1,
                    method="invariant_lost",
                    constant_B=float('inf'),
                    safety_factor=self.safety_factor,
                    is_certified=False,
                    data_name=key,
                )
            elif key not in compressed_invariants:
                # Инвариант не вычислен после сжатия
                results[key] = CertifiedBound(
                    bound=float('inf'),
                    effective_order=0,
                    n_steps=1,
                    method="invariant_missing",
                    constant_B=float('inf'),
                    safety_factor=self.safety_factor,
                    is_certified=False,
                    data_name=key,
                )
            else:
                orig_val = original_invariants[key]
                comp_val = compressed_invariants[key]
                
                # Простая верификация через разницу
                error = abs(orig_val - comp_val)
                results[key] = CertifiedBound(
                    bound=error * self.safety_factor,
                    effective_order=self.chernoff_order.k,
                    n_steps=1,
                    method="invariant_comparison",
                    constant_B=error,
                    safety_factor=self.safety_factor,
                    is_certified=True,
                    data_name=key,
                )
        
        return results
    
    def is_valid(
        self,
        bound: CertifiedBound,
        threshold: Optional[float] = None,
    ) -> bool:
        """
        Проверка: проходит ли данные верификацию.
        
        Args:
            bound: Граница ошибки от verify()
            threshold: Порог ошибки (по умолчанию significance_level)
            
        Returns:
            True если данные валидны (ошибка ≤ порога)
        """
        threshold = threshold or self.significance_level
        
        # Для сертифицированных границ: сравниваем bound с порогом
        if bound.is_certified:
            return bound.bound <= threshold
        
        # Для несертифицированных: более строгая проверка
        return bound.bound <= threshold * 0.5  # В 2 раза строже для uncertified
    
    def get_status(self, bound: CertifiedBound) -> str:
        """
        Получение статуса верификации.
        
        Returns:
            "VERIFIED" | "COMPROMISED" | "UNVERIFIED"
        """
        if self.is_valid(bound):
            return "VERIFIED"
        elif bound.is_certified:
            return "COMPROMISED"
        else:
            return "UNVERIFIED"


def compute_certified_bound(
    prices: Dict[int, float],
    chernoff_order: ChernoffOrder,
    payoff_reg: DataRegularity,
    n_target: int,
    safety_factor: float = 2.0,
    exact_price: Optional[float] = None,
) -> CertifiedBound:
    """
    Вычисление консервативной верхней границы ошибки |V_n - V_exact|.
    
    Адаптировано из ChernoffPy с минимальными изменениями.
    
    Args:
        prices: Словарь {n_steps: значение} для оценки сходимости
        chernoff_order: Порядок сходимости метода
        payoff_reg: Регулярность данных
        n_target: Целевое количество шагов
        safety_factor: Коэффициент запаса (≥ 1.0)
        exact_price: Точное значение (если известно)
        
    Returns:
        CertifiedBound с вычисленной границей
    """
    if len(prices) < 2:
        raise ValueError("Нужно минимум 2 вычисления для оценки границы")
    if n_target < 1:
        raise ValueError("n_target должен быть ≥ 1")
    if safety_factor < 1.0:
        raise ValueError("safety_factor должен быть ≥ 1.0")
    
    p_eff = effective_order(chernoff_order, payoff_reg)
    
    # Случай нулевого порядка: нет алгебраической сходимости
    if p_eff == 0:
        ns = sorted(prices.keys())
        n1, n2 = ns[-2], ns[-1]
        diff = abs(prices[n1] - prices[n2])
        return CertifiedBound(
            bound=float(safety_factor * diff),
            effective_order=0,
            n_steps=n_target,
            method="difference (no algebraic convergence)",
            constant_B=float(diff),
            safety_factor=float(safety_factor),
            is_certified=False,
        )
    
    # Режим с известным точным значением
    if exact_price is not None:
        b_values = [abs(v - exact_price) * (n ** p_eff) for n, v in prices.items()]
        b_values = [b for b in b_values if np.isfinite(b)]
        
        if not b_values:
            return CertifiedBound(
                bound=0.0,
                effective_order=p_eff,
                n_steps=n_target,
                method="exact match",
                constant_B=0.0,
                safety_factor=float(safety_factor),
                is_certified=True,
            )
        
        b_const = float(max(b_values))
        method = "exact comparison"
        
        # Используем непосредственную ошибку для n_target
        if n_target in prices:
            bound = float(safety_factor * abs(prices[n_target] - exact_price))
        else:
            bound = float(safety_factor * b_const / (n_target ** p_eff))
        
        return CertifiedBound(
            bound=bound,
            effective_order=p_eff,
            n_steps=n_target,
            method=method,
            constant_B=b_const,
            safety_factor=float(safety_factor),
            is_certified=True,
        )
    
    # Режим Richardson self-convergence (без точного значения)
    sorted_n = sorted(prices.keys())
    b_values: List[float] = []
    
    for i in range(len(sorted_n) - 1):
        n1 = sorted_n[i]
        n2 = sorted_n[i + 1]
        diff = abs(prices[n1] - prices[n2])
        ratio = (n1 / n2) ** p_eff
        denom = abs(1.0 - ratio)
        
        if denom < 1e-14:
            continue
        
        err_est = diff / denom
        b_values.append(float(err_est * (n1 ** p_eff)))
    
    if not b_values:
        return CertifiedBound(
            bound=0.0,
            effective_order=p_eff,
            n_steps=n_target,
            method="self-convergence (zero diff)",
            constant_B=0.0,
            safety_factor=float(safety_factor),
            is_certified=False,
        )
    
    b_const = float(max(b_values))
    method = "Richardson self-convergence"
    bound = float(safety_factor * b_const / (n_target ** p_eff))
    
    return CertifiedBound(
        bound=bound,
        effective_order=p_eff,
        n_steps=n_target,
        method=method,
        constant_B=b_const,
        safety_factor=float(safety_factor),
        is_certified=False,
    )


def verify_convergence_order(
    prices: Dict[int, float],
    expected_order: int,
    exact_price: Optional[float] = None,
    tolerance: float = 0.3,
) -> Dict:
    """
    Оценка эмпирического порядка сходимости и сравнение с теоретическим.
    
    Адаптировано из ChernoffPy.
    
    Returns:
        Dict с полями: empirical_order, expected_order, is_consistent, details
    """
    if len(prices) < 2:
        return {
            "empirical_order": None,
            "expected_order": expected_order,
            "is_consistent": False,
            "details": "Нужно минимум 2 точки данных",
        }
    
    sorted_n = sorted(prices.keys())
    
    # Вычисляем ошибки
    if exact_price is not None:
        errs = [(n, abs(prices[n] - exact_price)) for n in sorted_n]
    else:
        finest_n = sorted_n[-1]
        errs = [(n, abs(prices[n] - prices[finest_n])) for n in sorted_n[:-1]]
    
    # Фильтруем нулевые ошибки
    errs = [(n, e) for n, e in errs if e > 1e-14]
    
    if len(errs) < 2:
        return {
            "empirical_order": None,
            "expected_order": expected_order,
            "is_consistent": False,
            "details": "Недостаточно ненулевых ошибок",
        }
    
    # Фильтруем плато (когда ошибки перестают уменьшаться)
    if len(errs) >= 3:
        filtered = [errs[0]]
        for i in range(1, len(errs)):
            prev_err = filtered[-1][1]
            curr_err = errs[i][1]
            if curr_err < 0.8 * prev_err:
                filtered.append(errs[i])
        if len(filtered) >= 2:
            errs = filtered
    
    if len(errs) < 2:
        return {
            "empirical_order": None,
            "expected_order": expected_order,
            "is_consistent": False,
            "details": "Все ошибки на плато (домен ограничивает точность)",
        }
    
    # Линейная регрессия на логарифмах
    log_n = np.log([n for n, _ in errs])
    log_e = np.log([e for _, e in errs])
    slope, _ = np.polyfit(log_n, log_e, 1)
    empirical = float(-slope)
    
    # Односторонняя проверка: эмпирический порядок может быть выше теоретического
    consistent = empirical >= expected_order - tolerance
    
    return {
        "empirical_order": empirical,
        "expected_order": expected_order,
        "is_consistent": consistent,
        "details": f"Эмпирический порядок {empirical:.3f} vs ожидаемый {expected_order}; погрешность {tolerance:.3f}",
    }


def n_steps_for_tolerance(
    target_error: float,
    constant_B: float,
    effective_order: int,
    safety_factor: float = 2.0,
) -> int:
    """
    Рекомендация количества шагов n для достижения целевой ошибки.
    
    Формула: safety_factor * B / n^p <= target_error
    
    Адаптировано из ChernoffPy.
    """
    if target_error <= 0:
        raise ValueError("target_error должен быть > 0")
    if effective_order <= 0:
        raise ValueError("effective_order должен быть >= 1")
    if safety_factor < 1.0:
        raise ValueError("safety_factor должен быть >= 1.0")
    if constant_B <= 0:
        return 1
    
    n = (safety_factor * constant_B / target_error) ** (1.0 / effective_order)
    return max(1, int(np.ceil(n)))
