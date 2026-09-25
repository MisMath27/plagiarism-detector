"""
Массовая загрузка текстов в базу данных.
Источники: Project Gutenberg, Wikipedia, lib.ru
"""
from app.database import SessionLocal, ReferenceText
import os
import sys
import hashlib
import requests
import time
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

REQUEST_DELAY = 1.0
MAX_TEXT_LENGTH = 15000
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


class BulkLoader:
    def __init__(self):
        self.db = SessionLocal()
        self.total_added = 0
        self.total_skipped = 0
        self.seen_hashes = set()

    def save(self):
        try:
            self.db.commit()
        except Exception as e:
            print(f"⚠️ Ошибка при сохранении: {e}")
            self.db.rollback()
        # Сохраняем по одной записи
            print("Пробую сохранить по одной...")
            saved = 0
            for obj in list(self.db.new):
                try:
                    self.db.add(obj)
                    self.db.commit()
                    saved += 1
                except Exception:
                    self.db.rollback()
            print(f"Сохранено по одной: {saved}")

        print(f"\n✅ Всего добавлено: {self.total_added}")
        print(f"⏭️ Пропущено (дубликаты): {self.total_skipped}")
        self.db.close()

    def add_text(self, title, source, content):
        if not content or len(content) < 200:
            return False
        if len(content) > MAX_TEXT_LENGTH:
            content = content[:MAX_TEXT_LENGTH]
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        if content_hash in self.seen_hashes:
            self.total_skipped += 1
            return False
        self.seen_hashes.add(content_hash)

        existing = self.db.query(ReferenceText).filter(
            ReferenceText.content_hash == content_hash
        ).first()
        if existing:
            self.total_skipped += 1
            return False
        ref = ReferenceText(
            title=title[:200],
            source=source[:200],
            content=content.strip(),
            content_hash=content_hash
        )
        self.db.add(ref)
        self.total_added += 1
        if self.total_added % 10 == 0:
            self.db.commit()
            print(f"  💾 Сохранено {self.total_added} текстов...")
        return True

    def save(self):
        self.db.commit()
        print(f"\n✅ Всего добавлено: {self.total_added}")
        print(f"⏭️ Пропущено (дубликаты): {self.total_skipped}")
        self.db.close()


def load_gutenberg(loader, max_books=20):
    """Загружает книги с Project Gutenberg через Gutendex API"""
    print(f"\n📚 Project Gutenberg: загрузка до {max_books} книг...")

    base_url = "https://gutendex.com/books"
    loaded = 0
    next_url = base_url
    params = {"languages": "en"}

    while next_url and loaded < max_books:
        try:
            response = requests.get(
                next_url,
                params=params if next_url == base_url else None,
                timeout=30,
                headers={"User-Agent": USER_AGENT}
            )
            if response.status_code != 200:
                print(f"  ⚠️ Ошибка {response.status_code}")
                break

            data = response.json()
            books = data.get("results", [])

            for book in books:
                if loaded >= max_books:
                    break

                book_id = book.get("id")
                title = book.get("title", "Unknown")
                authors = book.get("authors", [])
                author_name = authors[0].get(
                    "name", "Unknown") if authors else "Unknown"

                formats = book.get("formats", {})
                txt_url = formats.get("text/plain; charset=utf-8") or \
                    formats.get("text/plain; charset=us-ascii")

                if not txt_url:
                    continue

                try:
                    txt_response = requests.get(
                        txt_url, timeout=30, headers={
                            "User-Agent": USER_AGENT})
                    if txt_response.status_code == 200:
                        text = txt_response.text
                        text = re.sub(r'\r\n', '\n', text)
                        text = re.sub(r'\n\s*\n', '\n\n', text)

                        start = text.find("*** START OF")
                        if start != -1:
                            text = text[start:]
                        end = text.find("*** END OF")
                        if end != -1:
                            text = text[:end]

                        if len(text) > 500:
                            loader.add_text(
                                title=f"{title} — {author_name}",
                                source=f"Project Gutenberg ({book_id})",
                                content=text
                            )
                            loaded += 1
                            print(f"  📖 {loaded}/{max_books}: {title[:50]}")
                except Exception:
                    continue

                time.sleep(REQUEST_DELAY)

            next_url = data.get("next")

        except Exception as e:
            print(f"  ⚠️ Ошибка: {e}")
            break

    print(f"  ✅ Загружено {loaded} книг")


