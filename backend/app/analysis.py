from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import re
import json
from datetime import datetime

from ..database import get_db, Document, AnalysisResult
from ..analyzer import TextAnalyzer

router = APIRouter()
analyzer = TextAnalyzer()

# Корпус документов для сравнения (для демонстрации)
SAMPLE_CORPUS = [
    "Это образец текста для сравнения с другими документами. Он содержит стандартные фразы и выражения.",
    "Второй образец документа с различными словами и предложениями. Используется для проверки уникальности.",
    "Третий пример текста с уникальным содержанием. Помогает определить оригинальность проверяемого документа."
]


@router.post("/plagiarism/{doc_id}")
async def check_plagiarism(
        doc_id: int,
        db: Session = Depends(get_db)
):
    """Проверка на плагиат с реальным анализом"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")

    # Получаем все документы из базы для сравнения
    all_docs = db.query(Document).filter(Document.id != doc_id).all()
    corpus = [d.content for d in all_docs[:10]]  # Используем до 10 документов

    # Добавляем образцы для сравнения
    if len(corpus) < 3:
        corpus.extend(SAMPLE_CORPUS[:3])

    # Выполняем анализ
    result = analyzer.calculate_uniqueness(doc.content, corpus)

    # Сохраняем результат
    analysis = AnalysisResult(
        document_id=doc_id,
        analysis_type="plagiarism",
        score=result['similarity_score'],
        details=json.dumps({
            'unique_phrases_percentage': result['unique_phrases_percentage'],
            'total_sentences': result['total_sentences'],
            'matched_sources': result['matched_sources'],
            'similarity_score': result['similarity_score']
        })
    )
    db.add(analysis)
    db.commit()

    return result


@router.post("/ai-detection/{doc_id}")
async def detect_ai(
        doc_id: int,
        db: Session = Depends(get_db)
):
    """Обнаружение ИИ с реальным анализом"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")

    # Выполняем анализ
    result = analyzer.detect_ai_content(doc.content)

    # Сохраняем результат
    analysis = AnalysisResult(
        document_id=doc_id,
        analysis_type="ai_detection",
        score=result['ai_probability'],
        details=json.dumps({
            'ai_probability': result['ai_probability'],
            'confidence_level': result['confidence_level'],
            'suspicious_patterns': result['suspicious_patterns'],
            'readability_score': result['readability_score'],
            'avg_sentence_length': result['avg_sentence_length']
        })
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
            "created_at": r.created_at.isoformat(),
            "details": json.loads(r.details) if r.details else {}
        }
        for r in results
    ]


@router.get("/stats")
async def get_stats(
        db: Session = Depends(get_db)
):
    """Получить статистику по анализам"""
    total_docs = db.query(Document).count()
    total_analysis = db.query(AnalysisResult).count()

    # Средний балл по плагиату
    plag_results = db.query(AnalysisResult).filter(
        AnalysisResult.analysis_type == "plagiarism"
    ).all()

    avg_plag_score = sum(r.score for r in plag_results) / len(plag_results) if plag_results else 0

    # Средний балл по ИИ
    ai_results = db.query(AnalysisResult).filter(
        AnalysisResult.analysis_type == "ai_detection"
    ).all()

    avg_ai_score = sum(r.score for r in ai_results) / len(ai_results) if ai_results else 0

    return {
        "total_documents": total_docs,
        "total_analyses": total_analysis,
        "average_plagiarism_score": round(avg_plag_score, 2),
        "average_ai_score": round(avg_ai_score, 2),
        "last_analysis": ai_results[-1].created_at.isoformat() if ai_results else None
    }