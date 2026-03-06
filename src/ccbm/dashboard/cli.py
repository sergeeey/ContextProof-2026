"""
CCBM Dashboard CLI

Запуск Dashboard для визуализации метрик.
"""

import argparse
import sys
import subprocess


def cmd_run(args):
    """Запуск Dashboard."""
    print("🚀 Запуск CCBM Dashboard...")
    print("=" * 60)
    
    try:
        # Запуск Streamlit
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "-m", "ccbm.dashboard.app"],
            cwd=args.project,
        )
    except KeyboardInterrupt:
        print("\n👋 Dashboard остановлен")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="CCBM Dashboard CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # run
    parser_run = subparsers.add_parser(
        "run",
        help="Запустить Dashboard",
    )
    parser_run.add_argument(
        "--project", "-p",
        default=".",
        help="Путь к проекту",
    )
    parser_run.set_defaults(func=cmd_run)
    
    # Parse and execute
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
