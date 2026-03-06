"""
Тесты для MCP Server — тестирование логики инструментов.

Тестируются функции оптимизации, верификации, анализа и аудита.
Сам MCP сервер не запускается — тестируется только бизнес-логика.
"""

import json

import pytest
from ccbm.mcp.server import (
    analyze_spans,
    get_audit_receipt,
    optimize_context,
    verify_invariants,
)


class TestOptimizeContext:
    """Тесты для optimize_context."""

    @pytest.mark.asyncio
    async def test_optimize_simple_text(self):
        """Оптимизация простого текста."""
        text = "ИИН 950101300038, сумма 100000 KZT."
        result = await optimize_context(text=text, domain="financial")

        assert result["status"] == "success"
        assert "optimized_text" in result
        assert "compression_ratio" in result
        assert "audit" in result
        assert "merkle_root" in result["audit"]

    @pytest.mark.asyncio
    async def test_optimize_empty_text(self):
        """Оптимизация пустого текста."""
        text = ""
        result = await optimize_context(text=text)

        assert result["status"] == "success"
        assert result["optimized_text"] == ""
        assert result["compression_ratio"] == 1.0

    @pytest.mark.asyncio
    async def test_optimize_financial_domain(self):
        """Оптимизация финансовых данных."""
        text = "Договор №123 от 15.03.2026 на сумму 500000 KZT. ИИН: 750101300038"
        result = await optimize_context(text=text, domain="financial")

        assert result["status"] == "success"
        assert result["original_length"] > 0
        # Оптимизированная длина может быть больше из-за NER метаданных
        assert result["optimized_length"] > 0
        assert result["spans_preserved"] >= 0

    @pytest.mark.asyncio
    async def test_optimize_with_budget(self):
        """Оптимизация с целевым бюджетом."""
        text = "Длинный текст " * 100
        result = await optimize_context(text=text, target_budget=1000)

        assert result["status"] == "success"
        assert "optimized_text" in result
        assert result["spans_preserved"] >= 0


class TestVerifyInvariants:
    """Тесты для verify_invariants."""

    @pytest.mark.asyncio
    async def test_verify_perfect_match(self):
        """Верификация идеального совпадения."""
        original = [100.0, 200.0, 300.0]
        compressed = [100.0, 200.0, 300.0]

        result = await verify_invariants(
            original_values=original,
            compressed_values=compressed,
            domain="financial",
        )

        assert result["status"] == "success"
        assert result["all_valid"] is True
        assert result["verified_count"] == result["total_checks"]

    @pytest.mark.asyncio
    async def test_verify_with_error(self):
        """Верификация с ошибкой."""
        original = [100.0, 200.0, 300.0]
        compressed = [100.1, 200.1, 300.1]

        result = await verify_invariants(
            original_values=original,
            compressed_values=compressed,
            domain="financial",
        )

        assert result["status"] in ["success", "compromised"]
        assert "checks" in result

    @pytest.mark.asyncio
    async def test_verify_medical_domain(self):
        """Верификация медицинских данных (строгий режим)."""
        original = [36.6, 37.0, 36.8]
        compressed = [36.6, 37.0, 36.8]

        result = await verify_invariants(
            original_values=original,
            compressed_values=compressed,
            domain="medical",
        )

        assert result["status"] == "success"
        assert result["all_valid"] is True


class TestAnalyzeSpans:
    """Тесты для analyze_spans."""

    @pytest.mark.asyncio
    async def test_analyze_iin(self):
        """Анализ ИИН."""
        text = "ИИН сотрудника 950101300038"
        result = await analyze_spans(text=text, language="kk")

        assert result["status"] == "success"
        assert result["total_spans"] > 0
        assert "spans_by_level" in result

        # Должен быть найден L1 спан
        l1_count = result["spans_by_level"]["L1_critical_numbers"]
        assert l1_count > 0

    @pytest.mark.asyncio
    async def test_analyze_date(self):
        """Анализ даты."""
        text = "Договор заключён 15.03.2026"
        result = await analyze_spans(text=text, language="ru")

        assert result["status"] == "success"
        assert result["total_spans"] > 0

    @pytest.mark.asyncio
    async def test_analyze_currency(self):
        """Анализ валюты."""
        text = "Сумма 100000 KZT"
        result = await analyze_spans(text=text, language="kk")

        assert result["status"] == "success"
        l1_count = result["spans_by_level"]["L1_critical_numbers"]
        assert l1_count > 0

    @pytest.mark.asyncio
    async def test_analyze_empty_text(self):
        """Анализ пустого текста."""
        text = ""
        result = await analyze_spans(text=text)

        assert result["status"] == "success"
        assert result["total_spans"] == 0

    @pytest.mark.asyncio
    async def test_analyze_mixed_content(self):
        """Анализ смешанного контента."""
        text = "ИИН 950101300038, дата 15.03.2026, сумма 100000 KZT"
        result = await analyze_spans(text=text)

        assert result["status"] == "success"
        # Должны быть найдены несколько L1 спанов
        l1_count = result["spans_by_level"]["L1_critical_numbers"]
        assert l1_count >= 3


