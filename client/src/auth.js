function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    if (password.length < 6) {
        return { valid: false, message: 'Пароль должен содержать минимум 6 символов' };
    }
    
    if (!/\d/.test(password)) {
        return { valid: false, message: 'Пароль должен содержать хотя бы одну цифру' };
    }
    
    if (!/[a-zA-Z]/.test(password)) {
        return { valid: false, message: 'Пароль должен содержать хотя бы одну букву' };
    }
    
    return { valid: true };
}

function saveSession(userData) {
    const sessionData = {
        ...userData,
        loginTime: new Date().toISOString()
    };
    localStorage.setItem('currentUser', JSON.stringify(sessionData));
}

function checkSession() {
    const userData = JSON.parse(localStorage.getItem('currentUser'));
    
    if (!userData) {
        return null;
    }
    
    const loginTime = new Date(userData.loginTime);
    const now = new Date();
    const hoursDiff = (now - loginTime) / (1000 * 60 * 60);
    
    if (hoursDiff > 24) {
        localStorage.removeItem('currentUser');
        return null;
    }
    
    return userData;
}

function refreshSession() {
    const userData = JSON.parse(localStorage.getItem('currentUser'));
    if (userData) {
        userData.loginTime = new Date().toISOString();
        localStorage.setItem('currentUser', JSON.stringify(userData));
    }
}