def load_wikipedia_ru(loader, max_articles=500):
    """Загружает статьи из русской Википедии"""
    print(f"\n🇷🇺 Wikipedia RU: загрузка до {max_articles} статей...")
    
    try:
        import wikipediaapi
    except ImportError:
        print("  ⚠️ Установите: pip install wikipedia-api")
        return
    
    wiki = wikipediaapi.Wikipedia(
        user_agent='PlagiarismDetector/2.0 (educational project)',
        language='ru',
        extract_format=wikipediaapi.ExtractFormat.WIKI
    )
    
    # Большой список русских тем по разным областям
    topics = [
        # Наука и технологии
        "Искусственный интеллект", "Машинное обучение", "Нейронная сеть",
        "Глубокое обучение", "Компьютерная наука", "Квантовые вычисления",
        "Криптография", "Блокчейн", "Интернет вещей", "Облачные вычисления",
        "Большие данные", "Анализ данных", "Обработка естественного языка",
        "Компьютерное зрение", "Робототехника", "Автоматизация",
        "Программная инженерия", "Алгоритм", "Структура данных",
        "База данных", "Операционная система", "Компьютерная сеть",
        # Физика и математика
        "Физика", "Квантовая механика", "Теория относительности",
        "Термодинамика", "Электромагнетизм", "Математика",
        "Математический анализ", "Линейная алгебра", "Статистика",
        "Теория вероятностей", "Геометрия", "Теория чисел",
        "Дифференциальное уравнение", "Топология", "Алгебра",
        # Биология и медицина
        "Биология", "Генетика", "ДНК", "Эволюция", "Медицина",
        "Нейробиология", "Иммунология", "Экология", "Микробиология",
        "Биохимия", "Анатомия", "Физиология", "Вирусология",
        "Бактериология", "Ботаника", "Зоология", "Палеонтология",
        # Экономика и общество
        "Экономика", "Макроэкономика", "Микроэкономика", "Финансы",
        "Маркетинг", "Менеджмент", "Психология", "Социология",
        "Философия", "История", "Политология", "Юриспруденция",
        "Социальная психология", "Клиническая психология",
        "Экономическая теория", "Международные отношения",
        # Искусство и культура
        "Литература", "Музыка", "Живопись", "Архитектура",
        "Кино", "Театр", "Фотография", "Танец", "Скульптура",
        "Русская литература", "Зарубежная литература",
        "История искусств", "Культурология", "Лингвистика",
        "Языкознание", "Филология", "Риторика", "Поэзия",
        # География и история
        "География", "Геология", "Метеорология", "Климатология",
        "Океанология", "Картография", "Геодезия", "Астрономия",
        "Космонавтика", "Планета", "Звезда", "Галактика",
        "История России", "Всемирная история", "Древний мир",
        "Средневековье", "Новое время", "Новейшая история",
        "Археология", "Этнография", "Антропология",
        # Техника и промышленность
        "Машиностроение", "Электротехника", "Энергетика",
        "Металлургия", "Химическая технология", "Строительство",
        "Транспорт", "Авиация", "Судостроение", "Автомобиль",
        "Железная дорога", "Мостостроение", "Тоннель",
        "Материаловедение", "Нанотехнология", "Биотехнология",
        # Медицина и здоровье
        "Здоровье", "Питание", "Спорт", "Физкультура",
        "Психиатрия", "Хирургия", "Терапия", "Педиатрия",
        "Стоматология", "Фармакология", "Эпидемиология",
        "Онкология", "Кардиология", "Неврология", "Эндокринология",
        # Образование и наука
        "Образование", "Педагогика", "Наука", "Исследование",
        "Методология", "Эксперимент", "Теория", "Гипотеза",
        "Научная статья", "Диссертация", "Конференция", "Симпозиум",
    ]
    
    loaded = 0
    for i, topic in enumerate(topics):
        if loaded >= max_articles:
            break
        
        try:
            page = wiki.page(topic)
            if page.exists():
                content = page.text
                if len(content) > 1000:
                    loader.add_text(
                        title=f"Википедия: {topic}",
                        source="Wikipedia RU",
                        content=content
                    )
                    loaded += 1
                    if loaded % 20 == 0:
                        print(f"  📄 {loaded}/{max_articles}: {topic}")
            
            # Небольшая задержка, чтобы не перегружать API
            time.sleep(0.2)
            
        except Exception as e:
            # Пропускаем ошибки, продолжаем
            continue
    
    print(f"  ✅ Загружено {loaded} статей из Википедии RU")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Массовая загрузка текстов в базу")
    parser.add_argument(
        "--source",
        choices=["all", "gutenberg", "libru", "wikipedia_ru"],
        default="all",
        help="Какой источник загружать"
    )
    parser.add_argument("--gutenberg", type=int, default=20, help="Книг с Project Gutenberg")
    parser.add_argument("--libru", type=int, default=12, help="Текстов с lib.ru (отключён)")
    parser.add_argument("--wikipedia_ru", type=int, default=500, help="Статей из Википедии RU")

    args = parser.parse_args()

    print("=" * 70)
    print("📚 МАССОВАЯ ЗАГРУЗКА ТЕКСТОВ В БАЗУ")
    print("=" * 70)

    loader = BulkLoader()

    # --- lib.ru временно отключён (отдаёт HTML вместо текста) ---
    # if args.source in ["all", "libru"]:
    #     load_libru(loader, max_texts=args.libru)

    # --- Project Gutenberg ---
    if args.source in ["all", "gutenberg"]:
        load_gutenberg(loader, max_books=args.gutenberg)

    # --- Wikipedia RU ---
    if args.source in ["all", "wikipedia_ru"]:
        load_wikipedia_ru(loader, max_articles=args.wikipedia_ru)

    loader.save()

    # --- Итоговая статистика ---
    print("\n" + "=" * 70)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 70)

    from collections import Counter
    db = SessionLocal()
    all_texts = db.query(ReferenceText.source).all()
    counts = Counter(t[0] for t in all_texts)
    for source, count in counts.most_common():
        print(f"  {source[:55]}: {count}")
    print(f"\n📚 ВСЕГО В БАЗЕ: {sum(counts.values())} текстов")
    db.close()

if __name__ == "__main__":
    main()
