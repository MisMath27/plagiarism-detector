"""
Строит TF-IDF индекс из эталонных текстов в базе.
Запускать после добавления новых текстов в базу.
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, ReferenceText
from app.indexer import TfidfIndex


def main():
    print("=" * 70)
    print("🔨 ПОСТРОЕНИЕ TF-IDF ИНДЕКСА")
    print("=" * 70)
    
    db = SessionLocal()
    
    # Загружаем все активные эталонные тексты
    refs = db.query(ReferenceText).filter(
        ReferenceText.is_active == True
    ).all()
    
    print(f"\n📚 Найдено эталонных текстов: {len(refs)}")
    
    if not refs:
        print("⚠️ База пуста, нечего индексировать")
        db.close()
        return
    
    texts = [r.content for r in refs]
    text_ids = [r.id for r in refs]
    meta = [{'title': r.title, 'source': r.source} for r in refs]
    
    # Считаем общий объём
    total_chars = sum(len(t) for t in texts)
    print(f"📊 Общий объём: {total_chars:,} символов")
    print(f"📊 Средний размер: {total_chars // len(texts):,} символов")
    
    # Строим индекс
    index = TfidfIndex()
    index.build(texts, text_ids, meta)
    
    # Сохраняем
    index.save()
    
    print(f"\n✅ Готово! Индекс сохранён, теперь анализ будет мгновенным.")
    
    db.close()


if __name__ == "__main__":
    main()