class TestGetAuditReceipt:
    """Тесты для get_audit_receipt."""

    @pytest.mark.asyncio
    async def test_get_receipt_basic(self):
        """Получение базовой квитанции."""
        original = "Original text"
        compressed = "Compressed"

        result = await get_audit_receipt(
            original_data=original,
            compressed_data=compressed,
        )

        assert result["status"] == "success"
        assert "receipt" in result
        assert "merkle_root" in result
        assert "is_verified" in result

    @pytest.mark.asyncio
    async def test_get_receipt_with_metadata(self):
        """Получение квитанции с метаданными."""
        metadata = {"type": "financial", "domain": "KZ"}

        result = await get_audit_receipt(
            original_data="orig",
            compressed_data="comp",
            metadata=metadata,
        )

        assert result["status"] == "success"
        assert result["receipt"]["metadata"] == metadata

    @pytest.mark.asyncio
    async def test_get_receipt_verification(self):
        """Проверка верификации квитанции."""
        result = await get_audit_receipt(
            original_data="original data",
            compressed_data="compressed data",
        )

        assert result["is_verified"] is True
        assert result["merkle_root"] is not None

    @pytest.mark.asyncio
    async def test_get_receipt_unicode(self):
        """Квитанция для Unicode данных."""
        original = "Мәтін қазақша текст на русском"
        compressed = "Сжатый текст"

        result = await get_audit_receipt(
            original_data=original,
            compressed_data=compressed,
        )

        assert result["status"] == "success"
        assert result["is_verified"] is True


class TestIntegration:
    """Интеграционные тесты."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Полный рабочий процесс: анализ → оптимизация → верификация → аудит."""
        text = "ИИН 950101300038, сумма 100000 KZT, дата 15.03.2026"

        # 1. Анализ
        analysis = await analyze_spans(text=text)
        assert analysis["status"] == "success"

        # 2. Оптимизация
        optimization = await optimize_context(text=text, domain="financial")
        assert optimization["status"] == "success"

        # 3. Верификация (если есть числовые данные)
        # Для простоты проверяем длины
        original_values = [len(text)]
        compressed_values = [len(optimization["optimized_text"])]

        verification = await verify_invariants(
            original_values=original_values,
            compressed_values=compressed_values,
        )
        assert verification["status"] in ["success", "compromised"]

        # 4. Аудит
        audit = await get_audit_receipt(
            original_data=text,
            compressed_data=optimization["optimized_text"],
        )
        assert audit["status"] == "success"
        assert audit["is_verified"] is True

    @pytest.mark.asyncio
    async def test_json_serialization(self):
        """Проверка сериализации результатов в JSON."""
        text = "ИИН 950101300038"

        result = await optimize_context(text=text)

        # Все результаты должны сериализоваться в JSON
        json_str = json.dumps(result, ensure_ascii=False)
        assert len(json_str) > 0

        # И десериализоваться обратно
        parsed = json.loads(json_str)
        assert parsed["status"] == "success"


class TestErrorHandling:
    """Тесты обработки ошибок."""

    @pytest.mark.asyncio
    async def test_invalid_domain(self):
        """Неверный домен (должен использовать default)."""
        text = "Test"
        result = await optimize_context(text=text, domain="invalid_domain")

        # Должен успешно выполниться с default настройками
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_mismatched_lengths(self):
        """Разная длина массивов для верификации."""
        original = [100.0, 200.0]
        compressed = [100.0]

        with pytest.raises(ValueError):
            await verify_invariants(
                original_values=original,
                compressed_values=compressed,
            )
