# CCBM Release Notes v2.0.1

**Дата релиза:** 7 марта 2026  
**Версия:** 2.0.1  
**Тег:** `v2.0.1`  
**Коммит релиза:** `016adb4`

---

## Что вошло в релиз

- Стабилизация production-gates: тесты, линт, сборка, типизация.
- Исправлен fallback для optional-компонентов (`llmlingua`, question-aware, NER), чтобы окружение без тяжелых ML-зависимостей не падало.
- Обновлен CI workflow: блокирующие проверки отделены от отчетных.
- Исправлены timezone-aware timestamp пути (`datetime.now(datetime.UTC)`).
- Приведены к一致ию зависимости и конфиги (`requirements.txt`, `pyproject.toml`).

---

## Проверки (артефакты)

- `pytest -q` -> `291 passed`
- `ruff check src tests` -> `0 issues`
- `mypy src` -> `Success: no issues found in 33 source files`
- `python -m build` -> `Successfully built ccbm-2.0.0.tar.gz and ccbm-2.0.0-py3-none-any.whl`

---

## Известные некритичные замечания

- В тестах остаются 2 предупреждения NumPy для edge-case с пустым массивом (`Mean of empty slice`, `invalid value encountered in scalar divide`).
- На функциональность релиза не влияет.

---

## CI/CD статус

- `master` запушен в `origin/master`.
- Тег `v2.0.1` запушен в `origin/v2.0.1`.

---

## Измененные области

- CI: `.github/workflows/ci.yml`
- Packaging/config: `pyproject.toml`, `requirements.txt`
- Core modules: `src/ccbm/*` (analyzer, optimizer, audit, metrics, mcp, replay, security, verifier, quality)
- Tests: `tests/test_*` (импорт/формат/совместимость)
