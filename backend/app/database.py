# backend/app/database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'plagiarism.db')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


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


class ReferenceText(Base):
    __tablename__ = "reference_texts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    source = Column(String)
    content = Column(Text)
    content_hash = Column(String, unique=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True)
    analysis_type = Column(String)
    score = Column(Float)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)