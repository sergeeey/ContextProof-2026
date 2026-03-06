"""
CCBM Contract — Information Contract Engine.

Формальный контракт сохранённой информации для compliance.
"""

from .information_contract import (
    ContractVersion,
    InformationClass,
    InformationContract,
    InformationContractEngine,
    InformationSegment,
    create_information_contract,
)

__all__ = [
    "InformationContract",
    "InformationContractEngine",
    "InformationSegment",
    "InformationClass",
    "ContractVersion",
    "create_information_contract",
]
