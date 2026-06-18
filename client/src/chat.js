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

function logout() {
    localStorage.removeItem('currentUser');
    window.location.href = '/pages/index.html';
}

function playTrack(trackId, filePath) {
    localStorage.setItem('currentTrack', JSON.stringify({
        id: trackId,
        filePath: filePath
    }));
    
    window.location.href = `/pages/track.html?id=${trackId}`;
}

function likeTrack(trackId) {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    
    if (!currentUser) {
        alert('Необходимо войти в систему');
        return;
    }
    
    fetch('/api/track/like', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            user_id: currentUser.id,
            track_id: trackId,
            action: 'like'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Лайк поставлен! Всего лайков: ${data.likes}`);
        }
    })
    .catch(error => console.error('Ошибка лайка:', error));
}

function showComments(trackId) {
    fetch(`/api/track/${trackId}/comments`)
        .then(response => response.json())
        .then(comments => {
            let commentsHtml = '<h3>Комментарии</h3>';
            
            if (comments.length === 0) {
                commentsHtml += '<p>Нет комментариев</p>';
            } else {
                commentsHtml += comments.map(comment => `
                    <div>
                        <strong>${comment.username}</strong>
                        <p>${comment.text}</p>
                        <small>${comment.date}</small>
                    </div>
                    <hr>
                `).join('');
            }
            
            const currentUser = JSON.parse(localStorage.getItem('currentUser'));
            if (currentUser) {
                commentsHtml += `
                    <div>
                        <textarea id="commentText" placeholder="Ваш комментарий..."></textarea>
                        <button onclick="addComment(${trackId})">Отправить</button>
                    </div>
                `;
            }
            
            alert('Комментарии: ' + JSON.stringify(comments, null, 2));
        })
        .catch(error => console.error('Ошибка загрузки комментариев:', error));
}

function addComment(trackId) {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    const commentText = document.getElementById('commentText')?.value;
    
    if (!commentText) {
        alert('Введите текст комментария');
        return;
    }
    
    fetch('/api/track/comment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            user_id: currentUser.id,
            track_id: trackId,
            comment_text: commentText
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Комментарий добавлен!');
            showComments(trackId);
        }
    })
    .catch(error => console.error('Ошибка добавления комментария:', error));
}
