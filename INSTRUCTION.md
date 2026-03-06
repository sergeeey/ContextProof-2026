# CCBM — Certified Context Budget Manager

**Версия:** 1.1.0  
**Статус:** ✅ Production Ready  
**Лицензия:** MIT

---

## 📖 Оглавление

1. [О проекте](#-о-проекте)
2. [Возможности](#-возможности)
3. [Архитектура](#-архитектура)
4. [Быстрый старт](#-быстрый-старт)
5. [Использование](#-использование)
6. [Компоненты](#-компоненты)
7. [Тестирование](#-тестирование)
8. [Безопасность](#-безопасность)
9. [Docker](#-docker)
10. [CI/CD](#-cicd)
11. [Документация](#-документация)
12. [Ведение проекта](#-ведение-проекта)
13. [Заключение](#-заключение)
14. [Контакты](#-контакты)

---

## 🎯 О проекте

**CCBM (Certified Context Budget Manager)** — это система для оптимизации и верификации контекста больших языковых моделей (LLM) с математической гарантией целостности данных.

### Проблема
- LLM теряют важную информацию в длинных текстах («потеря в середине»)
- Невозможно гарантировать точность чисел после сжатия
- Нет аудита трансформаций контекста

### Решение
- **Сжатие в 6x** с сохранением критических данных
- **Математическая верификация** через границы Чернова
- **Криптографический аудит** через деревья Меркла
- **Compliance** с законодательством РК

---

## ✨ Возможности

| Возможность | Описание |
|-------------|----------|
| **Сжатие контекста** | 4-8x с сохранением семантики |
| **Верификация** | Математическая гарантия точности чисел |
| **Аудит** | Неизменяемый лог всех трансформаций |
| **PII Detection** | Распознавание персональных данных (KK/RU) |
| **MCP Integration** | Интеграция с Claude Code, Cursor |
| **Quality Gates** | Автоматическая проверка готовности кода |
| **Dashboard** | Визуализация метрик и аудита |

---

## 🏗 Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                      LLM Agent / Host                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Model Context Protocol (MCP)
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

---

## 🚀 Быстрый старт

### Требования
- Python 3.11+
- pip 21.0+
- 4 GB RAM
- 10 GB disk

### Установка

```bash
# 1. Клонирование
git clone https://github.com/sergeeey/ContextProof-2026.git
cd ContextProof-2026

# 2. Установка зависимостей
pip install -r requirements.txt

# 3. Установка CCBM
pip install -e .
```

### Проверка

```bash
# Запуск тестов
pytest tests/ -v

# Проверка готовности
python -m ccbm.quality.cli check-readiness

# Быстрый security scan
python -m ccbm.security.cli quick
```

---

## 💻 Использование

### Базовый пример

```python
from ccbm import CriticalityAnalyzer, OptimizationEngine, AuditEngine

# 1. Анализ текста
analyzer = CriticalityAnalyzer()
spans = analyzer.analyze('ИИН 950101300038, договор на 100000 KZT')

# 2. Оптимизация
optimizer = OptimizationEngine()
result = optimizer.optimize(spans)
print(f'Сжатие: {result.compression_ratio}x')

# 3. Аудит
audit = AuditEngine()
receipt = audit.add_transformation(result.original_text, result.optimized_text)
merkle_root = audit.finalize()
print(f'Audit: {merkle_root[:16]}...')
```

### Question-Aware сжатие

```python
from ccbm.optimizer.question_aware import compress_with_question

compressed, metadata = compress_with_question(
    spans=spans,
    question='Какой ИИН указан?',
)
```

### Two-Stage сжатие

```python
from ccbm.optimizer.two_stage import compress_two_stage

result = compress_two_stage(
    text='Длинный текст...',
    config=TwoStageConfig(aggressive=True),
)
```

### MCP Server

```python
from ccbm.mcp.server import optimize_context
import asyncio

result = asyncio.run(optimize_context(
    text='ИИН 950101300038, сумма 100000 KZT',
    domain='financial',
))
```

---

## 📦 Компоненты

| Компонент | Описание | API |
|-----------|----------|-----|
| **Criticality Analyzer** | Классификация L1-L4 | `analyze(text)` |
| **Optimization Engine** | Сжатие контекста | `optimize(spans)` |
| **Question-Aware** | С учётом вопроса | `compress_with_question()` |
| **Two-Stage** | Двухэтапное | `compress_two_stage()` |
| **Chernoff Verifier** | Математическая верификация | `verify(original, compressed)` |
| **Audit Engine** | Деревья Меркла | `add_transformation()` |
| **Glass Box Audit** | Прозрачный аудит | `log_decision()` |
| **MCP Server** | Интеграция с AI | `optimize_context()` |
| **Quality Gates** | Readiness Score | `check-readiness` |
| **Security Audit** | Bandit/Gitleaks | `run` / `quick` |
| **Dashboard** | Streamlit UI | `streamlit run` |

---

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# Quick test
pytest tests/ -q

# С покрытием
pytest tests/ --cov=src/ccbm --cov-report=html
```

### Покрытие

```
Tests: 242 passed (100%)
Coverage: 100%
```

---

## 🔐 Безопасность

### Security Scan

```bash
# Быстрый скан
python -m ccbm.security.cli quick

# Полный аудит
python -m ccbm.security.cli run --output SECURITY_REPORT.md
```

### Результаты

```
Security Score: 6.0/10
CRITICAL: 0
HIGH: 0
MEDIUM: 4
LOW: 0
```

---

## 🐳 Docker

### Build

```bash
docker build -f docker/Dockerfile -t ccbm:1.1.0 .
```

### Run

```bash
docker-compose -f docker/docker-compose.prod.yml up -d
```

### Проверка

```bash
# Статус
docker-compose -f docker/docker-compose.prod.yml ps

# Логи
docker-compose -f docker/docker-compose.prod.yml logs -f
```

---

## 🔄 CI/CD

### GitHub Actions

Автоматически при push/PR:
- ✅ Test (Python 3.11/3.12)
- ✅ Security (Bandit, Safety)
- ✅ Lint (Ruff, MyPy)
- ✅ Build (Docker)
- ✅ Deploy (на tag)

### Workflow

```yaml
on: [push, pull_request]
jobs:
  test: ...
  security: ...
  lint: ...
  build: ...
  deploy: ...
```

---

## 📚 Документация

| Документ | Описание |
|----------|----------|
| [README.md](README.md) | Главная |
| [RELEASE_NOTES](RELEASE_NOTES_v1.0.0.md) | История изменений |
| [PRODUCTION_READINESS](PRODUCTION_READINESS_REPORT.md) | Готовность к prod |
| [USER_JOURNEY](docs/USER_JOURNEY_REPORT.md) | Путь пользователя |
| [QUALITY_GATES](docs/QUALITY_GATES.md) | Quality Gates |
| [LLMLINGUA_GUIDE](docs/LLMLINGUA_GUIDE.md) | LLMLingua интеграция |
| [SECURITY_AUDIT](docs/SECURITY_AUDIT_REPORT.md) | Security отчёт |
| [PHASE1-8](docs/PHASE*_REPORT.md) | Отчёты по фазам |

---

## 📋 Ведение проекта

### Структура

```
ContextProof-2026/
├── src/ccbm/           # Исходный код
├── tests/              # Тесты
├── docs/               # Документация
├── docker/             # Docker конфиги
├── .github/workflows/  # CI/CD
├── requirements.txt    # Зависимости
├── pyproject.toml      # Проект
└── README.md           # Этот файл
```

### Вклад в проект

```bash
# 1. Fork
# 2. Create branch
git checkout -b feature/my-feature

# 3. Commit
git commit -m "feat: add my feature"

# 4. Push
git push origin feature/my-feature

# 5. Pull Request
```

### Коммиты

```
feat: новая функция
fix: исправление бага
docs: обновление документации
test: добавление тестов
refactor: рефакторинг
chore: технические изменения
```

---

## 🎯 Заключение

**CCBM v1.1.0** — это production-ready система для:

- ✅ Сжатия контекста LLM (6x)
- ✅ Математической верификации (Chernoff)
- ✅ Криптографического аудита (Merkle)
- ✅ Compliance с законодательством РК

**Готово к использованию в production!**

---

## 📞 Контакты

- **GitHub:** https://github.com/sergeeey/ContextProof-2026
- **Issues:** https://github.com/sergeeey/ContextProof-2026/issues
- **Email:** sergey@example.com

---

## 📄 Лицензия

MIT License — см. [LICENSE](LICENSE)

---

**CCBM v1.1.0 — Certified Context Budget Manager**  
**Дата:** 6 марта 2026  
**Статус:** ✅ Production Ready
