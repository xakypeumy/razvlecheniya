from flask import Flask, g
import sqlite3
import os

# ==Конфиг==
app = Flask(__name__)
DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "database.db")
# =========

def get_db():
    """Получение соединения с БД"""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    """Закрытие соединения после запроса"""
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
    """)
    # Таблица загрузок
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            author TEXT NOT NULL,
            uploadedby INTEGER,
            FOREIGN KEY (uploadedby) REFERENCES users(id)
        )
    """)
    db.commit()
    db.close()

# ==Роуты==

@app.route("/")
def index():
    return "В разработке"

# =========

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
