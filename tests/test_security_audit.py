"""
Тесты для Security Audit.
"""

import pytest
from pathlib import Path
from ccbm.security.audit import (
    SecurityAuditor,
    SecurityFinding,
    SecurityReport,
    run_security_audit,
)


class TestSecurityFinding:
    """Тесты для SecurityFinding."""

    def test_finding_creation(self):
        """Создание находки."""
        finding = SecurityFinding(
            id="BANDIT-B101",
            severity="HIGH",
            category="bandit",
            message="assert_used",
            file="test.py",
            line=10,
            cvss_score=7.5,
            cwe_id="CWE-703",
        )
        
        assert finding.id == "BANDIT-B101"
        assert finding.severity == "HIGH"
        assert finding.cvss_score == 7.5

    def test_finding_to_dict(self):
        """Сериализация в словарь."""
        finding = SecurityFinding(
            id="TEST-001",
            severity="MEDIUM",
            category="test",
            message="Test message",
            file="test.py",
            line=5,
        )
        
        finding_dict = finding.to_dict()
        
        assert finding_dict["id"] == "TEST-001"
        assert finding_dict["severity"] == "MEDIUM"
        assert finding_dict["file"] == "test.py"


class TestSecurityReport:
    """Тесты для SecurityReport."""

    def test_report_creation(self):
        """Создание отчёта."""
        report = SecurityReport(
            timestamp="2026-03-06T12:00:00",
            project_name="CCBM",
            total_findings=5,
            critical=0,
            high=1,
            medium=2,
            low=2,
            info=0,
            findings=[],
            score=7.5,
            verdict="⚠️ NEEDS_WORK",
        )
        
        assert report.project_name == "CCBM"
        assert report.score == 7.5
        assert report.verdict == "⚠️ NEEDS_WORK"

    def test_report_to_dict(self):
        """Сериализация в словарь."""
        report = SecurityReport(
            timestamp="2026-03-06T12:00:00",
            project_name="Test",
            total_findings=0,
            critical=0,
            high=0,
            medium=0,
            low=0,
            info=0,
            findings=[],
            score=10.0,
            verdict="✅ PASS",
        )
        
        report_dict = report.to_dict()
        
        assert report_dict["project_name"] == "Test"
        assert report_dict["summary"]["total"] == 0
        assert report_dict["score"] == 10.0

    def test_report_to_markdown(self):
        """Генерация Markdown."""
        report = SecurityReport(
            timestamp="2026-03-06T12:00:00",
            project_name="CCBM",
            total_findings=3,
            critical=1,
            high=0,
            medium=1,
            low=1,
            info=0,
            findings=[],
            score=5.5,
            verdict="❌ FAIL",
        )
        
        md = report.to_markdown()
        
        assert "# CCBM Security Audit Report" in md
        assert "🔴 CRITICAL" in md
        assert "Score: 5.5/10" in md


class TestSecurityAuditor:
    """Тесты для SecurityAuditor."""

    def test_auditor_creation(self):
        """Создание аудитора."""
        auditor = SecurityAuditor(Path.cwd())
        
        assert auditor.project_path == Path.cwd()
        assert auditor.findings == []

    def test_calculate_score(self):
        """Расчёт score."""
        counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "INFO": 0,
        }
        
        score = SecurityAuditor._calculate_score(counts)
        assert score == 10.0

    def test_calculate_score_with_issues(self):
        """Расчёт score с проблемами."""
        counts = {
            "CRITICAL": 1,
            "HIGH": 2,
            "MEDIUM": 3,
            "LOW": 4,
            "INFO": 5,
        }
        
        score = SecurityAuditor._calculate_score(counts)
        # 10 - (1*3 + 2*2 + 3*1 + 4*0.5) = 10 - 12 = 0
        assert score == 0.0

    def test_deduplicate_findings(self):
        """Удаление дубликатов."""
        findings = [
            SecurityFinding("ID-1", "HIGH", "cat", "msg", "file.py", 10),
            SecurityFinding("ID-1", "HIGH", "cat", "msg", "file.py", 10),  # Дубликат
            SecurityFinding("ID-2", "MEDIUM", "cat", "msg2", "file.py", 20),
        ]
        
        unique = SecurityAuditor._deduplicate_findings(findings)
        
        assert len(unique) == 2

    def test_bandit_severity_mapping(self):
        """Маппинг severity Bandit."""
        assert SecurityAuditor._bandit_severity("HIGH") == "HIGH"
        assert SecurityAuditor._bandit_severity("MEDIUM") == "MEDIUM"
        assert SecurityAuditor._bandit_severity("LOW") == "LOW"
        assert SecurityAuditor._bandit_severity("UNKNOWN") == "INFO"

    def test_severity_to_cvss(self):
        """Конверсия severity в CVSS."""
        assert SecurityAuditor._severity_to_cvss("HIGH") == 7.5
        assert SecurityAuditor._severity_to_cvss("MEDIUM") == 5.0
        assert SecurityAuditor._severity_to_cvss("LOW") == 2.5
        assert SecurityAuditor._severity_to_cvss("UNKNOWN") == 0.0


class TestRunSecurityAudit:
    """Тесты для run_security_audit."""

    def test_run_audit_current_dir(self):
        """Запуск аудита в текущей директории."""
        report = run_security_audit()
        
        assert isinstance(report, SecurityReport)
        assert report.project_name == "CCBM"
        assert 0.0 <= report.score <= 10.0

    def test_run_audit_custom_path(self):
        """Запуск аудита в кастомной директории."""
        report = run_security_audit(Path.cwd())
        
        assert isinstance(report, SecurityReport)
        assert report.metadata["scan_path"] == str(Path.cwd())


class TestIntegration:
    """Интеграционные тесты."""

    def test_full_audit_workflow(self):
        """Полный рабочий процесс аудита."""
        auditor = SecurityAuditor(Path.cwd())
        
        # Запуск сканеров
        findings = auditor.run_all_scans()
        
        # Генерация отчёта
        report = auditor.generate_report()
        
        # Проверка
        assert isinstance(report, SecurityReport)
        assert report.total_findings == len(findings)
        assert 0.0 <= report.score <= 10.0
        
        # Markdown отчёт
        md = report.to_markdown()
        assert "# CCBM Security Audit Report" in md

    def test_empty_findings(self):
        """Отчёт без находок."""
        auditor = SecurityAuditor(Path.cwd())
        auditor.findings = []
        
        report = auditor.generate_report()
        
        assert report.total_findings == 0
        assert report.score == 10.0
        assert report.verdict == "✅ PASS"

    def test_critical_findings(self):
        """Отчёт с критическими находками."""
        auditor = SecurityAuditor(Path.cwd())
        auditor.findings = [
            SecurityFinding("CRIT-001", "CRITICAL", "test", "Critical issue", "file.py", 1),
        ]
        
        report = auditor.generate_report()
        
        assert report.critical == 1
        assert report.score < 10.0
        assert report.verdict == "❌ FAIL"

    def test_high_findings(self):
        """Отчёт с high находками."""
        auditor = SecurityAuditor(Path.cwd())
        auditor.findings = [
            SecurityFinding("HIGH-001", "HIGH", "test", "High issue", "file.py", 1),
        ]
        
        report = auditor.generate_report()
        
        assert report.high == 1
        assert report.critical == 0
        assert report.verdict == "⚠️ NEEDS_WORK"
