# backend/download_texts.py
"""
Скрипт для скачивания разнообразных текстов в базу данных
Без категорий - просто большая коллекция текстов для сравнения
"""

import os
import sys
import hashlib
import requests
import time
import re
from datetime import datetime
from typing import List, Optional

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.database import SessionLocal, ReferenceText

# ============================================================
# НАСТРОЙКИ
# ============================================================

REQUEST_DELAY = 1.5  # Задержка между запросами
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
MAX_TEXT_LENGTH = 8000  # Максимальная длина текста для сохранения


# ============================================================
# КЛАСС ДЛЯ ЗАГРУЗКИ
# ============================================================

class TextDownloader:
    def __init__(self):
        self.db = SessionLocal()
        self.total_added = 0
        self.total_skipped = 0

    def add_text(self, title: str, source: str, content: str) -> bool:
        """Добавляет текст в базу без категорий"""
        if not content or len(content) < 100:
            return False

        # Обрезаем текст если слишком длинный
        if len(content) > MAX_TEXT_LENGTH:
            content = content[:MAX_TEXT_LENGTH]

        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        # Проверяем дубликаты
        existing = self.db.query(ReferenceText).filter(
            ReferenceText.content_hash == content_hash
        ).first()

        if existing:
            self.total_skipped += 1
            print(f"⏭️ Пропущен (дубликат): {title[:40]}...")
            return False

        # Создаем запись без категории
        ref = ReferenceText(
            title=title[:200],
            source=source[:200],
            content=content.strip(),
            content_hash=content_hash
        )
        self.db.add(ref)
        self.total_added += 1
        print(f"✅ Добавлен: {title[:50]}... ({len(content)} символов)")
        return True

    def save(self):
        """Сохраняет изменения в базу"""
        self.db.commit()
        print("\n" + "=" * 60)
        print(f"📊 ИТОГО ДОБАВЛЕНО: {self.total_added} текстов")
        print(f"⏭️ ПРОПУЩЕНО (дубликаты): {self.total_skipped}")
        print("=" * 60)
        self.db.close()


# ============================================================
# 1. КЛАССИЧЕСКАЯ ЛИТЕРАТУРА (Project Gutenberg)
# ============================================================

def download_classics(downloader: TextDownloader, limit: int = 8):
    """Скачивает классические книги"""
    print("\n📚 Загрузка классической литературы...")

    books = [
        {"id": "1342", "title": "Pride and Prejudice - Jane Austen"},
        {"id": "11", "title": "Alice in Wonderland - Lewis Carroll"},
        {"id": "74", "title": "Huckleberry Finn - Mark Twain"},
        {"id": "84", "title": "Frankenstein - Mary Shelley"},
        {"id": "1661", "title": "The Picture of Dorian Gray - Oscar Wilde"},
        {"id": "345", "title": "Dracula - Bram Stoker"},
        {"id": "98", "title": "A Tale of Two Cities - Charles Dickens"},
        {"id": "2701", "title": "Moby Dick - Herman Melville"},
        {"id": "1400", "title": "Great Expectations - Charles Dickens"},
        {"id": "163", "title": "War and Peace - Leo Tolstoy"},
    ]

    for book in books[:limit]:
        try:
            book_id = book["id"]
            title = book["title"]

            # Пробуем разные форматы URL
            urls = [
                f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
                f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
                f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
            ]

            text = None
            for url in urls:
                try:
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        text = response.text
                        break
                except:
                    continue

            if text:
                # Очищаем текст
                text = re.sub(r'\r\n', '\n', text)
                text = re.sub(r'\n\s*\n', '\n\n', text)

                # Ищем начало книги
                start_markers = ["*** START OF", "***START OF", "Produced by", "CHAPTER"]
                start = -1
                for marker in start_markers:
                    pos = text.find(marker)
                    if pos != -1:
                        start = pos
                        break

                if start != -1:
                    text = text[start:]
                    text = text[:MAX_TEXT_LENGTH]

                downloader.add_text(
                    title=title,
                    source=f"Project Gutenberg - {book_id}",
                    content=text
                )
            else:
                print(f"⚠️ Не удалось скачать: {title}")

            time.sleep(REQUEST_DELAY)

        except Exception as e:
            print(f"⚠️ Ошибка: {title} - {e}")


