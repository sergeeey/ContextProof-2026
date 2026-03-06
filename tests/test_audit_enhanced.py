"""
Тесты для Dual-mode Audit и Conflict Logger.
"""

import pytest
import time
from ccbm.audit.glass_box import GlassBoxAudit
from ccbm.optimizer.conflict_logger import (
    ConflictLogger,
    ConflictType,
    ConflictResolution,
    CompressionConflict,
    get_conflict_logger,
    log_compression_conflict,
)


class TestDualModeAudit:
    """Тесты для Dual-mode Audit (fast/async)."""

    def test_fast_mode_verification(self):
        """Быстрая верификация (O(1))."""
        audit = GlassBoxAudit()
        
        audit.log_decision("Agent1", "DECISION1", 0.9, "Reason 1")
        audit.log_decision("Agent2", "DECISION2", 0.8, "Reason 2")
        audit.finalize()
        
        # Fast mode — должно быть мгновенно
        start = time.time()
        result = audit.verify_integrity(fast_mode=True)
        elapsed = time.time() - start
        
        assert result is True
        assert elapsed < 0.001  # Fast mode должен быть < 1ms

    def test_full_mode_verification(self):
        """Полная верификация (O(n))."""
        audit = GlassBoxAudit()
        
        # Создаём много записей
        for i in range(100):
            audit.log_decision(f"Agent{i}", f"DECISION{i}", 0.9, f"Reason {i}")
        
        audit.finalize()
        
        # Full mode — проверяет все квитанции
        start = time.time()
        result = audit.verify_integrity(fast_mode=False)
        elapsed = time.time() - start
        
        assert result is True
        # Full mode может быть быстрым для 100 записей, просто проверяем что работает
        assert isinstance(elapsed, float)

    def test_async_verification(self):
        """Асинхронная верификация."""
        audit = GlassBoxAudit()
        
        for i in range(50):
            audit.log_decision(f"Agent{i}", f"DECISION{i}", 0.9, f"Reason {i}")
        
        audit.finalize()
        
        # Callback для результата
        callback_result = {}
        
        def callback(task_id, result):
            callback_result["task_id"] = task_id
            callback_result["result"] = result
        
        # Запуск асинхронной проверки
        task_id = audit.verify_integrity_async(callback=callback)
        
        assert task_id is not None
        
        # Ждём завершения (в реальном use case это будет background)
        time.sleep(0.5)
        
        assert "task_id" in callback_result
        assert callback_result["result"] is True

    def test_fast_mode_empty_audit(self):
        """Fast mode для пустого аудита."""
        audit = GlassBoxAudit()
        
        result = audit.verify_integrity(fast_mode=True)
        assert result is True

    def test_performance_comparison(self):
        """Сравнение производительности fast vs full."""
        audit = GlassBoxAudit()
        
        for i in range(200):
            audit.log_decision(f"Agent{i}", f"DECISION{i}", 0.9, f"Reason {i}")
        
        audit.finalize()
        
        # Fast mode
        start_fast = time.time()
        for _ in range(10):
            audit.verify_integrity(fast_mode=True)
        time_fast = time.time() - start_fast
        
        # Full mode
        start_full = time.time()
        for _ in range(10):
            audit.verify_integrity(fast_mode=False)
        time_full = time.time() - start_full
        
        # Fast mode должен быть значительно быстрее
        assert time_fast < time_full
        assert time_fast / time_full < 0.5  # Хотя бы в 2 раза быстрее


