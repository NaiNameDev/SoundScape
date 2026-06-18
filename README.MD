# SoundScape — Техническая документация

## Общее описание

SoundScape представляет собой клон SoundCloud, реализованный на чистом Python без использования внешних фреймворков. Серверная часть построена на модуле `http.server` из стандартной библиотеки, в качестве системы управления базами данных используется SQLite, клиентская часть разработана на ванильном JavaScript. Проект сознательно избегает применения React, Django и прочих сторонних зависимостей, поскольку вся функциональность реализована с нуля.

## Технологический стек

- **Бэкенд**: Python 3.11 и выше, `http.server` из стандартной библиотеки
- **База данных**: SQLite 3 (`/server/local_data/database.db`)
- **Фронтенд**: HTML, CSS, ванильный JavaScript (без инструментов сборки)
- **Зависимости**: Отсутствуют. Весь функционал реализован с использованием стандартной библиотеки Python.

## Структура проекта

```
main_dir/
├── client/
│   ├── pages/          # HTML-страницы
│   │   ├── index.html       # Главная страница (лента треков и плеер)
│   │   ├── login.html       # Двухэтапная аутентификация
│   │   ├── register.html    # Регистрация с выбором роли
│   │   ├── profile.html     # Профиль пользователя
│   │   ├── track.html       # Страница трека с комментариями
│   │   ├── upload.html      # Загрузка трека (поддержка drag and drop)
│   │   ├── search.html      # Поиск треков
│   │   ├── communities.html # Список сообществ и создание
│   │   └── community.html   # Чат сообщества и участники
│   └── src/
│       ├── chat.js          # Общие функции (аутентификация, лайки, комментарии)
│       ├── auth.js          # Валидация и управление сессиями
│       ├── player.js        # Аудиоплеер (класс MusicPlayer)
│       └── upload.js        # Логика загрузки треков
├── server/
│   ├── local_data/
│   │   ├── database.db      # База данных SQLite (создаётся автоматически)
│   │   └── uploads/         # Загруженные аудиофайлы
│   ├── main.py              # HTTP-сервер и маршрутизация API
│   └── src/
│       └── server_modules.py # DatabaseManager (все операции с БД)
└── README.MD
```

## Схема базы данных

### Таблицы

**users** — Учётные записи пользователей
- `id` INTEGER PRIMARY KEY
- `username` TEXT UNIQUE
- `email` TEXT UNIQUE
- `password_hash` TEXT (SHA-256)
- `user_type` TEXT CHECK ('listener' | 'musician')
- `is_foreign_agent` BOOLEAN DEFAULT 0
- `registration_date`, `last_login` TIMESTAMP

**tracks** — Загруженные аудиотреки
- `id`, `title`, `artist_id` (FK → users)
- `file_path` TEXT (относительный путь к аудиофайлу)
- `genre`, `description`, `plays_count`
- `upload_date` TIMESTAMP

**comments** — Комментарии к трекам
- `id`, `user_id` (FK), `track_id` (FK)
- `comment_text`, `comment_date`

**likes** — Лайки треков (ограничение UNIQUE на user_id + track_id)
- `id`, `user_id`, `track_id`, `like_date`

**communities** — Сообщества пользователей
- `id`, `name`, `description`, `creator_id` (FK)
- `members_count`, `creation_date`

**community_members** — Участники сообществ (ограничение UNIQUE на community_id + user_id)

**community_messages** — Сообщения в чатах сообществ
- `id`, `community_id`, `user_id`, `message_text`, `message_date`

### Обоснование выбора SQLite

Использование SQLite обусловлено отсутствием необходимости в отдельном сервере баз данных. Один файл, отсутствие конфигурации, резервное копирование осуществляется простым копированием. Для проекта данного масштаба указанной производительности достаточно.

## API-эндпоинты

### Аутентификация
```
POST /api/register   # { username, email, password, user_type, is_foreign_agent }
POST /api/login      # { username, password } → { user: { id, username, ... } }
```

### Треки
```
GET  /api/tracks                  # ?search=&genre= → все треки / поиск
GET  /api/track/info/<id>         # детальная информация о треке
GET  /api/track/<id>/comments     # комментарии к треку
GET  /api/track/<id>/likes        # ?user_id= → лайки и проверка статуса пользователя
POST /api/track/like              # { user_id, track_id, action }
POST /api/track/comment           # { user_id, track_id, comment_text }
POST /api/track/play              # { track_id } → увеличение plays_count на 1
POST /api/upload                  # multipart/form-data (audio, title, artist_id, genre, description)
GET  /api/audio/<filename>        # потоковая передача аудиофайлов
```

### Пользователи
```
GET  /api/user/info/<id>          # профиль пользователя
GET  /api/user/tracks/<id>        # треки пользователя
GET  /api/user/communities/<id>   # сообщества пользователя
```

### Сообщества
```
GET  /api/communities                       # все сообщества
GET  /api/community/info/<id>               # информация о сообществе
GET  /api/community/members/<id>            # участники сообщества
GET  /api/community/messages/<id>           # ?limit= → сообщения чата
GET  /api/community/check-membership/<cid>/<uid>  # проверка членства
POST /api/community/create                  # { name, description, creator_id }
POST /api/community/join                    # { community_id, user_id }
POST /api/community/leave                   # { community_id, user_id }
POST /api/community/message                 # { community_id, user_id, message_text }
```

## Особенности реализации

### Парсинг multipart без использования cgi

В Python 3.13 модуль `cgi` был исключён из стандартной библиотеки, в связи с чем реализован ручной парсер multipart/form-data. Выполняется разбор boundary, извлечение полей и файлов. Реализация является работоспособной, несмотря на сложность кода.

### CORS

Все ответы содержат заголовок `Access-Control-Allow-Origin: *`. В производственной среде применение такой конфигурации не рекомендуется, однако для локальной разработки данное решение допустимо.

### Хеширование паролей

Используется SHA-256 без соли. Для производственных систем рекомендуется применение bcrypt или аналогичных алгоритмов, однако для прототипа текущая реализация является достаточной.

### Поиск треков

Реализован с использованием оператора LIKE по полям title и username. В перспективе возможно внедрение FTS5 от SQLite или полноценного поискового движка.

### Хранение файлов

Аудиофайлы сохраняются в директорию `server/local_data/uploads/` с именами, сгенерированными на основе UUID. Отдача файлов осуществляется как статический контент через эндпоинт `/api/audio/<filename>`. Размер файлов проверяется во время загрузки (лимит — 50 МБ).

### Чат сообществ

Обновление сообщений происходит автоматически каждые 3 секунды. Используется механизм поллинга, а не WebSocket. Для демонстрационных целей данное решение приемлемо, для производственной эксплуатации рекомендуется переход на WebSocket.

### Управление сессиями

Сессии хранятся в `localStorage`. JWT-токены не применяются — используется объект пользователя. При каждом запросе клиент передаёт `user_id`. Указанный подход не является безопасным, однако для прототипа признаётся допустимым.

## Запуск

```bash
cd server
python main.py
# Сервер доступен по адресу http://localhost:8000
```

Запуск возможен без использования виртуального окружения, поскольку зависимости отсутствуют.

### Системные требования

- Python 3.11 или выше
- Любой современный веб-браузер
- 50 МБ свободного дискового пространства для аудиофайлов
