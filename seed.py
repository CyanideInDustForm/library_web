from __future__ import annotations

import os
import sqlite3
from datetime import date, timedelta, datetime
import random

from werkzeug.security import generate_password_hash

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
SCHEMA_PATH = os.path.join(ROOT, "schema.sql")
DATABASES = {
    "main": ("library_sqlite.db", 10),     # (имя файла, «соль» генерации данных)
    "extra": ("library_postgres.db", 20),
}

STATUSES = [
    (1, "выдано"),
    (2, "возвращено"),
    (3, "просрочка"),
]

# --- ИМЕНА ---
MALE_NAMES = [
    "Иван Иванов", "Алексей Смирнов", "Дмитрий Кузнецов", "Сергей Попов",
    "Андрей Васильев", "Николай Соколов", "Павел Михайлов", "Евгений Фёдоров",
    "Владимир Никитин", "Константин Орлов", "Максим Захаров", "Юрий Белов", "Олег Тарасов",
    "Роман Гусев", "Виктор Крылов", "Игорь Лебедев", "Артур Егоров", "Георгий Макаров", "Степан Дорофеев"
]

FEMALE_NAMES = [
    "Анна Иванова", "Мария Смирнова", "Елена Кузнецова", "Ольга Попова",
    "Татьяна Морозова", "Наталья Волкова", "Ирина Павлова",
    "Светлана Алексеевна", "Дарья Романова", "Ксения Орлова", "Юлия Николаева"
]

ALL_NAMES = MALE_NAMES + FEMALE_NAMES
random.shuffle(ALL_NAMES)  # перемешиваем один раз для уникальной раздачи

LIBRARIAN_NAMES = [
    "Валерий Жуков", "Станислав Киселёв", "Григорий Исаев", "Леонид Зайцев",
    "Руслан Сафонов", "Вячеслав Корнилов", "Аркадий Фролов", "Борис Громов",
    "Людмила Сергеева", "Вера Андреева"
]

# --- КНИГИ ---
BOOKS = [
    ("Война и мир", "Лев Толстой"),
    ("Преступление и наказание", "Фёдор Достоевский"),
    ("Мастер и Маргарита", "Михаил Булгаков"),
    ("Анна Каренина", "Лев Толстой"),
    ("Идиот роман", "Фёдор Достоевский"),
    ("Отцы и дети", "Иван Тургенев"),
    ("Евгений Онегин", "Александр Пушкин"),
    ("Герой нашего времени", "Михаил Лермонтов"),
    ("Доктор Живаго", "Борис Пастернак"),
    ("Тихий Дон", "Михаил Шолохов"),
    ("Роман 1984", "Джордж Оруэлл"),
    ("Скотный двор", "Джордж Оруэлл"),
    ("Улисс роман", "Джеймс Джойс"),
    ("Великий Гэтсби", "Фрэнсис Скотт Фицджеральд"),
    ("Над пропастью во ржи", "Джером Сэлинджер"),
    ("451 градус по Фаренгейту", "Рэй Брэдбери"),
    ("О дивный новый мир", "Олдос Хаксли"),
    ("Моби Дик роман", "Герман Мелвилл"),
    ("Гамлет трагедия", "Уильям Шекспир"),
    ("Король Лир трагедия", "Уильям Шекспир"),
    ("Фауст поэма", "Иоганн Гёте"),
    ("Дон Кихот роман", "Мигель де Сервантес"),
    ("Сто лет одиночества", "Габриэль Гарсиа Маркес"),
    ("Имя розы", "Умберто Эко"),
    ("Парфюмер история", "Патрик Зюскинд"),
    ("Алхимик роман", "Пауло Коэльо"),
    ("Шантарам роман", "Грегори Дэвид Робертс"),
    ("Атлант расправил плечи", "Айн Рэнд"),
    ("Игра престолов книга", "Джордж Мартин"),
    ("Гарри Поттер философский камень", "Джоан Роулинг"),
]

