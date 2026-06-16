import json
import os
import hashlib

class AuthManager:
    def __init__(self):
        self.users_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "local_data", 
            "users.json"
        )
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
    
    def _hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _load_users(self) -> dict:
        """Загрузка пользователей из файла"""
        if not os.path.exists(self.users_file):
            return {}
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_users(self, users: dict):
        """Сохранение пользователей в файл"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
    
    def register(self, username: str, password: str) -> tuple:
        """Регистрация нового пользователя"""
        users = self._load_users()
        
        if username in users:
            return False, "Пользователь уже существует"
        
        users[username] = {
            "password": self._hash_password(password),
            "username": username
        }
        self._save_users(users)
        return True, "Регистрация успешна! Теперь вы можете войти."
    
    def login(self, username: str, password: str) -> tuple:
        """Вход пользователя"""
        users = self._load_users()
        
        if username not in users:
            return False, "Неверный логин или пароль"
        
        if users[username]["password"] != self._hash_password(password):
            return False, "Неверный логин или пароль"
        
        return True, f"Добро пожаловать, {username}!"
