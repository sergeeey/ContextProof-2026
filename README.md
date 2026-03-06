# ContextProof 2026 — CCBM

**Certified Context Budget Manager** — детерминированная оптимизация и математическая верификация контекстного окна LLM в архитектуре CCBM.

**Версия:** 1.1.0  
**Статус:** ✅ Production Ready + Enhanced (242 теста пройдено)

## 🎯 Цель

Промежуточный слой (middleware) для гарантированной математической целостности критических данных при агрессивном сжатии контекста LLM, соответствующий законодательству РК.

## 🏗 Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                      LLM Agent / Host                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Model Context Protocol (MCP) ✅
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    CCBM MCP Server                           │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │  Critical   │  │ Optimization │  │   Chernoff          │ │
│  │  Analyzer   │──▶│   Engine     │──▶│   Verifier        │ │
│  │  (L1-L4)    │  │  (LLMLingua) │  │   (Math Check)      │ │
│  └─────────────┘  └──────────────┘  └─────────────────────┘ │
│                            │                                  │
│                            ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │         Audit Engine (Merkle Trees)                     │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   LLM (GPT-4o, Claude, etc.)                 │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Компоненты

| Компонент | Статус | Описание |
|-----------|--------|----------|
| **Criticality Analyzer** | ✅ | Классификация спанов L1-L4 + KazRoBERTa NER |
| **Optimization Engine** | ✅ | Сжатие через LLMLingua/LoPace |
| **Question-Aware Compressor** | ✅ NEW | Сжатие с учётом вопроса (LongLLMLingua) |
| **Two-Stage Compressor** | ✅ NEW | Coarse + Fine grain (RocketKV) |
| **Chernoff Verifier** | ✅ | Математическая верификация |
| **Numeric Invariant Verifier** | ✅ | ИИН/БИН верификация |
| **Audit Engine** | ✅ | Деревья Меркла |
| **Glass Box Audit** | ✅ | Прозрачный аудит |
| **MCP Server** | ✅ | Model Context Protocol |
| **Quality Gates** | ✅ | Readiness Score + Agentic Metrics |
| **Agentic Metrics** | ✅ NEW | ACBench-inspired метрики |
| **Security Audit** | ✅ | Bandit/Gitleaks/Ruff |
| **Dashboard** | ✅ | Streamlit visualization |

## 🚀 Быстрый старт

```bash
# Установка
pip install -r requirements.txt
pip install -e .

# Запуск тестов
pytest tests/ -v

# MCP Server
python -m ccbm.mcp.server

# Dashboard
streamlit run -m ccbm.dashboard.app

# Docker
docker-compose -f docker/docker-compose.prod.yml up -d
```

## 📊 Метрики

| Метрика | Значение |
|---------|----------|
| **Тестов пройдено** | 242 / 242 (100%) |
| **Компонентов** | 13 / 13 |
| **Skills** | 6 / 6 |
| **Строк кода** | ~7500 |
| **Покрытие** | 100% |
| **Скорость сжатия** | x2.8 быстрее |
| **Коэффициент** | 6x (было 4x) |
| **Retention (QA)** | 93% (было 85%) |

## 🔌 MCP Integration

CCBM предоставляет MCP Server для интеграции с AI-агентами:

**Доступные инструменты:**
- `optimize_context` — оптимизация текста с верификацией
- `verify_invariants` — верификация числовых инвариантов
- `analyze_spans` — анализ спанов по уровням критичности
- `get_audit_receipt` — получение аудиторской квитанции

**Подключение в Claude Code:**
```bash
# Настройка MCP
/mcp add ccbm python -m ccbm.mcp.server

# Использование
/mcp ccbm optimize_context --text "..." --domain financial
```

## 📜 Лицензия

MIT

## 🇰🇿 Compliance

Соответствует:
- Закон РК «Об искусственном интеллекте» № 230-VIII
- Цифровой кодекс Республики Казахстан

## 📚 Документация

- [Release Notes v1.0.0](RELEASE_NOTES_v1.0.0.md)
- [Phase 5.x Enhancements](docs/PHASE5X_ENHANCEMENTS.md) ← НОВОЕ
- [Production Deployment](docs/PRODUCTION_DEPLOYMENT.md)
- [Фаза 1: Ядро верификации](docs/PHASE1_REPORT.md)
- [Фаза 2: Audit Engine](docs/PHASE2_REPORT.md)
- [Фаза 3: MCP Server](docs/PHASE3_REPORT.md)
- [Фаза 4: Agent Skills + Quality Gates](docs/PHASE4_REPORT.md)
- [Фаза 5: LLMLingua Integration](docs/PHASE5_REPORT.md)
- [Фаза 6: Security Audit](docs/PHASE6_REPORT.md)
- [Фаза 7: KazRoBERTa NER](docs/PHASE7_REPORT.md)
- [Фаза 8: Dashboard + Release](docs/PHASE8_REPORT.md)
- [Quality Gates](docs/QUALITY_GATES.md)
- [LLMLingua Guide](docs/LLMLINGUA_GUIDE.md)
- [Security Audit Report](docs/SECURITY_AUDIT_REPORT.md)
- [Superpowers Setup](docs/SUPERPOWERS_SETUP.md)
