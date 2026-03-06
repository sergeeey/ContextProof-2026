"""
Verifier — математическая верификация данных для CCBM.

Экспорт основных компонентов верификатора.
"""

from .chernoff_bound import (
    ChernoffVerifier,
    ChernoffOrder,
    DataRegularity,
    CertifiedBound,
    compute_certified_bound,
    verify_convergence_order,
    n_steps_for_tolerance,
    effective_order,
)

from .numeric_invariants import (
    NumericInvariantVerifier,
    InvariantCheck,
    VerificationReport,
)

__all__ = [
    # Chernoff bounds
    "ChernoffVerifier",
    "ChernoffOrder",
    "DataRegularity",
    "CertifiedBound",
    "compute_certified_bound",
    "verify_convergence_order",
    "n_steps_for_tolerance",
    "effective_order",
    # Numeric invariants
    "NumericInvariantVerifier",
    "InvariantCheck",
    "VerificationReport",
]
