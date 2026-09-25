"""
Модуль индексации эталонных текстов.
Предвычисляет TF-IDF матрицу и сохраняет её в файл,
чтобы не считать заново на каждый запрос.
"""
import os
import pickle
import hashlib
from typing import List, Tuple, Optional
from datetime import datetime

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "tfidf_index.pkl")


class TfidfIndex:
    """
    Предвычисленный TF-IDF индекс эталонных текстов.
    
    Хранит:
    - vectorizer: обученный TfidfVectorizer
    - matrix: TF-IDF матрица (n_texts × n_features)
    - text_ids: список id текстов в порядке строк матрицы
    - text_meta: метаданные (title, source) для каждого текста
    """
    
    def __init__(self):
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.matrix = None
        self.text_ids: List[int] = []
        self.text_meta: List[dict] = []
        self.built_at: Optional[str] = None
        self.n_texts: int = 0
    
    def build(self, texts: List[str], text_ids: List[int], meta: List[dict]):
        """Строит индекс из списка текстов"""
        if not texts:
            print("⚠️ Нет текстов для индексации")
            return
        
        print(f"🔨 Построение TF-IDF индекса для {len(texts)} текстов...")
        start = datetime.now()
        
        # Векторизатор с настройками под многоязычные тексты
        self.vectorizer = TfidfVectorizer(
            analyzer='word',
            ngram_range=(1, 2),      # униграммы + биграммы
            min_df=2,                 # игнорировать слова, встречающиеся < 2 раз
            max_df=0.85,              # игнорировать слова, встречающиеся > 85% текстов
            sublinear_tf=True,        # логарифмическое масштабирование TF
            use_idf=True,
            smooth_idf=True,
            max_features=50000,       # ограничение размера словаря
            strip_accents=None,
            lowercase=True,
        )
        
        self.matrix = self.vectorizer.fit_transform(texts)
        self.text_ids = list(text_ids)
        self.text_meta = list(meta)
        self.n_texts = len(texts)
        self.built_at = datetime.now().isoformat()
        
        elapsed = (datetime.now() - start).total_seconds()
        print(f"✅ Индекс построен за {elapsed:.1f} сек. "
              f"Размер матрицы: {self.matrix.shape}")
    
    def save(self, path: str = INDEX_PATH):
        """Сохраняет индекс в файл"""
        with open(path, 'wb') as f:
            pickle.dump({
                'vectorizer': self.vectorizer,
                'matrix': self.matrix,
                'text_ids': self.text_ids,
                'text_meta': self.text_meta,
                'built_at': self.built_at,
                'n_texts': self.n_texts,
            }, f)
        print(f"💾 Индекс сохранён: {path}")
    
    def load(self, path: str = INDEX_PATH) -> bool:
        """Загружает индекс из файла. Возвращает True, если успешно."""
        if not os.path.exists(path):
            return False
        
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            self.vectorizer = data['vectorizer']
            self.matrix = data['matrix']
            self.text_ids = data['text_ids']
            self.text_meta = data['text_meta']
            self.built_at = data.get('built_at')
            self.n_texts = data.get('n_texts', 0)
            
            print(f"📂 Индекс загружен: {self.n_texts} текстов, "
                  f"построен {self.built_at}")
            return True
        except Exception as e:
            print(f"⚠️ Ошибка загрузки индекса: {e}")
            return False
    
    def is_stale(self, current_count: int, threshold: int = 10) -> bool:
        """Проверяет, устарел ли индекс (изменилось ли число текстов)"""
        return abs(current_count - self.n_texts) > threshold
    
    def query(self, text: str, top_k: int = 20) -> Tuple[np.ndarray, List[int]]:
        """
        Ищет top_k наиболее похожих текстов.
        Возвращает: (scores, indices) — массивы оценок и индексов.
        """
        if self.vectorizer is None or self.matrix is None:
            return np.array([]), []
        
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Трансформируем новый текст тем же векторизатором
        query_vec = self.vectorizer.transform([text])
        
        # Считаем косинусное сходство со всеми текстами
        scores = cosine_similarity(query_vec, self.matrix)[0]
        
        # Сортируем по убыванию
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        return scores, top_indices.tolist()


# Глобальный экземпляр индекса (singleton)
_index_instance: Optional[TfidfIndex] = None


def get_index() -> TfidfIndex:
    """Возвращает глобальный экземпляр индекса"""
    global _index_instance
    if _index_instance is None:
        _index_instance = TfidfIndex()
    return _index_instance
