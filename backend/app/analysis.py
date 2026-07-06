from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from ..database import get_db, Document, AnalysisResult, ReferenceText
from ..analyzer import TextAnalyzer

router = APIRouter()
analyzer = TextAnalyzer()


@router.post("/plagiarism/{doc_id}")
async def check_plagiarism(
        doc_id: int,
        db: Session = Depends(get_db)
):
    """
    Проверка на плагиат с использованием гибридного подхода:
    - Jaccard Index (40%) - для буквальных совпадений
    - TF-IDF (60%) - для семантических совпадений
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")

    reference_texts = db.query(ReferenceText).filter(
        ReferenceText.is_active == True
    ).limit(100).all()

    corpus = [ref.content for ref in reference_texts]

    result = analyzer.calculate_hybrid_similarity(doc.content, corpus)

    analysis = AnalysisResult(
        document_id=doc_id,
        analysis_type="plagiarism",
        score=result['hybrid_score'],
        details=json.dumps({
            'jaccard_score': result['jaccard_score'],
            'tfidf_score': result['tfidf_score'],
            'hybrid_score': result['hybrid_score'],
            'unique_phrases_percentage': result['unique_phrases_percentage'],
            'total_sentences': result['total_sentences'],
            'matched_sources': result['matched_sources'],
            'method_details': result.get('method_details', 'Гибридный анализ')
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
    """Обнаружение ИИ с расширенным анализом"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")

    result = analyzer.detect_ai_content(doc.content)

    analysis = AnalysisResult(
        document_id=doc_id,
        analysis_type="ai_detection",
        score=result['ai_probability'],
        details=json.dumps({
            'ai_probability': result['ai_probability'],
            'confidence_level': result['confidence_level'],
            'suspicious_patterns': result['suspicious_patterns'],
            'readability_score': result['readability_score'],
            'avg_sentence_length': result['avg_sentence_length'],
            'vocabulary_diversity': result.get('vocabulary_diversity', 0)
        })
    )
    db.add(analysis)
    db.commit()

    return result


@router.post("/full-analysis/{doc_id}")
async def full_analysis(
        doc_id: int,
        db: Session = Depends(get_db)
):
    """
    Полный анализ текста:
    1. Гибридный анализ на плагиат (Jaccard + TF-IDF)
    2. Обнаружение ИИ
    3. Статистика текста
    4. Рекомендации
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")

    reference_texts = db.query(ReferenceText).filter(
        ReferenceText.is_active == True
    ).limit(100).all()

    corpus = [ref.content for ref in reference_texts]

    result = analyzer.full_analysis(doc.content, corpus)

    plag_analysis = AnalysisResult(
        document_id=doc_id,
        analysis_type="plagiarism",
        score=result['plagiarism']['hybrid_score'],
        details=json.dumps(result['plagiarism'])
    )
    db.add(plag_analysis)

    ai_analysis = AnalysisResult(
        document_id=doc_id,
        analysis_type="ai_detection",
        score=result['ai_detection']['ai_probability'],
        details=json.dumps(result['ai_detection'])
    )
    db.add(ai_analysis)

    db.commit()

    return result