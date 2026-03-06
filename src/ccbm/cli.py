"""
CCBM CLI — Command Line Interface.

Usage:
    ccbm --help
    ccbm version
    ccbm test
"""

import argparse
import sys


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CCBM — Certified Context Budget Manager",
    )
    
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Show version",
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        choices=["version", "test", "help"],
        default="help",
        help="Command to run",
    )
    
    args = parser.parse_args()
    
    if args.version or args.command == "version":
        from ccbm import __version__
        print(f"CCBM v{__version__}")
        sys.exit(0)
    elif args.command == "test":
        print("Run: pytest tests/ -v")
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
