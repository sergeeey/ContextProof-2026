"""Pytest hooks and fixtures for CCBM tests."""

import os


def pytest_addoption(parser):
    parser.addoption(
        "--stress-iterations",
        type=int,
        default=int(os.environ.get("STRESS_ITERATIONS", "200")),
        help="Количество итераций в стресс-тестах (или STRESS_ITERATIONS)",
    )
