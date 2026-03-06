# MCP Server для CCBM

**Model Context Protocol** — стандартный протокол для интеграции CCBM с AI-агентами.

## 🎯 Назначение

MCP Server позволяет:
- Подключать CCBM к любым MCP-совместимым клиентам (Claude Code, Cursor, Cline)
- Оптимизировать контекст через стандартный API
- Получать сертифицированные квитанции верификации

## 📋 Компоненты

### 1. MCP Server (TODO)
```python
from mcp.server import Server
from ccbm import CriticalityAnalyzer, OptimizationEngine, ChernoffVerifier, AuditEngine

server = Server("ccbm")

@server.call_tool()
async def optimize_context(arguments: dict) -> dict:
    """Оптимизация контекста через MCP."""
    text = arguments["text"]
    domain = arguments.get("domain", "general")
    
    # Анализ
    analyzer = CriticalityAnalyzer()
    spans = analyzer.analyze(text)
    
    # Оптимизация
    optimizer = OptimizationEngine()
    result = optimizer.optimize(spans)
    
    # Верификация
    verifier = ChernoffVerifier(domain=domain)
    # ... верификация числовых данных
    
    # Аудит
    audit = AuditEngine()
    audit.add_transformation(text, result.optimized_text)
    audit.finalize()
    
    return {
        "optimized_text": result.optimized_text,
        "compression_ratio": result.compression_ratio,
        "audit_receipt": audit.get_audit_log(),
    }
```

### 2. MCP Client Integration
```python
# Подключение в Claude Code
/mcp connect ccbm

# Оптимизация текста
/mcp ccbm optimize_context --text "..." --domain financial
```

## 🔧 Установка

```bash
# Установка MCP SDK
pip install mcp>=1.0.0

# Запуск сервера
python -m ccbm.mcp.server

# Подключение клиента
# В Claude Code: /plugin install ccbm
```

## 📊 Endpoints

| Endpoint | Описание |
|----------|----------|
| `optimize_context` | Оптимизация текста с верификацией |
| `verify_invariants` | Верификация числовых инвариантов |
| `get_audit_receipt` | Получение аудиторской квитанции |
| `analyze_spans` | Анализ спанов по уровням критичности |

## 🔐 Безопасность

- Все трансформации логируются в дереве Меркла
- Квитанции верификации подписываются
- Поддержка AttestMCP для аттестации сообщений

## 📝 Пример использования

```python
import requests

# Запрос на оптимизацию
response = requests.post(
    "http://localhost:8080/optimize",
    json={
        "text": "ИИН 950101300038, сумма 100000 KZT",
        "domain": "financial",
    }
)

result = response.json()
print(f"Оптимизировано: {result['optimized_text']}")
print(f"Коэффициент: {result['compression_ratio']}")
print(f"Квитанция: {result['audit_receipt']['merkle_root']}")
```

## 🚀 Roadmap

- [ ] MCP Server implementation
- [ ] SSE transport для streaming
- [ ] AttestMCP integration
- [ ] OAuth2 аутентификация
- [ ] Rate limiting
