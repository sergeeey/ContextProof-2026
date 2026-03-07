"""
Стресс-тесты CCBM: массовые вызовы analyzer, optimizer, verifier, MCP-потоков.

Запуск:
  PYTHONPATH=src pytest tests/test_stress_ccbm.py -v -s
  PYTHONPATH=src pytest tests/test_stress_ccbm.py -v --stress-iterations=500
"""
from __future__ import annotations

import asyncio
import time
from itertools import cycle

import pytest

# Количество итераций по умолчанию (можно переопределить через --stress-iterations)
STRESS_ITERATIONS = 200


@pytest.fixture(scope="module")
def stress_iterations(request):
    return getattr(
        request.config.option,
        "stress_iterations",
        STRESS_ITERATIONS,
    )


# --- Синхронные стресс-тесты ---


class TestStressAnalyzer:
    """Массовые вызовы CriticalityAnalyzer."""

    def test_analyzer_many_texts(self, stress_iterations):
        from ccbm import CriticalityAnalyzer

        analyzer = CriticalityAnalyzer(language="kk")
        samples = [
            "ИИН 950101300038, договор на 100000 KZT от 01.01.2025.",
            "Клиент Иванов И.И., тел. +7 777 123 4567, сумма 50 000 ₸.",
            "",
            "A" * 500,
            "1. Пункт один. 2. Пункт два. 3. Пункт три. " * 20,
        ]
        start = time.perf_counter()
        for i, text in enumerate(cycle(samples)):
            if i >= stress_iterations:
                break
            spans = analyzer.analyze(text)
            assert isinstance(spans, list)
        elapsed = time.perf_counter() - start
        assert elapsed > 0
        assert elapsed < 120, f"Analyzer stress too slow: {elapsed:.1f}s"


class TestStressOptimizer:
    """Массовые вызовы OptimizationEngine."""

    def test_optimizer_many_batches(self, stress_iterations):
        from ccbm import CriticalityAnalyzer, OptimizationEngine

        analyzer = CriticalityAnalyzer(language="kk")
        optimizer = OptimizationEngine(target_budget=2000)
        text = "ИИН 950101300038. Сумма 100000 KZT. " + "Дополнительный контекст. " * 30
        spans = analyzer.analyze(text)
        start = time.perf_counter()
        for _ in range(stress_iterations):
            result = optimizer.optimize(spans)
            assert result.optimized_text is not None
            assert result.compression_ratio >= 0
        elapsed = time.perf_counter() - start
        assert elapsed < 120, f"Optimizer stress too slow: {elapsed:.1f}s"


class TestStressVerifiers:
    """Массовые вызовы Chernoff и NumericInvariantVerifier."""

    def test_chernoff_many_verify(self, stress_iterations):
        import numpy as np
        from ccbm import ChernoffVerifier

        verifier = ChernoffVerifier(domain="financial")
        orig = np.array([100.0, 200.0, 300.0])
        comp = np.array([100.0, 200.0, 300.0])
        start = time.perf_counter()
        for _ in range(stress_iterations):
            bound = verifier.verify(orig, comp, data_name="stress")
            assert bound.is_certified in (True, False)
        elapsed = time.perf_counter() - start
        assert elapsed < 60, f"Chernoff stress too slow: {elapsed:.1f}s"

    def test_numeric_invariant_many_verify(self, stress_iterations):
        from ccbm import NumericInvariantVerifier

        verifier = NumericInvariantVerifier(domain="financial")
        orig = [100.0, 200.0, 300.0]
        comp = [100.0, 200.0, 300.0]
        start = time.perf_counter()
        for _ in range(stress_iterations):
            checks = verifier.verify_values(orig, comp, name="stress")
            assert verifier.is_all_valid(checks) is True
        elapsed = time.perf_counter() - start
        assert elapsed < 60, f"NumericInvariant stress too slow: {elapsed:.1f}s"


class TestStressAudit:
    """Массовые трансформации и finalize в AuditEngine."""

    def test_audit_many_transformations(self, stress_iterations):
        from ccbm import AuditEngine

        n = min(stress_iterations, 100)
        engine = AuditEngine()
        start = time.perf_counter()
        for i in range(n):
            engine.add_transformation(
                original_data=f"original_{i}",
                compressed_data=f"compressed_{i}",
                metadata={"i": i},
            )
        root = engine.finalize()
        assert root is not None
        elapsed = time.perf_counter() - start
        assert elapsed < 30, f"Audit stress too slow: {elapsed:.1f}s"


# --- Асинхронные стресс-тесты (MCP-подобный поток) ---


class TestStressMCPFlow:
    """Стресс асинхронных вызовов optimize_context, analyze_spans, verify_invariants."""

    @pytest.mark.asyncio
    async def test_optimize_context_many_calls(self, stress_iterations):
        from ccbm.mcp.server import optimize_context

        n = min(stress_iterations, 50)
        start = time.perf_counter()
        for i in range(n):
            result = await optimize_context(
                text=f"ИИН 950101300038. Сумма {1000 + i} KZT. Текст для сжатия. " * 5,
                domain="financial",
                target_budget=1000,
            )
            assert result.get("status") == "success"
            assert "optimized_text" in result
        elapsed = time.perf_counter() - start
        assert elapsed < 120, f"MCP optimize_context stress too slow: {elapsed:.1f}s"

    @pytest.mark.asyncio
    async def test_analyze_spans_many_calls(self, stress_iterations):
        from ccbm.mcp.server import analyze_spans

        n = min(stress_iterations, 100)
        start = time.perf_counter()
        for i in range(n):
            result = await analyze_spans(
                text=f"Документ {i}. ИИН 950101300038. Сумма 100000 KZT.",
                language="kk",
            )
            assert result.get("status") == "success"
            assert "spans_by_level" in result
        elapsed = time.perf_counter() - start
        assert elapsed < 90, f"MCP analyze_spans stress too slow: {elapsed:.1f}s"

    @pytest.mark.asyncio
    async def test_verify_invariants_many_calls(self, stress_iterations):
        from ccbm.mcp.server import verify_invariants

        orig = [10.0, 20.0, 30.0]
        comp = [10.0, 20.0, 30.0]
        start = time.perf_counter()
        for _ in range(stress_iterations):
            result = await verify_invariants(
                original_values=orig,
                compressed_values=comp,
                domain="financial",
            )
            assert result.get("status") in ("success", "compromised")
            assert result.get("all_valid") is True
        elapsed = time.perf_counter() - start
        assert elapsed < 60, f"MCP verify_invariants stress too slow: {elapsed:.1f}s"

    @pytest.mark.asyncio
    async def test_concurrent_analyze_spans(self, stress_iterations):
        from ccbm.mcp.server import analyze_spans

        n = min(stress_iterations, 30)
        start = time.perf_counter()
        tasks = [
            analyze_spans(text=f"Текст {i}. ИИН 950101300038.", language="kk")
            for i in range(n)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.perf_counter() - start
        failures = [r for r in results if isinstance(r, Exception)]
        assert not failures, f"Concurrent analyze_spans failed: {failures[:3]}"
        assert all(isinstance(r, dict) and r.get("status") == "success" for r in results)
        assert elapsed < 60, f"Concurrent stress too slow: {elapsed:.1f}s"
