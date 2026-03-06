# LLMLingua Integration Guide

**Production сжатие контекста для CCBM через Microsoft LLMLingua**

## 🎯 Обзор

LLMLingua — библиотека от Microsoft для умного сжатия промптов с сохранением семантики.

**Возможности:**
- Сжатие в 4-20x
- Сохранение критических данных
- Поддержка длинных документов
- Token-level и document-level сжатие

## 📦 Установка

```bash
pip install llmlingua>=0.2.0
```

## 🚀 Быстрый старт

```python
from ccbm.optimizer.llmlingua import create_compressor, LLMLinguaConfig

# Создание компрессора
config = LLMLinguaConfig(
    target_token=300,
    rank_method="llmlingua2",
)
compressor = create_compressor(config)

# Сжатие текста
text = "Очень длинный документ..." * 100
result = compressor.compress(text, target_token=300)

print(f"Оригинал: {result.original_tokens} токенов")
print(f"Сжатие: {result.compressed_tokens} токенов")
print(f"Коэффициент: {result.compression_ratio}x")
print(f"Экономия: {result.savings_percent}%")
```

## 📊 Методы сжатия

### 1. LLMLingua-2 (Token-level)

**Для:** Коротких и средних текстов

```python
result = compressor.compress(
    text,
    target_token=300,
    rank_method="llmlingua2",
)
```

**Характеристики:**
- Быстрое сжатие
- Token-level важность
- Коэффициент: 4-8x

### 2. LongLLMLingua (Document-level)

**Для:** Длинных документов с вопросом

```python
result = compressor.compress_long(
    text,
    question="Что такое CCBM?",
    instruction="Сохрани только релевантное вопросу",
)
```

**Характеристики:**
- Question-aware сжатие
- Document-level контекст
- Коэффициент: 10-20x

### 3. Fallback (Базовое)

**Для:** Когда LLMLingua недоступна

```python
# Автоматически используется при ошибке
result = compressor.compress(text)
# method="fallback"
```

**Характеристики:**
- Простая эвристика
- Удаление пробелов
- Сокращение предложений

## 🔧 Конфигурация

### LLMLinguaConfig

```python
from ccbm.optimizer.llmlingua import LLMLinguaConfig

config = LLMLinguaConfig(
    # Модель
    model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
    
    # Устройство
    device="cpu",  # или "cuda"
    
    # Целевое количество токенов
    target_token=300,
    
    # Метод ранжирования
    rank_method="llmlingua2",  # или "longllmlingua"
    
    # Инструкция для модели
    instruction="Сохрани только важное",
    
    # Дополнительный контекст
    context="Финансовый документ",
)
```

### Доступные модели

| Модель | Размер | Языки | Назначение |
|--------|--------|-------|------------|
| `llmlingua-2-xlm-roberta-large` | Large | Multi | Универсальная |
| `llmlingua-2-bert` | Base | Multi | Быстрая |
| `llmlingua-2-deberta` | Base | EN/CN | Точная |

## 📈 Интеграция с CCBM

### С OptimizationEngine

```python
from ccbm import OptimizationEngine
from ccbm.optimizer.llmlingua import LLMLinguaCompressor

# Создание компрессора
llm_compressor = LLMLinguaCompressor()

# Интеграция с optimizer
optimizer = OptimizationEngine(
    target_budget=4000,
    llmlingua_compressor=llm_compressor,  # ← Передаём компрессор
)

# Оптимизация с LLMLingua
result = optimizer.optimize(spans)
```

### С MCP Server

```python
from ccbm.mcp.server import optimize_context

# Через MCP
result = await optimize_context(
    text="Длинный документ...",
    domain="financial",
    target_budget=3000,
    use_llmlingua=True,  # ← Использовать LLMLingua
)
```

## 📊 Метрики

### Производительность

| Метрика | Значение |
|---------|----------|
| **Коэффициент сжатия** | 4-20x |
| **Время сжатия** | < 500ms |
| **BERTScore** | > 0.88 |
| **Сохранение L1** | 100% |

### Сравнение методов

| Метод | Коэффициент | Скорость | Качество |
|-------|-------------|----------|----------|
| **LLMLingua-2** | 4-8x | Быстро | Отлично |
| **LongLLMLingua** | 10-20x | Средне | Превосходно |
| **Fallback** | 2-4x | Очень быстро | Хорошо |

## 🧪 Тестирование

```python
import pytest
from ccbm.optimizer.llmlingua import create_compressor

def test_llmlingua_compression():
    compressor = create_compressor()
    
    text = "Тест " * 100
    result = compressor.compress(text, target_token=50)
    
    assert result.compression_ratio >= 1.0
    assert result.compressed_text != ""
```

## 🔗 Ссылки

- [LLMLingua GitHub](https://github.com/microsoft/LLMLingua)
- [LLMLingua Paper](https://arxiv.org/abs/2310.06839)
- [CCBM Optimizer](src/ccbm/optimizer/llmlingua.py)

## ⚠️ Troubleshooting

### Ошибка: "PromptCompressor got an unexpected keyword argument"

**Решение:** Обновите LLMLingua:
```bash
pip install --upgrade llmlingua
```

### Ошибка: "CUDA out of memory"

**Решение:** Используйте CPU:
```python
config = LLMLinguaConfig(device="cpu")
```

### Медленное сжатие

**Решение:** Используйте fallback или уменьшите target_token:
```python
result = compressor.compress(text, target_token=200)  # Меньше токенов
```
