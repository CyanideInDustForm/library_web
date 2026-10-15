# app.py — сайт городской библиотеки (Лабораторная работа №1 «Интернет-технологии»)
from __future__ import annotations

import os
import re
import sqlite3
import ssl
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
from xml.sax.saxutils import escape as xml_escape

from flask import (
    Flask, g, render_template, request, redirect, url_for,
    session, flash, jsonify, Response
)

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "library.sqlite3")

ALLOWED_ADMIN_TABLES = {"readers", "books", "librarians", "statuses", "loans"}

DATE_MIN = date(2026, 1, 1)

# --- Контактные данные организации (выводятся в подвале каждой страницы) ---
SITE = {
    "name": "Городская библиотека",
    "city": "г. Обнинск",
    "address": "ул. Ленина, 12, г. Обнинск, Калужская обл., 249030",
    "phone": "+7 (48439) 2-15-15",
    "email": "library@obninsk-lib.ru",
    "developer": "Студентка факультета кибернетики — Анастасия",
    "year": "2026",
}

# Координаты библиотеки (для карты на странице контактов)
LIBRARY_LAT = 55.0968
LIBRARY_LON = 36.6129

# Погода берётся для города библиотеки
WEATHER_LAT = LIBRARY_LAT
WEATHER_LON = LIBRARY_LON

# ------------------- Индекс страниц для поиска по сайту -------------------
# Поисковик ищет введённые слова по этому индексу и по новостям из БД
# и выдаёт ссылки на страницы, где слова встречаются.
SITE_INDEX: List[Dict[str, str]] = [
    {"url": "/", "title": "Главная",
     "text": "Городская библиотека главная страница новости читатели книги абонемент читальный зал электронный каталог режим работы"},
    {"url": "/about", "title": "О библиотеке",
     "text": "О библиотеке история учредитель директор для кого предназначен сайт читатели школьники студенты пенсионеры услуги абонемент читальный зал правила пользования фонды книги периодика"},
    {"url": "/achievements", "title": "Достижения",
     "text": "Достижения библиотеки награды дипломы конкурсы грамоты проекты рейтинг признание"},
    {"url": "/news", "title": "Новости",
     "text": "Новости библиотеки объявления события акции мероприятия выставки встречи"},
    {"url": "/links", "title": "Полезные ссылки",
     "text": "Ссылки полезные ресурсы электронные библиотеки книги читать онлайн литература каталоги"},
    {"url": "/contacts", "title": "Контакты",
     "text": "Контакты адрес телефон email почта как проехать карта геолокация расположение обратная связь"},
    {"url": "/services", "title": "Сервисы",
     "text": "Сервисы погода прогноз курсы валют ЦБ рубль доллар евро топ посещаемых страниц рейтинг"},
    {"url": "/xml", "title": "XML-доступ к данным",
     "text": "XML доступ данные экспорт новости книги выдачи RSS формат обмен данными"},
    {"url": "/db", "title": "Приложение к БД — выдача книг",
     "text": "Приложение база данных выдача книг читатели библиотекарь статус оформить запись"},
    {"url": "/db/search", "title": "Поиск по базе данных",
     "text": "Поиск база данных читатели книги выдачи агрегация запрос"},
    {"url": "/db/admin", "title": "Администрирование БД",
     "text": "Администрирование база данных таблицы добавить удалить запись"},
]

# ------------------------------ Сервисы (кэш) ------------------------------
_weather_cache: Dict[str, Any] = {"ts": 0.0, "data": None}
_currency_cache: Dict[str, Any] = {"ts": 0.0, "data": None}

WEATHER_CODES = {
    0: "Ясно", 1: "Преимущественно ясно", 2: "Переменная облачность", 3: "Пасмурно",
    45: "Туман", 48: "Изморозь", 51: "Лёгкая морось", 53: "Морось",
    55: "Сильная морось", 61: "Небольшой дождь", 63: "Дождь", 65: "Сильный дождь",
    71: "Небольшой снегопад", 73: "Снегопад", 75: "Сильный снегопад",
    80: "Небольшие ливни", 81: "Ливни", 82: "Сильные ливни",
    95: "Гроза", 96: "Гроза с градом", 99: "Гроза с сильным градом",
}


