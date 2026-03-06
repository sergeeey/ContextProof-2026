# Навык: Аудит Меркла (Merkle Auditor)

**Версия:** 1.0.0  
**Статус:** ✅ Готов  
**Приоритет:** Критический

## 🎯 Назначение

Неизменяемое логирование всех трансформаций контекста через деревья Меркла.

## 📋 Функции

- **add_transformation()** — добавление записи о трансформации
- **finalize()** — финализация дерева Меркла
- **get_proof()** — получение доказательства включения
- **verify_receipt()** — верификация квитанции

## 🔧 Использование

```python
from ccbm.skills.merkle_auditor import AuditEngine

audit = AuditEngine()

# Добавление трансформации
receipt = audit.add_transformation(
    original_data="ИИН 950101300038",
    compressed_data="ИИН [REDACTED]",
    metadata={"type": "pii_masking"},
)

# Финализация
merkle_root = audit.finalize()

# Верификация
is_valid = audit.verify_receipt(receipt)
print(f"Квитанция валидна: {is_valid}")
```

## 📊 Метрики

| Метрика | Значение |
|---------|----------|
| Время хеширования | < 1ms |
| Размер proof | O(log n) |
| Поддержка | до 1M записей |
| Безопасность | SHA-256 |

## 📚 Теория

### Дерево Меркла

```
        Root = H(A+B)
       /           \
    H(A)          H(B)
    / \           / \
  L1  L2       L3   L4
```

### Формула хеширования

```
leaf_hash = SHA256(json({
    "original": SHA256(original_data),
    "compressed": SHA256(compressed_data),
    "timestamp": ISO_timestamp,
    "metadata": {...}
}))

parent_hash = SHA256(left_child + right_child)
```

## 🔗 Ссылки

- [Merkle Tree Wikipedia](https://en.wikipedia.org/wiki/Merkle_tree)
- [rs-merkle-tree](https://github.com/lazyledger/rs-merkle-tree)
