from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pika
import json
import os
from datetime import datetime
import uvicorn

app = FastAPI(title="Notification Service")

# Конфигурация RabbitMQ
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://admin:password@rabbitmq:5672/")
QUEUE_NAME = "email_queue"

# Модель запроса
class NotificationRequest(BaseModel):
    type: str
    user_email: str
    user_name: str
    subject: str
    message: str

# Настройка RabbitMQ
@app.on_event("startup")
async def startup():
    print("🔄 Подключение к RabbitMQ...")
    try:
        app.state.connection = pika.BlockingConnection(
            pika.URLParameters(RABBITMQ_URL)
        )
        app.state.channel = app.state.connection.channel()
        app.state.channel.queue_declare(queue=QUEUE_NAME, durable=True)
        print("✅ Подключение к RabbitMQ установлено")
    except Exception as e:
        print(f"❌ Ошибка подключения к RabbitMQ: {e}")

@app.on_event("shutdown")
async def shutdown():
    if hasattr(app.state, 'connection'):
        app.state.connection.close()
        print("📴 Соединение с RabbitMQ закрыто")

@app.get("/")
async def root():
    return {"service": "Notification Service", "status": "running"}

@app.get("/health")
async def health():
    if hasattr(app.state, 'connection') and app.state.connection.is_open:
        return {"status": "healthy", "rabbitmq": "connected"}
    return {"status": "unhealthy", "rabbitmq": "disconnected"}

@app.post("/notify")
async def send_notification(request: NotificationRequest):
    if not hasattr(app.state, 'channel'):
        raise HTTPException(status_code=503, detail="Notification service unavailable")
    
    try:
        message = {
            "type": request.type,
            "user_email": request.user_email,
            "user_name": request.user_name,
            "subject": request.subject,
            "message": request.message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        app.state.channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json.dumps(message, ensure_ascii=False),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent
            )
        )
        
        print(f"📨 Уведомление отправлено в очередь для {request.user_email}")
        
        return {
            "status": "success",
            "message": "Notification queued for delivery",
            "user_email": request.user_email
        }
        
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-test-email")
async def send_test_email():
    """Тестовый эндпоинт для отправки сообщения в очередь"""
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        channel.queue_declare(queue="email_queue", durable=True)
        
        message = {
            "type": "test_email",
            "user_email": "test@example.com",
            "user_name": "Test User",
            "subject": "Тестовое письмо",
            "message": "Это тестовое сообщение для проверки worker"
        }
        
        channel.basic_publish(
            exchange="",
            routing_key="email_queue",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        
        connection.close()
        print(f"📨 Тестовое сообщение отправлено в очередь")
        return {"status": "success", "message": "Тестовое сообщение отправлено"}
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    print("🚀 Запуск Notification Service на порту 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")