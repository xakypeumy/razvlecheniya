from flask import Flask, g, render_template, request, redirect, url_for, session, flash
import os, sqlite3, uuid, hashlib, datetime

# ==Конфиг==
app = Flask(__name__)
database = os.path.join(os.path.abspath(os.path.dirname(__file__)), "database.db")
db = sqlite3.connect(database)
cursor = db.cursor()
# =========

def init_db():
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

def load_users():
    users_list = []
    try:
        cursor.execute('''
        SELECT * FROM users
        ''')
        existing_users = cursor.fetchall()
        for user in existing_users:
            user_dict = {
                'username': user[1],
                'password': user[2],
                'email': user[3],
            }
            users_list.append(user_dict)
        database.commit()

    except FileNotFoundError:
        print("База данных не найдена.")
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
    return users_list

def user_exists(username):
    try:
        info = cursor.execute('SELECT username FROM users WHERE username = ?', (username,)).fetchone()
        if info is None:
            return False
        else:
            return True
    except FileNotFoundError:
        return False

def save_user_to_file(username, password, email):
    cursor.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', (username, password, email))
    database.commit()

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
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        users = load_users()
        user_found = False
        for user in users:
            if user['username'] == username and user['password'] == password or user['email'] == email and user['password'] == password:
                session['username'] = user['username']
                print(session)
                flash(f'Добро пожаловать, {username}!', 'success')
                user_found = True
                return redirect(url_for('index'))
        if not user_found:
            flash('Неверное имя пользователя или пароль', 'error')

    return render_template('login.html')

# ==Роуты==

@app.teardown_appcontext
def close_db(exception):
    """Закрытие соединения после запроса"""
    db = g.pop("db", None)
    if db is not None:
        db.close()

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

@app.route("/")
def index():
    return render_template('index.html')

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

# =========

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)