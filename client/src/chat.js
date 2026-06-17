// chat.js - Общие функции для всего приложения

// Проверка авторизации
function checkAuth() {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    const authLinks = document.getElementById('authLinks');
    const userLinks = document.getElementById('userLinks');
    
    if (currentUser) {
        if (authLinks) authLinks.style.display = 'none';
        if (userLinks) userLinks.style.display = 'inline';
    } else {
        if (authLinks) authLinks.style.display = 'inline';
        if (userLinks) userLinks.style.display = 'none';
    }
}

// Выход из системы
function logout() {
    localStorage.removeItem('currentUser');
    window.location.href = '/pages/index.html';
}

// Воспроизведение трека
function playTrack(trackId, filePath) {
    // Сохраняем текущий трек в localStorage для плеера
    localStorage.setItem('currentTrack', JSON.stringify({
        id: trackId,
        filePath: filePath
    }));
    
    // Открываем страницу трека
    window.location.href = `/pages/track.html?id=${trackId}`;
}