# --- НОВОСТИ ---
NEWS = [
    ("Неделя книгодарения", "С 12 по 18 октября в библиотеке проходит акция «Неделя книгодарения»: каждый читатель может внести в фонд библиотеки книгу в хорошем состоянии и получить читательский сувенир."),
    ("Новый читальный зал открыт", "Мы открыли обновлённый читальный зал на втором этаже. Теперь там 40 посадочных мест, бесплатный Wi-Fi и удлинённое время работы — до 21:00 по будням."),
    ("Литературный вечер с поэтами", "Приглашаем на традиционный литературный вечер: поэты города прочитают новые стихи, а библиотекари подготовят выставку редких изданий. Вход свободный."),
    ("Обновление электронного каталога", "В электронный каталог добавлено более 200 новых изданий за текущий год. Теперь искать книги можно по ключевым словам через поисковую строку сайта."),
    ("Клуб читателей объявляет набор", "Книжный клуб библиотеки открывает набор новых участников. Обсуждаем одну книгу в месяц, встречи проходят каждую среду в 18:00."),
    ("Режим работы в праздники", "Обратите внимание: в праздничные дни библиотека работает с 10:00 до 16:00, абонемент закрывается на час раньше."),
    ("Конкурс детского рисунка", "Стартовал ежегодный конкурс детского рисунка «Моя любимая книга». Работы принимаются до конца месяца на первом этаже библиотеки."),
]

# --- ПОЛЬЗОВАТЕЛИ САЙТА (пароль у всех тестовых: 12345) ---
SEED_USERS = [
    ("nastya", "Анастасия Иванова", "nastya@mail.ru"),
    ("reader", "Пётр Сидоров", "petr@mail.ru"),
    ("bookworm", "Ольга Книжкина", None),
]

# --- МЕРОПРИЯТИЯ --- (title, description, day_offset от сегодня, час, минуты, место, мест)
SEED_EVENTS = [
    ("Литературный вечер с поэтами", "Поэты города читают новые стихи, библиотекари готовят выставку редких изданий. Вход свободный, по записи.", 5, 18, 30, "Читальный зал, 2 этаж", 40),
    ("Встреча книжного клуба", "Обсуждаем роман «Мастер и Маргарита». Просим прочитать первые 15 глав.", 12, 18, 0, "Клубная комната", 15),
    ("Детский час: сказки на ночь", "Чтение вслух с демонстрацией кукольного театра для малышей 4–7 лет.", 19, 11, 0, "Детский отдел", 20),
    ("Лекция «История книгопечатания»", "От Гутенберга до цифровых библиотек: как менялась книга за 500 лет.", 26, 17, 0, "Конференц-зал", 50),
    ("Мастер-класс по скорочтению", "Практическое занятие: техники быстрого чтения и запоминания текста.", 9, 16, 0, "Читальный зал, 2 этаж", 25),
    ("Выставка редких изданий", "Открытие выставки книг XIX века из фонда библиотеки. Экскурсии каждый час.", 15, 12, 0, "Выставочный зал", 60),
]

# --- ОТЗЫВЫ (гостевая книга) ---
SEED_REVIEWS = [
    (2, "Отличная библиотека! Всегда находят нужную книгу, а новый читальный зал — просто мечта."),
    (3, "Хожу в книжный клуб каждую среду. Атмосфера уютная, обсуждения живые, рекомендую всем."),
    (1, "Очень удобно записываться на мероприятия через сайт. Всё понятно, пять минут — и место забронировано."),
    (2, "Детский отдел — спасение для родителей. Сын теперь сам просится на «сказки на ночь»."),
    (3, "Большой выбор классики, вежливые библиотекари. Небольшой минус — очередь на абонементе вечером."),
]


def read_schema() -> str:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return f.read()


def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)


def random_phone():
    return "+7" + "".join(str(random.randint(0, 9)) for _ in range(10))


def make_reader(i: int, salt: int):
    card = f"RC{salt:02d}-{i:04d}"
    full_name = ALL_NAMES[i - 1]  # гарантированно уникально
    phone = None if i % 4 == 0 else random_phone()
    email = None if i % 5 == 0 else f"r{i:02d}@mail.ru"
    return (card, full_name, phone, email)


def make_book(i: int, salt: int):
    inv = f"INV{salt:02d}-{i:04d}"
    title, author = BOOKS[i - 1]
    year = random.randint(1950, 2024)
    isbn = "".join(str(random.randint(0, 9)) for _ in range(13))
    return (inv, title, author, year, isbn)


def make_librarian(i: int, salt: int):
    emp = f"EMP{salt:02d}{i:02d}"
    full_name = LIBRARIAN_NAMES[i - 1]  # уникальные ФИО для библиотекарей
    phone = None if i % 3 == 0 else random_phone()
    return (emp, full_name, phone)


