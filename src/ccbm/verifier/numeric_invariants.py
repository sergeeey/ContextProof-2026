"""
Numeric Invariant Verifier — верификация числовых инвариантов.

Специализированный модуль для верификации:
- ИИН (индивидуальный идентификационный номер РК)
- БИН (бизнес-идентификационный номер)
- Контрольных сумм
- Финансовых сумм
- Дат
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .chernoff_bound import CertifiedBound, ChernoffVerifier


@dataclass
class InvariantCheck:
    """Результат проверки инварианта."""
    name: str
    original_value: float
    compressed_value: float
    bound: CertifiedBound
    is_valid: bool
    status: str  # "VERIFIED" | "COMPROMISED" | "UNVERIFIED"
    details: str = ""


class NumericInvariantVerifier:
    """
    Верификатор числовых инвариантов для CCBM.

    Применение:
    1. Вычисляем инварианты до сжатия (суммы, средние, контрольные суммы ИИН)
    2. Вычисляем инварианты после сжатия
    3. Сравниваем через границы Чернова
    4. Если COMPROMISED → откат к оригиналу
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
        domain: str = "financial",
        safety_factor: float = 2.0,
    ):
        """
        Инициализация верификатора.

        Args:
            domain: Домен данных (financial/legal/medical/general)
            safety_factor: Коэффициент запаса для границ
        """
        self.domain = domain
        self.safety_factor = safety_factor
        self.significance_level = self.SIGNIFICANCE_LEVELS.get(domain, 0.05)
        self.chernoff_verifier = ChernoffVerifier(
            method="crank-nicolson",
            safety_factor=safety_factor,
            domain=domain,
        )

    def compute_iin_checksum(self, iin: str) -> tuple[int, int]:
        """
        Вычисление контрольных сумм ИИН.

        Алгоритм модуля 11 для РК:
        1-я контрольная сумма: веса [1,2,3,4,5,6,7,8,9,10,11]
        2-я контрольная сумма: веса [3,4,5,6,7,8,9,10,11,1,2,3]

        Args:
            iin: 12-значный ИИН

        Returns:
            (ctrl1, ctrl2) — контрольные суммы
        """
        if len(iin) != 12 or not iin.isdigit():
            raise ValueError(f"Неверный формат ИИН: {iin}")

        digits = [int(d) for d in iin]

        # Первая контрольная сумма
        weights1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        sum1 = sum(w * d for w, d in zip(weights1, digits[:11], strict=False))
        ctrl1 = sum1 % 11

        # Вторая контрольная сумма
        weights2 = [3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2, 3]
        sum2 = sum(w * d for w, d in zip(weights2, digits, strict=False))
        ctrl2 = sum2 % 11

        return ctrl1, ctrl2

    def validate_iin(self, iin: str) -> bool:
        """
        Валидация ИИН по алгоритму модуля 11.

        Args:
            iin: 12-значный ИИН

        Returns:
            True если ИИН валиден
        """
        try:
            ctrl1, ctrl2 = self.compute_iin_checksum(iin)
            digits = [int(d) for d in iin]

            # Первая проверка
            if ctrl1 == 10:
                return False
            if ctrl1 != digits[11]:
                return False

            # Вторая проверка (для юрлиц)
            if ctrl2 == 10:
                return True  # Физлица могут не проходить вторую проверку
            return ctrl2 == digits[11]

        except (ValueError, IndexError):
            return False

    def extract_iin_invariants(self, iins: list[str]) -> dict[str, float]:
        """
        Извлечение инвариантов из списка ИИН.

        Args:
            iins: Список ИИН

        Returns:
            Словарь инвариантов:
            - count: количество
            - checksum1_sum: сумма первых контрольных сумм
            - checksum2_sum: сумма вторых контрольных сумм
            - valid_count: количество валидных
        """
        invariants = {
            "count": float(len(iins)),
            "checksum1_sum": 0.0,
            "checksum2_sum": 0.0,
            "valid_count": 0.0,
        }

        for iin in iins:
            try:
                ctrl1, ctrl2 = self.compute_iin_checksum(iin)
                invariants["checksum1_sum"] += ctrl1
                invariants["checksum2_sum"] += ctrl2

                if self.validate_iin(iin):
                    invariants["valid_count"] += 1

            except ValueError:
                continue

        return invariants

    def compute_sum_invariants(
        self,
        values: list[float],
        name: str = "values",
    ) -> dict[str, float]:
        """
        Вычисление инвариантов для числовых значений.

        Args:
            values: Список значений
            name: Префикс для имён инвариантов

        Returns:
            Словарь инвариантов:
            - {name}_sum: сумма
            - {name}_mean: среднее
            - {name}_min: минимум
            - {name}_max: максимум
            - {name}_count: количество
        """
        arr = np.array(values)

        return {
            f"{name}_sum": float(np.sum(arr)),
            f"{name}_mean": float(np.mean(arr)),
            f"{name}_min": float(np.min(arr)),
            f"{name}_max": float(np.max(arr)),
            f"{name}_count": float(len(values)),
        }

    def verify_iins(
        self,
        original_iins: list[str],
        compressed_iins: list[str],
    ) -> dict[str, InvariantCheck]:
        """
        Верификация ИИН через контрольные суммы.

        Args:
            original_iins: Оригинальные ИИН
            compressed_iins: Сжатые ИИН (после оптимизации)

        Returns:
            Словарь {имя_инварианта: InvariantCheck}
        """
        orig_inv = self.extract_iin_invariants(original_iins)
        comp_inv = self.extract_iin_invariants(compressed_iins)

        bounds = self.chernoff_verifier.verify_invariants(orig_inv, comp_inv)

        results = {}
        for name, bound in bounds.items():
            results[name] = InvariantCheck(
                name=name,
                original_value=orig_inv.get(name, 0.0),
                compressed_value=comp_inv.get(name, 0.0),
                bound=bound,
                is_valid=self.chernoff_verifier.is_valid(bound),
                status=self.chernoff_verifier.get_status(bound),
                details=f"Оригинал: {orig_inv.get(name, 0.0):.2f}, Сжатие: {comp_inv.get(name, 0.0):.2f}",
            )

        return results

    def verify_values(
        self,
        original_values: list[float],
        compressed_values: list[float],
        name: str = "values",
    ) -> dict[str, InvariantCheck]:
        """
        Верификация числовых значений.

        Args:
            original_values: Оригинальные значения
            compressed_values: Сжатые значения
            name: Имя набора данных

        Returns:
            Словарь {имя_инварианта: InvariantCheck}
        """
        if len(original_values) != len(compressed_values):
            raise ValueError(f"Длины массивов не совпадают: {len(original_values)} vs {len(compressed_values)}")

        orig_inv = self.compute_sum_invariants(original_values, name)
        comp_inv = self.compute_sum_invariants(compressed_values, name)

        bounds = self.chernoff_verifier.verify_invariants(orig_inv, comp_inv)

        results = {}
        for inv_name, bound in bounds.items():
            results[inv_name] = InvariantCheck(
                name=inv_name,
                original_value=orig_inv.get(inv_name, 0.0),
                compressed_value=comp_inv.get(inv_name, 0.0),
                bound=bound,
                is_valid=self.chernoff_verifier.is_valid(bound),
                status=self.chernoff_verifier.get_status(bound),
                details=f"Оригинал: {orig_inv.get(inv_name, 0.0):.4f}, Сжатие: {comp_inv.get(inv_name, 0.0):.4f}",
            )

        return results

    def is_all_valid(self, checks: dict[str, InvariantCheck]) -> bool:
        """
        Проверка: все ли инварианты валидны.

        Args:
            checks: Словарь результатов проверки

        Returns:
            True если все инварианты VERIFIED
        """
        return all(check.is_valid for check in checks.values())

    def get_summary(self, checks: dict[str, InvariantCheck]) -> str:
        """
        Получение сводного отчёта.

        Args:
            checks: Словарь результатов проверки

        Returns:
            Текстовый отчёт
        """
        total = len(checks)
        verified = sum(1 for c in checks.values() if c.status == "VERIFIED")
        compromised = sum(1 for c in checks.values() if c.status == "COMPROMISED")
        unverified = sum(1 for c in checks.values() if c.status == "UNVERIFIED")

        lines = [
            "=== Отчёт верификации инвариантов ===",
            f"Всего: {total}, Верифицировано: {verified}, Compromised: {compromised}, Неверифицировано: {unverified}",
            "",
        ]

        for name, check in sorted(checks.items()):
            status_icon = "✓" if check.is_valid else "✗"
            lines.append(f"  {status_icon} {name}: {check.status}")
            lines.append(f"    {check.details}")
            if not check.is_valid:
                lines.append(f"    Граница ошибки: {check.bound.bound:.6f}")

        return "\n".join(lines)


@dataclass
class VerificationReport:
    """Полный отчёт верификации для CCBM."""
    timestamp: str
    domain: str
    total_invariants: int
    verified_count: int
    compromised_count: int
    unverified_count: int
    checks: dict[str, InvariantCheck]
    is_passed: bool
    recommendation: str  # "APPROVED" | "FALLBACK" | "REVIEW"

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "timestamp": self.timestamp,
            "domain": self.domain,
            "summary": {
                "total": self.total_invariants,
                "verified": self.verified_count,
                "compromised": self.compromised_count,
                "unverified": self.unverified_count,
                "passed": self.is_passed,
            },
            "recommendation": self.recommendation,
            "checks": {
                name: {
                    "name": c.name,
                    "original": c.original_value,
                    "compressed": c.compressed_value,
                    "bound": c.bound.bound,
                    "is_valid": c.is_valid,
                    "status": c.status,
                }
                for name, c in self.checks.items()
            },
        }
