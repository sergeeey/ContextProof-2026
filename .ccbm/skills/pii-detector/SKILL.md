# Навык: Детекция PII (PII Detector)

**Версия:** 0.9.0  
**Статус:** 🟡 В разработке  
**Приоритет:** Высокий

## 🎯 Назначение

Автоматическое обнаружение и маскирование персональных данных (PII).

## 📋 Функции

- **detect_pii()** — обнаружение PII в тексте
- **mask_pii()** — маскирование всех PII
- **extract_pii()** — извлечение PII для аудита
- **get_pii_types()** — типы найденных PII

## 🔧 Использование

```python
from ccbm.skills.pii_detector import detect_pii, mask_pii

text = "Иван Иванов, ИИН 950101300038, тел. +7-777-123-4567"

# Детекция
pii_list = detect_pii(text)
print(f"Найдено PII: {len(pii_list)}")
for pii in pii_list:
    print(f"  - {pii.type}: {pii.value}")

# Маскирование
masked = mask_pii(text)
print(f"Замаскировано: {masked}")
# "Иван [MASKED_NAME], ИИН [MASKED_IIN], тел. [MASKED_PHONE]"
```

## 📊 Типы PII

| Тип | Паттерн | Пример | Статус |
|-----|---------|--------|--------|
| **ИИН** | 12 цифр | 950101300038 | ✅ Готово |
| **БИН** | 12 цифр | 010140000012 | ✅ Готово |
| **Телефон** | +7-XXX-XXX-XXXX | +7-777-123-4567 | ✅ Готово |
| **Email** | user@domain.com | user@example.kz | ✅ Готово |
| **Имя** | KazRoBERTa NER | Иван Иванов | ⏳ В разработке |
| **Адрес** | NER + паттерны | г. Алматы, ул. Абая 1 | ⏳ В разработке |
| **Дата рождения** | ДД.ММ.ГГГГ | 01.01.1995 | ✅ Готово |

## 📚 Паттерны

### Регулярные выражения

```python
IIN_PATTERN = r'\b\d{12}\b'
BIN_PATTERN = r'\b\d{12}\b'
PHONE_PATTERN = r'\+7[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{4}'
EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
DATE_PATTERN = r'\b\d{1,2}\.\d{1,2}\.\d{4}\b'
```

### NER модели (TODO)

```python
# KazRoBERTa для казахского языка
from transformers import AutoModelForTokenClassification

model = AutoModelForTokenClassification.from_pretrained("IS2AI/kazroberta-ner")
```

## 🔗 Ссылки

- [KazNERD Dataset](https://github.com/IS2AI/KazNERD)
- [Presidio PII Detection](https://microsoft.github.io/presidio/)
