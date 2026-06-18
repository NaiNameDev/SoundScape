струкута каталагов проекта
```
main_dir
├── client
│   ├── pages
│   │   └── page.html
│   └── src
│   	└── chat.js
├── README.MD
└── server
    ├── local_data
    │   └── database.db
    ├── main.py
    └── src
        └── server_modules.py
```
инструкция к запуску
зависимости: python, websocket, asyncio, fastapi.

1. скачиванеи зависимостей (пример на arch linux)
```
sudo pacman -S python python-websocket python-asyncio python-fastapi
```
2. запуск сервера
```
python ./server/main.py
```
3. заходим на 127.0.0.1:8000
4. готово

архитектура сайта
![архитектура](images/arch.png)
er-диограмма бд
![диограмма](images/di.png)

BACKLOG:
Легкие задачи (1–2 часа)
		Создание структуры базы данных
		Создать таблицы USER, SERVER, CHANNEL, MESSAGE, MUSIC_TRACK, PLAYLIST, PLAYLIST_TRACK, SUBSCRIPTION.
		Настроить первичные и внешние ключи.
		Регистрация пользователя
		Форма регистрации.
		Проверка уникальности email.
		Авторизация пользователя
		Вход по email и паролю.
		Создание пользовательской сессии.
		Редактирование профиля
		Изменение имени пользователя.
		Загрузка аватара.
		Создание музыкального сервера
		Форма создания сообщества.
		Сохранение владельца сервера.
		Просмотр списка серверов
		Отображение серверов, в которых состоит пользователь.
		Создание текстового канала
		Добавление канала внутри сервера.
		Отправка сообщений
		Отправка и сохранение сообщений в БД.
Средние задачи (3–6 часов)
		Просмотр истории сообщений
		Загрузка сообщений выбранного канала.
		Сортировка по времени отправки.
		Удаление и редактирование сообщений
		Доступ только автору сообщения.
		Загрузка музыкальных треков
		Загрузка mp3-файлов.
		Сохранение информации о треке.
		Страница музыканта
		Отображение профиля.
		Список опубликованных треков.
		Подписка на музыканта
		Создание записи в SUBSCRIPTION.
		Возможность отмены подписки.
		Создание плейлистов
		Создание пользовательских плейлистов.
		Добавление треков в плейлист
		Работа с таблицей PLAYLIST_TRACK.
		Поиск музыкантов
		Поиск по имени пользователя.
		Фильтрация по роли musician.
Сложные задачи (1–3 дня)
		Реализация голосовых каналов
		Подключение WebSocket.
		Поддержка подключения нескольких пользователей.
		Онлайн-статус пользователей
		Отображение статусов online/offline.
		Обновление в реальном времени.
		Уведомления о новых треках
		Автоматическое уведомление подписчиков.
		Отображение уведомлений в интерфейсе.
		Чат в реальном времени
		Передача сообщений через WebSocket.
		Мгновенное обновление без перезагрузки страницы.




# SoundScape Техническая документация

## Общее описание

Клон SoundCloud на голом Python без фреймворков. Сервер на `http.server`, база SQLite, фронт на ванильном JS. Никаких React'ов, никаких Django — всё с нуля, потому что могу.

## Стек

- **Бэкенд**: Python 3.11+, `http.server` из коробки
- **База**: SQLite 3 (`/server/local_data/database.db`)
- **Фронт**: HTML + CSS + ванильный JS (без сборщиков)
- **Зависимости**: нет. Вообще. Всё из stdlib.

## Структура проекта

```
main_dir/
├── client/
│   ├── pages/          # HTML страницы
│   │   ├── index.html       # Главная (лента треков + плеер)
│   │   ├── login.html       # Двухшаговый вход
│   │   ├── register.html    # Регистрация с выбором роли
│   │   ├── profile.html     # Профиль пользователя
│   │   ├── track.html       # Страница трека + комментарии
│   │   ├── upload.html      # Загрузка трека (drag & drop)
│   │   ├── search.html      # Поиск треков
│   │   ├── communities.html # Список сообществ + создание
│   │   └── community.html   # Чат сообщества + участники
│   └── src/
│       ├── chat.js          # Общие функции (auth, лайки, комментарии)
│       ├── auth.js          # Валидация и сессии
│       ├── player.js        # Плеер (класс MusicPlayer)
│       └── upload.js        # Логика загрузки треков
├── server/
│   ├── local_data/
│   │   ├── database.db      # SQLite база (автосоздаётся)
│   │   └── uploads/         # Загруженные аудиофайлы
│   ├── main.py              # HTTP сервер + роутинг API
│   └── src/
│       └── server_modules.py # DatabaseManager (вся работа с БД)
└── README.MD




```

## База данных

### Таблицы

