import json
from pathlib import Path
from datetime import datetime

class ChatManager:
    def __init__(self):
        self.messages_file = Path(__file__).parent.parent / "local_data" / "messages.json"
        self.messages_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.messages_file.exists():
            self._save_messages([])
    
    def _load_messages(self) -> list:
        """Загрузка истории сообщений"""
        try:
            with open(self.messages_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def _save_messages(self, messages: list):
        """Сохранение сообщений"""
        with open(self.messages_file, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=4, ensure_ascii=False)
    
    def save_message(self, username: str, message: str):
        """Сохранение нового сообщения"""
        messages = self._load_messages()
        messages.append({
            "username": username,
            "message": message,
            "timestamp": self.get_current_time(),
            "datetime": datetime.now().isoformat()
        })
        
        # Оставляем только последние 100 сообщений
        if len(messages) > 100:
            messages = messages[-100:]
        
        self._save_messages(messages)
    
    def get_message_history(self, limit: int = 50) -> list:
        """Получение истории сообщений"""
        messages = self._load_messages()
        return messages[-limit:]
    
    def get_current_time(self) -> str:
        """Получение текущего времени в формате HH:MM:SS"""
        return datetime.now().strftime("%H:%M:%S")
