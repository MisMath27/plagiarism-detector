# backend/app/database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os

# Путь к базе данных
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'plagiarism.db')}"

# Создаем движок
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Для SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Модель для документов (уже есть)
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    content = Column(Text)
    content_hash = Column(String, unique=True)
    source = Column(String, default="user_upload")
    file_type = Column(String)
    file_size = Column(Integer)
    word_count = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


# Новая модель для эталонных текстов
class ReferenceText(Base):
    __tablename__ = "reference_texts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    source = Column(String)  # URL, книга, автор
    content = Column(Text)
    content_hash = Column(String, unique=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


# Новая модель для результатов анализа
class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True)
    analysis_type = Column(String)  # "plagiarism" или "ai_detection"
    score = Column(Float)
    details = Column(Text)  # JSON строка с деталями
    created_at = Column(DateTime, default=datetime.utcnow)


# Функция для получения сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Создаем все таблицы
Base.metadata.create_all(bind=engine)