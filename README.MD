```markdown
# SoundScape

Полнофункциональная музыкальная платформа на стандартной библиотеке Python. Сервер на `http.server`, база SQLite, фронт на ванильном JS. Никаких фреймворков и внешних зависимостей.

Возможности: регистрация с ролями (слушатель/музыкант/иноагент), загрузка и стриминг треков, комментарии, лайки, сообщества с чатами, поиск, аудиоплеер.

---

## Структура проекта

```
├── client/
│   ├── pages/          # HTML: index, login, register, profile, track, upload, search, communities, community
│   └── src/            # JS: chat.js (общее), auth.js, player.js, upload.js
├── server/
│   ├── local_data/     # database.db + uploads/
│   ├── main.py         # HTTP-сервер, роутинг, CORS
│   └── src/
│       └── server_modules.py  # DatabaseManager
└── README.MD
```

---

## База данных

SQLite, файл `server/local_data/database.db`, создаётся автоматически.

### users
- `id`, `username` (UNIQUE), `email` (UNIQUE), `password_hash` (SHA-256)
- `user_type` (listener / musician), `is_foreign_agent` (BOOL)
- `registration_date`, `last_login`

### tracks
- `id`, `title`, `artist_id` (FK → users), `file_path`
- `genre`, `description`, `plays_count`, `upload_date`

### comments
- `id`, `user_id` (FK), `track_id` (FK), `comment_text`, `comment_date`

### likes
- `id`, `user_id` (FK), `track_id` (FK), `like_date`
- UNIQUE(user_id, track_id)

### communities
- `id`, `name`, `description`, `creator_id` (FK), `members_count`, `creation_date`

### community_members
- `id`, `community_id` (FK), `user_id` (FK), `join_date`
- UNIQUE(community_id, user_id)

### community_messages
- `id`, `community_id` (FK), `user_id` (FK), `message_text`, `message_date`

---

## API

Все ответы в JSON. Аутентификация через `localStorage` (прототип).

### Аутентификация
| Метод | Эндпоинт | Тело запроса |
|-------|----------|-------------|
| POST | `/api/register` | `username, email, password, user_type, is_foreign_agent` |
| POST | `/api/login` | `username, password` → `{user}` |

### Треки
| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/api/tracks?search=&genre=` | Список треков |
| GET | `/api/track/info/<id>` | Детали трека |
| GET | `/api/track/<id>/comments` | Комментарии |
| GET | `/api/track/<id>/likes?user_id=` | Лайки + статус |
| POST | `/api/track/like` | `{user_id, track_id, action}` |
| POST | `/api/track/comment` | `{user_id, track_id, comment_text}` |
| POST | `/api/track/play` | `{track_id}` (счётчик) |
| POST | `/api/upload` | multipart: audio, title, artist_id, genre, description |
| GET | `/api/audio/<filename>` | Стриминг аудио |

Ограничения загрузки: MP3, WAV, OGG до 50 МБ.

### Пользователи
| Метод | Эндпоинт |
|-------|----------|
| GET | `/api/user/info/<id>` |
| GET | `/api/user/tracks/<id>` |
| GET | `/api/user/communities/<id>` |

### Сообщества
| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/api/communities` | Список |
| GET | `/api/community/info/<id>` | Информация |
| GET | `/api/community/members/<id>` | Участники |
| GET | `/api/community/messages/<id>?limit=` | Чат |
| GET | `/api/community/check-membership/<cid>/<uid>` | Проверка |
| POST | `/api/community/create` | `{name, description, creator_id}` |
| POST | `/api/community/join` | `{community_id, user_id}` |
| POST | `/api/community/leave` | `{community_id, user_id}` |
| POST | `/api/community/message` | `{community_id, user_id, message_text}` |

---

## Запуск

```bash
cd server
python main.py
```

Сервер запустится на `http://localhost:8000`.

**Требования:** Python 3.11+. Зависимости отсутствуют. База данных и папка для загрузок создаются автоматически при первом запуске. Хост и порт настраиваются в функции `run_server()`.

---

## Ограничения

Прототип, не предназначен для продакшена:

- **Безопасность:** сессии без токенов, пароли SHA-256 без соли, CORS открыт
- **Производительность:** чат через поллинг (3 сек), поиск через LIKE, нет пагинации
- **Функциональность:** нет восстановления пароля, аватаров, UI плейлистов
- **Надёжность:** нет тестов, нет миграций БД
```