class TestConflictLogger:
    """Тесты для Conflict Logger."""

    def test_log_conflict(self):
        """Логирование конфликта."""
        logger = ConflictLogger(log_path="test_conflicts.log")
        
        conflict = logger.log_conflict(
            conflict_type=ConflictType.L1_RETENTION_VIOLATION,
            severity="CRITICAL",
            description="L1 данные удалены при сжатии",
            original_data={"iin": "950101300038"},
            compressed_data={"iin": "[REDACTED]"},
            resolution=ConflictResolution.AUTO_FIXED,
        )
        
        assert conflict.conflict_id.startswith("CONFLICT-")
        assert conflict.severity == "CRITICAL"
        assert conflict.resolved is False
        
        # Проверка что конфликт сохранён
        assert len(logger.conflicts) == 1

    def test_get_conflicts_filtered(self):
        """Получение конфликтов с фильтрацией."""
        logger = ConflictLogger()
        
        # Логируем несколько конфликтов
        logger.log_conflict(
            ConflictType.L1_RETENTION_VIOLATION,
            "CRITICAL",
            "Test 1",
            {}, {},
            ConflictResolution.AUTO_FIXED,
        )
        
        logger.log_conflict(
            ConflictType.PII_LEAKAGE,
            "HIGH",
            "Test 2",
            {}, {},
            ConflictResolution.MANUAL_REVIEW,
        )
        
        logger.log_conflict(
            ConflictType.L1_RETENTION_VIOLATION,
            "MEDIUM",
            "Test 3",
            {}, {},
            ConflictResolution.AUTO_FIXED,
        )
        
        # Фильтр по типу
        by_type = logger.get_conflicts(conflict_type=ConflictType.L1_RETENTION_VIOLATION)
        assert len(by_type) == 2
        
        # Фильтр по критичности
        by_severity = logger.get_conflicts(severity="CRITICAL")
        assert len(by_severity) == 1
        
        # Фильтр по resolved
        by_resolved = logger.get_conflicts(resolved=False)
        assert len(by_resolved) == 3

    def test_get_metrics(self):
        """Получение метрик конфликтов."""
        logger = ConflictLogger()
        
        # Логируем конфликты
        for i in range(10):
            logger.log_conflict(
                ConflictType.L1_RETENTION_VIOLATION if i % 2 == 0 else ConflictType.PII_LEAKAGE,
                "CRITICAL" if i < 3 else "HIGH",
                f"Test {i}",
                {}, {},
                ConflictResolution.AUTO_FIXED,
            )
        
        metrics = logger.get_metrics()
        
        assert metrics["total_conflicts"] == 10
        assert "l1_retention_violation" in metrics["conflicts_by_type"]
        assert "pii_leakage" in metrics["conflicts_by_type"]
        assert metrics["conflicts_by_severity"]["CRITICAL"] == 3
        assert metrics["conflicts_by_severity"]["HIGH"] == 7
        assert metrics["resolution_rate"] == 0.0  # Ни один не разрешён

    def test_resolve_conflict(self):
        """Разрешение конфликта."""
        logger = ConflictLogger()
        
        conflict = logger.log_conflict(
            ConflictType.SEMANTIC_DRIFT,
            "MEDIUM",
            "Test",
            {}, {},
            ConflictResolution.MANUAL_REVIEW,
        )
        
        assert conflict.resolved is False
        
        # Разрешаем конфликт
        logger.resolve_conflict(conflict.conflict_id, resolved=True)
        
        # Проверяем что разрешён
        conflicts = logger.get_conflicts(resolved=True)
        assert len(conflicts) == 1
        assert conflicts[0].conflict_id == conflict.conflict_id

    def test_export_to_golden_set(self, tmp_path):
        """Экспорт в Golden Set."""
        logger = ConflictLogger()
        
        logger.log_conflict(
            ConflictType.L1_RETENTION_VIOLATION,
            "CRITICAL",
            "Golden Set Test",
            {"original": "data"},
            {"compressed": "data"},
            ConflictResolution.AUTO_FIXED,
        )
        
        golden_path = tmp_path / "golden_set_conflicts.json"
        logger.export_to_golden_set(str(golden_path))
        
        # Проверяем что файл создан
        assert golden_path.exists()
        
        # Проверяем содержимое
        import json
        with open(golden_path) as f:
            data = json.load(f)
        
        assert data["version"] == "1.2.0"
        assert data["total_conflicts"] == 1
        assert len(data["conflicts"]) == 1

    def test_global_logger(self):
        """Глобальный логгер."""
        logger1 = get_conflict_logger()
        logger2 = get_conflict_logger()
        
        # Должен быть один и тот же экземпляр
        assert logger1 is logger2


class TestConflictIntegration:
    """Интеграционные тесты."""

    def test_audit_with_conflict_logging(self):
        """Аудит с логированием конфликтов."""
        audit = GlassBoxAudit()
        conflict_logger = ConflictLogger()
        
        # Логирование решения
        audit.log_decision(
            agent="ChernoffVerifier",
            decision="VERIFIED",
            confidence=0.97,
            reasoning="Chernoff bound < 0.01",
        )
        
        # Логирование конфликта (если есть)
        conflict_logger.log_conflict(
            ConflictType.CHERNOFF_MISMATCH,
            "HIGH",
            "Chernoff verifier обнаружил расхождение",
            {"original_mean": 100.0},
            {"compressed_mean": 105.0},
            ConflictResolution.AUTO_FIXED,
        )
        
        # Верификация
        audit.finalize()
        assert audit.verify_integrity(fast_mode=True) is True
        
        # Проверка метрик
        metrics = conflict_logger.get_metrics()
        assert metrics["total_conflicts"] == 1
        assert metrics["critical_conflicts"] == 0
        assert metrics["high_conflicts"] == 1

    def test_compression_conflict_helper(self):
        """Хелпер для логирования конфликтов."""
        conflict = log_compression_conflict(
            conflict_type=ConflictType.LLMLINGUA_VS_RULES,
            severity="MEDIUM",
            description="LLMLingua хочет удалить критичные данные",
            original_data={"text": "ИИН 950101300038"},
            compressed_data={"text": "[REDACTED]"},
            resolution=ConflictResolution.KEEP_ORIGINAL,
        )
        
        assert conflict.conflict_id.startswith("CONFLICT-")
        assert conflict.conflict_type == ConflictType.LLMLINGUA_VS_RULES
