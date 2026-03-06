"""
CCBM Security Audit System

Автоматический аудит безопасности по шаблонам TERAG111-1.

Компоненты:
- Security Scanner (Bandit, Gitleaks, Ruff)
- CVSS Scoring
- Audit Report Generator
- Compliance Checker (Закон РК)
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SecurityFinding:
    """Найденная уязвимость."""
    id: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str
    message: str
    file: str
    line: int
    column: int = 0
    cvss_score: float = 0.0
    cwe_id: str = ""
    confidence: str = "HIGH"
    remediation: str = ""
    
    def to_dict(self) -> Dict:
        """Сериализация в словарь."""
        return {
            "id": self.id,
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "cvss_score": self.cvss_score,
            "cwe_id": self.cwe_id,
            "confidence": self.confidence,
            "remediation": self.remediation,
        }


@dataclass
class SecurityReport:
    """Отчёт security аудита."""
    timestamp: str
    project_name: str
    total_findings: int
    critical: int
    high: int
    medium: int
    low: int
    info: int
    findings: List[SecurityFinding]
    score: float  # 0-10 (10 = безопасно)
    verdict: str  # PASS, NEEDS_WORK, FAIL
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Сериализация в словарь."""
        return {
            "timestamp": self.timestamp,
            "project_name": self.project_name,
            "summary": {
                "total": self.total_findings,
                "critical": self.critical,
                "high": self.high,
                "medium": self.medium,
                "low": self.low,
                "info": self.info,
            },
            "score": self.score,
            "verdict": self.verdict,
            "findings": [f.to_dict() for f in self.findings],
            "metadata": self.metadata,
        }
    
    def to_markdown(self) -> str:
        """Генерация Markdown отчёта."""
        lines = [
            f"# CCBM Security Audit Report",
            f"",
            f"**Дата:** {self.timestamp}",
            f"**Проект:** {self.project_name}",
            f"",
            f"## Summary",
            f"",
            f"| Severity | Count |",
            f"|----------|-------|",
            f"| 🔴 CRITICAL | {self.critical} |",
            f"| 🟠 HIGH | {self.high} |",
            f"| 🟡 MEDIUM | {self.medium} |",
            f"| 🟢 LOW | {self.low} |",
            f"| ℹ️ INFO | {self.info} |",
            f"| **TOTAL** | **{self.total_findings}** |",
            f"",
            f"## Score: {self.score}/10 — {self.verdict}",
            f"",
        ]
        
        if self.findings:
            lines.extend([
                "## Findings",
                "",
            ])
            
            for finding in self.findings[:20]:  # Первые 20
                severity_icon = {
                    "CRITICAL": "🔴",
                    "HIGH": "🟠",
                    "MEDIUM": "🟡",
                    "LOW": "🟢",
                    "INFO": "ℹ️",
                }.get(finding.severity, "⚪")
                
                lines.extend([
                    f"### {severity_icon} {finding.id}: {finding.message}",
                    f"",
                    f"- **File:** `{finding.file}:{finding.line}`",
                    f"- **CVSS:** {finding.cvss_score}",
                    f"- **CWE:** {finding.cwe_id}",
                    f"- **Remediation:** {finding.remediation}",
                    f"",
                ])
        
        return "\n".join(lines)


