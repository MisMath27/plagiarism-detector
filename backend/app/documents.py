from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db, Document

router = APIRouter()

@router.get("/")
async def get_documents(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Получить все документы"""
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).limit(limit).all()
    
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "uploaded_at": doc.uploaded_at.isoformat(),
            "file_size": doc.file_size,
            "word_count": doc.word_count,
            "content_preview": doc.content[:150] + "..." if len(doc.content) > 150 else doc.content
        }
        for doc in docs
    ]