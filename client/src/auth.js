// auth.js - Функции аутентификации

// Проверка валидности email
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Проверка силы пароля
function validatePassword(password) {
    // Минимум 6 символов
    if (password.length < 6) {
        return { valid: false, message: 'Пароль должен содержать минимум 6 символов' };
    }
    
    // Хотя бы одна цифра
    if (!/\d/.test(password)) {
        return { valid: false, message: 'Пароль должен содержать хотя бы одну цифру' };
    }
    
    // Хотя бы одна буква
    if (!/[a-zA-Z]/.test(password)) {
        return { valid: false, message: 'Пароль должен содержать хотя бы одну букву' };
    }
    
    return { valid: true };
}

// Сохранение сессии
function saveSession(userData) {
    const sessionData = {
        ...userData,
        loginTime: new Date().toISOString()
    };
    localStorage.setItem('currentUser', JSON.stringify(sessionData));
}

// Проверка сессии
function checkSession() {
    const userData = JSON.parse(localStorage.getItem('currentUser'));
    
    if (!userData) {
        return null;
    }
    
    // Проверяем, не истекла ли сессия (24 часа)
    const loginTime = new Date(userData.loginTime);
    const now = new Date();
    const hoursDiff = (now - loginTime) / (1000 * 60 * 60);
    
    if (hoursDiff > 24) {
        localStorage.removeItem('currentUser');
        return null;
    }
    
    return userData;
}

// Обновление времени сессии
function refreshSession() {
    const userData = JSON.parse(localStorage.getItem('currentUser'));
    if (userData) {
        userData.loginTime = new Date().toISOString();
        localStorage.setItem('currentUser', JSON.stringify(userData));
    }
}
