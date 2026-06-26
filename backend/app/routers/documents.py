from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db, Document

router = APIRouter()


@router.get("/")
async def get_all_documents(
        limit: int = 20,
        skip: int = 0,
        db: Session = Depends(get_db)
):
    """Получить все документы"""
    docs = db.query(Document).offset(skip).limit(limit).all()

    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "source": doc.source,
            "file_type": doc.file_type,
            "uploaded_at": doc.uploaded_at.isoformat(),
            "file_size": doc.file_size,
            "word_count": doc.word_count,
            "content_preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
        }
        for doc in docs
    ]


@router.get("/{doc_id}")
async def get_document(
        doc_id: int,
        db: Session = Depends(get_db)
):
    """Получить документ по ID"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")

    return {
        "id": doc.id,
        "filename": doc.filename,
        "content": doc.content,
        "source": doc.source,
        "file_type": doc.file_type,
        "uploaded_at": doc.uploaded_at.isoformat(),
        "file_size": doc.file_size,
        "word_count": doc.word_count
    }