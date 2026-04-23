from flask import Flask, g, render_template, request, redirect, url_for, session, flash
import os, sqlite3, uuid, hashlib, datetime

# ==Конфиг==
app = Flask(__name__)
# =========

def get_db():
    """Получение соединения с БД"""
    if "db" not in g:
        g.db = sqlite3.connect('database.db')
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    """Закрытие соединения после запроса"""
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    # Таблица пользователей
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
    """)
    # Таблица загрузок
    db.execute("""
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

def load_users():
    users_list = []
    db=get_db()
    try:
        db.execute('''
        SELECT * FROM users
        ''')
        existing_users = db.fetchall()
        for user in existing_users:
            user_dict = {
                'username': user[1],
                'password': user[2],
                'email': user[3],
            }
            users_list.append(user_dict)
        db.commit()

    except FileNotFoundError:
        print("База данных не найдена.")
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
    return users_list

def user_exists(username):
    try:
        db = get_db()
        info = db.execute('SELECT username FROM users WHERE username = ?', (username,)).fetchone()
        info2 = db.execute('SELECT email FROM users WHERE email = ?', (username,)).fetchone()
        if info is None:
            return False
        if info is not None:
            return True

        if info2 is None:
            return False
        if info2 is not None:
            return True

    except FileNotFoundError:
        return False

def save_user_to_file(username, password, email):
    db = get_db()
    db.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', (username, password, email))
    db.commit()

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Пожалуйста, войдите в систему', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function

def login():
    if 'username' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['usernameORemail']
        email = request.form['usernameORemail']
        password = request.form['password']

        users = load_users()
        user_found = False
        for user in users:
            if user['username'] == username and user['password'] == password:
                session['username'] = user['username']
                print(session)
                flash(f'Добро пожаловать, {username}!', 'success')
                user_found = True
                return redirect(url_for('index'))

            elif user['email'] == username and user['password'] == password:
                session['username'] = user['username']
                print(session)
                flash(f'Добро пожаловать, {username}!', 'success')
                user_found = True
                return redirect(url_for('index'))
        if not user_found:
            flash('Неверное имя пользователя или пароль', 'error')
    return render_template('login.html')

# ==Роуты==

@app.route("/")
def index():
    db = get_db()
    tracks = db.execute('SELECT * FROM uploads').fetchall()
    return render_template('index.html', tracks=tracks)

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        if user_exists(username):
            return render_template('register.html',message="Пользователь с таким логином уже существует!")

        save_user_to_file(username, password, email)

        return render_template('register.html',message="Регистрация успешна!")

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        name = request.form['name']
        author = request.form['author']

        db = get_db()
        db.execute('INSERT INTO uploads (name, author, uploadedby) VALUES (?, ?, ?)', (name, author, 1))
        db.commit()

        return redirect(url_for('index'))
    return render_template('upload.html')
# =========

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)