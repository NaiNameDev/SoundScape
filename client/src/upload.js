// upload.js - Загрузка треков

document.addEventListener('DOMContentLoaded', () => {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    
    // Проверка, что пользователь - музыкант
    if (!currentUser) {
        alert('Необходимо войти в систему');
        window.location.href = '/pages/login.html';
        return;
    }
    
    if (currentUser.user_type !== 'musician') {
        alert('Только музыканты могут загружать треки');
        window.location.href = '/pages/profile.html';
        return;
    }
    
    // Обработчик формы загрузки
    document.getElementById('uploadForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData();
        const audioFile = document.getElementById('audioFile').files[0];
        
        if (!audioFile) {
            showStatus('Выберите аудиофайл', 'error');
            return;
        }
        
        // Проверка размера файла (максимум 50MB)
        if (audioFile.size > 50 * 1024 * 1024) {
            showStatus('Файл слишком большой. Максимальный размер: 50MB', 'error');
            return;
        }
        
        formData.append('audio', audioFile);
        formData.append('title', document.getElementById('title').value);
        formData.append('artist_id', currentUser.id);
        formData.append('genre', document.getElementById('genre').value);
        formData.append('description', document.getElementById('description').value);
        
        showStatus('Загрузка трека...', 'info');
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                showStatus('Трек успешно загружен!', 'success');
                setTimeout(() => {
                    window.location.href = '/pages/profile.html';
                }, 2000);
            } else {
                showStatus(data.error || 'Ошибка загрузки', 'error');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            showStatus('Ошибка соединения с сервером', 'error');
        }
    });
    
    // Предпросмотр аудиофайла
    document.getElementById('audioFile').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const audioURL = URL.createObjectURL(file);
            const audio = new Audio(audioURL);
            
            audio.addEventListener('loadedmetadata', () => {
                const duration = audio.duration;
                const minutes = Math.floor(duration / 60);
                const seconds = Math.floor(duration % 60);
                showStatus(`Длительность: ${minutes}:${seconds.toString().padStart(2, '0')}`, 'info');
            });
        }
    });
});

function showStatus(message, type) {
    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.textContent = message;
    
    // Убираем все классы
    statusDiv.className = '';
    
    // Добавляем класс в зависимости от типа
    switch(type) {
        case 'error':
            statusDiv.style.color = 'red';
            break;
        case 'success':
            statusDiv.style.color = 'green';
            break;
        case 'info':
            statusDiv.style.color = 'blue';
            break;
        default:
            statusDiv.style.color = 'black';
    }
}
