"""
CCBM — Certified Context Budget Manager

Детерминированная оптимизация и математическая верификация
контекстного окна больших языковых моделей.

Архитектура:
- analyzer: Классификация спанов L1-L4 (числа, политики, PII, контекст)
- optimizer: Сжатие через LLMLingua/LoPace, дедупликация
- verifier: Границы Чернова для верификации числовых данных
- audit: Деревья Меркла для неизменяемого логирования
- mcp: Model Context Protocol для интеграции с агентами
"""

__version__ = "2.0.0"
__author__ = "sergeeey"

from .analyzer import CriticalityAnalyzer, CriticalityLevel, Span
from .audit import (
    AuditEngine,
    AuditReport,
    MerkleProof,
    MerkleTree,
    VerificationReceipt,
    create_audit_report,
)
from .optimizer import OptimizationEngine, OptimizationResult
from .verifier import (
    CertifiedBound,
    ChernoffOrder,
    ChernoffVerifier,
    DataRegularity,
    NumericInvariantVerifier,
)

# MCP Server доступен через ccbm.mcp
# from .mcp import ccbm_server, main

__all__ = [
    # Analyzer
    "CriticalityAnalyzer",
    "Span",
    "CriticalityLevel",
    # Optimizer
    "OptimizationEngine",
    "OptimizationResult",
    # Verifier
    "ChernoffVerifier",
    "NumericInvariantVerifier",
    "CertifiedBound",
    "ChernoffOrder",
    "DataRegularity",
    # Audit
    "AuditEngine",
    "MerkleTree",
    "MerkleProof",
    "VerificationReceipt",
    "AuditReport",
    "create_audit_report",
    # MCP (доступен через ccbm.mcp)
    # "ccbm_server",
    # "main",
]