# ============================================================
# 2. НАУЧНЫЕ СТАТЬИ (arXiv)
# ============================================================

def download_arxiv(downloader: TextDownloader, limit: int = 5):
    """Скачивает научные статьи из arXiv"""
    print("\n🔬 Загрузка научных статей из arXiv...")

    topics = ["cs.AI", "cs.LG", "physics", "q-bio", "math"]

    for topic in topics:
        try:
            url = f"http://export.arxiv.org/api/query?search_query=cat:{topic}&max_results={limit}&sortBy=submittedDate"
            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                ns = {"atom": "http://www.w3.org/2005/Atom"}

                for entry in root.findall("atom:entry", ns):
                    title_elem = entry.find("atom:title", ns)
                    abstract = entry.find("atom:summary", ns)

                    if abstract is not None and abstract.text:
                        title = title_elem.text[:80] if title_elem is not None else f"arXiv {topic}"
                        content = abstract.text

                        if len(content) > 200:
                            downloader.add_text(
                                title=f"arXiv: {title}",
                                source=f"arXiv ({topic})",
                                content=content
                            )
            time.sleep(REQUEST_DELAY)

        except Exception as e:
            print(f"⚠️ Ошибка arXiv ({topic}): {e}")


# ============================================================
# 3. ВИКИПЕДИЯ
# ============================================================

def download_wikipedia(downloader: TextDownloader):
    """Скачивает статьи из Википедии"""
    print("\n🌍 Загрузка статей из Wikipedia...")

    topics = [
        "Artificial intelligence", "Machine learning", "Data science",
        "Computer science", "Physics", "Chemistry", "Biology",
        "Medicine", "Economics", "Philosophy", "Psychology",
        "Climate change", "Space exploration", "Genetics",
        "Evolution", "Neural network", "Cryptography",
        "Quantum mechanics", "Theory of relativity"
    ]

    try:
        import wikipediaapi
        wiki = wikipediaapi.Wikipedia(
            user_agent='TextDownloader/1.0',
            language='en',
            extract_format=wikipediaapi.ExtractFormat.WIKI
        )

        for topic in topics:
            try:
                page = wiki.page(topic)
                if page.exists():
                    content = page.text[:MAX_TEXT_LENGTH]
                    if len(content) > 500:
                        downloader.add_text(
                            title=f"Wikipedia: {topic}",
                            source=f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}",
                            content=content
                        )
                    time.sleep(REQUEST_DELAY)
            except Exception as e:
                print(f"⚠️ Ошибка {topic}: {e}")

    except ImportError:
        print("⚠️ Установите: pip install wikipedia-api")


# ============================================================
# 4. НОВОСТИ (RSS)
# ============================================================

def download_news(downloader: TextDownloader, limit: int = 3):
    """Скачивает новостные статьи"""
    print("\n📰 Загрузка новостей...")

    feeds = [
        ("http://feeds.bbci.co.uk/news/rss.xml", "BBC News"),
        ("https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml", "NY Times"),
        ("https://feeds.npr.org/1001/rss.xml", "NPR"),
    ]

    import xml.etree.ElementTree as ET

    for feed_url, source in feeds:
        try:
            response = requests.get(feed_url, timeout=30)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                items = root.findall(".//item")

                for item in items[:limit]:
                    title = item.find("title")
                    description = item.find("description")
                    link = item.find("link")

                    if description is not None and description.text:
                        content = description.text
                        # Удаляем HTML теги
                        content = re.sub(r'<[^>]+>', '', content)
                        content = re.sub(r'&[a-z]+;', ' ', content)

                        if len(content) > 200:
                            title_text = title.text if title is not None else "News"
                            downloader.add_text(
                                title=f"{source}: {title_text[:60]}",
                                source=f"{source} - News",
                                content=content
                            )
            time.sleep(REQUEST_DELAY)

        except Exception as e:
            print(f"⚠️ Ошибка новостей {source}: {e}")


