from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from pydantic import BaseModel
import os
from datetime import datetime
import uvicorn
import httpx
from typing import Optional
import re

app = FastAPI(title="User Service")

# Валидация email (кастомная, чтобы не зависеть от email-validator)
def validate_email(email: str) -> bool:
    """Простая валидация email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Подключение к PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@postgres:5432/users_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Добавьте после подключения к БД
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8001")

# Pydantic модели с кастомной валидацией
class UserCreate(BaseModel):
    email: str
    name: str
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "name": "John Doe"
            }
        }
    
    def validate_email(self):
        if not validate_email(self.email):
            raise ValueError("Invalid email format")

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime

# Модель пользователя
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Создаем таблицы при запуске
@app.on_event("startup")
async def startup():
    print("🔄 Создание таблиц в базе данных...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Таблицы созданы успешно")
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")

# Эндпоинты
@app.get("/")
async def root():
    return {"service": "User Service", "status": "running", "version": "1.0"}

@app.get("/health")
async def health():
    try:
        # Проверяем подключение к БД
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate):
    # Валидация email
    if not validate_email(user.email):
        raise HTTPException(status_code=400, detail="Неверный формат email")
    
    db = SessionLocal()
    try:
        # Проверяем существование пользователя
        existing = db.query(User).filter(User.email == user.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email уже используется")
        
        # Создаем пользователя
        db_user = User(email=user.email, name=user.name)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        print(f"✅ Создан пользователь: {db_user.email}")
        
        # Пытаемся отправить приветственное письмо (асинхронно, без блокировки)
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{NOTIFICATION_SERVICE_URL}/notify",
                    json={
                        "type": "welcome_email",
                        "user_email": db_user.email,
                        "user_name": db_user.name,
                        "subject": "Добро пожаловать!",
                        "message": f"Привет, {db_user.name}! Добро пожаловать в наше приложение."
                    }
                )
                if response.status_code == 200:
                    print(f"📧 Приветственное письмо отправлено для {db_user.email}")
                else:
                    print(f"⚠️ Не удалось отправить письмо: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Ошибка отправки уведомления: {e}")
            # Продолжаем работу даже если уведомление не отправилось
        
        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка создания пользователя: {str(e)}")
    finally:
        db.close()

@app.get("/users/", response_model=list[UserResponse])
async def get_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        return users
    finally:
        db.close()

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        return user
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Запуск User Service на порту 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")