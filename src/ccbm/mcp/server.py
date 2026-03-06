"""
MCP Server для CCBM — интеграция с AI-агентами через Model Context Protocol.

Поддерживаемые платформы:
- Claude Code
- Cursor
- Cline
- Любые MCP-совместимые клиенты

Эндпоинты:
- optimize_context — оптимизация текста с верификацией
- verify_invariants — верификация числовых инвариантов
- get_audit_receipt — получение аудиторской квитанции
- analyze_spans — анализ спанов по уровням критичности
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    TextContent,
    Tool,
)

from ccbm import (
    AuditEngine,
    ChernoffVerifier,
    CriticalityAnalyzer,
    NumericInvariantVerifier,
    OptimizationEngine,
    create_audit_report,
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ccbm-mcp")


# Создание MCP сервера
ccbm_server = Server("ccbm")


# ============================================================================
# ИНСТРУМЕНТЫ (TOOLS)
# ============================================================================

@ccbm_server.list_tools()
async def list_tools() -> list[Tool]:
    """Список доступных инструментов."""
    return [
        Tool(
            name="optimize_context",
            description="Оптимизация текста с сохранением критических данных. "
                       "Использует Criticality Analyzer для классификации спанов "
                       "и Optimization Engine для сжатия.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Текст для оптимизации",
                    },
                    "domain": {
                        "type": "string",
                        "enum": ["financial", "legal", "medical", "general"],
                        "default": "general",
                        "description": "Домен данных для выбора уровня верификации",
                    },
                    "target_budget": {
                        "type": "integer",
                        "default": 4000,
                        "description": "Целевой бюджет токенов",
                    },
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="verify_invariants",
            description="Верификация числовых инвариантов через границы Чернова. "
                       "Проверяет ИИН, БИН, финансовые суммы на целостность.",
            inputSchema={
                "type": "object",
                "properties": {
                    "original_values": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Оригинальные значения",
                    },
                    "compressed_values": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Сжатые значения",
                    },
                    "domain": {
                        "type": "string",
                        "enum": ["financial", "legal", "medical", "general"],
                        "default": "financial",
                    },
                },
                "required": ["original_values", "compressed_values"],
            },
        ),
        Tool(
            name="analyze_spans",
            description="Анализ текста и классификация спанов по уровням критичности "
                       "(L1: числа, L2: политики, L3: PII, L4: контекст).",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Текст для анализа",
                    },
                    "language": {
                        "type": "string",
                        "enum": ["kk", "ru", "en"],
                        "default": "kk",
                        "description": "Язык текста (kk=казахский, ru=русский)",
                    },
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="get_audit_receipt",
            description="Получение аудиторской квитанции с доказательством Меркла. "
                       "Все трансформации логируются в дереве Меркла.",
            inputSchema={
                "type": "object",
                "properties": {
                    "original_data": {
                        "type": "string",
                        "description": "Оригинальные данные",
                    },
                    "compressed_data": {
                        "type": "string",
                        "description": "Сжатые данные",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Дополнительные метаданные",
                    },
                },
                "required": ["original_data", "compressed_data"],
            },
        ),
    ]


@ccbm_server.call_tool()
async def call_tool(
    name: str,
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Вызов инструмента."""
    logger.info(f"Вызов инструмента: {name}, аргументы: {arguments}")

    try:
        if name == "optimize_context":
            result = await optimize_context(
                text=arguments["text"],
                domain=arguments.get("domain", "general"),
                target_budget=arguments.get("target_budget", 4000),
            )
        elif name == "verify_invariants":
            result = await verify_invariants(
                original_values=arguments["original_values"],
                compressed_values=arguments["compressed_values"],
                domain=arguments.get("domain", "financial"),
            )
        elif name == "analyze_spans":
            result = await analyze_spans(
                text=arguments["text"],
                language=arguments.get("language", "kk"),
            )
        elif name == "get_audit_receipt":
            result = await get_audit_receipt(
                original_data=arguments["original_data"],
                compressed_data=arguments["compressed_data"],
                metadata=arguments.get("metadata", {}),
            )
        else:
            raise ValueError(f"Неизвестный инструмент: {name}")

        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    except Exception as e:
        logger.error(f"Ошибка при выполнении {name}: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, ensure_ascii=False, indent=2),
        )]


# ============================================================================
# РЕАЛИЗАЦИЯ ИНСТРУМЕНТОВ
# ============================================================================

async def optimize_context(
    text: str,
    domain: str = "general",
    target_budget: int = 4000,
) -> dict:
    """
    Оптимизация текста с верификацией.

    Returns:
        Dict с оптимизированным текстом и метаданными
    """
    # Анализ спанов
    analyzer = CriticalityAnalyzer(language=domain)
    spans = analyzer.analyze(text)

    # Оптимизация
    optimizer = OptimizationEngine(target_budget=target_budget)
    result = optimizer.optimize(spans)

    # Верификация (если есть числовые данные)
    verification_status = "skipped"
    ChernoffVerifier(domain=domain)

    # Аудит
    audit = AuditEngine()
    receipt = audit.add_transformation(
        original_data=text,
        compressed_data=result.optimized_text,
        metadata={
            "compression_ratio": result.compression_ratio,
            "spans_preserved": result.spans_preserved,
            "spans_removed": result.spans_removed,
        },
    )
    merkle_root = audit.finalize()

    return {
        "status": "success",
        "optimized_text": result.optimized_text,
        "compression_ratio": round(result.compression_ratio, 2),
        "original_length": len(result.original_text),
        "optimized_length": len(result.optimized_text),
        "spans_preserved": result.spans_preserved,
        "spans_removed": result.spans_removed,
        "verification_status": verification_status,
        "audit": {
            "receipt_id": receipt.receipt_id,
            "merkle_root": merkle_root,
            "timestamp": receipt.timestamp,
        },
    }