def fetch_json(url: str, timeout: int = 6) -> Optional[dict]:
    raw = fetch_bytes(url, timeout) or fetch_bytes_fallback(url, timeout)
    if not raw:
        return None
    try:
        import json
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def fetch_bytes(url: str, timeout: int = 6) -> Optional[bytes]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        return None


def fetch_bytes_fallback(url: str, timeout: int = 6) -> Optional[bytes]:
    """Запрос с отключённой проверкой сертификата — запасной вариант,
    если в системе нет корневых сертификатов (например, у учебных ПК)."""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read()
    except Exception:
        return None


def get_weather() -> Optional[dict]:
    """Сервис «Погода»: прогноз для города библиотеки (Open-Meteo, без ключа)."""
    if _weather_cache["data"] and time.time() - _weather_cache["ts"] < 600:
        return _weather_cache["data"]
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={WEATHER_LAT}"
        f"&longitude={WEATHER_LON}&current_weather=true&timezone=Europe%2FMoscow"
    )
    raw = fetch_json(url)
    if not raw or "current_weather" not in raw:
        return _weather_cache["data"]
    cw = raw["current_weather"]
    data = {
        "temperature": cw.get("temperature"),
        "wind": cw.get("windspeed"),
        "description": WEATHER_CODES.get(cw.get("weathercode"), "—"),
        "time": cw.get("time", ""),
    }
    _weather_cache["data"] = data
    _weather_cache["ts"] = time.time()
    return data


