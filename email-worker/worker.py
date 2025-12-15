#!/usr/bin/env python3
import pika
import json
import os
import time
import sys

print("=" * 60)
print("🚀 ЗАПУСК EMAIL WORKER")
print("=" * 60)

# Получаем URL RabbitMQ из переменных окружения
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://admin:password@rabbitmq:5672/")
QUEUE_NAME = "email_queue"

print(f"🔗 RabbitMQ URL: {RABBITMQ_URL}")
print(f"📬 Очередь: {QUEUE_NAME}")
print("⏳ Подключение к RabbitMQ...")

def wait_for_rabbitmq():
    """Ожидание доступности RabbitMQ с повторными попытками"""
    max_retries = 30
    retry_delay = 2
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 Попытка подключения {attempt}/{max_retries}...")
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            channel = connection.channel()
            
            # Просто проверяем подключение, не объявляем очередь с параметрами
            connection.close()
            print("✅ RabbitMQ доступен!")
            return True
            
        except pika.exceptions.AMQPConnectionError as e:
            print(f"❌ Ошибка подключения: {e}")
            if attempt < max_retries:
                print(f"⏳ Повтор через {retry_delay} секунд...")
                time.sleep(retry_delay)
            else:
                print("❌ Не удалось подключиться к RabbitMQ")
                return False
    
    return False

def delete_existing_queue(channel, queue_name):
    """Удаляет существующую очередь чтобы избежать конфликта параметров"""
    try:
        channel.queue_delete(queue=queue_name)
        print(f"🗑️ Удалена существующая очередь '{queue_name}'")
        time.sleep(1)  # Даем время на удаление
    except Exception as e:
        print(f"⚠️ Не удалось удалить очередь: {e}")

def process_message(ch, method, properties, body):
    """Обработка сообщения из очереди"""
    try:
        print(f"📩 Получено новое сообщение!")
        print(f"📦 Длина тела: {len(body)} байт")
        
        message = json.loads(body)
        print(f"📧 Email: {message.get('user_email', 'N/A')}")
        print(f"📋 Тема: {message.get('subject', 'N/A')}")
        print(f"👤 Имя: {message.get('user_name', 'N/A')}")
        print(f"📝 Тип: {message.get('type', 'N/A')}")
        
        # Имитация обработки
        time.sleep(1)
        
        # Подтверждаем обработку
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"✅ Сообщение обработано успешно")
        print("-" * 40)
        
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка декодирования JSON: {e}")
        print(f"❌ Сырые данные: {body[:100]}...")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        print(f"❌ Ошибка обработки: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def main():
    """Основная функция worker"""
    
    # Ждем RabbitMQ
    if not wait_for_rabbitmq():
        print("❌ Worker не может продолжить без RabbitMQ")
        sys.exit(1)
    
    # Основной цикл работы
    while True:
        try:
            print("\n🔄 Установка соединения с RabbitMQ...")
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            channel = connection.channel()
            
            # Сначала удаляем существующую очередь (чтобы избежать конфликта параметров)
            delete_existing_queue(channel, QUEUE_NAME)
            
            # Объявляем очередь с БЕЗ дополнительных аргументов (самый простой вариант)
            channel.queue_declare(
                queue=QUEUE_NAME,
                durable=True
            )
            
            # Объявляем DLQ (Dead Letter Queue) отдельно
            dlq_name = f"{QUEUE_NAME}_dlq"
            channel.queue_declare(
                queue=dlq_name,
                durable=True
            )
            
            # Настройка качества обслуживания
            channel.basic_qos(prefetch_count=1)
            
            # Начинаем слушать очередь
            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=process_message,
                auto_ack=False
            )
            
            print(f"\n✅ Worker готов к работе!")
            print(f"📊 Слушаю очередь: {QUEUE_NAME}")
            print(f"🗑️ DLQ очередь: {dlq_name}")
            print("📝 Для отправки тестового сообщения выполните:")
            print("   curl -X POST http://localhost:8001/send-test-email")
            print("=" * 60)
            
            # Запускаем бесконечный цикл обработки
            channel.start_consuming()
            
        except KeyboardInterrupt:
            print("\n\n🛑 Остановка worker по запросу пользователя...")
            if 'connection' in locals() and connection.is_open:
                connection.close()
            break
            
        except pika.exceptions.ConnectionClosedByBroker:
            print("🔌 Соединение закрыто брокером")
            time.sleep(5)
            continue
            
        except pika.exceptions.AMQPConnectionError:
            print("🔌 Потеряно соединение с RabbitMQ")
            time.sleep(5)
            continue
            
        except Exception as e:
            print(f"💥 Неожиданная ошибка: {e}")
            time.sleep(5)
            continue

if __name__ == "__main__":
    main()