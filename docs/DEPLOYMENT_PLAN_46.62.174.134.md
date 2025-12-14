# MPIS Персональный План Развертывания

**Сервер:** 46.62.174.134  
**Дата:** Декабрь 2025  
**Конфигурация:** Ubuntu 24.04 ARM64, n8n + Caddy уже установлены

---

## Ваша текущая инфраструктура

| Компонент | Статус | Порт |
|-----------|--------|------|
| Caddy | ✅ Работает | 80/443 |
| n8n | ✅ Работает | 127.0.0.1:5678 |
| PostgreSQL | ❓ Нужно проверить | 5432 |
| Qdrant | ❓ Нужно установить | 6333 |
| MPIS API | ⏳ Будет установлен | 127.0.0.1:8080 |

---

## Этап 1: Проверка существующей инфраструктуры

### 1.1 Подключение к серверу

```bash
ssh user@46.62.174.134
```

### 1.2 Проверка Docker

```bash
docker --version
docker compose version
```

### 1.3 Проверка существующих контейнеров

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**Ожидаемый вывод должен показать n8n и Caddy контейнеры.**

### 1.4 Проверка Docker сетей

```bash
docker network ls
```

**Запомните имя сети, где работают n8n и Caddy (вероятно `n8n_default`).**

---

## Этап 2: Проверка PostgreSQL

### Вариант A: PostgreSQL уже есть (проверить)

```bash
# Проверить есть ли контейнер PostgreSQL
docker ps -a | grep postgres

# Если есть, проверить подключение
docker exec -it <postgres_container_name> psql -U postgres -c "SELECT 1"
```

### Вариант B: PostgreSQL нужно установить

```bash
# Создать сеть MPIS (если её нет)
docker network create mpis_net

# Запустить PostgreSQL
docker run -d \
  --name mpis-postgres \
  --network mpis_net \
  -e POSTGRES_USER=mpis \
  -e POSTGRES_PASSWORD=$(openssl rand -base64 24) \
  -e POSTGRES_DB=mpis \
  -v /opt/mpis/postgres_data:/var/lib/postgresql/data \
  --restart unless-stopped \
  postgres:16-alpine

# ВАЖНО: Сохраните пароль!
docker logs mpis-postgres 2>&1 | head -20
```

---

## Этап 3: Установка Qdrant

```bash
# Запустить Qdrant
docker run -d \
  --name mpis-qdrant \
  --network mpis_net \
  -v /opt/mpis/qdrant_data:/qdrant/storage \
  --restart unless-stopped \
  qdrant/qdrant:latest

# Проверить запуск (через другой контейнер в сети)
docker exec mpis-postgres curl -s http://mpis-qdrant:6333/collections
```

---

## Этап 4: Подготовка MPIS

### 4.1 Создание директорий

```bash
sudo mkdir -p /opt/mpis/{personas,sources,input,infra,secrets,backups,tmp,exports}
sudo mkdir -p /opt/mpis/postgres_data
sudo mkdir -p /opt/mpis/qdrant_data
sudo chown -R 1000:1000 /opt/mpis
```

### 4.2 Клонирование репозитория

```bash
cd /opt/mpis
sudo git clone https://github.com/ivanvdovicenco/mpis.git repo
sudo chown -R 1000:1000 /opt/mpis/repo
```

### 4.3 Применение миграций базы данных

```bash
cd /opt/mpis/repo

# Genesis модуль
docker exec -i mpis-postgres psql -U mpis -d mpis < scripts/002_genesis.sql

# Life модуль  
docker exec -i mpis-postgres psql -U mpis -d mpis < scripts/003_life.sql

# Publisher модуль
docker exec -i mpis-postgres psql -U mpis -d mpis < scripts/004_publisher.sql

# Analytics модуль
docker exec -i mpis-postgres psql -U mpis -d mpis < scripts/005_analytics.sql

# Проверить таблицы
docker exec -i mpis-postgres psql -U mpis -d mpis -c "\dt"
```

---

## Этап 5: Конфигурация

### 5.1 Создание .env файла

```bash
cp /opt/mpis/repo/api/.env.example /opt/mpis/infra/.env
nano /opt/mpis/infra/.env
```

### 5.2 Настройка .env для вашего сервера

```env
# ========================================
# MPIS Configuration for 46.62.174.134
# ========================================

APP_NAME=MPIS API
APP_VERSION=1.0.0
DEBUG=false
DRY_RUN=false

# Database (замените YOUR_PASSWORD на ваш пароль PostgreSQL)
DATABASE_URL=******mpis-postgres:5432/mpis

# Qdrant
QDRANT_URL=http://mpis-qdrant:6333
QDRANT_COLLECTION_SOURCES=persona_sources_embeddings
EMBEDDING_DIMENSION=1536

# OpenAI (ваш ключ)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-ваш-ключ-здесь
LLM_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-small

# Пути
YOUTUBE_LINKS_DIR=/opt/mpis/input
PERSONAS_BASE_DIR=/opt/mpis/personas
SOURCES_BASE_DIR=/opt/mpis/sources
SECRETS_DIR=/opt/mpis/secrets

# API
API_HOST=0.0.0.0
API_PORT=8080
```

