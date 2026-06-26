from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

os.makedirs("backend/data", exist_ok=True)
os.makedirs("backend/uploads", exist_ok=True)

DATABASE_URL = "sqlite:///./backend/data/plagiarism.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    content = Column(Text)
    content_hash = Column(String, index=True, unique=True)
    source = Column(String, default="user_upload")
    file_type = Column(String, default="other")
    uploaded_at = Column(DateTime, default=datetime.now)
    file_size = Column(Integer, default=0)
    word_count = Column(Integer, default=0)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True)
    analysis_type = Column(String)
    score = Column(Float)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()