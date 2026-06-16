let ws = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

function connectWebSocket() {
    const wsUrl = `ws://${window.location.host}/ws`;
    
    console.log("Подключение к WebSocket:", wsUrl);
    ws = new WebSocket(wsUrl);
    
    ws.onopen = function() {
        console.log("WebSocket подключен");
        updateStatus(true);
        reconnectAttempts = 0;
        showMessage("Соединение с сервером установлено", "info");
    };
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log("Получено:", data);
        
        if (data.type === "success") {
            showMessage(data.message, "success");
            if (data.action === "login") {
                // Можно добавить перенаправление после входа
                // window.location.href = "/";
            }
        } else if (data.type === "error") {
            showMessage(data.message, "error");
        } else if (data.type === "pong") {
            showMessage(`Пинг получен!`, "info");
        }
    };
    
    ws.onerror = function(error) {
        console.error("WebSocket ошибка:", error);
        showMessage("Ошибка соединения", "error");
    };
    
    ws.onclose = function() {
        console.log("WebSocket закрыт");
        updateStatus(false);
        showMessage("Соединение потеряно", "error");
        
        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            setTimeout(connectWebSocket, 2000 * reconnectAttempts);
        }
    };
}

function updateStatus(connected) {
    const statusDiv = document.getElementById("status");
    if (statusDiv) {
        if (connected) {
            statusDiv.innerHTML = "🟢 Подключено к серверу";
            statusDiv.style.color = "green";
        } else {
            statusDiv.innerHTML = "⚫ Отключено от сервера";
            statusDiv.style.color = "red";
        }
    }
}

function showMessage(text, type) {
    const messageDiv = document.getElementById("messageArea");
    if (!messageDiv) return;
    
    const msg = document.createElement("div");
    
    if (type === "error") {
        msg.style.color = "red";
    } else if (type === "success") {
        msg.style.color = "green";
    } else {
        msg.style.color = "blue";
    }
    
    msg.innerHTML = `[${new Date().toLocaleTimeString()}] ${text}`;
    messageDiv.appendChild(msg);
    
    setTimeout(() => {
        if (msg.parentNode) {
            msg.remove();
        }
    }, 5000);
}

function clearMessages() {
    const messageDiv = document.getElementById("messageArea");
    if (messageDiv) {
        messageDiv.innerHTML = "";
    }
}

function register() {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        showMessage("Нет соединения с сервером", "error");
        return;
    }
    
    const username = document.getElementById("regUsername");
    const password = document.getElementById("regPassword");
    
    if (!username || !password) {
        showMessage("Элементы формы не найдены", "error");
        return;
    }
    
    const usernameVal = username.value;
    const passwordVal = password.value;
    
    if (!usernameVal || !passwordVal) {
        showMessage("Заполните все поля", "error");
        return;
    }
    
    ws.send(JSON.stringify({
        action: "register",
        username: usernameVal,
        password: passwordVal
    }));
    
    username.value = "";
    password.value = "";
}

function login() {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        showMessage("Нет соединения с сервером", "error");
        return;
    }
    
    const username = document.getElementById("loginUsername");
    const password = document.getElementById("loginPassword");
    
    if (!username || !password) {
        showMessage("Элементы формы не найдены", "error");
        return;
    }
    
    const usernameVal = username.value;
    const passwordVal = password.value;
    
    if (!usernameVal || !passwordVal) {
        showMessage("Заполните все поля", "error");
        return;
    }
    
    ws.send(JSON.stringify({
        action: "login",
        username: usernameVal,
        password: passwordVal
    }));
    
    username.value = "";
    password.value = "";
}

function checkConnection() {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        showMessage("Нет соединения с сервером", "error");
        return;
    }
    
    ws.send(JSON.stringify({
        action: "ping",
        timestamp: Date.now()
    }));
}

// Подключаемся при загрузке страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', connectWebSocket);
} else {
    connectWebSocket();
}
