"""
CCBM Security Audit CLI

Запуск аудита безопасности и генерация отчётов.
"""

import argparse
import sys
from pathlib import Path

from .audit import run_security_audit, SecurityReport


def cmd_run(args):
    """Запуск аудита."""
    project_path = Path(args.project) if args.project else Path.cwd()
    
    print(f"🔍 Security Audit для: {project_path}")
    print("=" * 60)
    
    report = run_security_audit(project_path)
    
    # Вывод summary
    print(f"\n📊 Summary:")
    print(f"  🔴 CRITICAL: {report.critical}")
    print(f"  🟠 HIGH: {report.high}")
    print(f"  🟡 MEDIUM: {report.medium}")
    print(f"  🟢 LOW: {report.low}")
    print(f"  ℹ️ INFO: {report.info}")
    print(f"  TOTAL: {report.total_findings}")
    print(f"\n🏆 Score: {report.score}/10 — {report.verdict}")
    
    # Сохранение отчёта
    if args.output:
        output_path = Path(args.output)
        
        if output_path.suffix == ".json":
            with open(output_path, "w", encoding="utf-8") as f:
                import json
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        elif output_path.suffix == ".md":
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report.to_markdown())
        else:
            # По умолчанию JSON
            with open(output_path.with_suffix(".json"), "w", encoding="utf-8") as f:
                import json
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Отчёт сохранён: {output_path}")
    
    # Exit code
    if report.critical > 0:
        sys.exit(2)
    elif report.high > 0:
        sys.exit(1)
    else:
        sys.exit(0)


def cmd_quick(args):
    """Быстрый аудит (только Bandit)."""
    from .audit import SecurityAuditor
    
    project_path = Path(args.project) if args.project else Path.cwd()
    auditor = SecurityAuditor(project_path)
    
    print(f"⚡ Quick Security Scan для: {project_path}")
    print("=" * 60)
    
    findings = auditor.run_bandit()
    
    print(f"\n📊 Найдено проблем: {len(findings)}")
    
    for finding in findings[:10]:
        severity_icon = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
        }.get(finding.severity, "⚪")
        
        print(f"  {severity_icon} {finding.id}: {finding.message}")
        print(f"     📍 {finding.file}:{finding.line}")
    
    if len(findings) > 10:
        print(f"  ... и ещё {len(findings) - 10}")
    
    sys.exit(0 if len(findings) == 0 else 1)


def main():
    parser = argparse.ArgumentParser(
        description="CCBM Security Audit CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # run (full audit)
    parser_run = subparsers.add_parser(
        "run",
        help="Полный security аудит",
    )
    parser_run.add_argument(
        "--project", "-p",
        default=".",
        help="Путь к проекту",
    )
    parser_run.add_argument(
        "--output", "-o",
        help="Путь к файлу отчёта (.json или .md)",
    )
    parser_run.set_defaults(func=cmd_run)
    
    # quick (quick scan)
    parser_quick = subparsers.add_parser(
        "quick",
        help="Быстрый скан (только Bandit)",
    )
    parser_quick.add_argument(
        "--project", "-p",
        default=".",
        help="Путь к проекту",
    )
    parser_quick.set_defaults(func=cmd_quick)
    
    # Parse and execute
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