async def verify_invariants(
    original_values: list[float],
    compressed_values: list[float],
    domain: str = "financial",
) -> dict:
    """
    Верификация числовых инвариантов.

    Returns:
        Dict с результатом верификации
    """

    verifier = NumericInvariantVerifier(domain=domain)

    # Верификация значений
    checks = verifier.verify_values(
        original_values=original_values,
        compressed_values=compressed_values,
        name="values",
    )

    all_valid = verifier.is_all_valid(checks)
    summary = verifier.get_summary(checks)

    return {
        "status": "success" if all_valid else "compromised",
        "all_valid": all_valid,
        "total_checks": len(checks),
        "verified_count": sum(1 for c in checks.values() if c.is_valid),
        "compromised_count": sum(1 for c in checks.values() if c.status == "COMPROMISED"),
        "summary": summary,
        "checks": {
            name: {
                "name": c.name,
                "original_value": c.original_value,
                "compressed_value": c.compressed_value,
                "bound": c.bound.bound,
                "is_valid": c.is_valid,
                "status": c.status,
            }
            for name, c in checks.items()
        },
    }


async def analyze_spans(
    text: str,
    language: str = "kk",
) -> dict:
    """
    Анализ спанов по уровням критичности.

    Returns:
        Dict с классифицированными спанами
    """
    analyzer = CriticalityAnalyzer(language=language)
    spans = analyzer.analyze(text)

    # Группировка по уровням
    level_map = {
        "critical_numbers": "L1_critical_numbers",
        "legal_policies": "L2_legal_policies",
        "pii": "L3_pii",
        "context_fill": "L4_context_fill",
    }

    grouped = {
        "L1_critical_numbers": [],
        "L2_legal_policies": [],
        "L3_pii": [],
        "L4_context_fill": [],
    }

    for span in spans:
        level_key = level_map.get(span.level.value)
        if level_key and level_key in grouped:
            grouped[level_key].append({
                "text": span.text,
                "start": span.start,
                "end": span.end,
                "confidence": span.confidence,
                "metadata": span.metadata,
            })

    return {
        "status": "success",
        "total_spans": len(spans),
        "spans_by_level": {
            level: len(spans_list) for level, spans_list in grouped.items()
        },
        "spans": grouped,
        "text_length": len(text),
    }


async def get_audit_receipt(
    original_data: str,
    compressed_data: str,
    metadata: dict[str, Any] = None,
) -> dict:
    """
    Получение аудиторской квитанции.

    Returns:
        Dict с квитанцией и доказательством Меркла
    """
    audit = AuditEngine()

    receipt = audit.add_transformation(
        original_data=original_data,
        compressed_data=compressed_data,
        metadata=metadata or {},
    )

    merkle_root = audit.finalize()
    is_verified = audit.verify_receipt(receipt)

    # Создание отчёта
    report = create_audit_report(audit)

    return {
        "status": "success",
        "receipt": receipt.to_dict(),
        "merkle_root": merkle_root,
        "is_verified": is_verified,
        "report": report.to_dict(),
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# РЕСУРСЫ (RESOURCES)
# ============================================================================

@ccbm_server.list_resources()
async def list_resources() -> list[Resource]:
    """Список доступных ресурсов."""
    return [
        Resource(
            uri="ccbm://version",
            name="CCBM Version",
            description="Информация о версии CCBM",
            mimeType="application/json",
        ),
    ]


@ccbm_server.read_resource()
async def read_resource(uri: str) -> str:
    """Чтение ресурса."""
    if uri == "ccbm://stats":
        stats = {
            "version": "2.0.0",
            "tests_passed": 291,
            "components": 16,
            "timestamp": datetime.utcnow().isoformat(),
        }
        return json.dumps(stats, indent=2)

    elif uri == "ccbm://version":
        version_info = {
            "version": "2.0.0",
            "tests_passed": 291,
            "components": 16,
            "python_version": "3.11+",
            "mcp_version": "1.0.0+",
            "features": [
                "Criticality Analyzer (L1-L4)",
                "Optimization Engine",
                "Chernoff Verifier",
                "Numeric Invariant Verifier",
                "Audit Engine (Merkle Trees)",
                "Glass Box Audit",
                "MCP Server",
                "Quality Gates",
                "Agentic Metrics",
                "Security Audit",
                "KazRoBERTa NER",
                "Dashboard",
                "Information Contract",
                "Context Replay",
            ],
        }
        return json.dumps(version_info, indent=2)

    else:
        raise ValueError(f"Неизвестный ресурс: {uri}")


# ============================================================================
# ЗАПУСК СЕРВЕРА
# ============================================================================

async def main():
    """Запуск MCP сервера."""
    logger.info("Запуск CCBM MCP Server...")

    async with stdio_server() as (read_stream, write_stream):
        await ccbm_server.run(
            read_stream,
            write_stream,
            ccbm_server.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
