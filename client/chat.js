let ws = null;
let currentUsername = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

function connectWebSocket() {
    const wsUrl = `ws://${window.location.host}/ws`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = function() {
        console.log("WebSocket подключен");
        updateStatus(true);
        reconnectAttempts = 0;
        
        const savedUser = localStorage.getItem('chat_username');
        if (savedUser) {
            currentUsername = savedUser;
            document.getElementById('currentUser').innerHTML = currentUsername;
        }
        
        addSystemMessage("Соединение с сервером установлено");
    };
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log("Получено:", data);
        
        if (data.type === "success" && data.action === "login") {
            currentUsername = data.username;
            localStorage.setItem('chat_username', currentUsername);
            document.getElementById('currentUser').innerHTML = currentUsername;
            addSystemMessage(`Добро пожаловать, ${currentUsername}!`);
        }
        else if (data.type === "chat_message") {
            addMessage(data.username, data.message, data.timestamp);
        }
        else if (data.type === "history") {
            displayMessageHistory(data.messages);
        }
        else if (data.type === "user_list") {
            updateUsersList(data.users);
        }
        else if (data.type === "error") {
            addSystemMessage(data.message, "error");
            if (data.message.includes("войдите")) {
                setTimeout(() => {
                    window.location.href = "/login";
                }, 2000);
            }
        }
    };
    
    ws.onerror = function(error) {
        console.error("WebSocket ошибка:", error);
        addSystemMessage("Ошибка соединения", "error");
    };
    
    ws.onclose = function() {
        updateStatus(false);
        addSystemMessage("Соединение потеряно", "error");
        
        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            setTimeout(connectWebSocket, 2000 * reconnectAttempts);
        }
    };
}

function updateStatus(connected) {
    const statusSpan = document.getElementById("status");
    if (connected) {
        statusSpan.innerHTML = "🟢 Подключено к серверу";
        statusSpan.style.color = "green";
    } else {
        statusSpan.innerHTML = "⚫ Отключено от сервера";
        statusSpan.style.color = "red";
    }
}

function addMessage(username, message, timestamp) {
    const messagesDiv = document.getElementById("messages");
    const messageDiv = document.createElement("div");
    
    const isCurrentUser = (username === currentUsername);
    const prefix = isCurrentUser ? "→ " : "← ";
    
    messageDiv.innerHTML = `
        <div><strong>${prefix}${username}</strong> [${timestamp}]</div>
        <div style="margin-left: 20px;">${escapeHtml(message)}</div>
        <hr style="margin: 5px 0;">
    `;
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function addSystemMessage(text, type = "info") {
    const messagesDiv = document.getElementById("messages");
    const messageDiv = document.createElement("div");
    const color = type === "error" ? "red" : "gray";
    
    messageDiv.style.color = color;
    messageDiv.style.fontStyle = "italic";
    messageDiv.style.margin = "5px 0";
    messageDiv.innerHTML = `[${new Date().toLocaleTimeString()}] ${text}`;
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.remove();
        }
    }, 3000);
}

function displayMessageHistory(messages) {
    const messagesDiv = document.getElementById("messages");
    messagesDiv.innerHTML = "";
    
    if (messages.length === 0) {
        addSystemMessage("История сообщений пуста. Начните общение!");
        return;
    }
    
    messages.forEach(msg => {
        const messageDiv = document.createElement("div");
        const isCurrentUser = (msg.username === currentUsername);
        const prefix = isCurrentUser ? "→ " : "← ";
        
        messageDiv.innerHTML = `
            <div><strong>${prefix}${escapeHtml(msg.username)}</strong> [${msg.timestamp}]</div>
            <div style="margin-left: 20px;">${escapeHtml(msg.message)}</div>
            <hr style="margin: 5px 0;">
        `;
        
        messagesDiv.appendChild(messageDiv);
    });
    
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function updateUsersList(users) {
    const usersDiv = document.getElementById("usersList");
    usersDiv.innerHTML = "";
    
    if (users.length === 0) {
        usersDiv.innerHTML = "Нет активных пользователей";
        return;
    }
    
    users.forEach(user => {
        const userSpan = document.createElement("div");
        userSpan.innerHTML = `${escapeHtml(user)}${user === currentUsername ? ' (Вы)' : ''}`;
        usersDiv.appendChild(userSpan);
    });
}

function sendMessage() {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        addSystemMessage("Нет соединения с сервером", "error");
        return;
    }
    
    const input = document.getElementById("messageInput");
    const message = input.value.trim();
    
    if (!message) {
        return;
    }
    
    ws.send(JSON.stringify({
        action: "chat_message",
        message: message
    }));
    
    input.value = "";
}

function handleKeyPress(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function checkAuth() {
    const savedUser = localStorage.getItem('chat_username');
    if (!savedUser) {
        addSystemMessage("Вы не авторизованы. Перенаправление на страницу входа...", "error");
        setTimeout(() => {
            window.location.href = "/login";
        }, 2000);
    }
}

// Подключаемся при загрузке
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        checkAuth();
        connectWebSocket();
    });
} else {
    checkAuth();
    connectWebSocket();
}
