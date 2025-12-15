mkdir notification-integration
cd notification-integration

# Создать все файлы из структуры выше

Шаг 2: Запуск системы
docker-compose up --build

Шаг 3: Тестирование

1. Создание пользователя через User Service:

curl -X POST "http://localhost:8000/users/" \
 -H "Content-Type: application/json" \
 -d '{"email": "test@example.com", "name": "Иван Иванов"}'

2. Проверка созданных пользователей:

curl "http://localhost:8000/users/"

3. Мониторинг логов:

# Просмотр логов всех сервисов

docker-compose logs -f

# Просмотр логов конкретного сервиса

docker-compose logs -f user-service
docker-compose logs -f email-worker

4. Веб-интерфейс RabbitMQ:

Откройте в браузере: http://localhost:15672

Логин: admin

Пароль: password

Перейдите в Queues → email_queue для мониторинга сообщений

7. Тестирование механизма retry

Симуляция ошибок в Email Worker:
В файле email-worker/worker.py в методе send_email уже есть симуляция 20% вероятности ошибки. Можно увеличить вероятность для тестирования:

if random.random() < 0.8:
raise Exception("Simulated email sending error")

Наблюдение за retry в логах:  
docker-compose logs -f email-worker
