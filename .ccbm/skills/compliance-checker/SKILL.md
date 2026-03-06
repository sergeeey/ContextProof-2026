# Навык: Compliance Checker (Закон РК)

**Версия:** 0.9.0  
**Статус:** 🟡 В разработке  
**Приоритет:** Высокий

## 🎯 Назначение

Проверка соответствия законодательству Республики Казахстан в области ИИ и данных.

## 📋 Функции

- **check_compliance()** — проверка на соответствие
- **get_requirements()** — получение требований
- **generate_report()** — генерация отчёта compliance
- **get_deadlines()** — дедлайны compliance

## 🔧 Использование

```python
from ccbm.skills.compliance_checker import check_compliance

result = check_compliance(
    system_type="financial_ai",
    data_types=["iin", "financial", "pii"],
    deployment="cloud_kz",
)

print(f"Соответствие: {result.is_compliant}")
print(f"Нарушения: {result.violations}")
print(f"Рекомендации: {result.recommendations}")
```

## 📚 Законы РК

### 1. Закон «Об искусственном интеллекте» № 230-VIII

**Статья 18: Управление рисками**
- ✅ Непрерывный мониторинг рисков
- ✅ Ежегодная актуализация документации
- ⏳ Реестр рисков в реальном времени

**Статья 21: Маркировка ИИ-контента**
- ✅ Визуальная маркировка
- ✅ Машиночитаемая маркировка
- ⏳ Watermark для мультимедиа

**Статья 23: Требования к высокорисковым системам**
- ⏳ Ежегодный аудит
- ⏳ Национальная платформа ИИ
- ✅ Объяснимость решений

### 2. Цифровой кодекс (июль 2026)

**Права субъектов данных:**
- ✅ Право на удаление
- ✅ Право на деперсонализацию
- ⏳ Citizen's Digital Space интеграция

**Требования к обработке:**
- ✅ Локализация данных в РК
- ✅ Шифрование PII
- ⏳ Суверенитет данных

### 3. Приказы НБ РК

**Для финансовых систем:**
- ⏳ AML/CFT compliance
- ⏳ Fraud reporting
- ✅ Transaction monitoring

## 📊 Чек-лист compliance

| Требование | Статус | Документ |
|------------|--------|----------|
| **Закон об ИИ** | | |
| Управление рисками | 🟡 Частично | Risk Register |
| Маркировка ИИ | ✅ Готово | AI Label Policy |
| Аудит высокорисковых | ⏳ В разработке | Audit Plan |
| **Цифровой кодекс** | | |
| Локализация данных | ✅ Готово | DC Location Policy |
| Права субъектов | 🟡 Частично | Data Subject Rights |
| Шифрование PII | ✅ Готово | Encryption Standard |
| **НБ РК** | | |
| AML/CFT | ⏳ В разработке | AML Policy |
| Fraud reporting | ⏳ В разработке | Fraud Report Format |

## 🔗 Ссылки

- [Закон об ИИ 230-VIII](https://adilet.zan.kz/rus/docs/Z2400000230)
- [Цифровой кодекс](https://adilet.zan.kz/rus/docs/P2400000007)
- [НБ РК Приказы](https://nationalbank.kz/ru/document/category/10)