---

## Этап 6: Запуск MPIS API

### 6.1 Сборка и запуск

```bash
cd /opt/mpis/repo/infra

# Собрать и запустить
docker compose -f docker-compose.full.yml up -d --build
```

### 6.2 Проверка логов

```bash
docker logs genesis-api --tail 50
```

### 6.3 Проверка здоровья

```bash
curl -s http://localhost:8080/health | jq
```

**Ожидаемый результат:**
```json
{
  "status": "healthy",
  "service": "MPIS API",
  "version": "1.0.0"
}
```

---

## Этап 7: Подключение к Caddy

### 7.1 Добавить конфигурацию в Caddyfile

Найдите ваш Caddyfile (обычно `/var/n8n/Caddyfile` или `/etc/caddy/Caddyfile`):

```bash
# Найти Caddyfile
find / -name "Caddyfile" 2>/dev/null
```

Добавьте в Caddyfile:

```
mpis.46.62.174.134.nip.io {
    reverse_proxy genesis-api:8080
}
```

### 7.2 Подключить MPIS к сети Caddy

```bash
# Найти имя сети Caddy
docker network ls | grep -E "n8n|caddy"

# Подключить (замените n8n_default на вашу сеть)
docker network connect n8n_default genesis-api
```

### 7.3 Перезагрузить Caddy

```bash
# Найти имя контейнера Caddy
docker ps | grep caddy

# Перезагрузить (замените имя контейнера)
docker exec n8n-caddy-1 caddy reload --config /etc/caddy/Caddyfile
```

---

## Этап 8: Тестирование

### Скрипт автоматического тестирования

```bash
cat > /opt/mpis/test_deployment.sh << 'EOF'
#!/bin/bash

echo "========================================="
echo "MPIS Deployment Test - 46.62.174.134"
echo "========================================="
echo ""

PASS=0
FAIL=0

# Test 1: Health Check
echo -n "Test 1: Health Check... "
HEALTH=$(curl -s http://localhost:8080/health 2>/dev/null)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "✓ PASS"
    ((PASS++))
else
    echo "✗ FAIL"
    ((FAIL++))
fi

# Test 2: Root Endpoint
echo -n "Test 2: Root Endpoint... "
ROOT=$(curl -s http://localhost:8080/ 2>/dev/null)
if echo "$ROOT" | grep -q "modules"; then
    echo "✓ PASS"
    ((PASS++))
else
    echo "✗ FAIL"
    ((FAIL++))
fi

# Test 3: OpenAPI Schema
echo -n "Test 3: OpenAPI Schema... "
OPENAPI=$(curl -s http://localhost:8080/openapi.json 2>/dev/null)
if echo "$OPENAPI" | grep -q "openapi"; then
    echo "✓ PASS"
    ((PASS++))
else
    echo "✗ FAIL"
    ((FAIL++))
fi

# Test 4: Genesis Module
echo -n "Test 4: Genesis Module... "
GENESIS=$(curl -s -X POST http://localhost:8080/genesis/start \
  -H "Content-Type: application/json" \
  -d '{"persona_name": "Test", "language": "ru"}' 2>/dev/null)
if echo "$GENESIS" | grep -q -E "job_id|error"; then
    echo "✓ PASS (responding)"
    ((PASS++))
else
    echo "✗ FAIL"
    ((FAIL++))
fi

# Test 5: Life Module
echo -n "Test 5: Life Module... "
LIFE=$(curl -s -X POST http://localhost:8080/life/event \
  -H "Content-Type: application/json" \
  -d '{"persona_id": "00000000-0000-0000-0000-000000000000", "event_type": "note", "content": "test"}' 2>/dev/null)
if echo "$LIFE" | grep -q -E "error|id"; then
    echo "✓ PASS (responding)"
    ((PASS++))
else
    echo "✗ FAIL"
    ((FAIL++))
fi

# Test 6: Publisher Module
echo -n "Test 6: Publisher Module... "
PUB=$(curl -s -X POST http://localhost:8080/publisher/plan \
  -H "Content-Type: application/json" \
  -d '{"persona_id": "00000000-0000-0000-0000-000000000000", "title": "test", "topic": "test", "channel": "telegram"}' 2>/dev/null)
if echo "$PUB" | grep -q -E "error|id"; then
    echo "✓ PASS (responding)"
    ((PASS++))
else
    echo "✗ FAIL"
    ((FAIL++))
fi

# Test 7: Analytics Module
echo -n "Test 7: Analytics Module... "
ANAL=$(curl -s "http://localhost:8080/analytics/persona/00000000-0000-0000-0000-000000000000/summary?range=7d" 2>/dev/null)
if echo "$ANAL" | grep -q -E "error|persona_id"; then
    echo "✓ PASS (responding)"
    ((PASS++))
else
    echo "✗ FAIL"
    ((FAIL++))
fi

# Test 8: Database Connection
echo -n "Test 8: Database Connection... "
DB=$(docker exec mpis-postgres psql -U mpis -d mpis -c "SELECT COUNT(*) FROM personas" 2>/dev/null)
if echo "$DB" | grep -q -E "[0-9]"; then
    echo "✓ PASS"
    ((PASS++))
else
    echo "✗ FAIL"
    ((FAIL++))
fi

# Test 9: Qdrant Connection
echo -n "Test 9: Qdrant Connection... "
QDRANT=$(docker exec mpis-postgres curl -s http://mpis-qdrant:6333/collections 2>/dev/null)
if echo "$QDRANT" | grep -q "collections"; then
    echo "✓ PASS"
    ((PASS++))
else
    echo "✗ FAIL"
    ((FAIL++))
fi

# Test 10: External Access (через nip.io)
echo -n "Test 10: External Access... "
EXT=$(curl -s --connect-timeout 5 https://mpis.46.62.174.134.nip.io/health 2>/dev/null)
if echo "$EXT" | grep -q "healthy"; then
    echo "✓ PASS"
    ((PASS++))
else
    echo "○ SKIP (Caddy not configured yet)"
fi

echo ""
echo "========================================="
echo "Results: $PASS passed, $FAIL failed"
echo "========================================="

if [ $FAIL -eq 0 ]; then
    echo "🎉 All tests passed! MPIS is ready."
else
    echo "⚠️  Some tests failed. Check the logs."
fi
EOF

chmod +x /opt/mpis/test_deployment.sh
```