def get_currency() -> Optional[List[dict]]:
    """Сервис «Курсы валют»: официальные курсы ЦБ РФ."""
    if _currency_cache["data"] and time.time() - _currency_cache["ts"] < 3600:
        return _currency_cache["data"]
    raw = fetch_bytes("https://www.cbr.ru/scripts/XML_daily.asp")
    if raw is None:
        raw = fetch_bytes_fallback("https://www.cbr.ru/scripts/XML_daily.asp")
    if not raw:
        return _currency_cache["data"]
    try:
        root = ET.fromstring(raw.decode("windows-1251"))
        wanted = {"USD": "Доллар США", "EUR": "Евро", "CNY": "Юань"}
        result = []
        for v in root.findall("Valute"):
            code = v.findtext("CharCode")
            if code in wanted:
                value = float(v.findtext("Value").replace(",", "."))  # за Nominal единиц
                nominal = int(v.findtext("Nominal"))
                result.append({
                    "code": code,
                    "name": wanted[code],
                    "value": round(value / nominal, 2),
                    "nominal": 1,
                })
        _currency_cache["data"] = result
        _currency_cache["ts"] = time.time()
        return result
    except Exception:
        return _currency_cache["data"]


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # ------------------------------ БД ------------------------------
    def get_db() -> sqlite3.Connection:
        if "db" not in g:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            g.db = conn
        return g.db

    @app.teardown_appcontext
    def close_db(exc: Optional[BaseException]) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def q_all(sql: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
        cur = get_db().execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]

    def q_one(sql: str, params: Tuple[Any, ...] = ()) -> Optional[Dict[str, Any]]:
        cur = get_db().execute(sql, params)
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None

    def exec1(sql: str, params: Tuple[Any, ...] = ()) -> int:
        db = get_db()
        cur = db.execute(sql, params)
        db.commit()
        last_id = cur.lastrowid
        cur.close()
        return last_id

    # --------------------- Счётчики посещений ---------------------
    # Каждый GET страницы (в том числе обновление) = одно посещение.
    COUNTED_PREFIXES = ("/static", "/api", "/xml/")

    @app.before_request
    def count_visit():
        if request.method != "GET":
            return None
        path = request.path
        if path.startswith(COUNTED_PREFIXES) or path == "/favicon.ico":
            return None
        db = get_db()
        db.execute(
            "INSERT INTO page_visits(page, visits) VALUES (?, 1) "
            "ON CONFLICT(page) DO UPDATE SET visits = visits + 1;",
            (path,),
        )
        db.commit()
        return None

    def visit_stats(page: str) -> Tuple[int, int]:
        row = q_one("SELECT visits FROM page_visits WHERE page = ?;", (page,))
        total = q_one("SELECT COALESCE(SUM(visits), 0) AS t FROM page_visits;")
        return (row["visits"] if row else 0, total["t"] if total else 0)

    # Данные в шапку/подвал каждой страницы
    @app.context_processor
    def inject_globals():
        page_visits, total_visits = visit_stats(request.path)
        return {
            "site": SITE,
            "page_visits": page_visits,
            "total_visits": total_visits,
            "active_path": request.path,
            "year_now": date.today().year,
        }

    # ------------------------- Валидация выдачи -------------------------
    def parse_date(s: str) -> date:
        return date.fromisoformat(s)

    def validate_loan(issue_date_s: str, due_date_s: str, status_id: int,
                      return_date_s: Optional[str]) -> None:
        today = date.today()
        issue = parse_date(issue_date_s)
        due = parse_date(due_date_s)
        ret = parse_date(return_date_s) if return_date_s else None

        if issue < DATE_MIN or issue > today:
            raise ValueError("issue_date должен быть между 2026-01-01 и текущей датой.")
        if due < DATE_MIN or due > today:
            raise ValueError("due_date должен быть между 2026-01-01 и текущей датой.")
        if due < issue:
            raise ValueError("due_date должен быть >= issue_date.")
        if ret is not None:
            if ret < DATE_MIN or ret > today:
                raise ValueError("return_date должен быть между 2026-01-01 и текущей датой.")
            if ret < issue:
                raise ValueError("return_date должен быть >= issue_date.")
        if status_id == 2 and ret is None:
            raise ValueError("Для статуса 'возвращено' return_date обязателен.")

    # =========================================================
    #   СТАТИЧЕСКИЕ СТРАНИЦЫ САЙТА
    # =========================================================
    @app.get("/")
    def index():
        latest_news = q_all(
            "SELECT id, title, body, published_at FROM news "
            "ORDER BY published_at DESC LIMIT 3;"
        )
        stats = {
            "readers": q_one("SELECT COUNT(*) AS c FROM readers;")["c"],
            "books": q_one("SELECT COUNT(*) AS c FROM books;")["c"],
            "loans": q_one("SELECT COUNT(*) AS c FROM loans;")["c"],
            "news": q_one("SELECT COUNT(*) AS c FROM news;")["c"],
        }
        return render_template("index.html", latest_news=latest_news, stats=stats)

    @app.get("/about")
    def about():
        return render_template("about.html")

    @app.get("/achievements")
    def achievements():
        return render_template("achievements.html")

    @app.get("/links")
    def links():
        return render_template("links.html")

    @app.get("/contacts")
    def contacts():
        return render_template(
            "contacts.html",
            lat=LIBRARY_LAT, lon=LIBRARY_LON,
        )

    # =========================================================
    #   НОВОСТИ — ввод и показ через БД
    # =========================================================
    @app.get("/news")
    def news():
        items = q_all(
            "SELECT id, title, body, published_at FROM news "
            "ORDER BY published_at DESC;"
        )
        return render_template("news.html", news=items)

    @app.post("/news/add")
    def news_add():
        try:
            title = request.form["title"].strip()
            body = request.form["body"].strip()
            if len(title) < 5:
                raise ValueError("Заголовок новости — минимум 5 символов.")
            if len(body) < 10:
                raise ValueError("Текст новости — минимум 10 символов.")
            published = datetime.now().strftime("%Y-%m-%d %H:%M")
            exec1(
                "INSERT INTO news(title, body, published_at) VALUES (?, ?, ?);",
                (title, body, published),
            )
            flash("Новость опубликована.", "success")
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Не удалось добавить новость (проверьте длину полей).", "danger")
        return redirect(url_for("news"))

    # =========================================================
    #   СЕРВИСЫ: погода, курсы валют, топ страниц
    # =========================================================
    @app.get("/services")
    def services():
        top_pages = q_all(
            "SELECT page, visits FROM page_visits ORDER BY visits DESC LIMIT 10;"
        )
        page_titles = {p["url"]: p["title"] for p in SITE_INDEX}
        for row in top_pages:
            row["title"] = page_titles.get(row["page"], row["page"])
        return render_template(
            "services.html",
            weather=get_weather(),
            currency=get_currency(),
            top_pages=top_pages,
        )

    # =========================================================
    #   ПОИСКОВИК ПО САЙТУ (под горизонтальным меню)
    # =========================================================
    @app.get("/site-search")
    def site_search():
        query = (request.args.get("q") or "").strip()
        words = [w.lower() for w in re.findall(r"[а-яА-Яa-zA-Z0-9]+", query)]
        results: List[dict] = []
        if words:
            # 1) статические страницы
            for page in SITE_INDEX:
                hay = (page["title"] + " " + page["text"]).lower()
                matched = [w for w in words if w in hay]
                if matched:
                    results.append({
                        "title": page["title"],
                        "url": page["url"],
                        "kind": "Страница сайта",
                        "snippet": "Совпали слова: " + ", ".join(matched),
                        "score": len(matched),
                    })
            # 2) новости из БД
            for n in q_all("SELECT id, title, body, published_at FROM news;"):
                hay = (n["title"] + " " + n["body"]).lower()
                matched = [w for w in words if w in hay]
                if matched:
                    results.append({
                        "title": n["title"],
                        "url": url_for("news") + f"#news-{n['id']}",
                        "kind": "Новость",
                        "snippet": n["body"][:120] + ("…" if len(n["body"]) > 120 else ""),
                        "score": len(matched),
                    })
            results.sort(key=lambda r: r["score"], reverse=True)

        return render_template(
            "site_search.html", query=query, words=words, results=results
        )

    # =========================================================
    #   XML-ДОСТУП К ДАННЫМ
    # =========================================================
    @app.get("/xml")
    def xml_info():
        feeds = [
            {"url": url_for("xml_news"), "title": "Новости библиотеки", "desc": "Все новости из базы данных в формате XML (оформляются в браузере через XSL)."},
            {"url": url_for("xml_books"), "title": "Книжный фонд", "desc": "Каталог книг с авторами, годом издания и ISBN."},
            {"url": url_for("xml_loans"), "title": "Журнал выдач", "desc": "Последние выдачи книг читателям со статусами."},
        ]
        return render_template("xml.html", feeds=feeds)

    def xml_response(payload: str, feed_name: str) -> Response:
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<?xml-stylesheet type="text/xsl" href="/static/news.xsl"?>\n'
            f'<{feed_name} generated="{datetime.now().isoformat(timespec="seconds")}">\n'
            f'{payload}\n</{feed_name}>'
        )
        return Response(xml, mimetype="application/xml; charset=utf-8")

    @app.get("/xml/news.xml")
    def xml_news():
        items = q_all(
            "SELECT id, title, body, published_at FROM news ORDER BY published_at DESC;"
        )
        payload = "\n".join(
            "  <item>\n"
            f"    <id>{n['id']}</id>\n"
            f"    <title>{xml_escape(n['title'])}</title>\n"
            f"    <text>{xml_escape(n['body'])}</text>\n"
            f"    <published>{n['published_at']}</published>\n"
            "  </item>"
            for n in items
        )
        return xml_response(payload, "news")

    @app.get("/xml/books.xml")
    def xml_books():
        items = q_all(
            "SELECT inventory_number, title, author, publish_year, isbn "
            "FROM books ORDER BY title;"
        )
        payload = "\n".join(
            "  <item>\n"
            f"    <inventory>{b['inventory_number']}</inventory>\n"
            f"    <title>{xml_escape(b['title'])}</title>\n"
            f"    <author>{xml_escape(b['author'])}</author>\n"
            f"    <year>{b['publish_year']}</year>\n"
            f"    <isbn>{b['isbn']}</isbn>\n"
            "  </item>"
            for b in items
        )
        return xml_response(payload, "books")

    @app.get("/xml/loans.xml")
    def xml_loans():
        items = q_all("""
            SELECT l.id, r.full_name AS reader, b.title AS book,
                   lb.full_name AS librarian, s.title AS status,
                   l.issue_date, l.due_date, l.return_date
            FROM loans l
            JOIN readers r ON r.id = l.reader_id
            JOIN books b ON b.id = l.book_id
            JOIN librarians lb ON lb.id = l.librarian_id
            JOIN statuses s ON s.id = l.status_id
            ORDER BY l.issue_date DESC, l.id DESC LIMIT 100;
        """)
        payload = "\n".join(
            "  <item>\n"
            f"    <reader>{xml_escape(l['reader'])}</reader>\n"
            f"    <book>{xml_escape(l['book'])}</book>\n"
            f"    <librarian>{xml_escape(l['librarian'])}</librarian>\n"
            f"    <status>{xml_escape(l['status'])}</status>\n"
            f"    <issue>{l['issue_date']}</issue>\n"
            f"    <due>{l['due_date']}</due>\n"
            f"    <returned>{l['return_date'] or ''}</returned>\n"
            "  </item>"
            for l in items
        )
        return xml_response(payload, "loans")

    # =========================================================
    #   ПРИЛОЖЕНИЕ К БД (выдача книг, поиск, администрирование)
    # =========================================================
    def loan_form_data():
        return {
            "readers": q_all("SELECT id, full_name FROM readers ORDER BY full_name;"),
            "books": q_all("SELECT id, title FROM books ORDER BY title;"),
            "librarians": q_all("SELECT id, full_name FROM librarians ORDER BY full_name;"),
            "statuses": q_all("SELECT id, title FROM statuses ORDER BY id;"),
        }

    @app.get("/db")
    def db_app():
        data = loan_form_data()
        loans = q_all("""
            SELECT
              l.id, l.issue_date, l.due_date, l.return_date,
              r.full_name AS reader_name,
              b.title AS book_title,
              lb.full_name AS librarian_name,
              s.title AS status_title
            FROM loans l
            JOIN readers r ON r.id = l.reader_id
            JOIN books b ON b.id = l.book_id
            JOIN librarians lb ON lb.id = l.librarian_id
            JOIN statuses s ON s.id = l.status_id
            ORDER BY l.issue_date DESC, l.id DESC
            LIMIT 200;
        """)
        return render_template("db.html", loans=loans, **data)

    @app.post("/loans/create")
    def create_loan():
        try:
            reader_id = int(request.form["reader_id"])
            book_id = int(request.form["book_id"])
            librarian_id = int(request.form["librarian_id"])
            status_id = int(request.form["status_id"])

            issue_date = request.form["issue_date"].strip()
            due_date = request.form["due_date"].strip()

            return_date = request.form.get("return_date")
            return_date = return_date.strip() if return_date else None
            if return_date == "":
                return_date = None

            validate_loan(issue_date, due_date, status_id, return_date)

            exec1("""
                INSERT INTO loans(
                  reader_id, book_id, librarian_id, status_id,
                  issue_date, due_date, return_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (reader_id, book_id, librarian_id, status_id,
                  issue_date, due_date, return_date))

            flash("Выдача создана.", "success")
        except ValueError as e:
            flash(str(e), "danger")
        except sqlite3.IntegrityError as e:
            flash(f"Ошибка ограничения БД: {e}", "danger")
        except Exception:
            flash("Не удалось создать выдачу (ошибка формы).", "danger")

        return redirect(url_for("db_app"))

    @app.get("/db/search")
    def db_search():
        mode = request.args.get("mode", "one")

        readers = q_all("SELECT id, full_name FROM readers ORDER BY full_name;")
        librarians = q_all("SELECT id, full_name FROM librarians ORDER BY full_name;")
        statuses = q_all("SELECT id, title FROM statuses ORDER BY id;")
        authors = q_all("SELECT DISTINCT author FROM books ORDER BY author;")

        meta: Dict[str, Any] = {"mode": mode}
        results: List[Dict[str, Any]] = []

        if mode == "one":
            entity = request.args.get("entity", "readers")
            meta["entity"] = entity

            if entity == "readers":
                name_prefix = (request.args.get("full_name_prefix") or "").strip()
                card_prefix = (request.args.get("card_prefix") or "").strip()
                phone_contains = (request.args.get("phone_contains") or "").strip()

                where, params = [], []
                if name_prefix:
                    where.append("full_name LIKE ?")
                    params.append(name_prefix + "%")
                if card_prefix:
                    where.append("reader_card_number LIKE ?")
                    params.append(card_prefix + "%")
                if phone_contains:
                    where.append("phone LIKE ?")
                    params.append("%" + phone_contains + "%")

                sql = "SELECT id, reader_card_number, full_name, phone, email FROM readers"
                if where:
                    sql += " WHERE " + " AND ".join(where)
                sql += " ORDER BY full_name LIMIT 200;"
                results = q_all(sql, tuple(params))

            elif entity == "books":
                title_prefix = (request.args.get("title_prefix") or "").strip()
                author = (request.args.get("author") or "").strip()
                year = (request.args.get("publish_year") or "").strip()

                where, params = [], []
                if title_prefix:
                    where.append("title LIKE ?")
                    params.append(title_prefix + "%")
                if author:
                    where.append("author = ?")
                    params.append(author)
                if year:
                    where.append("publish_year = ?")
                    params.append(int(year))

                sql = "SELECT id, inventory_number, title, author, publish_year, isbn FROM books"
                if where:
                    sql += " WHERE " + " AND ".join(where)
                sql += " ORDER BY title LIMIT 200;"
                results = q_all(sql, tuple(params))

            elif entity == "loans":
                status_id = (request.args.get("status_id") or "").strip()
                librarian_id = (request.args.get("librarian_id") or "").strip()
                issue_from = (request.args.get("issue_from") or "").strip()

                where, params = [], []
                if status_id:
                    where.append("l.status_id = ?")
                    params.append(int(status_id))
                if librarian_id:
                    where.append("l.librarian_id = ?")
                    params.append(int(librarian_id))
                if issue_from:
                    where.append("l.issue_date >= ?")
                    params.append(issue_from)

                sql = """
                    SELECT
                      l.id, l.issue_date, l.due_date, l.return_date,
                      r.full_name AS reader_name,
                      b.title AS book_title,
                      lb.full_name AS librarian_name,
                      s.title AS status_title
                    FROM loans l
                    JOIN readers r ON r.id = l.reader_id
                    JOIN books b ON b.id = l.book_id
                    JOIN librarians lb ON lb.id = l.librarian_id
                    JOIN statuses s ON s.id = l.status_id
                """
                if where:
                    sql += " WHERE " + " AND ".join(where)
                sql += " ORDER BY l.issue_date DESC, l.id DESC LIMIT 200;"
                results = q_all(sql, tuple(params))

        elif mode == "two":
            reader_id = (request.args.get("reader_id") or "").strip()
            book_id = (request.args.get("book_id") or "").strip()
            meta["reader_id"] = reader_id
            meta["book_id"] = book_id

            if reader_id:
                sql = """
                    SELECT
                      r.full_name AS reader_name,
                      b.title AS book_title,
                      l.issue_date, l.due_date, l.return_date,
                      s.title AS status_title,
                      lb.full_name AS librarian_name
                    FROM loans l
                    JOIN readers r ON r.id = l.reader_id
                    JOIN books b ON b.id = l.book_id
                    JOIN statuses s ON s.id = l.status_id
                    JOIN librarians lb ON lb.id = l.librarian_id
                    WHERE l.reader_id = ?
                """
                params: List[Any] = [int(reader_id)]
                if book_id:
                    sql += " AND l.book_id = ?"
                    params.append(int(book_id))
                sql += " ORDER BY l.issue_date DESC, l.id DESC LIMIT 200;"
                results = q_all(sql, tuple(params))

        elif mode == "agg":
            results = q_all("""
                SELECT
                  lb.full_name AS librarian_name,
                  COUNT(l.id) AS loans_count
                FROM librarians lb
                LEFT JOIN loans l ON l.librarian_id = lb.id
                GROUP BY lb.id
                ORDER BY loans_count DESC, lb.full_name ASC;
            """)

        return render_template(
            "db_search.html",
            mode=mode, meta=meta, results=results,
            readers=readers, librarians=librarians,
            statuses=statuses, authors=authors,
        )

    @app.get("/api/options/books-by-reader")
    def api_books_by_reader():
        rid = request.args.get("reader_id", "").strip()
        if not rid:
            return jsonify({"ok": True, "items": []})
        try:
            rows = q_all("""
                SELECT DISTINCT b.id, b.title
                FROM loans l
                JOIN books b ON b.id = l.book_id
                WHERE l.reader_id = ?
                ORDER BY b.title;
            """, (int(rid),))
            items = [{"value": r["id"], "label": r["title"]} for r in rows]
            return jsonify({"ok": True, "items": items})
        except Exception:
            return jsonify({"ok": False, "error": "bad reader_id"}), 400

    @app.get("/db/admin")
    def db_admin():
        table = request.args.get("table", "readers")
        if table not in ALLOWED_ADMIN_TABLES:
            table = "readers"

        rows = q_all(f"SELECT * FROM {table} LIMIT 200;")
        data = loan_form_data()

        return render_template(
            "db_admin.html",
            table=table,
            today=date.today().isoformat(),
            rows=rows,
            **data,
        )

    @app.post("/admin/<table>/create")
    def admin_create(table: str):
        if table not in ALLOWED_ADMIN_TABLES:
            flash("Недопустимая таблица.", "danger")
            return redirect(url_for("db_admin"))

        try:
            if table == "readers":
                exec1("""
                    INSERT INTO readers(reader_card_number, full_name, phone, email)
                    VALUES (?, ?, ?, ?);
                """, (
                    request.form["reader_card_number"].strip(),
                    request.form["full_name"].strip(),
                    (request.form.get("phone") or "").strip() or None,
                    (request.form.get("email") or "").strip() or None,
                ))
                flash("Читатель добавлен.", "success")

            elif table == "books":
                exec1("""
                    INSERT INTO books(inventory_number, title, author, publish_year, isbn)
                    VALUES (?, ?, ?, ?, ?);
                """, (
                    request.form["inventory_number"].strip(),
                    request.form["title"].strip(),
                    request.form["author"].strip(),
                    int(request.form["publish_year"]),
                    request.form["isbn"].strip(),
                ))
                flash("Книга добавлена.", "success")

            elif table == "librarians":
                exec1("""
                    INSERT INTO librarians(employee_number, full_name, phone)
                    VALUES (?, ?, ?);
                """, (
                    request.form["employee_number"].strip(),
                    request.form["full_name"].strip(),
                    (request.form.get("phone") or "").strip() or None,
                ))
                flash("Библиотекарь добавлен.", "success")

            elif table == "loans":
                reader_id = int(request.form["reader_id"])
                book_id = int(request.form["book_id"])
                librarian_id = int(request.form["librarian_id"])
                status_id = int(request.form["status_id"])
                issue_date = request.form["issue_date"].strip()
                due_date = request.form["due_date"].strip()
                return_date = (request.form.get("return_date") or "").strip() or None

                validate_loan(issue_date, due_date, status_id, return_date)

                exec1("""
                    INSERT INTO loans(reader_id, book_id, librarian_id, status_id, issue_date, due_date, return_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (reader_id, book_id, librarian_id, status_id, issue_date, due_date, return_date))
                flash("Выдача добавлена.", "success")

            elif table == "statuses":
                flash("Справочник статусов фиксирован и не редактируется.", "warning")

        except ValueError as e:
            flash(str(e), "danger")
        except sqlite3.IntegrityError as e:
            flash(f"Ошибка ограничения БД: {e}", "danger")
        except Exception:
            flash("Некорректные данные.", "danger")

        return redirect(url_for("db_admin", table=table))

    @app.post("/admin/<table>/delete/<int:id>")
    def admin_delete(table: str, id: int):
        if table not in ALLOWED_ADMIN_TABLES:
            flash("Недопустимая таблица.", "danger")
            return redirect(url_for("db_admin"))

        if table in ("statuses",):
            flash("Эти записи нельзя удалять", "danger")
            return redirect(url_for("db_admin", table=table))

        try:
            exec1(f"DELETE FROM {table} WHERE id = ?;", (id,))
            flash("Запись удалена.", "success")
        except Exception as e:
            flash(f"Ошибка удаления: {e}", "danger")

        return redirect(url_for("db_admin", table=table))

    # ---------- API: модалки создания сущностей ----------
    @app.post("/api/readers/create")
    def api_create_reader():
        try:
            card = request.form["reader_card_number"].strip()
            full_name = request.form["full_name"].strip()
            phone = (request.form.get("phone") or "").strip() or None
            email = (request.form.get("email") or "").strip() or None

            new_id = exec1("""
                INSERT INTO readers(reader_card_number, full_name, phone, email)
                VALUES (?, ?, ?, ?);
            """, (card, full_name, phone, email))

            row = q_one("SELECT id, full_name FROM readers WHERE id=?;", (new_id,))
            return jsonify({"ok": True, "id": row["id"], "label": row["full_name"]})
        except sqlite3.IntegrityError as e:
            return jsonify({"ok": False, "error": str(e)}), 400
        except Exception:
            return jsonify({"ok": False, "error": "Некорректные данные."}), 400

    @app.post("/api/books/create")
    def api_create_book():
        try:
            inv = request.form["inventory_number"].strip()
            title = request.form["title"].strip()
            author = request.form["author"].strip()
            year = int(request.form["publish_year"])
            isbn = request.form["isbn"].strip()

            new_id = exec1("""
                INSERT INTO books(inventory_number, title, author, publish_year, isbn)
                VALUES (?, ?, ?, ?, ?);
            """, (inv, title, author, year, isbn))

            row = q_one("SELECT id, title FROM books WHERE id=?;", (new_id,))
            return jsonify({"ok": True, "id": row["id"], "label": row["title"]})
        except sqlite3.IntegrityError as e:
            return jsonify({"ok": False, "error": str(e)}), 400
        except Exception:
            return jsonify({"ok": False, "error": "Некорректные данные."}), 400

    @app.post("/api/librarians/create")
    def api_create_librarian():
        try:
            emp = request.form["employee_number"].strip()
            full_name = request.form["full_name"].strip()
            phone = (request.form.get("phone") or "").strip() or None

            new_id = exec1("""
                INSERT INTO librarians(employee_number, full_name, phone)
                VALUES (?, ?, ?);
            """, (emp, full_name, phone))

            row = q_one("SELECT id, full_name FROM librarians WHERE id=?;", (new_id,))
            return jsonify({"ok": True, "id": row["id"], "label": row["full_name"]})
        except sqlite3.IntegrityError as e:
            return jsonify({"ok": False, "error": str(e)}), 400
        except Exception:
            return jsonify({"ok": False, "error": "Некорректные данные."}), 400

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
