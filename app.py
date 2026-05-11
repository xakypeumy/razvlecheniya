from flask import Flask, g, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
import os, sqlite3, uuid, hashlib, datetime
from werkzeug.utils import secure_filename
import requests
import urllib.parse
import json
from datetime import timedelta

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
    # Таблица для кеширования информации о треках
    db.execute("""
        CREATE TABLE IF NOT EXISTS track_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_name TEXT NOT NULL,
            artist_name TEXT NOT NULL,
            mbid TEXT,
            length INTEGER,
            is_cover BOOLEAN DEFAULT 0,
            original_title TEXT,
            original_artist TEXT,
            genius_lyrics TEXT,
            genius_url TEXT,
            spotify_data TEXT,
            lastfm_data TEXT,
            similar_tracks TEXT,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(track_name, artist_name)
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

# ===== API =====

def get_cached_track_info(artist, title):
    """Получение кешированной информации о треке"""
    db = get_db()
    cached = db.execute(
        'SELECT * FROM track_cache WHERE artist_name = ? AND track_name = ?',
        (artist, title)
    ).fetchone()
    
    if cached:
        return {
            'cached': True,
            'title': cached['track_name'],
            'artist': cached['artist_name'],
            'mbid': cached['mbid'],
            'length': cached['length'],
            'is_cover': bool(cached['is_cover']),
            'original_title': cached['original_title'],
            'original_artist': cached['original_artist'],
            'lyrics_text': cached['genius_lyrics'],
            'lyrics_url': None,  # Для обратной совместимости
            'genius_url': cached['genius_url'],
            'spotify': json.loads(cached['spotify_data']) if cached['spotify_data'] else None,
            'lastfm': json.loads(cached['lastfm_data']) if cached['lastfm_data'] else None,
            'similar': json.loads(cached['similar_tracks']) if cached['similar_tracks'] else []
        }
    return None

def save_track_cache(artist, title, mbid=None, length=None, is_cover=False, original_title=None, 
                      original_artist=None, lyrics_text=None, lyrics_url=None, genius_url=None, 
                      spotify_data=None, lastfm_data=None, similar=None):
    """Сохранение информации о треке в кеш"""
    db = get_db()
    try:
        db.execute("""
            INSERT OR REPLACE INTO track_cache 
            (artist_name, track_name, mbid, length, is_cover, original_title, original_artist,
             genius_lyrics, genius_url, spotify_data, lastfm_data, similar_tracks, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            artist, title,
            mbid, length, is_cover, original_title, original_artist,
            lyrics_text, genius_url,
            json.dumps(spotify_data) if spotify_data else None,
            json.dumps(lastfm_data) if lastfm_data else None,
            json.dumps(similar) if similar else None
        ))
        db.commit()
    except Exception as e:
        print(f"Error saving track cache: {e}")

