from flask import Flask, g, render_template, request, redirect, url_for, session, flash, send_from_directory
import os, sqlite3, uuid, hashlib, datetime
from werkzeug.utils import secure_filename

# ==Конфиг==
app = Flask(__name__)
app.secret_key = '123'
app.config['UPLOAD_FOLDER'] = 'uploads'
# =========

# ==Функции==
@app.route('/uploads/<filename>')
def uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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
    db = sqlite3.connect('database.db')
    db.row_factory = sqlite3.Row
    # Таблица пользователей
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL DEFAULT 'user'
        )
    """)
    # Таблица загрузок
    db.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            author TEXT NOT NULL,
            uploadedby INTEGER,
            audio_file TEXT,
            cover_file TEXT,
            FOREIGN KEY (uploadedby) REFERENCES users(id)
        )
    """)
    # Таблица тикетов
    db.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            artist TEXT NOT NULL,
            audio_file TEXT,
            cover_file TEXT,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    # Создать админа если нет
    admin_exists = db.execute('SELECT id FROM users WHERE role = "admin"').fetchone()
    if not admin_exists:
        db.execute('INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)',
                   ('admin', 'admin', 'admin@example.com', 'admin'))
    db.commit()
    db.close()

def load_users():
    users_list = []
    db=get_db()
    try:
        cursor = db.execute('''
        SELECT * FROM users
        ''')
        existing_users = cursor.fetchall()
        for user in existing_users:
            user_dict = {
                'id': user[0],
                'username': user[1],
                'password': user[2],
                'email': user[3],
                'role': user[4],
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

        elif info2 is None:
            return False
        elif info2 is not None:
            return True

    except FileNotFoundError:
        return False

def save_user_to_file(username, password, email, role='user'):
    db = get_db()
    db.execute('INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)', (username, password, email, role))
    db.commit()

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Пожалуйста, войдите в систему', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function

# ==Руты==

@app.route("/")
def index():
    db = get_db()
    tracks = db.execute('SELECT * FROM uploads').fetchall()
    return render_template('index.html', tracks=tracks)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['usernameORemail']
        password = request.form['password']

        print(f"Login attempt: usernameORemail={username}, password={password}")
        users = load_users()
        print(f"Loaded users: {users}")
        user_found = False
        for user in users:
            print(f"Checking user: {user}")
            if user['username'] == username and user['password'] == password:
                session['username'] = user['username']
                session['role'] = user['role']
                session['user_id'] = user['id']
                print(session)
                flash(f'Добро пожаловать, {username}!', 'success')
                user_found = True
                return redirect(url_for('index'))

            elif user['email'] == username and user['password'] == password:
                session['username'] = user['username']
                session['role'] = user['role']
                session['user_id'] = user['id']
                print(session)
                flash(f'Добро пожаловать, {username}!', 'success')
                user_found = True
                return redirect(url_for('index'))
        if not user_found:
            flash('Неверное имя пользователя или пароль', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        if user_exists(username):
            flash('Пользователь с таким логином уже существует!', 'error')
            return render_template('register.html')

        save_user_to_file(username, password, email)

        flash('Регистрация успешна! Теперь войдите.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/tickets')
@login_required
def tickets():
    if session.get('role') != 'admin':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('index'))
    db = get_db()
    tickets = db.execute('SELECT * FROM tickets WHERE status = "pending"').fetchall()
    return render_template('tickets.html', tickets=tickets)

@app.route('/approve/<int:ticket_id>', methods=['POST'])
@login_required
def approve_ticket(ticket_id):
    if session.get('role') != 'admin':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('index'))
    db = get_db()
    ticket = db.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
    if ticket:
        db.execute('INSERT INTO uploads (name, author, uploadedby, audio_file, cover_file) VALUES (?, ?, ?, ?, ?)',
                   (ticket['title'], ticket['artist'], ticket['user_id'], ticket['audio_file'], ticket['cover_file']))
        db.execute('UPDATE tickets SET status = "approved" WHERE id = ?', (ticket_id,))
        db.commit()
        flash('Трек опубликован!', 'success')
    return redirect(url_for('tickets'))

@app.route('/reject/<int:ticket_id>', methods=['POST'])
@login_required
def reject_ticket(ticket_id):
    if session.get('role') != 'admin':
        flash('Доступ запрещен', 'error')
        return redirect(url_for('index'))
    db = get_db()
    db.execute('UPDATE tickets SET status = "rejected" WHERE id = ?', (ticket_id,))
    db.commit()
    flash('Трек отклонен!', 'success')
    return redirect(url_for('tickets'))

@app.route('/about')
def about():
    db = get_db()
    tracks = db.execute('SELECT * FROM uploads').fetchall()
    return render_template('about.html', tracks=tracks)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form['title']
        artist = request.form['artist']
        audio = request.files['audio']
        cover = request.files['cover']

        if audio and cover:
            audio_filename = secure_filename(audio.filename)
            cover_filename = secure_filename(cover.filename)
            audio_path = os.path.join('uploads', audio_filename)
            cover_path = os.path.join('uploads', cover_filename)
            audio.save(audio_path)
            cover.save(cover_path)

            db = get_db()
            db.execute('INSERT INTO tickets (user_id, title, artist, audio_file, cover_file) VALUES (?, ?, ?, ?, ?)',
                       (session['user_id'], title, artist, audio_filename, cover_filename))
            db.commit()

            flash('Трек отправлен на проверку!', 'success')
            return redirect(url_for('index'))
    db = get_db()
    tracks = db.execute('SELECT * FROM uploads').fetchall()
    return render_template('upload.html', tracks=tracks)

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

# =========

if __name__ == "__main__":
    init_db()  # Инициализация базы данных
    app.run(debug=True, host='0.0.0.0', port=5000)