Запустить тесты:

```bash
/opt/mpis/test_deployment.sh
```

---

## Этап 9: Интеграция с n8n

### 9.1 Подключить n8n к сети MPIS

```bash
# Найти имя контейнера n8n
docker ps | grep n8n

# Подключить (замените имя)
docker network connect mpis_net n8n-n8n-1
```

### 9.2 Импортировать workflow в n8n

1. Откройте n8n: http://46.62.174.134.nip.io (или ваш домен)
2. Создайте новый workflow
3. Нажмите ⋮ → Import from file
4. Загрузите: `/opt/mpis/repo/n8n/workflows/content-publishing.json`
5. Повторите для: `/opt/mpis/repo/n8n/workflows/daily-reflection.json`

### 9.3 Настройка Telegram бота

1. Создайте бота через @BotFather в Telegram
2. Получите токен бота
3. Создайте канал/группу для публикаций
4. Добавьте бота в канал как администратора
5. Получите chat_id канала

В n8n добавьте credentials:
- Name: `MPIS Telegram Bot`
- Token: `ваш-токен`

---

## Этап 10: Первый тест с реальной персоной

### 10.1 Создание персоны

```bash
curl -X POST http://localhost:8080/genesis/start \
  -H "Content-Type: application/json" \
  -d '{
    "persona_name": "Алексей",
    "inspiration_source": "Тим Келлер",
    "language": "ru",
    "public_persona": false
  }' | jq
```

Сохраните `job_id` из ответа.

### 10.2 Проверка статуса

```bash
curl -s "http://localhost:8080/genesis/status/ВАШ_JOB_ID" | jq
```

### 10.3 Подтверждение персоны

```bash
curl -X POST http://localhost:8080/genesis/approve \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "ВАШ_JOB_ID",
    "draft_no": 1,
    "confirm": true
  }' | jq
```

---

## Чеклист после развертывания

- [ ] Docker работает
- [ ] PostgreSQL контейнер запущен
- [ ] Qdrant контейнер запущен
- [ ] Миграции применены (проверить `\dt` в psql)
- [ ] .env настроен с OpenAI ключом
- [ ] MPIS API запущен и отвечает на /health
- [ ] Caddy настроен для проксирования
- [ ] n8n подключен к сети MPIS
- [ ] Тестовый скрипт проходит все тесты
- [ ] Telegram бот создан и настроен

---

## Полезные команды

```bash
# Логи MPIS
docker logs genesis-api -f

# Перезапуск MPIS
docker restart genesis-api

# Статус всех контейнеров
docker ps --format "table {{.Names}}\t{{.Status}}"

# Бэкап базы данных
docker exec mpis-postgres pg_dump -U mpis mpis > /opt/mpis/backups/mpis_$(date +%Y%m%d).sql

# Обновление MPIS
cd /opt/mpis/repo && git pull && cd infra && docker compose -f docker-compose.full.yml up -d --build
```

---

## Следующие шаги

После успешного развертывания:

1. **Создать первую персону** через Genesis API
2. **Настроить n8n workflow** для автоматической публикации
3. **Добавить YouTube ссылки** в `/opt/mpis/input/youtube_links.txt`
4. **Протестировать Telegram публикацию** через Publisher
5. **Настроить ежедневные рефлексии** через Life модуль

---

## Контакты для помощи

- API документация: https://mpis.46.62.174.134.nip.io/docs
- GitHub Issues: https://github.com/ivanvdovicenco/mpis/issues
