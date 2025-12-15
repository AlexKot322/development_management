### Запуск всех сервисов:

```
docker-compose up --build
```

## Альтернативный запуск (в фоновом режиме):

```
docker-compose up --build -d
```

## Просмотр логов:

```
docker-compose logs -f
```

## Остановка:

```
docker-compose down
```

## Проверка запущенных контейнеров:

```
docker-compose ps
```

## Проверка доступности сервисов:

- User Service API: http://localhost:8000/docs (документация)
- RabbitMQ Management: http://localhost:15672
- http://localhost:8001/health

## Создание пользователя:

1. Через терминал bash:

```
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "name": "Иван Иванов"}'
```

2. С помощью браузера и openapi:

- Откройте http://localhost:8000/docs
- Нажмите на "POST /users/"
- Нажмите "Try it out"
- Введите данные:

```
{
  "email": "test@example.com",
  "name": "Иван Иванов"
}
```

- Нажмите "Execute"

## Получить пользователей:

1. С помощью bash терминала:

```
curl "http://localhost:8000/users/"
```

2. С помощью браузера и openapi:

- Откройте http://localhost:8000/docs
- Нажмите на "GET/users/"
- Нажмите "Try it out"
- Нажмите "Execute"

## Дополнительные команды:

```
# Просмотр логов всех сервисов
docker-compose logs -f

# Просмотр логов конкретного сервиса
docker-compose logs -f user-service
docker-compose logs -f email-worker

# Проверка использования ресурсов
docker stats

# Остановить все сервисы
docker-compose down

# Остановить и удалить тома (данные БД)
docker-compose down -v

# Перезапустить конкретный сервис
docker-compose restart user-service
```
