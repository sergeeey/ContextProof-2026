# Навык: Сжатие контекста (Context Compression)

**Версия:** 1.0.0  
**Статус:** ✅ Готов  
**Приоритет:** Критический

## 🎯 Назначение

Сжатие контекста LLM с сохранением критических данных через LLMLingua/LoPace.

## 📋 Функции

- **compress()** — сжатие текста с указанием домена
- **decompress()** — восстановление (если lossless)
- **estimate_compression()** — оценка коэффициента сжатия
- **validate_compression()** — валидация качества сжатия

## 🔧 Использование

```python
from ccbm.skills.context_compression import compress

result = compress(
    text="ИИН 950101300038, договор на 100000 KZT...",
    domain="financial",
    target_budget=4000,
)

print(f"Оригинал: {len(result.original)} символов")
print(f"Сжатие: {len(result.compressed)} символов")
print(f"Коэффициент: {result.compression_ratio}x")
```

## 📊 Метрики

| Метрика | Значение |
|---------|----------|
| Коэффициент сжатия | 4-8x |
| Сохранение L1 данных | 100% |
| BERTScore (юридические) | > 0.88 |
| Время сжатия | < 100ms |

## 🔗 Ссылки

- [LLMLingua GitHub](https://github.com/microsoft/LLMLingua)
- [LoPace GitHub](https://github.com/connectaman/LoPace)
