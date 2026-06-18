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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                cover_path TEXT,
                duration REAL,
                genre TEXT,
                description TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                plays_count INTEGER DEFAULT 0,
                FOREIGN KEY (artist_id) REFERENCES users (id)
            )
        ''')
        
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
        return sqlite3.connect(self.db_path)
    
    def register_user(self, username, email, password, user_type, is_foreign_agent):
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
    
    def upload_track(self, title, artist_id, file_path, genre=None, description=None, cover_path=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tracks (title, artist_id, file_path, genre, description, cover_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, artist_id, file_path, genre, description, cover_path))
        
        conn.commit()
        track_id = cursor.lastrowid
        conn.close()
        
        return track_id
    
    def delete_track(self, track_id, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT file_path, cover_path FROM tracks WHERE id = ? AND artist_id = ?', (track_id, user_id))
        track = cursor.fetchone()
        
        if not track:
            conn.close()
            return False, "Трек не найден или у вас нет прав"
        
        cursor.execute('DELETE FROM comments WHERE track_id = ?', (track_id,))
        cursor.execute('DELETE FROM likes WHERE track_id = ?', (track_id,))
        cursor.execute('DELETE FROM playlist_tracks WHERE track_id = ?', (track_id,))
        cursor.execute('DELETE FROM tracks WHERE id = ?', (track_id,))
        
        conn.commit()
        conn.close()
        
        return True, "Трек удален"
    
    def get_track_info(self, track_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.id, t.title, u.username, u.id as artist_id, t.genre, 
                   t.description, t.plays_count, t.upload_date, t.file_path, t.cover_path
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
                'file_path': track[8],
                'cover_path': track[9]
            }
        return None
    
    def get_all_tracks(self, search_query=None, genre=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT t.id, t.title, u.username as artist, u.id as artist_id, t.genre, t.description, 
                   t.plays_count, t.upload_date, t.file_path, t.cover_path
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
            'artist_id': track[3],
            'genre': track[4],
            'description': track[5],
            'plays_count': track[6],
            'upload_date': track[7],
            'file_path': track[8],
            'cover_path': track[9]
        } for track in tracks]
    
    def get_user_tracks(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.id, t.title, u.username as artist, u.id as artist_id, t.genre, t.description, 
                   t.plays_count, t.upload_date, t.file_path, t.cover_path
            FROM tracks t
            JOIN users u ON t.artist_id = u.id
            WHERE t.artist_id = ?
            ORDER BY t.upload_date DESC
        ''', (user_id,))
        
        tracks = cursor.fetchall()
        conn.close()
        
        return [{
            'id': track[0],
            'title': track[1],
            'artist': track[2],
            'artist_id': track[3],
            'genre': track[4],
            'description': track[5],
            'plays_count': track[6],
            'upload_date': track[7],
            'file_path': track[8],
            'cover_path': track[9]
        } for track in tracks]
    
    def increment_play_count(self, track_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tracks SET plays_count = plays_count + 1 WHERE id = ?
        ''', (track_id,))
        
        conn.commit()
        conn.close()
    
    def like_track(self, user_id, track_id):
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
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM likes WHERE user_id = ? AND track_id = ?
        ''', (user_id, track_id))
        
        conn.commit()
        conn.close()
    
    def is_liked_by_user(self, user_id, track_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM likes WHERE user_id = ? AND track_id = ?
        ''', (user_id, track_id))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def get_track_likes_count(self, track_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM likes WHERE track_id = ?', (track_id,))
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def add_comment(self, user_id, track_id, comment_text):
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
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO playlist_tracks (playlist_id, track_id) VALUES (?, ?)
        ''', (playlist_id, track_id))
        
        conn.commit()
        conn.close()
    
    def get_user_playlists(self, user_id):
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
    
    def create_community(self, name, description, creator_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO communities (name, description, creator_id)
            VALUES (?, ?, ?)
        ''', (name, description, creator_id))
        
        community_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO community_members (community_id, user_id)
            VALUES (?, ?)
        ''', (community_id, creator_id))
        
        conn.commit()
        conn.close()
        
        return community_id
    
    def get_all_communities(self):
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
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO community_members (community_id, user_id)
                VALUES (?, ?)
            ''', (community_id, user_id))
            
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
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM community_members 
            WHERE community_id = ? AND user_id = ?
        ''', (community_id, user_id))
        
        cursor.execute('''
            UPDATE communities SET members_count = members_count - 1
            WHERE id = ?
        ''', (community_id,))
        
        conn.commit()
        conn.close()
    
    def is_member_of_community(self, community_id, user_id):
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
        
        return [{
            'id': m[0],
            'username': m[1],
            'user_id': m[2],
            'text': m[3],
            'date': m[4]
        } for m in reversed(messages)]
