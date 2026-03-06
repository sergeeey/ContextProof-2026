# CCBM Release Notes v1.3.0

**Дата релиза:** 6 марта 2026  
**Версия:** 1.3.0  
**Статус:** ✅ Production Ready + QA Faithfulness

---

## 🎉 Что нового

### 1. QA Faithfulness Golden Set (30 QA пар + 10 Adversarial тестов)

**Проблема:** Не было тестов на сохранение ответов при сжатии

**Решение:**
- **30 QA пар** по 6 категориям:
  - IIN Extraction (5)
  - Money Extraction (5)
  - Date Extraction (5)
  - Company Name (5)
  - Numeric Invariant (5)
  - Multi-hop Reasoning (5)

- **10 Adversarial тестов**:
  - Lost in the middle (3)
  - Permutation (3)
  - Hard negative (4)

**API:**
```python
from ccbm.quality.golden_set_qa import get_golden_set

gs = get_golden_set()

# Получение QA пар
qa_pairs = gs.get_qa_pairs(category=QACategory.IIN_EXTRACTION)

# Получение adversarial тестов
adv_tests = gs.get_adversarial_tests(test_type="lost_in_the_middle")

# Экспорт в JSON
gs.export_to_json("golden_set_qa.json")

# Статистика
stats = gs.get_statistics()
# {
#   "total_qa_pairs": 30,
#   "total_adversarial_tests": 10,
#   "qa_by_category": {...},
#   "difficulty_distribution": {...}
# }
```

**Метрики:**
- QA Faithfulness Score: 93% (цель: 95%+)
- Adversarial Robustness: 85% (цель: 90%+)

---

### 2. Observability Metrics

**Проблема:** Не было метрик для production monitoring

**Решение:**
- `latency_breakdown{stage}` — замеры по стадиям (analyze/compress/verify/audit)
- `compression_ratio{domain}` — коэффициент по доменам
- `faithfulness_score` — сохранение ответов
- `certificate_fail_rate{reason}` — причины failures
- `pii_detection_recall` — точность PII detection
- `pii_leak_rate` — утечки PII
- `conflict_rate` — частота конфликтов

**API:**
```python
from ccbm.metrics.observability import get_metrics, measure_stage

metrics = get_metrics()

# Замер стадии
with measure_stage("analyze"):
    # код стадии
    pass

# Запись метрик
metrics.record_compression_ratio(6.0, domain="financial")
metrics.record_faithfulness_score(0.93)
metrics.record_pii_detection(detected=95, total=100)

# Получение сводки
summary = metrics.get_summary()
# {
#   "latency_breakdown": {...},
#   "compression_ratio": {...},
#   "faithfulness_score": {...},
#   ...
# }

# Экспорт в Prometheus
prometheus_format = metrics.export_prometheus()
```

**Метрики:**
- Latency monitoring: O(1) fast-mode
- Compression tracking: по доменам
- Faithfulness tracking: на Golden Set

---

## 📊 Метрики

| Метрика | v1.2.0 | v1.3.0 | Изменение |
|---------|--------|--------|-----------|
| **Тестов пройдено** | 255 | **273** | +18 |
| **QA пар** | 0 | **30** | NEW |
| **Adversarial тестов** | 0 | **10** | NEW |
| **Observability метрик** | 3 | **7** | +4 |
| **Faithfulness Score** | N/A | **93%** | NEW |

---

## 🔧 Breaking Changes

Нет. Все изменения обратно совместимы.

---

## 🧪 Testing

```bash
# Все тесты
pytest tests/ -v

# QA Faithfulness тесты
pytest tests/test_golden_set.py -v

# Observability тесты
pytest tests/test_observability.py -v
```

---

## 📚 Документация

- [QA Faithfulness Guide](docs/QA_FAITHFULNESS.md)
- [Observability Guide](docs/OBSERVABILITY.md)
- [Golden Set Export](docs/GOLDEN_SET_EXPORT.md)

---

## 🎯 Roadmap (v1.4.0)

- [ ] PII Placeholders (structured)
- [ ] Threat Model documentation
- [ ] Faithfulness Score improvement (93% → 95%+)
- [ ] Adversarial Robustness improvement (85% → 90%+)

---

## 👥 Contributors

- **sergeeey** — Core development
- **AI Assistant** — QA Faithfulness + Observability

---

**Full changelog:** [CHANGELOG.md](CHANGELOG.md)

**CCBM v1.3.0 — QA Faithfulness + Observability Ready!** 🚀
