# CCBM Production Deployment Guide

**Версия:** 1.0.0  
**Дата:** 6 марта 2026

---

## 🎯 Обзор

Руководство по развёртыванию CCBM в production среде.

---

## 📦 Требования

### Минимальные
- **CPU:** 2 cores
- **RAM:** 4 GB
- **Disk:** 10 GB
- **Python:** 3.11+

### Рекомендуемые
- **CPU:** 4+ cores
- **RAM:** 8+ GB
- **Disk:** 20+ GB
- **GPU:** Optional (для LLMLingua)

---

## 🚀 Быстрый старт

### 1. Установка

```bash
# Клонирование репозитория
git clone https://github.com/sergeeey/ContextProof-2026.git
cd ContextProof-2026

# Установка зависимостей
pip install -r requirements.txt

# Установка CCBM
pip install -e .
```

### 2. Запуск API

```bash
# MCP Server
python -m ccbm.mcp.server
```

### 3. Запуск Dashboard

```bash
# Streamlit Dashboard
streamlit run -m ccbm.dashboard.app
```

---

## 🐳 Docker Deployment

### Build

```bash
# Build Docker image
docker build -f docker/Dockerfile -t ccbm:1.0.0 .
```

### Run

```bash
# Запуск контейнера
docker run -d -p 8000:8000 -p 8501:8501 ccbm:1.0.0
```

### Docker Compose

```bash
# Запуск всех сервисов
docker-compose -f docker/docker-compose.prod.yml up -d

# Проверка статуса
docker-compose -f docker/docker-compose.prod.yml ps

# Логи
docker-compose -f docker/docker-compose.prod.yml logs -f
```

---

## 🔧 Конфигурация

### Environment Variables

```env
# Core
CCBM_ENV=production
CCBM_LOG_LEVEL=INFO

# Security
JWT_SECRET_KEY=<your-secret-key>
CCBM_REQUIRE_AUTH=true

# API
API_HOST=0.0.0.0
API_PORT=8000

# Dashboard
DASHBOARD_PORT=8501

# Redis
REDIS_URL=redis://localhost:6379
```

### Config File

```yaml
# config.yaml
ccbm:
  env: production
  log_level: INFO
  
  llmlingua:
    model: microsoft/llmlingua-2-xlm-roberta-large
    target_token: 300
  
  security:
    require_auth: true
    rate_limit: 100/minute
  
  audit:
    enabled: true
    merkle_tree: true
```

---

## 📊 Monitoring

### Health Check

```bash
# API Health
curl http://localhost:8000/health

# Dashboard Health
curl http://localhost:8501/_stcore/health
```

### Metrics

```bash
# Prometheus Metrics
curl http://localhost:8000/metrics
```

**Доступные метрики:**
- `ccbm_requests_total` — количество запросов
- `ccbm_compression_ratio` — коэффициент сжатия
- `ccbm_verification_errors` — ошибки верификации
- `ccbm_audit_entries` — записей в audit trail

---

## 🔐 Security

### Hardening

1. **Включить аутентификацию:**
   ```bash
   export CCBM_REQUIRE_AUTH=true
   export JWT_SECRET_KEY=<secure-random-key>
   ```

2. **Настроить rate limiting:**
   ```bash
   export CCBM_RATE_LIMIT=100/minute
   ```

3. **Включить HTTPS:**
   ```bash
   # Через reverse proxy (nginx)
   ```

4. **Регулярные security сканы:**
   ```bash
   # Bandit
   bandit -r src/
   
   # Safety
   safety check
   ```

---

## 📈 Scaling

### Horizontal

```yaml
# docker-compose.scale.yml
services:
  ccmb-api:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 2G
```

### Load Balancer

```nginx
# nginx.conf
upstream ccbm {
    server ccmb-api-1:8000;
    server ccmb-api-2:8000;
    server ccmb-api-3:8000;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://ccbm;
    }
}
```

---

## 🔧 Troubleshooting

### API не запускается

```bash
# Проверить логи
docker-compose -f docker/docker-compose.prod.yml logs ccmb-api

# Проверить порты
netstat -tlnp | grep 8000
```

### Dashboard не доступен

```bash
# Перезапустить сервис
docker-compose -f docker/docker-compose.prod.yml restart ccmb-dashboard

# Проверить логи
docker-compose -f docker/docker-compose.prod.yml logs ccmb-dashboard
```

### Security Audit fails

```bash
# Запустить аудит
python -m ccbm.security.cli run

# Исправить проблемы
# ...
```

---

## 📚 Ссылки

- [GitHub Repository](https://github.com/sergeeey/ContextProof-2026)
- [Documentation](docs/README.md)
- [Security Audit](docs/SECURITY_AUDIT_REPORT.md)
- [Quality Gates](docs/QUALITY_GATES.md)

---

**Версия:** 1.0.0  
**Последнее обновление:** 2026-03-06
