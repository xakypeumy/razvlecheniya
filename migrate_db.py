#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Миграция БД для добавления новых полей кеша
"""

import sqlite3
import os
import shutil

def migrate_database():
    """Обновляет схему БД с новыми полями кеша"""
    db_path = 'database.db'
    backup_path = 'database_backup.db'
    
    # Создаем резервную копию
    if os.path.exists(db_path):
        shutil.copy(db_path, backup_path)
        print(f"OK: Backup created: {backup_path}")
    
    db = sqlite3.connect(db_path)
    cursor = db.cursor()
    
    try:
        # Проверяем наличие новых полей
        cursor.execute("PRAGMA table_info(track_cache)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'mbid' not in columns:
            print("Migrating track_cache table...")
            
            # Переименовываем старую таблицу
            cursor.execute("ALTER TABLE track_cache RENAME TO track_cache_old")
            
            # Создаем новую таблицу с правильной схемой
            cursor.execute("""
                CREATE TABLE track_cache (
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
            
            # Копируем данные из старой таблицы
            cursor.execute("""
                INSERT INTO track_cache 
                (track_name, artist_name, genius_lyrics, genius_url, spotify_data, lastfm_data, similar_tracks, cached_at)
                SELECT track_name, artist_name, genius_lyrics, genius_url, spotify_data, lastfm_data, similar_tracks, cached_at
                FROM track_cache_old
            """)
            
            # Удаляем старую таблицу
            cursor.execute("DROP TABLE track_cache_old")
            
            db.commit()
            print("OK: Migration completed successfully!")
        else:
            print("INFO: Database schema is already up to date")
            if os.path.exists(backup_path):
                os.remove(backup_path)
    
    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        db.rollback()
        # Восстанавливаем из резервной копии
        if os.path.exists(backup_path):
            shutil.copy(backup_path, db_path)
            print("OK: Database restored from backup")
        return False
    finally:
        db.close()
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("  Database Migration")
    print("=" * 60 + "\n")
    
    if migrate_database():
        print("\n" + "=" * 60)
        print("  Done!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("  Failed!")
        print("=" * 60)
