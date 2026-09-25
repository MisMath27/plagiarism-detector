import re
import hashlib
import numpy as np
from collections import Counter
from typing import List, Dict, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TextAnalyzer:
    """
    ГИБРИДНЫЙ АНАЛИЗАТОР
    Использует два алгоритма:
    1. Jaccard Index - для буквальных совпадений
    2. TF-IDF + Cosine Similarity - для семантических совпадений
    Итоговый результат - взвешенная комбинация обоих методов
    """

    def __init__(self):
        self.stop_words = {'и', 'в', 'на', 'с', 'по', 'к', 'у', 'а', 'но', 'за',
                           'из', 'о', 'об', 'при', 'от', 'до', 'для', 'без', 'через',
                           'над', 'под', 'про', 'как', 'что', 'это', 'был', 'была',
                           'было', 'были', 'есть', 'нет', 'то', 'же', 'его', 'ее'}

        self.ai_patterns = {
            'однако': 0.7, 'кроме': 0.6, 'также': 0.5,
            'следовательно': 0.8, 'таким образом': 0.7,
            'более того': 0.6, 'в частности': 0.5,
            'с другой стороны': 0.8, 'например': 0.4,
            'важно отметить': 0.7, 'следует отметить': 0.7,
            'необходимо учитывать': 0.8, 'в заключение': 0.5,
            'подводя итог': 0.6, 'резюмируя': 0.7
        }

        self.jaccard_weight = 0.4
        self.tfidf_weight = 0.6

        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='english',
            min_df=2,
            max_df=0.8,
            use_idf=True,
            smooth_idf=True,
            sublinear_tf=True,
            ngram_range=(1, 2)
        )

        self.is_fitted = False



    def preprocess_text(self, text: str) -> str:
        """Очищает текст от мусора"""
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^а-яёa-z\s]', '', text)
        return text.strip()

    def get_sentences(self, text: str) -> List[str]:
        """Разбивает текст на предложения"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 5]

    def get_words(self, text: str) -> List[str]:
        """Разбивает текст на слова"""
        return text.split()

    def remove_stopwords(self, words: List[str]) -> List[str]:
        """Удаляет стоп-слова"""
        return [w for w in words if w not in self.stop_words]



    def calculate_jaccard_similarity(self, text1: str, text2: str) -> float:
        """
        Вычисляет сходство по коэффициенту Жаккара
        |A ∩ B| / |A ∪ B|
        """
        t1 = self.preprocess_text(text1)
        t2 = self.preprocess_text(text2)

        if not t1 or not t2:
            return 0.0

        words1 = set(t1.split())
        words2 = set(t2.split())

        words1 = set(self.remove_stopwords(list(words1)))
        words2 = set(self.remove_stopwords(list(words2)))

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        jaccard = len(intersection) / len(union) if union else 0

        return min(jaccard * 100, 95)



def calculate_tfidf_similarity(self, text: str, corpus: List[str]) -> Tuple[float, List[Dict]]:
    """
    Использует предвычисленный TF-IDF индекс (если доступен).
    Иначе — fallback на старый метод.
    """
    from .indexer import get_index
    
    index = get_index()
    
    # Если индекс не загружен — пробуем загрузить
    if index.matrix is None:
        if not index.load():
            # Fallback: старый метод
            return self._calculate_tfidf_fallback(text, corpus)
    
    # Используем индекс
    try:
        scores, top_indices = index.query(text, top_k=10)
        
        if len(scores) == 0:
            return 0.0, []
        
        max_sim = float(np.max(scores)) if len(scores) > 0 else 0.0
        
        top_matches = []
        for idx in top_indices:
            score = float(scores[idx])
            if score > 0.05:
                meta = index.text_meta[idx] if idx < len(index.text_meta) else {}
                top_matches.append({
                    'index': idx,
                    'score': round(score * 100, 2),
                    'title': meta.get('title', 'Unknown'),
                    'source': meta.get('source', 'Unknown'),
                })
        
        return max_sim * 100, top_matches
    except Exception as e:
        print(f"Ошибка при использовании индекса: {e}")
        return self._calculate_tfidf_fallback(text, corpus)


def _calculate_tfidf_fallback(self, text: str, corpus: List[str]) -> Tuple[float, List[Dict]]:
    """Старый метод — считает TF-IDF на лету (для fallback)"""
    if not corpus:
        return 0.0, []
    
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    
    all_texts = [text] + corpus
    vectorizer = TfidfVectorizer(
        max_features=10000,
        min_df=2,
        max_df=0.8,
        sublinear_tf=True,
        ngram_range=(1, 2),
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(all_texts)
    except Exception as e:
        print(f"Ошибка TF-IDF: {e}")
        return 0.0, []
    
    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
    if similarities.size == 0:
        return 0.0, []
    
    max_sim = float(np.max(similarities))
    top_indices = np.argsort(similarities[0])[-3:][::-1]
    
    top_matches = []
    for idx in top_indices:
        score = float(similarities[0][idx])
        if score > 0.1:
            top_matches.append({
                'index': idx,
                'score': round(score * 100, 2)
            })
    
    return max_sim * 100, top_matches

    def detect_ai_content(self, text: str) -> Dict:
        """
        Обнаружение ИИ-текста с использованием множества факторов
        """
        clean_text = self.preprocess_text(text)
        words = self.get_words(clean_text)
        words_filtered = self.remove_stopwords(words)

        if not words:
            return {
                'ai_probability': 0,
                'confidence_level': 'Низкая',
                'suspicious_patterns': ['Текст слишком короткий'],
                'readability_score': 0,
                'avg_sentence_length': 0,
                'vocabulary_diversity': 0
            }

        total_words = len(words_filtered)
        unique_words = len(set(words_filtered))
        diversity_ratio = unique_words / total_words if total_words > 0 else 0
        diversity_score = min(100, diversity_ratio * 100 * 2)

        sentences = self.get_sentences(text)
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        else:
            avg_sentence_length = 0

        found_patterns = []
        pattern_score = 0

        for pattern, weight in self.ai_patterns.items():
            if pattern in clean_text:
                found_patterns.append(pattern)
                pattern_score += weight

        repetitive_phrases = []
        word_freq = Counter(words_filtered)
        for word, count in word_freq.most_common(5):
            if count > total_words * 0.1:
                repetitive_phrases.append(f"'{word}' повторяется {count} раз")

        ai_probability = 0

        if diversity_ratio < 0.3:
            ai_probability += 35
        elif diversity_ratio < 0.5:
            ai_probability += 20
        elif diversity_ratio < 0.7:
            ai_probability += 10

        if avg_sentence_length > 25:
            ai_probability += 20
        elif avg_sentence_length > 18:
            ai_probability += 10
        elif avg_sentence_length > 12:
            ai_probability += 5

        if pattern_score > 4:
            ai_probability += 25
        elif pattern_score > 2:
            ai_probability += 15
        elif pattern_score > 0:
            ai_probability += 5

        if len(repetitive_phrases) > 2:
            ai_probability += 10

        template_phrases = ['в данной', 'следует отметить', 'важно подчеркнуть', 'необходимо учитывать']
        for phrase in template_phrases:
            if phrase in clean_text:
                ai_probability += 5

        ai_probability = max(0, min(95, ai_probability))

        if ai_probability > 70:
            confidence = 'Высокая'
        elif ai_probability > 40:
            confidence = 'Средняя'
        else:
            confidence = 'Низкая'

        readability_score = self.calculate_readability(text)

        all_patterns = found_patterns[:4]
        if repetitive_phrases:
            all_patterns.extend(repetitive_phrases[:2])

        return {
            'ai_probability': round(ai_probability, 2),
            'confidence_level': confidence,
            'suspicious_patterns': all_patterns if all_patterns else ['Не обнаружено'],
            'readability_score': round(readability_score, 2),
            'avg_sentence_length': round(avg_sentence_length, 1),
            'vocabulary_diversity': round(diversity_ratio * 100, 2)
        }



    def calculate_readability(self, text: str) -> float:
        """
        Индекс читаемости Флеша для русского языка
        Чем выше, тем легче читать текст
        """
        clean_text = self.preprocess_text(text)
        words = self.get_words(clean_text)
        sentences = self.get_sentences(clean_text)

        if not sentences or not words:
            return 0

        word_count = len(words)
        sentence_count = len(sentences)

        vowels = 'аеёиоуыэюя'
        syllable_count = 0
        for word in words:
            syllable_count += sum(1 for char in word if char in vowels)

        if word_count == 0 or sentence_count == 0:
            return 0

        readability = 206.835 - (1.3 * (word_count / sentence_count)) - (60.1 * (syllable_count / word_count))

        return max(0, min(100, readability))



    def full_analysis(self, text: str, corpus: List[str]) -> Dict:
        """
        Выполняет полный анализ текста:
        1. Гибридный анализ на плагиат (Jaccard + TF-IDF)
        2. Обнаружение ИИ
        3. Статистика текста
        """
        plagiarism_result = self.calculate_hybrid_similarity(text, corpus)

        ai_result = self.detect_ai_content(text)

        clean_text = self.preprocess_text(text)
        words = self.get_words(clean_text)
        sentences = self.get_sentences(text)

        return {
            'plagiarism': plagiarism_result,
            'ai_detection': ai_result,
            'text_stats': {
                'word_count': len(words),
                'sentence_count': len(sentences),
                'character_count': len(text),
                'unique_words': len(set(words)),
                'avg_word_length': round(sum(len(w) for w in words) / len(words), 2) if words else 0
            },
            'summary': self.generate_summary(plagiarism_result, ai_result)
        }


    def generate_summary(self, plagiarism_result: Dict, ai_result: Dict) -> Dict:
        """Генерирует краткое резюме анализа"""
        plag_score = plagiarism_result.get('similarity_score', 0)
        if plag_score < 20:
            uniqueness_status = 'Высокая уникальность'
            uniqueness_color = 'green'
        elif plag_score < 50:
            uniqueness_status = 'Средняя уникальность'
            uniqueness_color = 'yellow'
        else:
            uniqueness_status = 'Низкая уникальность'
            uniqueness_color = 'red'

        ai_score = ai_result.get('ai_probability', 0)
        if ai_score < 30:
            ai_status = 'Написано человеком'
            ai_color = 'green'
        elif ai_score < 60:
            ai_status = 'Возможно ИИ'
            ai_color = 'yellow'
        else:
            ai_status = 'Высокая вероятность ИИ'
            ai_color = 'red'

        return {
            'uniqueness_status': uniqueness_status,
            'uniqueness_color': uniqueness_color,
            'ai_status': ai_status,
            'ai_color': ai_color,
            'overall_score': round((100 - plag_score + (100 - ai_score)) / 2, 2),
            'recommendation': self.get_recommendation(plag_score, ai_score)
        }

    def get_recommendation(self, plag_score: float, ai_score: float) -> str:
        """Дает рекомендацию на основе анализа"""
        if plag_score < 20 and ai_score < 30:
            return "Текст оригинальный и написан человеком. Отлично!"
        elif plag_score < 20 and ai_score >= 60:
            return "Текст оригинальный, но похож на ИИ. Проверьте источники."
        elif plag_score >= 50 and ai_score < 30:
            return "Текст имеет совпадения, но написан человеком. Проверьте источники."
        elif plag_score >= 50 and ai_score >= 60:
            return "Высокая вероятность плагиата и ИИ. Рекомендуется проверить."
        else:
            return "ℹРекомендуется дополнительная проверка."
