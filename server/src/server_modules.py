import sqlite3
import json
import os
import hashlib
import uuid
from datetime import datetime
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                user_type TEXT NOT NULL CHECK(user_type IN ('listener', 'musician')),
                is_foreign_agent BOOLEAN DEFAULT 0,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Таблица песен/треков
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                duration REAL,
                genre TEXT,
                description TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                plays_count INTEGER DEFAULT 0,
                FOREIGN KEY (artist_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица плейлистов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_public BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица связи плейлистов и треков
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlist_tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_id INTEGER NOT NULL,
                track_id INTEGER NOT NULL,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (playlist_id) REFERENCES playlists (id),
                FOREIGN KEY (track_id) REFERENCES tracks (id)
            )
        ''')
        
        # Таблица лайков
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                track_id INTEGER NOT NULL,
                like_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (track_id) REFERENCES tracks (id),
                UNIQUE(user_id, track_id)
            )
        ''')
        
        # Таблица комментариев
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                track_id INTEGER NOT NULL,
                comment_text TEXT NOT NULL,
                comment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (track_id) REFERENCES tracks (id)
            )
        ''')
        
        # Таблица сообществ
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS communities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                creator_id INTEGER NOT NULL,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                members_count INTEGER DEFAULT 1,
                FOREIGN KEY (creator_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица участников сообществ
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS community_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                community_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (community_id) REFERENCES communities (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(community_id, user_id)
            )
        ''')
        
        # Таблица сообщений в чатах сообществ
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS community_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                community_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                message_text TEXT NOT NULL,
                message_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (community_id) REFERENCES communities (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Получение соединения с базой данных"""
        return sqlite3.connect(self.db_path)
    
    def register_user(self, username, email, password, user_type, is_foreign_agent):
        """Регистрация нового пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, user_type, is_foreign_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, user_type, is_foreign_agent))
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return True, user_id
        except sqlite3.IntegrityError:
            conn.close()
            return False, "Пользователь с таким именем или email уже существует"
        except Exception as e:
            conn.close()
            return False, str(e)
    
    def authenticate_user(self, username, password):
        """Аутентификация пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute('''
            SELECT id, username, email, user_type, is_foreign_agent
            FROM users
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        
        user = cursor.fetchone()
        
        if user:
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (user[0],))
            conn.commit()
            
            user_data = {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'user_type': user[3],
                'is_foreign_agent': bool(user[4])
            }
            conn.close()
            return True, user_data
        else:
            conn.close()
            return False, "Неверное имя пользователя или пароль"
    
    def get_user_info(self, user_id):
        """Получение информации о пользователе"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, user_type, is_foreign_agent, registration_date
            FROM users WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'user_type': user[3],
                'is_foreign_agent': bool(user[4]),
                'registration_date': user[5]
            }
        return None
    
    def upload_track(self, title, artist_id, file_path, genre=None, description=None):
        """Загрузка нового трека"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tracks (title, artist_id, file_path, genre, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, artist_id, file_path, genre, description))
        
        conn.commit()
        track_id = cursor.lastrowid
        conn.close()
        
        return track_id
    
    def get_track_info(self, track_id):
        """Получение информации о конкретном треке"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.id, t.title, u.username, u.id as artist_id, t.genre, 
                   t.description, t.plays_count, t.upload_date, t.file_path
            FROM tracks t
            JOIN users u ON t.artist_id = u.id
            WHERE t.id = ?
        ''', (track_id,))
        
        track = cursor.fetchone()
        conn.close()
        
        if track:
            return {
                'id': track[0],
                'title': track[1],
                'artist': track[2],
                'artist_id': track[3],
                'genre': track[4],
                'description': track[5],
                'plays_count': track[6],
                'upload_date': track[7],
                'file_path': track[8]
            }
        return None
    
    def get_all_tracks(self, search_query=None, genre=None):
        """Получение всех треков с возможностью поиска и фильтрации"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT t.id, t.title, u.username as artist, t.genre, t.description, 
                   t.plays_count, t.upload_date, t.file_path
            FROM tracks t
            JOIN users u ON t.artist_id = u.id
            WHERE 1=1
        '''
        params = []
        
        if search_query:
            query += ' AND (t.title LIKE ? OR u.username LIKE ?)'
            params.extend([f'%{search_query}%', f'%{search_query}%'])
        
        if genre:
            query += ' AND t.genre = ?'
            params.append(genre)
        
        query += ' ORDER BY t.upload_date DESC'
        
        cursor.execute(query, params)
        tracks = cursor.fetchall()
        conn.close()
        
        return [{
            'id': track[0],
            'title': track[1],
            'artist': track[2],
            'genre': track[3],
            'description': track[4],
            'plays_count': track[5],
            'upload_date': track[6],
            'file_path': track[7]
        } for track in tracks]
    
    def get_user_tracks(self, user_id):
        """Получение треков конкретного пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.id, t.title, t.genre, t.description, t.plays_count, t.upload_date, t.file_path
            FROM tracks t
            WHERE t.artist_id = ?
            ORDER BY t.upload_date DESC
        ''', (user_id,))
        
        tracks = cursor.fetchall()
        conn.close()
        
        return [{
            'id': track[0],
            'title': track[1],
            'genre': track[2],
            'description': track[3],
            'plays_count': track[4],
            'upload_date': track[5],
            'file_path': track[6]
        } for track in tracks]
    
    def increment_play_count(self, track_id):
        """Увеличение счетчика прослушиваний"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tracks SET plays_count = plays_count + 1 WHERE id = ?
        ''', (track_id,))
        
        conn.commit()
        conn.close()
    
    def like_track(self, user_id, track_id):
        """Лайкнуть трек"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO likes (user_id, track_id) VALUES (?, ?)
            ''', (user_id, track_id))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def unlike_track(self, user_id, track_id):
        """Убрать лайк с трека"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM likes WHERE user_id = ? AND track_id = ?
        ''', (user_id, track_id))
        
        conn.commit()
        conn.close()
    
    def is_liked_by_user(self, user_id, track_id):
        """Проверка, лайкнул ли пользователь трек"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM likes WHERE user_id = ? AND track_id = ?
        ''', (user_id, track_id))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def get_track_likes_count(self, track_id):
        """Получение количества лайков трека"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM likes WHERE track_id = ?', (track_id,))
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def add_comment(self, user_id, track_id, comment_text):
        """Добавление комментария к треку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO comments (user_id, track_id, comment_text)
            VALUES (?, ?, ?)
        ''', (user_id, track_id, comment_text))
        
        conn.commit()
        comment_id = cursor.lastrowid
        conn.close()
        
        return comment_id
    
    def get_track_comments(self, track_id):
        """Получение комментариев к треку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.id, u.username, u.id as user_id, c.comment_text, c.comment_date
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.track_id = ?
            ORDER BY c.comment_date DESC
        ''', (track_id,))
        
        comments = cursor.fetchall()
        conn.close()
        
        return [{
            'id': comment[0],
            'username': comment[1],
            'user_id': comment[2],
            'text': comment[3],
            'date': comment[4]
        } for comment in comments]
    
    def create_playlist(self, name, user_id, is_public=True):
        """Создание плейлиста"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO playlists (name, user_id, is_public) VALUES (?, ?, ?)
        ''', (name, user_id, is_public))
        
        conn.commit()
        playlist_id = cursor.lastrowid
        conn.close()
        
        return playlist_id
    
    def add_track_to_playlist(self, playlist_id, track_id):
        """Добавление трека в плейлист"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO playlist_tracks (playlist_id, track_id) VALUES (?, ?)
        ''', (playlist_id, track_id))
        
        conn.commit()
        conn.close()
    
    def get_user_playlists(self, user_id):
        """Получение плейлистов пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, creation_date, is_public
            FROM playlists
            WHERE user_id = ?
            ORDER BY creation_date DESC
        ''', (user_id,))
        
        playlists = cursor.fetchall()
        conn.close()
        
        return [{
            'id': pl[0],
            'name': pl[1],
            'creation_date': pl[2],
            'is_public': bool(pl[3])
        } for pl in playlists]
    
    # Методы для работы с сообществами
    
    def create_community(self, name, description, creator_id):
        """Создание нового сообщества"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO communities (name, description, creator_id)
            VALUES (?, ?, ?)
        ''', (name, description, creator_id))
        
        community_id = cursor.lastrowid
        
        # Автоматически добавляем создателя как участника
        cursor.execute('''
            INSERT INTO community_members (community_id, user_id)
            VALUES (?, ?)
        ''', (community_id, creator_id))
        
        conn.commit()
        conn.close()
        
        return community_id
    
    def get_all_communities(self):
        """Получение всех сообществ"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.id, c.name, c.description, u.username, c.creator_id, 
                   c.creation_date, c.members_count
            FROM communities c
            JOIN users u ON c.creator_id = u.id
            ORDER BY c.creation_date DESC
        ''')
        
        communities = cursor.fetchall()
        conn.close()
        
        return [{
            'id': c[0],
            'name': c[1],
            'description': c[2],
            'creator_name': c[3],
            'creator_id': c[4],
            'creation_date': c[5],
            'members_count': c[6]
        } for c in communities]
    
    def get_community_info(self, community_id):
        """Получение информации о сообществе"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.id, c.name, c.description, u.username, c.creator_id, 
                   c.creation_date, c.members_count
            FROM communities c
            JOIN users u ON c.creator_id = u.id
            WHERE c.id = ?
        ''', (community_id,))
        
        community = cursor.fetchone()
        conn.close()
        
        if community:
            return {
                'id': community[0],
                'name': community[1],
                'description': community[2],
                'creator_name': community[3],
                'creator_id': community[4],
                'creation_date': community[5],
                'members_count': community[6]
            }
        return None
    
    def join_community(self, community_id, user_id):
        """Вступление в сообщество"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO community_members (community_id, user_id)
                VALUES (?, ?)
            ''', (community_id, user_id))
            
            # Обновляем счетчик участников
            cursor.execute('''
                UPDATE communities SET members_count = members_count + 1
                WHERE id = ?
            ''', (community_id,))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def leave_community(self, community_id, user_id):
        """Выход из сообщества"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM community_members 
            WHERE community_id = ? AND user_id = ?
        ''', (community_id, user_id))
        
        # Обновляем счетчик участников
        cursor.execute('''
            UPDATE communities SET members_count = members_count - 1
            WHERE id = ?
        ''', (community_id,))
        
        conn.commit()
        conn.close()
    
    def is_member_of_community(self, community_id, user_id):
        """Проверка, является ли пользователь участником сообщества"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM community_members 
            WHERE community_id = ? AND user_id = ?
        ''', (community_id, user_id))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def get_user_communities(self, user_id):
        """Получение сообществ пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.id, c.name, c.description, c.members_count
            FROM communities c
            JOIN community_members cm ON c.id = cm.community_id
            WHERE cm.user_id = ?
            ORDER BY c.creation_date DESC
        ''', (user_id,))
        
        communities = cursor.fetchall()
        conn.close()
        
        return [{
            'id': c[0],
            'name': c[1],
            'description': c[2],
            'members_count': c[3]
        } for c in communities]
    
    def get_community_members(self, community_id):
        """Получение участников сообщества"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.username, u.user_type, cm.join_date
            FROM users u
            JOIN community_members cm ON u.id = cm.user_id
            WHERE cm.community_id = ?
            ORDER BY cm.join_date
        ''', (community_id,))
        
        members = cursor.fetchall()
        conn.close()
        
        return [{
            'id': m[0],
            'username': m[1],
            'user_type': m[2],
            'join_date': m[3]
        } for m in members]
    
    def send_community_message(self, community_id, user_id, message_text):
        """Отправка сообщения в чат сообщества"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO community_messages (community_id, user_id, message_text)
            VALUES (?, ?, ?)
        ''', (community_id, user_id, message_text))
        
        conn.commit()
        message_id = cursor.lastrowid
        conn.close()
        
        return message_id
    
    def get_community_messages(self, community_id, limit=50):
        """Получение сообщений чата сообщества"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.id, u.username, u.id as user_id, m.message_text, m.message_date
            FROM community_messages m
            JOIN users u ON m.user_id = u.id
            WHERE m.community_id = ?
            ORDER BY m.message_date DESC
            LIMIT ?
        ''', (community_id, limit))
        
        messages = cursor.fetchall()
        conn.close()
        
        # Возвращаем в обратном порядке (старые сверху)
        return [{
            'id': m[0],
            'username': m[1],
            'user_id': m[2],
            'text': m[3],
            'date': m[4]
        } for m in reversed(messages)]
