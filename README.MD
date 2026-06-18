```markdown
# SoundCloud Clone — Техническая документация

**Версия:** 1.0.0  
**Статус:** Прототип

---

## Обзор

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

**users**: id, username (UNIQUE), email (UNIQUE), password_hash (SHA-256), user_type (listener/musician), is_foreign_agent, registration_date, last_login.

**tracks**: id, title, artist_id (FK→users), file_path, genre, description, plays_count, upload_date.

**comments**: id, user_id (FK), track_id (FK), comment_text, comment_date.

**likes**: id, user_id, track_id, like_date. UNIQUE(user_id, track_id).

**communities**: id, name, description, creator_id (FK), members_count, creation_date.

**community_members**: id, community_id, user_id, join_date. UNIQUE(community_id, user_id).

**community_messages**: id, community_id, user_id, message_text, message_date.

---

## API

Все ответы в JSON. Аутентификация через `localStorage` (прототип).

**Аутентификация:**  
`POST /api/register` — `{username, email, password, user_type, is_foreign_agent}`  
`POST /api/login` — `{username, password}` → `{user}`

**Треки:**  
`GET /api/tracks` — `?search=&genre=` → список  
`GET /api/track/info/<id>` — детали  
`GET /api/track/<id>/comments` — комментарии  
`GET /api/track/<id>/likes` — `?user_id=` → количество + статус  
`POST /api/track/like` — `{user_id, track_id, action}`  
`POST /api/track/comment` — `{user_id, track_id, comment_text}`  
`POST /api/track/play` — `{track_id}` → +1 к счётчику  
`POST /api/upload` — multipart: audio, title, artist_id, genre, description (до 50 МБ, MP3/WAV/OGG)  
`GET /api/audio/<filename>` — стриминг

**Пользователи:**  
`GET /api/user/info/<id>`  
`GET /api/user/tracks/<id>`  
`GET /api/user/communities/<id>`

**Сообщества:**  
`GET /api/communities` — список  
`GET /api/community/info/<id>`  
`GET /api/community/members/<id>`  
`GET /api/community/messages/<id>` — `?limit=`  
`GET /api/community/check-membership/<cid>/<uid>`  
`POST /api/community/create` — `{name, description, creator_id}`  
`POST /api/community/join` — `{community_id, user_id}`  
`POST /api/community/leave` — `{community_id, user_id}`  
`POST /api/community/message` — `{community_id, user_id, message_text}`

---

## Запуск

```bash
cd server
python main.py
# → http://localhost:8000
```

Требования: Python 3.11+. Зависимости отсутствуют. База и папка uploads создаются автоматически. Хост и порт меняются в `run_server()`.

---

## Ограничения

Прототип, не для продакшена. Сессии без токенов (доверие к user_id). Пароли — SHA-256 без соли. CORS открыт всем. Чат — поллинг раз в 3 секунды вместо веб-сокетов. Поиск — LIKE без FTS. Нет пагинации, восстановления пароля, аватаров, UI плейлистов. Тесты отсутствуют.
```
