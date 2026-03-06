# ContextProof 2026 — Superpowers Integration

## 🎯 Настройка Superpowers для разработки CCBM

### Шаг 1: Установка Superpowers

#### Для Claude Code:
```bash
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

#### Для Cursor:
```bash
/plugin-add superpowers
```

### Шаг 2: Активация Навыков

После установки активируйте следующие навыки для работы над CCBM:

```
/using-superpowers — введение в систему
/writing-plans — создание планов реализации
/test-driven-development — TDD цикл RED-GREEN-REFACTOR
/systematic-debugging — отладка по методологии
/verification-before-completion — верификация перед завершением
```

### Шаг 3: Рабочий Процесс

1. **brainstorming** — перед проектированием компонента
2. **writing-plans** — разбивка на задачи по 2-5 минут
3. **using-git-worktrees** — создание изолированной ветки
4. **subagent-driven-development** — параллельная реализация
5. **test-driven-development** — RED-GREEN-REFACTOR
6. **requesting-code-review** — проверка перед merge
7. **verification-before-completion** — финальная верификация

### Шаг 4: Первый Запуск

```bash
# В Claude Code или Cursor выполните:
/brainstorming

Тема: Спроектировать архитектуру Criticality Analyzer для CCBM
Контекст: Классификация спанов L1-L4 (числа, политики, PII, контекст)
Требования: Поддержка казахского языка (KazRoBERTa), compliance РК
```

## 📋 Чек-лист Навыков для CCBM

| Навык | Когда Использовать |
|-------|-------------------|
| `brainstorming` | Перед каждым новым компонентом |
| `writing-plans` | После утверждения дизайна |
| `executing-plans` | Для последовательной реализации |
| `dispatching-parallel-agents` | Для параллельных задач (NER, crypto, MCP) |
| `test-driven-development` | Для каждого модуля |
| `systematic-debugging` | При проблемах с производительностью |
| `verification-before-completion` | Перед коммитом |
| `requesting-code-review` | Перед merge в main |
| `using-git-worktrees` | Для изоляции фич |
| `writing-skills` | Для создания внутренних навыков CCBM |

## 🔗 Полезные Ссылки

- [Superpowers README](https://github.com/obra/superpowers)
- [MCP Specification](https://modelcontextprotocol.io/)
- [LLMLingua GitHub](https://github.com/microsoft/LLMLingua)
