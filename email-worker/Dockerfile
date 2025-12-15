FROM python:3.11-alpine

WORKDIR /app

# Устанавливаем системные зависимости
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY worker.py .

# Делаем файл исполняемым
RUN chmod +x worker.py

# Запускаем worker
CMD ["python", "-u", "worker.py"]