**users** — пользователи
- `id` INTEGER PRIMARY KEY
- `username` TEXT UNIQUE
- `email` TEXT UNIQUE
- `password_hash` TEXT (SHA-256)
- `user_type` TEXT CHECK ('listener' | 'musician')
- `is_foreign_agent` BOOLEAN DEFAULT 0
- `registration_date`, `last_login` TIMESTAMP

**tracks** — загруженные треки
- `id`, `title`, `artist_id` (FK → users)
- `file_path` TEXT (относительный путь к аудио)
- `genre`, `description`, `plays_count`
- `upload_date` TIMESTAMP

**comments** — комментарии к трекам
- `id`, `user_id` (FK), `track_id` (FK)
- `comment_text`, `comment_date`

**likes** — лайки (UNIQUE на user_id + track_id)
- `id`, `user_id`, `track_id`, `like_date`

**communities** — сообщества
- `id`, `name`, `description`, `creator_id` (FK)
- `members_count`, `creation_date`

**community_members** — участники (UNIQUE на community_id + user_id)

**community_messages** — сообщения в чатах
- `id`, `community_id`, `user_id`, `message_text`, `message_date`

### Почему SQLite

Потому что не нужен отдельный сервер БД. Один файл, ноль конфигурации, бекап копированием. Для такого проекта хватает за глаза.

## API эндпоинты

### Авторизация
```
POST /api/register   # { username, email, password, user_type, is_foreign_agent }
POST /api/login      # { username, password } → { user: { id, username, ... } }
```

### Треки
```
GET  /api/tracks                  # ?search=&genre= → все/поиск треков
GET  /api/track/info/<id>         # детали трека
GET  /api/track/<id>/comments     # комментарии
GET  /api/track/<id>/likes        # ?user_id= → лайки + проверка юзера
POST /api/track/like              # { user_id, track_id, action }
POST /api/track/comment           # { user_id, track_id, comment_text }
POST /api/track/play              # { track_id } → +1 к plays_count
POST /api/upload                  # multipart/form-data (audio, title, artist_id, genre, description)
GET  /api/audio/<filename>        # стриминг аудиофайлов
```

### Пользователи
```
GET  /api/user/info/<id>          # профиль
GET  /api/user/tracks/<id>        # треки юзера
GET  /api/user/communities/<id>   # сообщества юзера
```

### Сообщества
```
GET  /api/communities                       # все сообщества
GET  /api/community/info/<id>               # информация
GET  /api/community/members/<id>            # участники
GET  /api/community/messages/<id>           # ?limit= → сообщения чата
GET  /api/community/check-membership/<cid>/<uid>  # проверка участника
POST /api/community/create                  # { name, description, creator_id }
POST /api/community/join                    # { community_id, user_id }
POST /api/community/leave                   # { community_id, user_id }
POST /api/community/message                 # { community_id, user_id, message_text }
```

## Особенности реализации

### Парсинг multipart без cgi

Python 3.13 выпилил модуль `cgi`, поэтому написал ручной парсер multipart/form-data. Разбирает boundary, вытаскивает поля и файлы. Да, выглядит страшно. Да, работает.

### CORS

Все ответы с `Access-Control-Allow-Origin: *`. В продакшене так делать нельзя, но для локалхоста норм.

### Хеширование паролей

SHA-256 без соли. Опять же — для прода надо bcrypt, но для прототипа сойдёт.

### Поиск треков

Простой LIKE по title и username. В будущем — FTS5 от SQLite или нормальный поисковый движок.

### Хранение файлов

Аудио сохраняются в `server/local_data/uploads/` с UUID-именами. Отдаются как статика через `/api/audio/<filename>`. Размер не проверяется на лету, кроме как при загрузке (50MB лимит).

### Чат сообществ

Автообновление каждые 3 секунды. Не вебсокеты — поллинг. Для демки ок, для продакшена переписать на WebSocket.

### Сессии

Хранятся в `localStorage`. Никаких JWT токенов — просто объект пользователя. При каждом запросе клиент сам передаёт `user_id`. Да, небезопасно. Да, для прототипа норм.

## Запуск

```bash
cd server
python main.py
# Сервер на http://localhost:8000
```

Можно без виртуалки — зависимостей всё равно нет.

### Требования

- Python 3.11+
- Любой браузер
- 50MB свободного места под аудио

## Известные баги / TODO

- [ ] Нет нормальной авторизации (сессии без токенов)
- [ ] Поллинг чата вместо WebSocket
- [ ] Нет пагинации в API
- [ ] Пароли хешируются без соли
- [ ] Нет защиты от CSRF
- [ ] Нет ресайза изображений (их вообще нет)
- [ ] CORS разрешён всем
- [ ] Нет ограничения частоты запросов
- [ ] Поиск сообществ только на фронте
- [ ] Нет плейлистов в UI (только в БД)

## Как контрибьютить

1. Форкнуть
2. Создать ветку
3. Запушить
4. Открыть PR

Перед PR убедиться что сервер запускается и страницы открываются. Тестов нет, линтеров нет — всё на честном слове.
