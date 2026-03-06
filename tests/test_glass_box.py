"""
Тесты для Glass Box Audit.
"""

import pytest
from ccbm.audit.glass_box import (
    GlassBoxAudit,
    AuditEntry,
    GlassBoxReport,
    create_glass_box_report,
)


class TestAuditEntry:
    """Тесты для AuditEntry."""

    def test_entry_creation(self):
        """Создание записи аудита."""
        entry = AuditEntry(
            step_id=1,
            timestamp_ns=1706700000000000000,
            agent="ChernoffVerifier",
            decision="VERIFIED",
            confidence=0.97,
            reasoning="Chernoff bound < 0.01",
        )
        
        assert entry.step_id == 1
        assert entry.agent == "ChernoffVerifier"
        assert entry.decision == "VERIFIED"
        assert entry.confidence == 0.97
        assert entry.merkle_hash == ""

    def test_entry_to_dict(self):
        """Сериализация в словарь."""
        entry = AuditEntry(
            step_id=1,
            timestamp_ns=1706700000000000000,
            agent="TestAgent",
            decision="TEST",
            confidence=1.0,
            reasoning="Test reasoning",
        )
        
        entry_dict = entry.to_dict()
        
        assert entry_dict["step_id"] == 1
        assert entry_dict["agent"] == "TestAgent"
        assert entry_dict["decision"] == "TEST"


class TestGlassBoxAudit:
    """Тесты для GlassBoxAudit."""

    def test_log_decision(self):
        """Логирование решения."""
        audit = GlassBoxAudit()
        
        entry = audit.log_decision(
            agent="ChernoffVerifier",
            decision="VERIFIED",
            confidence=0.97,
            reasoning="Chernoff bound < 0.01",
            metadata={"test": "data"},
        )
        
        assert entry.step_id == 1
        assert entry.agent == "ChernoffVerifier"
        assert entry.merkle_hash is not None
        assert len(audit.entries) == 1

    def test_multiple_decisions(self):
        """Множество решений."""
        audit = GlassBoxAudit()
        
        audit.log_decision("Agent1", "DECISION1", 0.9, "Reason 1")
        audit.log_decision("Agent2", "DECISION2", 0.8, "Reason 2")
        audit.log_decision("Agent3", "DECISION3", 0.95, "Reason 3")
        
        assert len(audit.entries) == 3
        assert audit._step_counter == 3

    def test_finalize(self):
        """Финализация дерева Меркла."""
        audit = GlassBoxAudit()
        
        audit.log_decision("Agent1", "DECISION1", 0.9, "Reason 1")
        audit.log_decision("Agent2", "DECISION2", 0.8, "Reason 2")
        
        merkle_root = audit.finalize()
        
        assert merkle_root is not None
        assert len(merkle_root) == 64  # SHA-256 hex

    def test_get_audit_trail(self):
        """Получение audit trail."""
        audit = GlassBoxAudit()
        
        audit.log_decision("Agent1", "DECISION1", 0.9, "Reason 1")
        audit.log_decision("Agent2", "DECISION2", 0.8, "Reason 2")
        
        trail = audit.get_audit_trail()
        
        assert len(trail) == 2
        assert all("step_id" in entry for entry in trail)
        assert all("merkle_hash" in entry for entry in trail)

    def test_verify_integrity(self):
        """Проверка целостности."""
        audit = GlassBoxAudit()
        
        audit.log_decision("Agent1", "DECISION1", 0.9, "Reason 1")
        audit.log_decision("Agent2", "DECISION2", 0.8, "Reason 2")
        audit.finalize()
        
        assert audit.verify_integrity() is True

    def test_verify_integrity_empty(self):
        """Проверка целостности пустого аудита."""
        audit = GlassBoxAudit()
        
        assert audit.verify_integrity() is True

    def test_export_for_blockchain(self):
        """Экспорт для блокчейна."""
        audit = GlassBoxAudit()
        
        audit.log_decision("Agent1", "DECISION1", 0.9, "Reason 1")
        export = audit.export_for_blockchain()
        
        assert "merkle_root" in export
        assert "timestamp" in export
        assert "total_leaves" in export

    def test_get_summary(self):
        """Получение сводки."""
        audit = GlassBoxAudit()
        
        audit.log_decision("ChernoffVerifier", "VERIFIED", 0.97, "Reason 1")
        audit.log_decision("ChernoffVerifier", "COMPROMISED", 0.85, "Reason 2")
        audit.log_decision("AuditEngine", "VERIFIED", 0.99, "Reason 3")
        
        summary = audit.get_summary()
        
        assert summary["total_decisions"] == 3
        assert summary["avg_confidence"] > 0.9
        assert "ChernoffVerifier" in summary["decisions_by_agent"]
        assert "VERIFIED" in summary["decisions_by_type"]

    def test_get_summary_empty(self):
        """Сводка для пустого аудита."""
        audit = GlassBoxAudit()
        
        summary = audit.get_summary()
        
        assert summary["total_decisions"] == 0
        assert summary["integrity_valid"] is True


