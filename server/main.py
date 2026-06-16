from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from src.auth import AuthManager
from src.socket import ConnectionManager
from src.chat import ChatManager
import asyncio
from pathlib import Path
import json

app = FastAPI()

# Настройка путей
BASE_DIR = Path(__file__).parent.parent
CLIENT_DIR = BASE_DIR / "client"

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory=str(CLIENT_DIR)), name="static")

# Инициализация менеджеров
auth_manager = AuthManager()
ws_manager = ConnectionManager()
chat_manager = ChatManager()

# Хранилище активных пользователей (connection_id -> username)
active_users = {}

@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = CLIENT_DIR / "index.html"
    with open(html_path, 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    html_path = CLIENT_DIR / "login.html"
    with open(html_path, 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    html_path = CLIENT_DIR / "chat.html"
    with open(html_path, 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    connection_id = await ws_manager.connect(websocket)
    current_user = None
    
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "register":
                username = data.get("username", "").strip()
                password = data.get("password", "")
                
                if not username or not password:
                    await ws_manager.send_message(connection_id, {
                        "type": "error",
                        "message": "Логин и пароль не могут быть пустыми"
                    })
                    continue
                
                success, message = auth_manager.register(username, password)
                
                if success:
                    await ws_manager.send_message(connection_id, {
                        "type": "success",
                        "message": message,
                        "action": "register"
                    })
                    print(f"Зарегистрирован: {username}")
                else:
                    await ws_manager.send_message(connection_id, {
                        "type": "error",
                        "message": message
                    })
            
            elif action == "login":
                username = data.get("username", "").strip()
                password = data.get("password", "")
                
                if not username or not password:
                    await ws_manager.send_message(connection_id, {
                        "type": "error",
                        "message": "Введите логин и пароль"
                    })
                    continue
                
                success, message = auth_manager.login(username, password)
                
                if success:
                    current_user = username
                    active_users[connection_id] = username
                    
                    await ws_manager.send_message(connection_id, {
                        "type": "success",
                        "message": message,
                        "action": "login",
                        "username": username
                    })
                    
                    # Отправляем историю сообщений
                    history = chat_manager.get_message_history()
                    if history:
                        await ws_manager.send_message(connection_id, {
                            "type": "history",
                            "messages": history
                        })
                    
                    # Отправляем список активных пользователей
                    await broadcast_active_users()
                    
                    print(f"Вход: {username}")
                else:
                    await asyncio.sleep(0.5)
                    await ws_manager.send_message(connection_id, {
                        "type": "error",
                        "message": message
                    })
            
            elif action == "chat_message":
                if not current_user:
                    await ws_manager.send_message(connection_id, {
                        "type": "error",
                        "message": "Сначала войдите в систему"
                    })
                    continue
                
                message = data.get("message", "").strip()
                if not message:
                    continue
                
                # Сохраняем сообщение
                chat_manager.save_message(current_user, message)
                
                # Отправляем сообщение всем пользователям
                broadcast_data = {
                    "type": "chat_message",
                    "username": current_user,
                    "message": message,
                    "timestamp": chat_manager.get_current_time()
                }
                
                for conn_id in ws_manager.active_connections:
                    await ws_manager.send_message(conn_id, broadcast_data)
            
            elif action == "get_users":
                # Отправляем список активных пользователей
                await ws_manager.send_message(connection_id, {
                    "type": "user_list",
                    "users": list(set(active_users.values()))
                })
            
            elif action == "ping":
                await ws_manager.send_message(connection_id, {
                    "type": "pong",
                    "timestamp": data.get("timestamp")
                })
    
    except WebSocketDisconnect:
        ws_manager.disconnect(connection_id)
        if connection_id in active_users:
            del active_users[connection_id]
        await broadcast_active_users()
        print(f"Клиент отключен: {connection_id}")
    except Exception as e:
        print(f"Ошибка: {e}")
        ws_manager.disconnect(connection_id)
        if connection_id in active_users:
            del active_users[connection_id]
        await broadcast_active_users()

async def broadcast_active_users():
    """Отправляет список активных пользователей всем"""
    users_list = list(set(active_users.values()))
    broadcast_data = {
        "type": "user_list",
        "users": users_list
    }
    
    for conn_id in ws_manager.active_connections:
        await ws_manager.send_message(conn_id, broadcast_data)

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print(f"Сервер запущен на http://127.0.0.1:8000")
    print(f"Страницы:")
    print("  - http://127.0.0.1:8000/ (главная)")
    print("  - http://127.0.0.1:8000/login (вход/регистрация)")
    print("  - http://127.0.0.1:8000/chat (чат)")
    print("=" * 50)
    uvicorn.run(app, host="127.0.0.1", port=8000)
