#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для очистки кеша треков
Используйте, если хотите обновить кешированные данные (например, после добавления lyrics)
"""

import sqlite3
import os

def clear_cache():
    """Очистка всего кеша треков"""
    db_path = 'database.db'
    if not os.path.exists(db_path):
        print("База данных не найдена!")
        return

    db = sqlite3.connect(db_path)
    try:
        # Показать сколько записей будет удалено
        count = db.execute('SELECT COUNT(*) FROM track_cache').fetchone()[0]
        print(f"Найдено {count} кешированных треков")

        if count > 0:
            # Очистить кеш
            db.execute('DELETE FROM track_cache')
            db.commit()
            print(f"✅ Очищено {count} записей из кеша")
            print("Теперь при следующем запросе данные загрузятся заново")
        else:
            print("Кеш уже пуст")

    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        db.close()

def clear_specific_track(artist, title):
    """Очистка кеша для конкретного трека"""
    db = sqlite3.connect('database.db')
    try:
        result = db.execute(
            'DELETE FROM track_cache WHERE artist_name = ? AND track_name = ?',
            (artist, title)
        )
        if result.rowcount > 0:
            db.commit()
            print(f"✅ Очищен кеш для {artist} - {title}")
        else:
            print(f"Трек {artist} - {title} не найден в кеше")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    print("Очистка кеша треков")
    print("=" * 30)

    choice = input("Выберите действие:\n1. Очистить весь кеш\n2. Очистить кеш для конкретного трека\nВаш выбор: ")

    if choice == '1':
        clear_cache()
    elif choice == '2':
        artist = input("Исполнитель: ")
        title = input("Название трека: ")
        clear_specific_track(artist, title)
    else:
        print("Неверный выбор")

    print("\nГотово!")