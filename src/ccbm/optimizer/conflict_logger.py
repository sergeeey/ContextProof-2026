"""
Compression Conflict Logger — логирование конфликтов сжатия.

Конфликты возникают когда:
- LLMLingua хочет удалить то, что правила помечают как must-keep
- Question-Aware приоритезирует не те спаны
- Chernoff verifier обнаруживает расхождения

Все конфликты логируются для:
- Обучения системы качества
- Golden Set тестов
- Аудита и комплаенса
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Типы конфликтов сжатия."""
    LLMLINGUA_VS_RULES = "llmlingua_vs_rules"
    QUESTION_AWARE_MISPRIORITY = "question_aware_mispriority"
    CHERNOFF_MISMATCH = "chernoff_mismatch"
    L1_RETENTION_VIOLATION = "l1_retention_violation"
    PII_LEAKAGE = "pii_leakage"
    SEMANTIC_DRIFT = "semantic_drift"


class ConflictResolution(Enum):
    """Способы разрешения конфликтов."""
    KEEP_ORIGINAL = "keep_original"
    USE_COMPRESSED = "use_compressed"
    MANUAL_REVIEW = "manual_review"
    AUTO_FIXED = "auto_fixed"


@dataclass
class CompressionConflict:
    """Запись о конфликте сжатия."""
    conflict_id: str
    timestamp: int
    conflict_type: ConflictType
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    original_data: dict[str, Any]
    compressed_data: dict[str, Any]
    resolution: ConflictResolution
    resolved: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "conflict_id": self.conflict_id,
            "timestamp": self.timestamp,
            "conflict_type": self.conflict_type.value,
            "severity": self.severity,
            "description": self.description,
            "original_data": self.original_data,
            "compressed_data": self.compressed_data,
            "resolution": self.resolution.value,
            "resolved": self.resolved,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Сериализация в JSON."""
        return json.dumps(self.to_dict(), indent=2)


class ConflictLogger:
    """
    Логгер конфликтов сжатия.

    Использование:
    1. Логирование конфликтов между контурами A/B
    2. Экспорт в Golden Set для тестов
    3. Метрики для observability
    """

    def __init__(self, log_path: str = "conflicts.log"):
        """
        Инициализация логгера.

        Args:
            log_path: Путь к файлу логов
        """
        self.log_path = log_path
        self.conflicts: list[CompressionConflict] = []
        self._conflict_counter = 0

    def log_conflict(
        self,
        conflict_type: ConflictType,
        severity: str,
        description: str,
        original_data: dict[str, Any],
        compressed_data: dict[str, Any],
        resolution: ConflictResolution,
        metadata: dict[str, Any] | None = None,
    ) -> CompressionConflict:
        """
        Логирование конфликта.

        Args:
            conflict_type: Тип конфликта
            severity: Критичность
            description: Описание
            original_data: Оригинальные данные
            compressed_data: Сжатые данные
            resolution: Способ разрешения
            metadata: Дополнительные метаданные

        Returns:
            CompressionConflict
        """
        self._conflict_counter += 1
        conflict_id = f"CONFLICT-{self._conflict_counter:06d}"

        conflict = CompressionConflict(
            conflict_id=conflict_id,
            timestamp=time.time_ns(),
            conflict_type=conflict_type,
            severity=severity,
            description=description,
            original_data=original_data,
            compressed_data=compressed_data,
            resolution=resolution,
            metadata=metadata or {},
        )

        self.conflicts.append(conflict)

        # Логирование в файл
        self._write_to_log(conflict)

        logger.warning(
            f"Conflict logged: {conflict_id} — {conflict_type.value} "
            f"(severity: {severity}, resolution: {resolution.value})"
        )

        return conflict

    def _write_to_log(self, conflict: CompressionConflict):
        """Запись конфликта в лог-файл."""
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(conflict.to_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to write conflict to log: {e}")

    def get_conflicts(
        self,
        conflict_type: ConflictType | None = None,
        severity: str | None = None,
        resolved: bool | None = None,
    ) -> list[CompressionConflict]:
        """
        Получение конфликтов с фильтрацией.

        Args:
            conflict_type: Фильтр по типу
            severity: Фильтр по критичности
            resolved: Фильтр по статусу разрешения

        Returns:
            Список конфликтов
        """
        conflicts = self.conflicts

        if conflict_type:
            conflicts = [c for c in conflicts if c.conflict_type == conflict_type]

        if severity:
            conflicts = [c for c in conflicts if c.severity == severity]

        if resolved is not None:
            conflicts = [c for c in conflicts if c.resolved == resolved]

        return conflicts

    def export_to_golden_set(self, path: str = "golden_set_conflicts.json"):
        """
        Экспорт конфликтов в Golden Set для тестов.

        Args:
            path: Путь к файлу Golden Set
        """
        golden_set = {
            "version": "1.2.0",
            "exported_at": time.time(),
            "total_conflicts": len(self.conflicts),
            "conflicts": [c.to_dict() for c in self.conflicts],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(golden_set, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(self.conflicts)} conflicts to Golden Set")

    def get_metrics(self) -> dict[str, Any]:
        """
        Получение метрик конфликтов.

        Returns:
            Словарь с метриками
        """
        if not self.conflicts:
            return {
                "total_conflicts": 0,
                "conflicts_by_type": {},
                "conflicts_by_severity": {},
                "resolution_rate": 0.0,
            }

        # Подсчёт по типам
        by_type: dict[str, int] = {}
        for conflict in self.conflicts:
            type_name = conflict.conflict_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

        # Подсчёт по критичности
        by_severity: dict[str, int] = {}
        for conflict in self.conflicts:
            severity = conflict.severity
            by_severity[severity] = by_severity.get(severity, 0) + 1

        # Rate разрешения
        resolved_count = sum(1 for c in self.conflicts if c.resolved)
        resolution_rate = resolved_count / len(self.conflicts)

        return {
            "total_conflicts": len(self.conflicts),
            "conflicts_by_type": by_type,
            "conflicts_by_severity": by_severity,
            "resolution_rate": resolution_rate,
            "critical_conflicts": by_severity.get("CRITICAL", 0),
            "high_conflicts": by_severity.get("HIGH", 0),
        }

    def resolve_conflict(self, conflict_id: str, resolved: bool = True):
        """
        Разрешение конфликта.

        Args:
            conflict_id: ID конфликта
            resolved: Статус разрешения
        """
        for conflict in self.conflicts:
            if conflict.conflict_id == conflict_id:
                conflict.resolved = resolved
                logger.info(f"Conflict {conflict_id} marked as {'resolved' if resolved else 'unresolved'}")
                return

        logger.warning(f"Conflict {conflict_id} not found")


# Global instance для удобного доступа
_conflict_logger: ConflictLogger | None = None


def get_conflict_logger() -> ConflictLogger:
    """Получение глобального логгера конфликтов."""
    global _conflict_logger
    if _conflict_logger is None:
        _conflict_logger = ConflictLogger()
    return _conflict_logger


def log_compression_conflict(
    conflict_type: ConflictType,
    severity: str,
    description: str,
    original_data: dict[str, Any],
    compressed_data: dict[str, Any],
    resolution: ConflictResolution,
) -> CompressionConflict:
    """
    Быстрое логирование конфликта.

    Args:
        conflict_type: Тип конфликта
        severity: Критичность
        description: Описание
        original_data: Оригинальные данные
        compressed_data: Сжатые данные
        resolution: Способ разрешения

    Returns:
        CompressionConflict
    """
    logger = get_conflict_logger()
    return logger.log_conflict(
        conflict_type=conflict_type,
        severity=severity,
        description=description,
        original_data=original_data,
        compressed_data=compressed_data,
        resolution=resolution,
    )
