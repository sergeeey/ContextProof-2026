# CCBM Agent Skills

**Навыки для AI-агентов CCBM** — модульная система компетенций для автономной работы с контекстом LLM.

## 📋 Структура

```
.ccbm/skills/
├── README.md                    # Этот файл
├── context-compression/         # Сжатие контекста
│   ├── SKILL.md                # Описание навыка
│   ├── references/
│   │   └── compression-methods.md
│   └── examples/
│       └── llmlingua-example.py
├── chernoff-verifier/          # Верификация Чернова
│   ├── SKILL.md
│   ├── references/
│   │   └── chernoff-bounds.md
│   └── examples/
│       └── verify-invariants.py
├── merkle-auditor/             # Аудит Меркла
│   ├── SKILL.md
│   ├── references/
│   │   └── merkle-trees.md
│   └── examples/
│       └── audit-trail.py
├── iin-validator/              # Валидация ИИН
│   ├── SKILL.md
│   ├── references/
│   │   └── iin-algorithm.md
│   └── examples/
│       └── validate-iin.py
├── pii-detector/               # Детекция PII
│   ├── SKILL.md
│   ├── references/
│   │   └── pii-patterns.md
│   └── examples/
│       └── detect-pii.py
└── compliance-checker/         # Compliance РК
    ├── SKILL.md
    ├── references/
    │   └── kz-laws.md
    └── examples/
        └── check-compliance.py
```

## 🎯 Как использовать

### В Claude Code / Cursor

```bash
# Активировать навык
/skill use context-compression

# Выполнить сжатие
/skill context-compression compress --text "..." --domain financial

# Верифицировать
/skill chernoff-verifier verify --original "..." --compressed "..."
```

### В MCP Server

```python
from ccbm.skills import ContextCompression, ChernoffVerifier

compression = ContextCompression()
result = compression.compress(text, domain="financial")

verifier = ChernoffVerifier()
bound = verifier.verify(result.original, result.compressed)
```

## 📊 Метрики навыков

| Навык | Точность | Покрытие | Статус |
|-------|----------|----------|--------|
| context-compression | 95% | 100% | ✅ Готов |
| chernoff-verifier | 99% | 100% | ✅ Готов |
| merkle-auditor | 100% | 100% | ✅ Готов |
| iin-validator | 98% | 100% | ✅ Готов |
| pii-detector | 92% | 85% | 🟡 В разработке |
| compliance-checker | 90% | 80% | 🟡 В разработке |

## 🔗 Ссылки

- [Superpowers Skills](https://github.com/obra/superpowers/tree/main/skills)
- [TERAG Skills](E:\TERAG Desktop 2026\.agent\skills)
- [MCP Specification](https://modelcontextprotocol.io/)