def get_lyrics(artist, title):
    """Получение текста песни через Lyrics.ovh API (бесплатный)"""
    try:
        # Lyrics.ovh API
        response = requests.get(
            f'https://api.lyrics.ovh/v1/{urllib.parse.quote(artist)}/{urllib.parse.quote(title)}',
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            lyrics = data.get('lyrics', '')
            if lyrics:
                return {
                    'lyrics': lyrics.strip(),
                    'url': f'https://www.google.com/search?q=lyrics+{urllib.parse.quote(f"{artist} {title}")}'
                }
        
        return None
    except Exception as e:
        print(f"Error getting lyrics: {e}")
        return None

def get_genius_info(artist, title):
    """Получение информации о песне через Genius API (без ключа - базовый поиск)"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # Genius
        query = urllib.parse.quote(f'{artist} {title}')
        
        # Поиск песен
        response = requests.get(
            f'https://genius.com/api/search?q={query}&type=song',
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            hits = data.get('hits', [])
            
            if hits:
                # точное совпадение исполнителя
                for hit in hits:
                    song = hit.get('result', {})
                    song_artist = song.get('primary_artist', {}).get('name', '').lower()
                    track_artist = artist.lower()
                    
                    # Проверяем совпадение
                    if track_artist in song_artist or song_artist in track_artist:
                        return {
                            'title': song.get('title', title),
                            'url': song.get('url', ''),
                            'artist': song.get('primary_artist', {}).get('name', artist)
                        }
                
                # Если точного совпадения нет, берем первый результат
                song = hits[0].get('result', {})
                return {
                    'title': song.get('title', title),
                    'url': song.get('url', ''),
                    'artist': song.get('primary_artist', {}).get('name', artist)
                }
        
        return None
    except Exception as e:
        print(f"Error getting Genius info: {e}")
        return None

def get_spotify_info(artist, title):
    """Получение информации о треке через Spotify"""
    try:
        headers = {'User-Agent': 'MyMusicApp/1.0'}
        query = urllib.parse.quote(f'track:{title} artist:{artist}')
        
        response = requests.get(
            f'https://open.spotify.com/search?q={query}&type=track',
            headers=headers,
            timeout=5
        )
        
        return None
    except Exception as e:
        print(f"Error getting Spotify info: {e}")
        return None

def get_lastfm_info(artist, title):
    """Получение информации о треке через Last.fm API (бесплатный ключ)"""
    try:
        lastfm_key = 'b755b6f6517152401963453ab70fa942'
        
        response = requests.get(
            'http://ws.audioscrobbler.com/2.0/',
            params={
                'method': 'track.getInfo',
                'artist': artist,
                'track': title,
                'api_key': lastfm_key,
                'format': 'json'
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'track' in data and data['track'] != 'null':
                track = data['track']
                return {
                    'playcount': track.get('playcount', '0'),
                    'listeners': track.get('listeners', '0'),
                    'duration': track.get('duration', 0),
                    'url': track.get('url', ''),
                    'artist': track.get('artist', {}).get('name', artist) if isinstance(track.get('artist'), dict) else track.get('artist', artist),
                    'tags': [tag.get('name', tag) for tag in track.get('toptags', {}).get('tag', [])[:5]] if isinstance(track.get('toptags', {}), dict) else []
                }
        
        return None
    except Exception as e:
        print(f"Error getting LastFM info: {e}")
        return None

def get_similar_tracks(artist, title):
    """Получение похожих треков через Last.fm API"""
    try:
        lastfm_key = 'b755b6f6517152401963453ab70fa942'
        
        response = requests.get(
            'http://ws.audioscrobbler.com/2.0/',
            params={
                'method': 'track.getSimilar',
                'artist': artist,
                'track': title,
                'api_key': lastfm_key,
                'format': 'json',
                'limit': 10
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            similar_list = []
            
            if 'similartracks' in data and data['similartracks'] != 'null':
                tracks = data['similartracks'].get('track', [])
                # Если один результат, это будет dict, нужно преобразовать в список
                if isinstance(tracks, dict):
                    tracks = [tracks]
                
                for track in tracks:
                    similar_list.append({
                        'name': track.get('name', ''),
                        'artist': track.get('artist', {}).get('name', '') if isinstance(track.get('artist'), dict) else track.get('artist', ''),
                        'url': track.get('url', ''),
                        'match': float(track.get('match', 0)) * 100  # Convert to percentage
                    })
            
            return similar_list
        
        return []
    except Exception as e:
        print(f"Error getting similar tracks: {e}")
        return []

def get_track_info(artist, title):
    """Получение полной информации о треке из всех источников с кешированием"""
    try:
        # Сначала проверяем кеш
        cached = get_cached_track_info(artist, title)
        if cached:
            return cached
        
        track_info = {
            'title': title,
            'artist': artist,
            'is_cover': False,
            'original_artist': None,
            'lyrics_text': None,
            'lyrics_url': None,
            'genius_url': None,
            'spotify': None,
            'lastfm': None,
            'similar': []
        }
        
        # MusicBrainz для определения кавера
        try:
            query = urllib.parse.quote(f'{title} artist:{artist}')
            headers = {'User-Agent': 'MyMusicApp/1.0 (contact@example.com)'}
            
            response = requests.get(
                f'https://musicbrainz.org/ws/2/recording?query={query}&fmt=json&limit=5',
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                recordings = data.get('recordings', [])
                
                if recordings:
                    recording = recordings[0]
                    track_info['mbid'] = recording.get('id', '')
                    track_info['length'] = recording.get('length')
                    
                    # Проверка на кавер
                    relations = recording.get('relations', [])
                    for relation in relations:
                        if relation.get('type') == 'cover of':
                            track_info['is_cover'] = True
                            work = relation.get('work', {})
                            if work:
                                track_info['original_title'] = work.get('title', title)
                                artist_relations = work.get('relations', [])
                                for artist_rel in artist_relations:
                                    if artist_rel.get('type') == 'composer':
                                        artist_obj = artist_rel.get('artist', {})
                                        track_info['original_artist'] = artist_obj.get('name')
                                        break
        except:
            pass
        
        # Получаем текст песни через Lyrics.ovh
        lyrics_info = get_lyrics(artist, title)
        if lyrics_info:
            track_info['lyrics_text'] = lyrics_info.get('lyrics')
            track_info['lyrics_url'] = lyrics_info.get('url')
        
        # Получаем информацию от Genius
        genius_info = get_genius_info(artist, title)
        if genius_info:
            track_info['genius_url'] = genius_info.get('url')
        
        # Получаем информацию от Last.fm
        lastfm_info = get_lastfm_info(artist, title)
        if lastfm_info:
            track_info['lastfm'] = lastfm_info
        
        # Получаем похожие треки от Last.fm
        similar_tracks = get_similar_tracks(artist, title)
        if similar_tracks:
            track_info['similar'] = similar_tracks
        
        # Сохраняем в кеш
        save_track_cache(
            artist, title,
            mbid=track_info.get('mbid'),
            length=track_info.get('length'),
            is_cover=track_info['is_cover'],
            original_title=track_info.get('original_title'),
            original_artist=track_info['original_artist'],
            lyrics_text=track_info['lyrics_text'],
            lyrics_url=track_info['lyrics_url'],
            genius_url=track_info['genius_url'],
            spotify_data=track_info['spotify'],
            lastfm_data=track_info['lastfm'],
            similar=track_info['similar']
        )
        
        return track_info
    except Exception as e:
        print(f"Error getting track info: {e}")
        return None

# ==Руты==

@app.route("/")
def index():
    db = get_db()
    tracks = db.execute('SELECT * FROM uploads').fetchall()
    return render_template('index.html', tracks=tracks)

@app.route('/api/track-info')
def track_info_api():
    """API endpoint для получения информации о треке"""
    artist = request.args.get('artist', '')
    title = request.args.get('title', '')
    
    if not artist or not title:
        return jsonify({'error': 'Missing artist or title'}), 400
    
    info = get_track_info(artist, title)
    
    if info:
        return jsonify(info)
    else:
        return jsonify({
            'title': title,
            'artist': artist,
            'is_cover': False,
            'error': 'Could not fetch additional information'
        })

@app.route('/api/recommendations')
def recommendations_api():
    """API endpoint для получения рекомендаций похожих песен"""
    artist = request.args.get('artist', '')
    title = request.args.get('title', '')
    
    if not artist or not title:
        return jsonify({'error': 'Missing artist or title'}), 400
    
    # Получаем похожие треки
    similar = get_similar_tracks(artist, title)
    
    if similar:
        return jsonify({'similar': similar, 'count': len(similar)})
    else:
        return jsonify({'similar': [], 'count': 0, 'error': 'Could not fetch recommendations'})

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