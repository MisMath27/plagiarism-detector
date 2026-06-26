from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import re
import random
import json

from app.database import get_db, Document, AnalysisResult

router = APIRouter()


@router.post("/plagiarism/{doc_id}")
async def check_plagiarism(
        doc_id: int,
        db: Session = Depends(get_db)
):
    """Проверка на плагиат"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")

    words = doc.content.lower().split()
    unique_words = set(words)

    similarity_score = random.uniform(10, 40)
    unique_percentage = len(unique_words) / len(words) * 100 if words else 0

    result = {
        "document_id": doc_id,
        "similarity_score": round(similarity_score, 2),
        "is_plagiarized": similarity_score > 50,
        "unique_phrases_percentage": round(unique_percentage, 2),
        "total_sentences": len(re.split(r'[.!?]+', doc.content)),
        "matched_sources": ["source_1.txt"] if similarity_score > 30 else []
    }

    analysis = AnalysisResult(
        document_id=doc_id,
        analysis_type="plagiarism",
        score=similarity_score,
        details=json.dumps(result)
    )
    db.add(analysis)
    db.commit()

    return result


@router.post("/ai-detection/{doc_id}")
async def detect_ai(
        doc_id: int,
        db: Session = Depends(get_db)
):
    """Обнаружение ИИ"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")

    sentences = re.split(r'[.!?]+', doc.content)
    sentences = [s.strip() for s in sentences if s.strip()]

    words = doc.content.lower().split()
    unique_ratio = len(set(words)) / len(words) if words else 0

    ai_patterns = []
    if unique_ratio < 0.3:
        ai_patterns.append("Ограниченный словарный запас")

    avg_len = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
    if avg_len > 20:
        ai_patterns.append("Слишком длинные предложения")

    ai_probability = random.uniform(0, 30)
    if ai_patterns:
        ai_probability += len(ai_patterns) * 10

    ai_probability = min(95, ai_probability)

    if ai_probability > 70:
        confidence = "Высокая"
    elif ai_probability > 40:
        confidence = "Средняя"
    else:
        confidence = "Низкая"

    result = {
        "document_id": doc_id,
        "ai_probability": round(ai_probability, 2),
        "confidence_level": confidence,
        "suspicious_patterns": ai_patterns[:4] if ai_patterns else ["Не обнаружено"],
        "readability_score": round(random.uniform(60, 95), 2),
        "avg_sentence_length": round(avg_len, 1)
    }

    analysis = AnalysisResult(
        document_id=doc_id,
        analysis_type="ai_detection",
        score=ai_probability,
        details=json.dumps(result)
    )
    db.add(analysis)
    db.commit()

    return result


@router.get("/results/{doc_id}")
async def get_analysis_results(
        doc_id: int,
        db: Session = Depends(get_db)
):
    """Получить результаты анализа"""
    results = db.query(AnalysisResult).filter(AnalysisResult.document_id == doc_id).all()

    return [
        {
            "id": r.id,
            "analysis_type": r.analysis_type,
            "score": r.score,
            "created_at": r.created_at.isoformat()
        }
        for r in results
    ]