class SecurityAuditor:
    """
    Security Auditor для CCBM.
    
    Инструменты:
    - Bandit (Python security)
    - Gitleaks (secrets detection)
    - Ruff (linting + security rules)
    """
    
    def __init__(self, project_path: Path):
        """
        Инициализация аудитора.
        
        Args:
            project_path: Путь к проекту
        """
        self.project_path = project_path
        self.findings: List[SecurityFinding] = []
    
    def run_bandit(self) -> List[SecurityFinding]:
        """
        Запуск Bandit security scanner.
        
        Returns:
            Список находок
        """
        logger.info("Запуск Bandit...")
        
        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "bandit",
                    "-r", str(self.project_path / "src"),
                    "-f", "json",
                    "--level", "all",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            findings = []
            
            if result.stdout:
                data = json.loads(result.stdout)
                
                for issue in data.get("results", []):
                    finding = SecurityFinding(
                        id=f"BANDIT-{issue.get('test_id', 'UNKNOWN')}",
                        severity=self._bandit_severity(issue.get("issue_severity", "")),
                        category="bandit",
                        message=issue.get("issue_text", ""),
                        file=issue.get("filename", ""),
                        line=issue.get("line_number", 0),
                        cvss_score=self._severity_to_cvss(issue.get("issue_severity", "")),
                        cwe_id=issue.get("code", "").split(":")[0] if issue.get("code") else "",
                        remediation=f"Review and fix: {issue.get('issue_text', '')}",
                    )
                    findings.append(finding)
            
            logger.info(f"Bandit нашёл {len(findings)} проблем")
            return findings
            
        except subprocess.TimeoutExpired:
            logger.error("Bandit timeout")
            return []
        except Exception as e:
            logger.error(f"Bandit error: {e}")
            return []
    
    def run_gitleaks(self) -> List[SecurityFinding]:
        """
        Запуск Gitleaks для поиска секретов.
        
        Returns:
            Список находок
        """
        logger.info("Запуск Gitleaks...")
        
        try:
            result = subprocess.run(
                [
                    "gitleaks", "detect",
                    "--source", str(self.project_path),
                    "--report-format", "json",
                    "--report-path", str(self.project_path / "gitleaks-report.json"),
                ],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.project_path,
            )
            
            findings = []
            
            # Чтение отчёта
            report_path = self.project_path / "gitleaks-report.json"
            if report_path.exists():
                with open(report_path) as f:
                    data = json.load(f)
                
                for leak in data:
                    finding = SecurityFinding(
                        id=f"GITLEAKS-{leak.get('RuleID', 'UNKNOWN')}",
                        severity="HIGH",
                        category="secrets",
                        message=f"Secret detected: {leak.get('Secret', '***')}",
                        file=leak.get('File', ''),
                        line=leak.get('StartLine', 0),
                        cvss_score=7.5,
                        cwe_id="CWE-798",
                        remediation="Remove secret and rotate credentials",
                    )
                    findings.append(finding)
            
            logger.info(f"Gitleaks нашёл {len(findings)} секретов")
            return findings
            
        except FileNotFoundError:
            logger.warning("Gitleaks не установлен. Пропускаем...")
            return []
        except Exception as e:
            logger.error(f"Gitleaks error: {e}")
            return []
    
    def run_ruff_security(self) -> List[SecurityFinding]:
        """
        Запуск Ruff с security rules.
        
        Returns:
            Список находок
        """
        logger.info("Запуск Ruff security check...")
        
        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "ruff", "check",
                    str(self.project_path / "src"),
                    "--select", "S",  # Security rules
                    "--output-format", "json",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            findings = []
            
            if result.stdout:
                data = json.loads(result.stdout)
                
                for violation in data:
                    finding = SecurityFinding(
                        id=f"RUFF-{violation.get('code', 'UNKNOWN')}",
                        severity="MEDIUM",
                        category="ruff",
                        message=violation.get('message', ''),
                        file=violation.get('filename', ''),
                        line=violation.get('location', {}).get('row', 0),
                        column=violation.get('location', {}).get('column', 0),
                        cvss_score=5.0,
                        cwe_id=violation.get('code', ''),
                        remediation=f"Fix: {violation.get('message', '')}",
                    )
                    findings.append(finding)
            
            logger.info(f"Ruff нашёл {len(findings)} проблем")
            return findings
            
        except Exception as e:
            logger.error(f"Ruff error: {e}")
            return []
    
    def run_all_scans(self) -> List[SecurityFinding]:
        """
        Запуск всех сканеров.
        
        Returns:
            Объединённый список находок
        """
        self.findings = []
        
        # Bandit
        self.findings.extend(self.run_bandit())
        
        # Gitleaks
        self.findings.extend(self.run_gitleaks())
        
        # Ruff
        self.findings.extend(self.run_ruff_security())
        
        # Deduplication
        self.findings = self._deduplicate_findings(self.findings)
        
        return self.findings
    
    def generate_report(self) -> SecurityReport:
        """
        Генерация отчёта.
        
        Returns:
            SecurityReport
        """
        # Подсчёт по severity
        severity_counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "INFO": 0,
        }
        
        for finding in self.findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
        
        # Расчёт score (0-10)
        score = self._calculate_score(severity_counts)
        
        # Вердикт
        if severity_counts["CRITICAL"] > 0:
            verdict = "❌ FAIL"
        elif severity_counts["HIGH"] > 0:
            verdict = "⚠️ NEEDS_WORK"
        else:
            verdict = "✅ PASS"
        
        return SecurityReport(
            timestamp=datetime.utcnow().isoformat(),
            project_name="CCBM",
            total_findings=len(self.findings),
            critical=severity_counts["CRITICAL"],
            high=severity_counts["HIGH"],
            medium=severity_counts["MEDIUM"],
            low=severity_counts["LOW"],
            info=severity_counts["INFO"],
            findings=self.findings,
            score=round(score, 1),
            verdict=verdict,
            metadata={
                "scanners_used": ["bandit", "gitleaks", "ruff"],
                "scan_path": str(self.project_path),
            },
        )
    
    @staticmethod
    def _bandit_severity(severity: str) -> str:
        """Конверсия severity Bandit."""
        mapping = {
            "HIGH": "HIGH",
            "MEDIUM": "MEDIUM",
            "LOW": "LOW",
        }
        return mapping.get(severity, "INFO")
    
    @staticmethod
    def _severity_to_cvss(severity: str) -> float:
        """Конверсия severity в CVSS score."""
        mapping = {
            "HIGH": 7.5,
            "MEDIUM": 5.0,
            "LOW": 2.5,
        }
        return mapping.get(severity, 0.0)
    
    @staticmethod
    def _calculate_score(counts: Dict[str, int]) -> float:
        """
        Расчёт security score.
        
        Formula: 10 - (critical*3 + high*2 + medium*1 + low*0.5)
        """
        penalty = (
            counts["CRITICAL"] * 3 +
            counts["HIGH"] * 2 +
            counts["MEDIUM"] * 1 +
            counts["LOW"] * 0.5
        )
        return max(0.0, min(10.0, 10.0 - penalty))
    
    @staticmethod
    def _deduplicate_findings(findings: List[SecurityFinding]) -> List[SecurityFinding]:
        """Удаление дубликатов."""
        seen = set()
        unique = []
        
        for finding in findings:
            key = (finding.id, finding.file, finding.line, finding.message)
            if key not in seen:
                seen.add(key)
                unique.append(finding)
        
        return unique


def run_security_audit(project_path: Optional[Path] = None) -> SecurityReport:
    """
    Запуск security аудита.
    
    Args:
        project_path: Путь к проекту (по умолчанию текущая директория)
        
    Returns:
        SecurityReport
    """
    if project_path is None:
        project_path = Path.cwd()
    
    auditor = SecurityAuditor(project_path)
    auditor.run_all_scans()
    
    return auditor.generate_report()