class TestGlassBoxReport:
    """Тесты для GlassBoxReport."""

    def test_create_report(self):
        """Создание отчёта."""
        audit = GlassBoxAudit()
        
        audit.log_decision("Agent1", "DECISION1", 0.9, "Reason 1")
        audit.finalize()
        
        report = create_glass_box_report(audit)
        
        assert report.total_decisions == 1
        assert report.merkle_root is not None
        assert report.integrity_valid is True

    def test_report_serialization(self):
        """Сериализация отчёта."""
        audit = GlassBoxAudit()
        
        audit.log_decision("Agent1", "DECISION1", 0.9, "Reason 1")
        
        report = create_glass_box_report(audit)
        report_dict = report.to_dict()
        
        assert "timestamp" in report_dict
        assert "entries" in report_dict
        assert len(report_dict["entries"]) == 1


class TestIntegration:
    """Интеграционные тесты."""

    def test_full_workflow(self):
        """Полный рабочий процесс."""
        audit = GlassBoxAudit()
        
        # Логирование решений
        entry1 = audit.log_decision(
            agent="ChernoffVerifier",
            decision="VERIFIED",
            confidence=0.97,
            reasoning="Chernoff bound < 0.01",
            metadata={"test": "data1"},
        )
        
        entry2 = audit.log_decision(
            agent="AuditEngine",
            decision="VALID",
            confidence=0.99,
            reasoning="Merkle proof valid",
            metadata={"test": "data2"},
        )
        
        # Финализация
        merkle_root = audit.finalize()
        
        # Проверка
        assert audit.verify_integrity() is True
        
        # Отчёт
        report = create_glass_box_report(audit)
        assert report.integrity_valid is True
        
        # Export
        export = audit.export_for_blockchain()
        assert export["merkle_root"] == merkle_root

    def test_ccbm_integration(self):
        """Интеграция с CCBM компонентами."""
        from ccbm import ChernoffVerifier, AuditEngine
        import numpy as np
        
        audit = GlassBoxAudit()
        
        # Верификация через ChernoffVerifier
        verifier = ChernoffVerifier(domain="financial")
        original = np.array([100.0, 200.0, 300.0])
        compressed = np.array([100.0, 200.0, 300.0])
        
        bound = verifier.verify(original, compressed, "test_data")
        
        # Логирование решения
        audit.log_decision(
            agent="ChernoffVerifier",
            decision=verifier.get_status(bound),
            confidence=0.97,
            reasoning=f"Bound: {bound.bound:.6f}",
            metadata={
                "original": original.tolist(),
                "compressed": compressed.tolist(),
                "bound": bound.bound,
            },
        )
        
        audit.finalize()
        
        # Проверка
        assert audit.verify_integrity() is True
        
        summary = audit.get_summary()
        assert summary["total_decisions"] == 1
        assert summary["decisions_by_agent"]["ChernoffVerifier"] == 1
