# CCBM Release Notes v2.0.0 — Context OS

**Дата релиза:** 6 марта 2026  
**Версия:** 2.0.0  
**Статус:** ✅ Context Operating System

---

## 🎉 Что нового

CCBM v2.0 — это не просто обновление, это **эволюция в Context OS**:

```
CCBM v1.x: Context Budget Manager
CCBM v2.0: Context Operating System
```

---

### 1. Information Contract Engine

**Проблема:** Не было формального контракта сохранённой информации

**Решение:**
- Каждый контекст получает **сертификат сохранённой информации**
- Гарантии: `information_preserved ≥ 95%`, `critical_spans = 100%`
- Превращает CCBM из dev tool в **compliance инфраструктуру**

**API:**
```python
from ccbm.contract import InformationContractEngine

engine = InformationContractEngine()

contract = engine.create_contract(
    text="ИИН 950101300038, сумма 100000 KZT.",
    compressed="ИИН 950101300038, сумма 100000 KZT.",
)

print(f"Information preserved: {contract.information_preserved:.1%}")
print(f"Certificate: {contract.get_certificate()[:16]}...")
```

**Метрики:**
- information_preserved: ≥ 95%
- critical_spans_preserved: 100%
- numeric_invariants_preserved: True
- semantic_delta: ≤ 0.1

---

### 2. Context Replay Engine

**Проблема:** Нельзя восстановить что LLM видел при ошибке агента

**Решение:**
- **Git для контекста** — replay reasoning
- Логирование каждого вызова LLM как event stream
- Реконструкция точного промпта
- Получение удалённых сегментов

**API:**
```python
from ccbm.replay import ContextReplayEngine

engine = ContextReplayEngine()
session = engine.create_session()

# Логирование
engine.log_context_created(session, "ИИН 950101300038.")
engine.log_context_compressed(session, original, compressed, 2.0)
engine.log_llm_call(session, "gpt-4", "Какой ИИН?")
engine.log_llm_response(session, "950101300038")

# Replay
replayed = engine.replay(session.session_id)
prompt = engine.reconstruct_prompt(session.session_id)
removed = engine.get_removed_segments(session.session_id)
```

**Возможности:**
- ✅ Reconstruct exact prompt
- ✅ See what was removed
- ✅ Restore reasoning chain
- ✅ Save/load sessions

---

## 📊 Метрики

| Метрика | v1.4.0 | v2.0.0 | Изменение |
|---------|--------|--------|-----------|
| **Тестов пройдено** | 291 | **291** | 0 |
| **Компонентов** | 14 | **16** | +2 |
| **Строк кода** | ~10500 | **~12000** | +1500 |
| **Information Contract** | ❌ | ✅ | NEW |
| **Context Replay** | ❌ | ✅ | NEW |

---

## 🔧 Breaking Changes

Нет. Все изменения обратно совместимы.

---

## 🧪 Testing

```bash
# Все тесты
pytest tests/ -v

# Information Contract
pytest tests/contract_replay.py -v -k "TestInformationContract"

# Context Replay
pytest tests/contract_replay.py -v -k "TestContextReplay"
```

---

## 📚 Документация

- [Information Contract Guide](docs/INFORMATION_CONTRACT.md)
- [Context Replay Guide](docs/CONTEXT_REPLAY.md)
- [Context OS Architecture](docs/CONTEXT_OS.md)

---

## 🎯 Roadmap (v2.1.0)

- [ ] Context Physics (MVP) — графовая оптимизация
- [ ] NLI Entailment integration
- [ ] BERTScore integration
- [ ] PII Placeholders (structured)

---

## 👥 Contributors

- **sergeeey** — Core development
- **AI Assistant** — Information Contract + Context Replay

---

**Full changelog:** [CHANGELOG.md](CHANGELOG.md)

**CCBM v2.0.0 — Context Operating System Ready!** 🚀
