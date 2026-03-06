# CCBM Quality Gates

**Formal Verification System** для CCBM — система гарантий качества кода.

## 🎯 Назначение

Объективная оценка готовности кода к merge через формулу Readiness Score.

## 📊 Readiness Score Formula

```
Readiness Score = 0.30 × Correctness
                + 0.25 × Validation
                + 0.20 × Coverage
                + 0.15 × Monitoring
                + 0.10 × Documentation
```

### Компоненты

| Компонент | Вес | Метрики |
|-----------|-----|---------|
| **Correctness** | 30% | Tests pass, type check, lint clean |
| **Validation** | 25% | Golden set, security scan |
| **Coverage** | 20% | Line coverage, branch coverage |
| **Monitoring** | 15% | Performance benchmarks |
| **Documentation** | 10% | Docstrings, API docs, changelog |

## 🚦 Verdict Thresholds

| Score | Verdict | Action |
|-------|---------|--------|
| **≥ 0.95** | ✅ MERGE APPROVED | Merge без ограничений |
| **≥ 0.90** | ⚠️ MERGE + Monitoring | Merge + performance monitoring |
| **≥ 0.80** | 🔧 REWORK | Доработать перед merge |
| **< 0.80** | ❌ REJECT | Отклонить PR |

## 📋 PR Classification

### CRITICAL (threshold: 0.95)

Изменения в критических компонентах:
- `src/ccbm/verifier/` — ChernoffVerifier
- `src/ccbm/audit/` — AuditEngine, MerkleTree
- `src/ccbm/mcp/server.py` — MCP Server
- `.ccbm/skills/*/SKILL.md` — Skills система

**Требования:**
- 100% тестов passed
- ≥ 95% coverage
- Security scan clean
- Golden set validation

### MAJOR (threshold: 0.90)

Новые функции и компоненты:
- `src/ccbm/analyzer/` — CriticalityAnalyzer
- `src/ccbm/optimizer/` — OptimizationEngine
- Новые skills
- MCP endpoints

**Требования:**
- 100% тестов passed
- ≥ 90% coverage
- Type check clean

### MINOR (threshold: 0.85)

Исправления багов, оптимизация:
- Bug fixes
- Performance improvements
- Refactoring

**Требования:**
- Тесты на исправление passed
- ≥ 85% coverage
- No regression

### TRIVIAL (threshold: 0.75)

Документация, комментарии:
- Docs updates
- Comments
- README changes

**Требования:**
- No code changes
- Lint clean

## 🔧 CLI Usage

```bash
# Проверка готовности PR
python -m ccbm.quality.cli check-readiness \
  --level MAJOR \
  --coverage 90 \
  --test-count 50 \
  --report

# Классификация PR
python -m ccbm.quality.cli classify-pr \
  src/ccbm/verifier/chernoff_bound.py \
  tests/test_chernoff_verifier.py

# Валидация Golden Set
python -m ccbm.quality.cli validate-golden --verbose
```

## 📚 Property-Based Tests

### Monotonicity (Монотонность)

```python
# Для ChernoffVerifier: больше шагов → меньше ошибка
@given(n_steps=st.integers(10, 1000))
def test_more_steps_less_error(n_steps):
    bound_10 = verify(n_steps=10)
    bound_100 = verify(n_steps=100)
    assert bound_100.bound <= bound_10.bound
```

### Anti-inversion (Анти-инверсия)

```python
# COMPROMISED данные не должны быть VERIFIED
def test_compromised_not_verified():
    bound = verify(original=[100], compressed=[200])
    assert not (bound.status == "COMPROMISED" and bound.is_valid)
```

### CDI Bounds (для AI-REPS Council)

```python
# CDI всегда в диапазоне [0, 1]
@given(opinions=st.lists(st.floats(0, 1), min_size=2))
def test_cdi_bounds(opinions):
    cdi = calculate_cdi(opinions)
    assert 0.0 <= cdi <= 1.0
```

## 🏆 Golden Set

### Тестовые кейсы

| Case ID | Scenario | Expected | Status |
|---------|----------|----------|--------|
| **VERIFY-001** | Perfect match | VERIFIED | ✅ |
| **VERIFY-002** | Small error (< 0.01) | VERIFIED | ✅ |
| **VERIFY-003** | Large error (> 0.1) | COMPROMISED | ✅ |
| **AUDIT-001** | Single transformation | Merkle root valid | ✅ |
| **AUDIT-002** | Multiple transformations | All proofs valid | ✅ |
| **IIN-001** | Valid IIN | True | ✅ |
| **IIN-002** | Invalid IIN (ctrl1=10) | False | ✅ |
| **IIN-003** | Invalid IIN (wrong length) | False | ✅ |
| **COMPRESS-001** | L1 data preserved | 100% retention | ✅ |
| **COMPRESS-002** | L3 data masked | [PII REDACTED] | ✅ |

## 📈 Quality Metrics Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│              CCBM Quality Dashboard                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Readiness Score: 0.92/1.00  ⚠️ MERGE + Monitoring         │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Component       │ Weight │ Score │ Weighted │ Status │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ Correctness     │  30%   │ 1.00  │  0.300   │   ✅   │  │
│  │ Validation      │  25%   │ 0.95  │  0.238   │   ✅   │  │
│  │ Coverage        │  20%   │ 0.87  │  0.174   │   🟡   │  │
│  │ Monitoring      │  15%   │ 0.80  │  0.120   │   🟡   │  │
│  │ Documentation   │  10%   │ 0.90  │  0.090   │   ✅   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Tests: 145 passed, 0 failed                               │
│  Coverage: 87% (target: 90%)                               │
│  Security: 0 critical, 0 high                              │
│  Performance: All benchmarks pass                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔗 Ссылки

- [TERAG Formal Verification](E:\TERAG Desktop 2026\FORMAL_VERIFICATION_SYSTEM.md)
- [Hypothesis Property-Based Testing](https://hypothesis.readthedocs.io/)
- [ChernoffPy](E:\MarkovChains\ChernoffPy)