# ============================================================
# 5. РУССКАЯ КЛАССИКА (ОТРЫВКИ)
# ============================================================

def download_russian_classics(downloader: TextDownloader):
    """Добавляет отрывки русской классики"""
    print("\n📖 Загрузка русской классики...")

    russian_texts = [
        {
            "title": "Война и мир - Лев Толстой",
            "source": "Русская классика",
            "content": """
Война и мир — роман-эпопея Льва Николаевича Толстого, 
описывающий русское общество в эпоху войн против Наполеона.
В центре повествования — судьбы нескольких дворянских семей, 
их взаимоотношения, любовь, поиски смысла жизни и философские размышления 
о роли личности в истории. Роман охватывает период с 1805 по 1812 год 
и включает масштабные батальные сцены и глубокий психологизм.
"""
        },
        {
            "title": "Преступление и наказание - Федор Достоевский",
            "source": "Русская классика",
            "content": """
Преступление и наказание — социально-психологический роман 
Фёдора Михайловича Достоевского. Главный герой, Родион Раскольников, 
разрабатывает теорию о делении людей на обыкновенных и необыкновенных, 
решаясь на убийство. Роман исследует темы вины, искупления, 
нравственных границ и поиска смысла существования.
"""
        },
        {
            "title": "Мастер и Маргарита - Михаил Булгаков",
            "source": "Русская классика",
            "content": """
Мастер и Маргарита — роман Михаила Афанасьевича Булгакова, 
в котором переплетаются сатирическая повесть о Москве 1930-х годов, 
евангельский сюжет о Понтии Пилате и любовная линия Мастера и Маргариты. 
Воланд со своей свитой посещает столицу, обнажая пороки советского общества.
"""
        },
        {
            "title": "Евгений Онегин - Александр Пушкин",
            "source": "Русская классика",
            "content": """
Евгений Онегин — роман в стихах Александра Сергеевича Пушкина, 
написанный в 1823-1831 годах. Главный герой — молодой дворянин, 
разочарованный в жизни, который уезжает в деревню, где знакомится 
с Татьяной Лариной. Роман считается энциклопедией русской жизни 
и одним из важнейших произведений русской литературы.
"""
        },
        {
            "title": "Мертвые души - Николай Гоголь",
            "source": "Русская классика",
            "content": """
Мертвые души — поэма Николая Васильевича Гоголя, 
опубликованная в 1842 году. Главный герой Чичиков путешествует по России, 
скупая мертвые души крестьян у помещиков. Сатирическое изображение 
помещиков и чиновников, яркие характеры и глубокий психологизм 
делают произведение классикой русской литературы.
"""
        }
    ]

    for text in russian_texts:
        downloader.add_text(
            title=text["title"],
            source=text["source"],
            content=text["content"]
        )
        time.sleep(0.5)


# ============================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================

def main():
    print("=" * 60)
    print("📚 СКАЧИВАНИЕ ТЕКСТОВ В БАЗУ")
    print("=" * 60)
    print("ℹ️  Будут скачаны тексты из разных источников")
    print("")

    downloader = TextDownloader()

    # 1. Русская классика (быстро, локально)
    download_russian_classics(downloader)

    # 2. Классическая литература (Gutenberg)
    download_classics(downloader, limit=5)

    # 3. Научные статьи (arXiv)
    download_arxiv(downloader, limit=3)

    # 4. Википедия
    download_wikipedia(downloader)

    # 5. Новости
    download_news(downloader, limit=2)

    # Сохраняем все в базу
    downloader.save()

    print("\n🎉 ЗАВЕРШЕНО!")
    print(f"📊 Всего в базе: {downloader.total_added} новых текстов")


if __name__ == "__main__":
    main()