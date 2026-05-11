#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для добавления тестовых треков в приложение
Создает необходимые файлы для тестирования функционала
"""

import os
import sqlite3
from pathlib import Path

def add_test_tracks_to_db():
    """Добавляет тестовые треки в базу данных"""
    db = sqlite3.connect('database.db')
    db.row_factory = sqlite3.Row
    
    test_tracks = [
        {
            'name': 'Let It Be',
            'author': 'The Beatles',
            'uploadedby': 1,
            'audio_file': 'test_beatles.mp3',
            'cover_file': 'test_beatles.jpg'
        },
        {
            'name': 'Hello',
            'author': 'Adele',
            'uploadedby': 1,
            'audio_file': 'test_adele.mp3',
            'cover_file': 'test_adele.jpg'
        },
        {
            'name': 'Bohemian Rhapsody',
            'author': 'Queen',
            'uploadedby': 1,
            'audio_file': 'test_queen.mp3',
            'cover_file': 'test_queen.jpg'
        },
        {
            'name': 'Imagine',
            'author': 'John Lennon',
            'uploadedby': 1,
            'audio_file': 'test_lennon.mp3',
            'cover_file': 'test_lennon.jpg'
        },
        {
            'name': 'Shape of You',
            'author': 'Ed Sheeran',
            'uploadedby': 1,
            'audio_file': 'test_sheeran.mp3',
            'cover_file': 'test_sheeran.jpg'
        }
    ]
    
    try:
        for track in test_tracks:
            # Проверяем, существует ли трек
            existing = db.execute(
                'SELECT id FROM uploads WHERE name = ? AND author = ?',
                (track['name'], track['author'])
            ).fetchone()
            
            if not existing:
                db.execute(
                    'INSERT INTO uploads (name, author, uploadedby, audio_file, cover_file) VALUES (?, ?, ?, ?, ?)',
                    (track['name'], track['author'], track['uploadedby'], 
                     track['audio_file'], track['cover_file'])
                )
                print(f"OK: Added track: {track['name']} - {track['author']}")
            else:
                print(f"INFO: Track already exists: {track['name']} - {track['author']}")
        
        db.commit()
        print("\nOK: All test tracks added to database!")
    except Exception as e:
        print(f"ERROR: Failed to add tracks: {e}")
    finally:
        db.close()

def create_dummy_files():
    """Создает пустые dummy файлы для тестирования"""
    os.makedirs('uploads', exist_ok=True)
    
    # Создаем пустые файлы если их нет
    test_files = [
        'test_beatles.mp3',
        'test_beatles.jpg',
        'test_adele.mp3',
        'test_adele.jpg',
        'test_queen.mp3',
        'test_queen.jpg',
        'test_lennon.mp3',
        'test_lennon.jpg',
        'test_sheeran.mp3',
        'test_sheeran.jpg'
    ]
    
    for filename in test_files:
        filepath = os.path.join('uploads', filename)
        if not os.path.exists(filepath):
            # Создаем пустой файл
            with open(filepath, 'w') as f:
                f.write('')
            print(f"OK: Created dummy file: {filename}")
        else:
            print(f"INFO: File already exists: {filename}")

def main():
    """Главная функция"""
    print("=" * 60)
    print("  Adding test tracks")
    print("=" * 60 + "\n")
    
    print("Creating dummy files...")
    create_dummy_files()
    
    print("\nAdding tracks to database...")
    add_test_tracks_to_db()
    
    print("\n" + "=" * 60)
    print("  Done!")
    print("=" * 60)
    print("\nFor testing:")
    print("1. Run the app: python app.py")
    print("2. Click on a track card")
    print("3. Information should display correctly")
    print("4. On second click - information from cache\n")

if __name__ == '__main__':
    main()
