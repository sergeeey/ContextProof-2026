"""
CCBM Observability Metrics — метрики для production monitoring.

Метрики:
- latency_breakdown (по стадиям)
- compression_ratio (по доменам)
- faithfulness_score (на Golden Set)
- certificate_fail_rate (по причинам)
- pii_detection_recall
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Точка метрики."""
    timestamp: float
    value: float
    labels: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "timestamp": self.timestamp,
            "value": self.value,
            "labels": self.labels,
        }


class CCBBMetrics:
    """
    Сборщик метрик для CCBM.
    
    Метрики:
    - latency_breakdown{stage}
    - compression_ratio{domain}
    - faithfulness_score
    - certificate_fail_rate{reason}
    - pii_detection_recall
    - pii_leak_rate
    - conflict_rate
    """

    def __init__(self):
        """Инициализация метрик."""
        self._metrics: dict[str, list[MetricPoint]] = {
            "latency_breakdown": [],
            "compression_ratio": [],
            "faithfulness_score": [],
            "certificate_fail_rate": [],
            "pii_detection_recall": [],
            "pii_leak_rate": [],
            "conflict_rate": [],
        }
        self._current_stage: str | None = None
        self._stage_start: float = 0.0

    def start_stage(self, stage: str):
        """
        Начало стадии для замера latency.
        
        Args:
            stage: Название стадии (analyze/compress/verify/audit)
        """
        self._current_stage = stage
        self._stage_start = time.time()

        logger.debug(f"Started stage: {stage}")

    def end_stage(self):
        """Завершение стадии с записью метрики latency."""
        if self._current_stage is None:
            return

        elapsed = time.time() - self._stage_start

        self._metrics["latency_breakdown"].append(
            MetricPoint(
                timestamp=time.time(),
                value=elapsed,
                labels={"stage": self._current_stage},
            )
        )

        logger.debug(f"Ended stage: {self._current_stage}, elapsed: {elapsed:.3f}s")

        self._current_stage = None
        self._stage_start = 0.0

    def record_compression_ratio(self, ratio: float, domain: str = "general"):
        """
        Запись коэффициента сжатия.
        
        Args:
            ratio: Коэффициент сжатия
            domain: Домен (financial/legal/medical/general)
        """
        self._metrics["compression_ratio"].append(
            MetricPoint(
                timestamp=time.time(),
                value=ratio,
                labels={"domain": domain},
            )
        )

    def record_faithfulness_score(self, score: float):
        """
        Запись faithfulness score.
        
        Args:
            score: Faithfulness score (0-1)
        """
        self._metrics["faithfulness_score"].append(
            MetricPoint(
                timestamp=time.time(),
                value=score,
                labels={},
            )
        )

    def record_certificate_fail(self, reason: str):
        """
        Запись failure сертификата.
        
        Args:
            reason: Причина failure
        """
        self._metrics["certificate_fail_rate"].append(
            MetricPoint(
                timestamp=time.time(),
                value=1.0,
                labels={"reason": reason},
            )
        )

    def record_pii_detection(self, detected: int, total: int):
        """
        Запись PII detection recall.
        
        Args:
            detected: Количество обнаруженных PII
            total: Общее количество PII
        """
        if total > 0:
            recall = detected / total
            self._metrics["pii_detection_recall"].append(
                MetricPoint(
                    timestamp=time.time(),
                    value=recall,
                    labels={},
                )
            )

    def record_pii_leak(self, leaked: int, total: int):
        """
        Запись PII leak rate.
        
        Args:
            leaked: Количество утекших PII
            total: Общее количество PII
        """
        if total > 0:
            leak_rate = leaked / total
            self._metrics["pii_leak_rate"].append(
                MetricPoint(
                    timestamp=time.time(),
                    value=leak_rate,
                    labels={},
                )
            )

    def record_conflict(self, conflict_count: int, total_operations: int):
        """
        Запись conflict rate.
        
        Args:
            conflict_count: Количество конфликтов
            total_operations: Общее количество операций
        """
        if total_operations > 0:
            conflict_rate = conflict_count / total_operations
            self._metrics["conflict_rate"].append(
                MetricPoint(
                    timestamp=time.time(),
                    value=conflict_rate,
                    labels={},
                )
            )

    def get_metric(self, name: str, window_seconds: float | None = None) -> list[MetricPoint]:
        """
        Получение метрики.
        
        Args:
            name: Название метрики
            window_seconds: Временное окно (None = все данные)
            
        Returns:
            Список MetricPoint
        """
        if name not in self._metrics:
            return []

        points = self._metrics[name]

        if window_seconds is None:
            return points

        # Фильтрация по временному окну
        now = time.time()
        cutoff = now - window_seconds

        return [p for p in points if p.timestamp >= cutoff]

    def get_summary(self) -> dict[str, Any]:
        """
        Получение сводки всех метрик.
        
        Returns:
            Словарь со сводкой
        """
        summary = {}

        for name, points in self._metrics.items():
            if not points:
                summary[name] = {
                    "count": 0,
                    "avg": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                }
                continue

            values = [p.value for p in points]
            summary[name] = {
                "count": len(points),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "latest": points[-1].value if points else 0.0,
            }

        # Дополнительно: latency breakdown по стадиям
        latency_points = self._metrics["latency_breakdown"]
        if latency_points:
            by_stage = {}
            for point in latency_points:
                stage = point.labels.get("stage", "unknown")
                if stage not in by_stage:
                    by_stage[stage] = []
                by_stage[stage].append(point.value)

            summary["latency_by_stage"] = {
                stage: {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                }
                for stage, values in by_stage.items()
            }

        # Compression ratio по доменам
        compression_points = self._metrics["compression_ratio"]
        if compression_points:
            by_domain = {}
            for point in compression_points:
                domain = point.labels.get("domain", "general")
                if domain not in by_domain:
                    by_domain[domain] = []
                by_domain[domain].append(point.value)

            summary["compression_by_domain"] = {
                domain: {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                }
                for domain, values in by_domain.items()
            }

        return summary

    def export_prometheus(self) -> str:
        """
        Экспорт в формате Prometheus.
        
        Returns:
            Строка в формате Prometheus
        """
        lines = []

        for name, points in self._metrics.items():
            if not points:
                continue

            # Создаём метрику
            metric_name = f"ccbm_{name}"

            # Group by labels
            by_labels = {}
            for point in points:
                label_key = ",".join(f'{k}="{v}"' for k, v in sorted(point.labels.items()))
                if label_key not in by_labels:
                    by_labels[label_key] = []
                by_labels[label_key].append(point.value)

            # Выводим последнюю точку для каждого набора labels
            for label_key, values in by_labels.items():
                lines.append(f"# TYPE {metric_name} gauge")
                lines.append(f'{metric_name}{{{label_key}}} {values[-1]}')

        return "\n".join(lines)


# Global instance
_metrics: CCBBMetrics | None = None


def get_metrics() -> CCBBMetrics:
    """Получение глобального сборщика метрик."""
    global _metrics
    if _metrics is None:
        _metrics = CCBBMetrics()
    return _metrics


# Context manager для удобного замера стадий
class measure_stage:
    """
    Context manager для замера стадии.
    
    Usage:
        with measure_stage("analyze"):
            # код стадии
    """

    def __init__(self, stage: str):
        self.stage = stage
        self.metrics = get_metrics()

    def __enter__(self):
        self.metrics.start_stage(self.stage)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.metrics.end_stage()
        return False