def random_date_between(start: date, end: date) -> date:
    days = (end - start).days
    return start + timedelta(days=random.randint(0, max(days, 0)))




def seed_db(filename: str, salt: int):
    """Создаёт (пересоздаёт) файл БД и наполняет его данными."""
    db_path = os.path.join(DATA_DIR, filename)

    if os.path.exists(db_path):
        os.remove(db_path)

    schema = read_schema()
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")

    con.executescript(schema)

    con.executemany("INSERT INTO statuses(id, title) VALUES (?, ?);", STATUSES)

    for i in range(1, 11):
        emp, full_name, phone = make_librarian(i, salt)
        con.execute(
            "INSERT INTO librarians(id, employee_number, full_name, phone) VALUES (?, ?, ?, ?);",
            (i, emp, full_name, phone)
        )

    readers = [make_reader(i, salt) for i in range(1, 31)]
    books = [make_book(i, salt) for i in range(1, 31)]

    con.executemany(
        "INSERT INTO readers(reader_card_number, full_name, phone, email) VALUES (?, ?, ?, ?);",
        readers,
    )
    con.executemany(
        "INSERT INTO books(inventory_number, title, author, publish_year, isbn) VALUES (?, ?, ?, ?, ?);",
        books,
    )

    today = date.today()
    start = date(2026, 1, 1)

    for i in range(1, 31):
        reader_id = i
        book_id = i
        librarian_id = 1 + (i % 10)

        issue = random_date_between(start, today)
        due = min(issue + timedelta(days=14), today)

        if i % 3 == 0:
            status_id = 2
            return_date = min(due, today).isoformat()
        elif i % 5 == 0:
            status_id = 3
            return_date = None
        else:
            status_id = 1
            return_date = None

        con.execute(
            """
            INSERT INTO loans(
              reader_id, book_id, librarian_id, status_id,
              issue_date, due_date, return_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (reader_id, book_id, librarian_id, status_id,
             issue.isoformat(), due.isoformat(), return_date)
        )

    # --- новости: от старых к новым, последняя — сегодня ---
    base_day = datetime.now()
    for idx, (title, body) in enumerate(NEWS):
        published = (base_day - timedelta(days=(len(NEWS) - idx) * 3)).strftime("%Y-%m-%d %H:%M")
        con.execute(
            "INSERT INTO news(title, body, published_at) VALUES (?, ?, ?);",
            (title, body, published),
        )

    # --- пользователи сайта ---
    user_ids = {}
    for username, full_name, email in SEED_USERS:
        cur = con.execute(
            "INSERT INTO users(username, password_hash, full_name, email, created_at) "
            "VALUES (?, ?, ?, ?, ?);",
            (username, generate_password_hash("12345"), full_name, email,
             base_day.strftime("%Y-%m-%d %H:%M")),
        )
        user_ids[username] = cur.lastrowid

    # --- мероприятия ---
    event_ids = []
    for title, desc, day_off, hour, minute, place, seats in SEED_EVENTS:
        event_dt = (base_day + timedelta(days=day_off)).replace(hour=hour, minute=minute)
        cur = con.execute(
            "INSERT INTO events(title, description, event_date, place, seats) VALUES (?, ?, ?, ?, ?);",
            (title, desc, event_dt.strftime("%Y-%m-%d %H:%M"), place, seats),
        )
        event_ids.append(cur.lastrowid)

    # --- записи на мероприятия (nastya на 2 мероприятия, reader на 1) ---
    registrations = [
        (event_ids[0], user_ids["nastya"]),
        (event_ids[2], user_ids["nastya"]),
        (event_ids[0], user_ids["reader"]),
    ]
    for event_id, user_id in registrations:
        con.execute(
            "INSERT OR IGNORE INTO event_registrations(event_id, user_id, created_at) VALUES (?, ?, ?);",
            (event_id, user_id, base_day.strftime("%Y-%m-%d %H:%M")),
        )

    # --- отзывы (гостевая книга) ---
    for user_id, text in SEED_REVIEWS:
        days_ago = random.randint(0, 20)
        con.execute(
            "INSERT INTO reviews(user_id, text, created_at) VALUES (?, ?, ?);",
            (user_id, text, (base_day - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M")),
        )

    con.commit()
    con.close()
    print(f"OK: seeded {DB_PATH}")


def main():
    ensure_dirs()
    for filename, salt in DATABASES.values():
        seed_db(filename, salt)


if __name__ == "__main__":
    main()
