# MPIS Полное Руководство по Развертыванию

Пошаговая инструкция для развертывания Multi-Persona Intelligence System (MPIS) на вашем сервере с Ubuntu 24.04 ARM64.

## Содержание

1. [Требования к серверу](#требования-к-серверу)
2. [Подготовка сервера](#подготовка-сервера)
3. [Установка Docker](#установка-docker)
4. [Создание инфраструктуры](#создание-инфраструктуры)
5. [Запуск базы данных](#запуск-базы-данных)
6. [Запуск Qdrant](#запуск-qdrant)
7. [Клонирование репозитория](#клонирование-репозитория)
8. [Применение миграций](#применение-миграций)
9. [Конфигурация](#конфигурация)
10. [Запуск MPIS API](#запуск-mpis-api)
11. [Тестирование функциональности](#тестирование-функциональности)
12. [Интеграция с n8n](#интеграция-с-n8n)
13. [Настройка HTTPS через Caddy](#настройка-https-через-caddy)
14. [Мониторинг и обслуживание](#мониторинг-и-обслуживание)

---

## Требования к серверу

### Минимальные требования
- **ОС:** Ubuntu 24.04 LTS (ARM64 или x86_64)
- **RAM:** 4 GB
- **Диск:** 20 GB свободного места
- **CPU:** 2 ядра

### Рекомендуемые требования
- **RAM:** 8 GB
- **Диск:** 50 GB SSD
- **CPU:** 4 ядра

### Что нужно иметь готовым
- [ ] SSH доступ к серверу с правами sudo
- [ ] OpenAI API ключ (или Anthropic API ключ)
- [ ] Доменное имя или IP адрес сервера
- [ ] (Опционально) Telegram бот токен для n8n интеграции

---

## Подготовка сервера

### Шаг 1: Подключение к серверу

```bash
ssh user@YOUR_SERVER_IP
```

### Шаг 2: Обновление системы

```bash
sudo apt update && sudo apt upgrade -y
```

### Шаг 3: Установка базовых утилит

```bash
sudo apt install -y curl wget git nano jq htop
```

### Шаг 4: Настройка файрвола (UFW)

```bash
# Включить UFW
sudo ufw enable

# Разрешить SSH
sudo ufw allow 22/tcp

# Разрешить HTTP/HTTPS для Caddy
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Проверить статус
sudo ufw status
```

**Важно:** Порты 5678, 8080, 5432, 6333 НЕ должны быть открыты извне.

---

## Установка Docker

### Шаг 1: Установка Docker

```bash
# Скачать и запустить установщик
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавить пользователя в группу docker
sudo usermod -aG docker $USER

# Перелогиниться для применения изменений
exit
# Подключиться снова
ssh user@YOUR_SERVER_IP
```

### Шаг 2: Проверка Docker

```bash
docker --version
# Ожидаемый вывод: Docker version 24.x.x или выше

docker compose version
# Ожидаемый вывод: Docker Compose version v2.x.x
```

### Шаг 3: Запуск тестового контейнера

```bash
docker run hello-world
# Должен вывести "Hello from Docker!"
```

---

## Создание инфраструктуры

### Шаг 1: Создание директорий

```bash
# Создать основную структуру
sudo mkdir -p /opt/mpis/{api,scripts,docs,n8n,personas,sources,input,infra,secrets,tmp,exports,backups}

# Создать директории для данных
sudo mkdir -p /opt/mpis/postgres_data
sudo mkdir -p /opt/mpis/qdrant_data

# Установить права (UID 1000 используется Docker контейнерами)
sudo chown -R 1000:1000 /opt/mpis
```

### Шаг 2: Проверка структуры

```bash
ls -la /opt/mpis/
# Все папки должны принадлежать пользователю 1000
```

### Шаг 3: Создание Docker сети

```bash
docker network create mpis_net

# Проверить
docker network ls | grep mpis_net
```

---

## Запуск базы данных

### Шаг 1: Генерация надежного пароля

```bash
# Сгенерировать пароль
openssl rand -base64 32
# Сохраните этот пароль! Он понадобится дальше.
```

### Шаг 2: Запуск PostgreSQL

```bash
# Замените YOUR_SECURE_PASSWORD на сгенерированный пароль
docker run -d \
  --name mpis-postgres \
  --network mpis_net \
  -e POSTGRES_USER=mpis \
  -e POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD \
  -e POSTGRES_DB=mpis \
  -v /opt/mpis/postgres_data:/var/lib/postgresql/data \
  --restart unless-stopped \
  postgres:16-alpine
```

### Шаг 3: Проверка PostgreSQL

```bash
# Подождать 10 секунд для запуска
sleep 10

# Проверить статус
docker ps | grep mpis-postgres
# Должен показать "Up" статус

# Проверить подключение
docker exec mpis-postgres pg_isready -U mpis
# Ожидаемый вывод: accepting connections
```

---

## Запуск Qdrant

### Шаг 1: Запуск Qdrant

```bash
docker run -d \
  --name mpis-qdrant \
  --network mpis_net \
  -v /opt/mpis/qdrant_data:/qdrant/storage \
  --restart unless-stopped \
  qdrant/qdrant:latest
```

### Шаг 2: Проверка Qdrant

```bash
# Подождать запуска
sleep 10

# Проверить статус
docker ps | grep mpis-qdrant

# Проверить API (через внутреннюю сеть)
docker exec mpis-postgres curl -s http://mpis-qdrant:6333/collections | jq
# Должен вернуть: {"result":{"collections":[]},"status":"ok","time":...}
```

---

## Клонирование репозитория

### Шаг 1: Клонировать репозиторий

```bash
cd /opt/mpis
sudo git clone https://github.com/ivanvdovicenco/mpis.git repo
sudo chown -R 1000:1000 /opt/mpis/repo
```

### Шаг 2: Проверить структуру

```bash
ls -la /opt/mpis/repo/
# Должны быть: api/, scripts/, infra/, docs/, n8n/, README.md
```

---

## Применение миграций

### Шаг 1: Применить миграции последовательно

```bash
cd /opt/mpis/repo

# Миграция 1: Genesis (Module 1)
docker exec -i mpis-postgres psql -U mpis -d mpis < scripts/002_genesis.sql
echo "Genesis migration: OK"

# Миграция 2: Life (Module 2)
docker exec -i mpis-postgres psql -U mpis -d mpis < scripts/003_life.sql
echo "Life migration: OK"

# Миграция 3: Publisher (Module 3)
docker exec -i mpis-postgres psql -U mpis -d mpis < scripts/004_publisher.sql
echo "Publisher migration: OK"

# Миграция 4: Analytics (Module 4)
docker exec -i mpis-postgres psql -U mpis -d mpis < scripts/005_analytics.sql
echo "Analytics migration: OK"
```

### Шаг 2: Проверить таблицы

```bash
docker exec -i mpis-postgres psql -U mpis -d mpis -c "\dt"
```

**Ожидаемые таблицы:**
- `personas`, `persona_versions`, `sources`, `audit_log`
- `genesis_jobs`, `genesis_drafts`, `genesis_messages`
- `life_events`, `life_cycles`, `life_cycle_drafts`, `life_metrics`, `recommendations`
- `content_plans`, `content_drafts`, `published_items`, `channel_accounts`, `item_metrics`
- `analytics_rollups`, `eidos_recommendations`, `experiments`, `dashboard_views`

---

## Конфигурация

### Шаг 1: Создать файл конфигурации

```bash
cp /opt/mpis/repo/api/.env.example /opt/mpis/infra/.env
```

### Шаг 2: Редактировать конфигурацию

```bash
nano /opt/mpis/infra/.env
```

**Обязательные изменения:**

```env
# Замените YOUR_SECURE_PASSWORD на ваш пароль PostgreSQL
DATABASE_URL=postgresql+asyncpg://mpis:YOUR_SECURE_PASSWORD@mpis-postgres:5432/mpis

# Укажите ваш OpenAI API ключ
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Или Anthropic API ключ (если используете Claude)
# ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# LLM_PROVIDER=anthropic
# LLM_MODEL=claude-3-opus-20240229
```

### Шаг 3: Проверить конфигурацию

```bash
cat /opt/mpis/infra/.env | grep -E "DATABASE_URL|OPENAI_API_KEY|LLM_PROVIDER"
# Убедитесь, что значения правильные (без реальных секретов в выводе)
```

---

## Запуск MPIS API

### Шаг 1: Собрать и запустить

```bash
cd /opt/mpis/repo/infra

# Собрать образ и запустить
docker compose -f docker-compose.full.yml up -d --build
```

### Шаг 2: Проверить логи

```bash
# Просмотр логов
docker logs genesis-api --tail 50

# Следить за логами в реальном времени
docker logs genesis-api -f
# (Ctrl+C для выхода)
```

### Шаг 3: Проверить статус

```bash
docker ps | grep genesis-api
# Должен показать статус "Up" и "healthy"
```

---

## Тестирование функциональности

### Тест 1: Проверка здоровья API

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

### Тест 2: Проверка корневого эндпоинта

```bash
curl -s http://localhost:8080/ | jq
```

**Ожидаемый результат:** JSON с описанием всех модулей (genesis, life, publisher, analytics)

### Тест 3: Проверка OpenAPI документации

```bash
curl -s http://localhost:8080/openapi.json | jq '.info'
```

**Ожидаемый результат:**
```json
{
  "title": "MPIS API",
  "version": "1.0.0"
}
```

### Тест 4: Создание тестовой персоны (DRY_RUN)

```bash
# Создать персону (в режиме DRY_RUN если LLM ключ не настроен)
curl -s -X POST http://localhost:8080/genesis/start \
  -H "Content-Type: application/json" \
  -d '{
    "persona_name": "Test Persona",
    "inspiration_source": "Test Source",
    "language": "ru"
  }' | jq
```

**Ожидаемый результат:** JSON с `job_id` и `status`

### Тест 5: Тестирование Life модуля

```bash
# Сначала получите persona_id из предыдущего теста
# Замените YOUR_PERSONA_ID на реальный ID

curl -s -X POST http://localhost:8080/life/event \
  -H "Content-Type: application/json" \
  -d '{
    "persona_id": "YOUR_PERSONA_ID",
    "event_type": "note",
    "content": "Test event for verification",
    "tags": ["test"]
  }' | jq
```

### Тест 6: Тестирование Publisher модуля

```bash
curl -s -X POST http://localhost:8080/publisher/plan \
  -H "Content-Type: application/json" \
  -d '{
    "persona_id": "YOUR_PERSONA_ID",
    "title": "Test Content Plan",
    "topic": "testing",
    "channel": "telegram"
  }' | jq
```

### Тест 7: Тестирование Analytics модуля

```bash
curl -s "http://localhost:8080/analytics/persona/YOUR_PERSONA_ID/summary?range=7d" | jq
```

### Скрипт автоматического тестирования

Создайте файл для автоматической проверки:

```bash
cat > /opt/mpis/test_mpis.sh << 'EOF'
#!/bin/bash

echo "=== MPIS Functionality Tests ==="
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
HEALTH=$(curl -s http://localhost:8080/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed"
    exit 1
fi

# Test 2: Root Endpoint
echo "Test 2: Root Endpoint"
ROOT=$(curl -s http://localhost:8080/)
if echo "$ROOT" | grep -q "modules"; then
    echo "✓ Root endpoint passed"
else
    echo "✗ Root endpoint failed"
fi

# Test 3: OpenAPI Schema
echo "Test 3: OpenAPI Schema"
OPENAPI=$(curl -s http://localhost:8080/openapi.json)
if echo "$OPENAPI" | grep -q "openapi"; then
    echo "✓ OpenAPI schema passed"
else
    echo "✗ OpenAPI schema failed"
fi

# Test 4: Genesis Endpoint Available
echo "Test 4: Genesis Endpoint"
GENESIS=$(curl -s -X POST http://localhost:8080/genesis/start \
  -H "Content-Type: application/json" \
  -d '{"persona_name": "Test", "language": "en"}' 2>&1)
if echo "$GENESIS" | grep -q "job_id\|error"; then
    echo "✓ Genesis endpoint responding"
else
    echo "✗ Genesis endpoint not responding"
fi

# Test 5: Life Endpoint Available
echo "Test 5: Life Endpoint"
LIFE=$(curl -s -X POST http://localhost:8080/life/event \
  -H "Content-Type: application/json" \
  -d '{"persona_id": "00000000-0000-0000-0000-000000000000", "event_type": "note", "content": "test"}' 2>&1)
if echo "$LIFE" | grep -q "error\|id"; then
    echo "✓ Life endpoint responding"
else
    echo "✗ Life endpoint not responding"
fi

# Test 6: Publisher Endpoint Available
echo "Test 6: Publisher Endpoint"
PUB=$(curl -s -X POST http://localhost:8080/publisher/plan \
  -H "Content-Type: application/json" \
  -d '{"persona_id": "00000000-0000-0000-0000-000000000000", "title": "test", "topic": "test", "channel": "telegram"}' 2>&1)
if echo "$PUB" | grep -q "error\|id"; then
    echo "✓ Publisher endpoint responding"
else
    echo "✗ Publisher endpoint not responding"
fi

# Test 7: Analytics Endpoint Available
echo "Test 7: Analytics Endpoint"
ANAL=$(curl -s "http://localhost:8080/analytics/persona/00000000-0000-0000-0000-000000000000/summary?range=7d" 2>&1)
if echo "$ANAL" | grep -q "error\|persona_id"; then
    echo "✓ Analytics endpoint responding"
else
    echo "✗ Analytics endpoint not responding"
fi

echo ""
echo "=== All tests completed ==="
EOF

chmod +x /opt/mpis/test_mpis.sh
```

Запустить тесты:

```bash
/opt/mpis/test_mpis.sh
```

---

## Интеграция с n8n

### Если n8n уже запущен

```bash
# Подключить n8n к сети MPIS
docker network connect mpis_net n8n-n8n-1
```

### Импорт workflow шаблонов

1. Откройте n8n в браузере
2. Создайте новый workflow
3. Импортируйте JSON из `/opt/mpis/repo/n8n/workflows/content-publishing.json`
4. Импортируйте JSON из `/opt/mpis/repo/n8n/workflows/daily-reflection.json`

### Настройка переменных окружения n8n

Добавьте в конфигурацию n8n:

```
PERSONA_ID=your-persona-id
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_APPROVAL_CHAT_ID=your-chat-id
```

---

## Настройка HTTPS через Caddy

### Если у вас есть n8n с Caddy

Добавьте в Caddyfile:

```
mpis.46.62.174.134.nip.io {
    reverse_proxy genesis-api:8080
}
```

Подключите API к сети Caddy:

```bash
docker network connect n8n_default genesis-api
docker exec n8n-caddy-1 caddy reload --config /etc/caddy/Caddyfile
```

---

## Мониторинг и обслуживание

### Просмотр логов

```bash
# API логи
docker logs genesis-api --tail 100

# PostgreSQL логи
docker logs mpis-postgres --tail 100

# Qdrant логи
docker logs mpis-qdrant --tail 100
```

### Создание бэкапов

```bash
# Бэкап базы данных
docker exec mpis-postgres pg_dump -U mpis mpis > /opt/mpis/backups/mpis_$(date +%Y%m%d_%H%M).sql

# Бэкап персон
tar -czf /opt/mpis/backups/personas_$(date +%Y%m%d).tar.gz -C /opt/mpis personas/
```

### Перезапуск сервисов

```bash
# Перезапустить API
docker restart genesis-api

# Перезапустить все
cd /opt/mpis/repo/infra
docker compose -f docker-compose.full.yml restart
```

### Обновление MPIS

```bash
cd /opt/mpis/repo
git pull origin main

cd infra
docker compose -f docker-compose.full.yml up -d --build
```

---

## Чеклист после развертывания

- [ ] Docker установлен и работает
- [ ] PostgreSQL контейнер запущен
- [ ] Qdrant контейнер запущен
- [ ] Все миграции применены
- [ ] .env файл настроен с правильными ключами
- [ ] MPIS API контейнер запущен
- [ ] Health check проходит
- [ ] Все эндпоинты отвечают
- [ ] UFW настроен (порты 80, 443, 22 открыты)
- [ ] Бэкапы настроены

---

## Контакты для помощи

- Документация: `/opt/mpis/repo/docs/`
- API документация: `http://localhost:8080/docs`
- GitHub Issues: https://github.com/ivanvdovicenco/mpis/issues
