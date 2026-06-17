from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import uuid
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from src.server_modules import DatabaseManager
from datetime import datetime

# Настройка путей
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / 'server' / 'local_data' / 'database.db'
UPLOAD_DIR = BASE_DIR / 'server' / 'local_data' / 'uploads'
CLIENT_DIR = BASE_DIR / 'client'

# Создание необходимых директорий
os.makedirs(DB_PATH.parent, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Инициализация базы данных
db = DatabaseManager(str(DB_PATH))

class MusicPlatformHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Обработка GET запросов"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        # API endpoints
        if path.startswith('/api/'):
            self.handle_api_get(path, query_params)
        else:
            # Статические файлы
            self.serve_static_file(path)
    
    def do_POST(self):
        """Обработка POST запросов"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path.startswith('/api/'):
            content_type = self.headers.get('Content-Type', '')
            
            if 'multipart/form-data' in content_type:
                self.handle_file_upload(path)
            else:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length > 0 else b'{}'
                try:
                    data = json.loads(body.decode('utf-8'))
                except:
                    data = {}
                self.handle_api_post(path, data)
        else:
            self.send_error(404)
    
    def serve_static_file(self, path):
        """Отдача статических файлов"""
        if path == '/' or path == '':
            path = '/pages/index.html'
        
        # Безопасность: предотвращаем выход за пределы директории
        safe_path = CLIENT_DIR / path.lstrip('/')
        
        try:
            safe_path = safe_path.resolve()
            if not str(safe_path).startswith(str(CLIENT_DIR.resolve())):
                raise Exception("Access denied")
            
            if safe_path.exists() and safe_path.is_file():
                content_type = self.get_content_type(str(safe_path))
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                with open(safe_path, 'rb') as file:
                    self.wfile.write(file.read())
            else:
                self.send_error(404)
        except Exception as e:
            self.send_error(500, str(e))
    
    def get_content_type(self, filepath):
        """Определение типа контента"""
        ext = Path(filepath).suffix.lower()
        content_types = {
            '.html': 'text/html; charset=utf-8',
            '.js': 'application/javascript',
            '.css': 'text/css',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def handle_api_get(self, path, query_params):
        """Обработка GET API запросов"""
        if path == '/api/tracks':
            search = query_params.get('search', [None])[0]
            genre = query_params.get('genre', [None])[0]
            tracks = db.get_all_tracks(search, genre)
            self.send_json_response(tracks)
        
        elif path.startswith('/api/track/info/'):
            try:
                track_id = int(path.split('/')[-1])
                track = db.get_track_info(track_id)
                if track:
                    self.send_json_response(track)
                else:
                    self.send_error(404, "Track not found")
            except:
                self.send_error(400, "Invalid track ID")
        
        elif path.startswith('/api/user/tracks/'):
            try:
                user_id = int(path.split('/')[-1])
                tracks = db.get_user_tracks(user_id)
                self.send_json_response(tracks)
            except:
                self.send_error(400, "Invalid user ID")
        
        elif path.startswith('/api/user/info/'):
            try:
                user_id = int(path.split('/')[-1])
                user_info = db.get_user_info(user_id)
                if user_info:
                    self.send_json_response(user_info)
                else:
                    self.send_error(404, "User not found")
            except:
                self.send_error(400, "Invalid user ID")
        
        elif path == '/api/playlists':
            user_id = query_params.get('user_id', [None])[0]
            if user_id:
                playlists = db.get_user_playlists(int(user_id))
                self.send_json_response(playlists)
            else:
                self.send_error(400, "User ID required")
        
        elif path.startswith('/api/track/'):
            parts = path.split('/')
            if len(parts) >= 4:
                track_id = int(parts[3])
                if 'comments' in parts:
                    comments = db.get_track_comments(track_id)
                    self.send_json_response(comments)
                elif 'likes' in parts:
                    likes_count = db.get_track_likes_count(track_id)
                    user_id = query_params.get('user_id', [None])[0]
                    is_liked = False
                    if user_id:
                        is_liked = db.is_liked_by_user(int(user_id), track_id)
                    self.send_json_response({
                        'likes': likes_count,
                        'is_liked': is_liked
                    })
                else:
                    self.send_error(404)
            else:
                self.send_error(400)
        
        elif path.startswith('/api/audio/'):
            filename = path.split('/')[-1]
            file_path = UPLOAD_DIR / filename
            
            if file_path.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'audio/mpeg')
                self.send_header('Content-Length', str(file_path.stat().st_size))
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Audio file not found")
        
        # API для сообществ
        elif path == '/api/communities':
            communities = db.get_all_communities()
            self.send_json_response(communities)
        
        elif path.startswith('/api/community/info/'):
            try:
                community_id = int(path.split('/')[-1])
                community = db.get_community_info(community_id)
                if community:
                    self.send_json_response(community)
                else:
                    self.send_error(404, "Community not found")
            except:
                self.send_error(400, "Invalid community ID")
        
        elif path.startswith('/api/community/members/'):
            try:
                community_id = int(path.split('/')[-1])
                members = db.get_community_members(community_id)
                self.send_json_response(members)
            except:
                self.send_error(400, "Invalid community ID")
        
        elif path.startswith('/api/community/messages/'):
            try:
                community_id = int(path.split('/')[-1])
                limit = query_params.get('limit', [50])[0]
                messages = db.get_community_messages(community_id, int(limit))
                self.send_json_response(messages)
            except:
                self.send_error(400, "Invalid community ID")
        
        elif path.startswith('/api/user/communities/'):
            try:
                user_id = int(path.split('/')[-1])
                communities = db.get_user_communities(user_id)
                self.send_json_response(communities)
            except:
                self.send_error(400, "Invalid user ID")
        
        elif path.startswith('/api/community/check-membership/'):
            parts = path.split('/')
            if len(parts) >= 5:
                community_id = int(parts[4])
                user_id = int(parts[5])
                is_member = db.is_member_of_community(community_id, user_id)
                self.send_json_response({'is_member': is_member})
            else:
                self.send_error(400)
        
        else:
            self.send_error(404)
    
    def handle_api_post(self, path, data):
        """Обработка POST API запросов"""
        if path == '/api/register':
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            user_type = data.get('user_type', 'listener')
            is_foreign_agent = data.get('is_foreign_agent', False)
            
            if not all([username, email, password]):
                self.send_json_response({'success': False, 'error': 'Все поля обязательны'}, 400)
                return
            
            if user_type not in ['listener', 'musician']:
                self.send_json_response({'success': False, 'error': 'Неверный тип пользователя'}, 400)
                return
            
            success, result = db.register_user(username, email, password, user_type, is_foreign_agent)
            
            if success:
                self.send_json_response({
                    'success': True,
                    'user_id': result,
                    'message': 'Регистрация успешна'
                })
            else:
                self.send_json_response({'success': False, 'error': str(result)}, 400)
        
        elif path == '/api/login':
            username = data.get('username')
            password = data.get('password')
            
            if not all([username, password]):
                self.send_json_response({'success': False, 'error': 'Все поля обязательны'}, 400)
                return
            
            success, result = db.authenticate_user(username, password)
            
            if success:
                self.send_json_response({
                    'success': True,
                    'user': result,
                    'message': 'Вход выполнен успешно'
                })
            else:
                self.send_json_response({'success': False, 'error': result}, 401)
        
        elif path == '/api/track/like':
            user_id = data.get('user_id')
            track_id = data.get('track_id')
            action = data.get('action', 'like')
            
            if not all([user_id, track_id]):
                self.send_json_response({'success': False, 'error': 'Требуются user_id и track_id'}, 400)
                return
            
            if action == 'like':
                success = db.like_track(user_id, track_id)
            else:
                db.unlike_track(user_id, track_id)
                success = True
            
            likes_count = db.get_track_likes_count(track_id)
            is_liked = db.is_liked_by_user(user_id, track_id)
            self.send_json_response({
                'success': success, 
                'likes': likes_count,
                'is_liked': is_liked
            })
        
        elif path == '/api/track/comment':
            user_id = data.get('user_id')
            track_id = data.get('track_id')
            comment_text = data.get('comment_text')
            
            if not all([user_id, track_id, comment_text]):
                self.send_json_response({'success': False, 'error': 'Требуются все поля'}, 400)
                return
            
            comment_id = db.add_comment(user_id, track_id, comment_text)
            self.send_json_response({'success': True, 'comment_id': comment_id})
        
        elif path == '/api/track/play':
            track_id = data.get('track_id')
            if track_id:
                db.increment_play_count(track_id)
                self.send_json_response({'success': True})
            else:
                self.send_json_response({'success': False, 'error': 'Track ID required'}, 400)
        
        elif path == '/api/playlist/create':
            name = data.get('name')
            user_id = data.get('user_id')
            is_public = data.get('is_public', True)
            
            if not all([name, user_id]):
                self.send_json_response({'success': False, 'error': 'Требуются name и user_id'}, 400)
                return
            
            playlist_id = db.create_playlist(name, user_id, is_public)
            self.send_json_response({'success': True, 'playlist_id': playlist_id})
        
        elif path == '/api/playlist/add-track':
            playlist_id = data.get('playlist_id')
            track_id = data.get('track_id')
            
            if not all([playlist_id, track_id]):
                self.send_json_response({'success': False, 'error': 'Требуются playlist_id и track_id'}, 400)
                return
            
            db.add_track_to_playlist(playlist_id, track_id)
            self.send_json_response({'success': True})
        
        # API для сообществ
        elif path == '/api/community/create':
            name = data.get('name')
            description = data.get('description', '')
            creator_id = data.get('creator_id')
            
            if not all([name, creator_id]):
                self.send_json_response({'success': False, 'error': 'Требуются name и creator_id'}, 400)
                return
            
            community_id = db.create_community(name, description, creator_id)
            self.send_json_response({
                'success': True,
                'community_id': community_id,
                'message': 'Сообщество создано'
            })
        
        elif path == '/api/community/join':
            community_id = data.get('community_id')
            user_id = data.get('user_id')
            
            if not all([community_id, user_id]):
                self.send_json_response({'success': False, 'error': 'Требуются community_id и user_id'}, 400)
                return
            
            success = db.join_community(community_id, user_id)
            self.send_json_response({
                'success': success,
                'message': 'Вы вступили в сообщество' if success else 'Вы уже участник'
            })
        
        elif path == '/api/community/leave':
            community_id = data.get('community_id')
            user_id = data.get('user_id')
            
            if not all([community_id, user_id]):
                self.send_json_response({'success': False, 'error': 'Требуются community_id и user_id'}, 400)
                return
            
            db.leave_community(community_id, user_id)
            self.send_json_response({
                'success': True,
                'message': 'Вы вышли из сообщества'
            })
        
        elif path == '/api/community/message':
            community_id = data.get('community_id')
            user_id = data.get('user_id')
            message_text = data.get('message_text')
            
            if not all([community_id, user_id, message_text]):
                self.send_json_response({'success': False, 'error': 'Требуются все поля'}, 400)
                return
            
            message_id = db.send_community_message(community_id, user_id, message_text)
            self.send_json_response({
                'success': True,
                'message_id': message_id
            })
        
        else:
            self.send_error(404)
    
    def handle_file_upload(self, path):
        """Обработка загрузки файлов (без использования cgi)"""
        if path == '/api/upload':
            try:
                content_type = self.headers.get('Content-Type')
                content_length = int(self.headers.get('Content-Length', 0))
                
                body = self.rfile.read(content_length)
                boundary = content_type.split('boundary=')[1].encode()
                form_data = self.parse_multipart(body, boundary)
                
                audio_data = None
                audio_filename = None
                title = 'Unknown Track'
                artist_id = None
                genre = 'Other'
                description = ''
                
                for field_name, field_value in form_data.items():
                    if field_name == 'audio':
                        audio_data = field_value['content']
                        audio_filename = field_value['filename']
                    elif field_name == 'title':
                        title = field_value.decode('utf-8') if isinstance(field_value, bytes) else field_value
                    elif field_name == 'artist_id':
                        artist_id = field_value.decode('utf-8') if isinstance(field_value, bytes) else field_value
                    elif field_name == 'genre':
                        genre = field_value.decode('utf-8') if isinstance(field_value, bytes) else field_value
                    elif field_name == 'description':
                        description = field_value.decode('utf-8') if isinstance(field_value, bytes) else field_value
                
                if not audio_data or not artist_id:
                    self.send_json_response({'success': False, 'error': 'Требуются файл и ID исполнителя'}, 400)
                    return
                
                file_ext = Path(audio_filename).suffix.lower() if audio_filename else '.mp3'
                if file_ext not in ['.mp3', '.wav', '.ogg']:
                    self.send_json_response({'success': False, 'error': 'Неподдерживаемый формат файла'}, 400)
                    return
                
                unique_filename = f"{uuid.uuid4()}{file_ext}"
                file_path = UPLOAD_DIR / unique_filename
                
                with open(file_path, 'wb') as f:
                    f.write(audio_data)
                
                track_id = db.upload_track(
                    title=title,
                    artist_id=int(artist_id),
                    file_path=f"/api/audio/{unique_filename}",
                    genre=genre,
                    description=description
                )
                
                self.send_json_response({
                    'success': True,
                    'track_id': track_id,
                    'message': 'Трек успешно загружен'
                })
                
            except Exception as e:
                self.send_json_response({'success': False, 'error': str(e)}, 500)
        else:
            self.send_error(404)
    
    def parse_multipart(self, body, boundary):
        """Парсинг multipart/form-data вручную"""
        fields = {}
        boundary = b'--' + boundary
        parts = body.split(boundary)
        
        for part in parts:
            if not part or part == b'--\r\n' or part == b'--':
                continue
            
            part = part.lstrip(b'\r\n').rstrip(b'\r\n')
            
            if not part:
                continue
            
            try:
                headers_end = part.index(b'\r\n\r\n')
                headers_section = part[:headers_end].decode('utf-8')
                content = part[headers_end + 4:]
            except:
                continue
            
            headers = {}
            for line in headers_section.split('\r\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()
            
            disposition = headers.get('content-disposition', '')
            
            if 'name="' in disposition:
                name_start = disposition.index('name="') + 6
                name_end = disposition.index('"', name_start)
                field_name = disposition[name_start:name_end]
                
                if 'filename="' in disposition:
                    filename_start = disposition.index('filename="') + 10
                    filename_end = disposition.index('"', filename_start)
                    filename = disposition[filename_start:filename_end]
                    
                    fields[field_name] = {
                        'filename': filename,
                        'content': content
                    }
                else:
                    fields[field_name] = content
        
        return fields
    
    def send_json_response(self, data, status_code=200):
        """Отправка JSON ответа"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Обработка CORS preflight запросов"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Кастомное логирование"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {self.client_address[0]} - {args[0]}")

def run_server(host='localhost', port=8000):
    """Запуск сервера"""
    server = HTTPServer((host, port), MusicPlatformHandler)
    print(f"=== SoundCloud Clone Server ===")
    print(f"Сервер запущен на http://{host}:{port}")
    print(f"Для остановки нажмите Ctrl+C")
    print(f"Версия Python: {os.sys.version}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен")
        server.shutdown()

if __name__ == '__main__':
    run_server()
