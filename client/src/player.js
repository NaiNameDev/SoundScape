class MusicPlayer {
    constructor() {
        this.audioPlayer = document.getElementById('audioPlayer');
        this.playlist = [];
        this.currentTrackIndex = -1;
        this.isPlaying = false;
        
        this.init();
    }
    
    init() {
        const savedPlaylist = localStorage.getItem('playlist');
        if (savedPlaylist) {
            this.playlist = JSON.parse(savedPlaylist);
        }
        
        const urlParams = new URLSearchParams(window.location.search);
        const trackId = urlParams.get('track');
        
        if (trackId) {
            const currentTrack = JSON.parse(localStorage.getItem('currentTrack'));
            if (currentTrack) {
                this.addToPlaylist(currentTrack);
                this.loadTrack(currentTrack);
            }
        }
        
        this.audioPlayer.addEventListener('ended', () => this.nextTrack());
        this.audioPlayer.addEventListener('error', () => this.onTrackError());
        
        this.updatePlaylistDisplay();
    }
    
    loadTrack(track) {
        this.audioPlayer.src = track.filePath;
        this.currentTrackIndex = this.playlist.findIndex(t => t.id === track.id);
        
        document.getElementById('nowPlaying').innerHTML = `
            <p>Сейчас играет: Трек #${track.id}</p>
        `;
        
        this.play();
    }
    
    play() {
        this.audioPlayer.play()
            .then(() => {
                this.isPlaying = true;
                this.updatePlayButton();
            })
            .catch(error => {
                console.error('Ошибка воспроизведения:', error);
            });
    }
    
    pause() {
        this.audioPlayer.pause();
        this.isPlaying = false;
        this.updatePlayButton();
    }
    
    togglePlayPause() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }
    
    nextTrack() {
        if (this.playlist.length === 0) return;
        
        this.currentTrackIndex = (this.currentTrackIndex + 1) % this.playlist.length;
        const nextTrack = this.playlist[this.currentTrackIndex];
        this.loadTrack(nextTrack);
    }
    
    previousTrack() {
        if (this.playlist.length === 0) return;
        
        this.currentTrackIndex = this.currentTrackIndex <= 0 
            ? this.playlist.length - 1 
            : this.currentTrackIndex - 1;
        
        const prevTrack = this.playlist[this.currentTrackIndex];
        this.loadTrack(prevTrack);
    }
    
    addToPlaylist(track) {
        const exists = this.playlist.find(t => t.id === track.id);
        if (!exists) {
            this.playlist.push(track);
            this.savePlaylist();
            this.updatePlaylistDisplay();
        }
    }
    
    removeFromPlaylist(trackId) {
        this.playlist = this.playlist.filter(t => t.id !== trackId);
        this.savePlaylist();
        this.updatePlaylistDisplay();
    }
    
    savePlaylist() {
        localStorage.setItem('playlist', JSON.stringify(this.playlist));
    }
    
    updatePlayButton() {
        const button = document.getElementById('playPauseBtn');
        if (button) {
            button.textContent = this.isPlaying ? '⏸ Пауза' : '▶ Воспроизвести';
        }
    }
    
    updatePlaylistDisplay() {
        const container = document.getElementById('playlist');
        
        if (this.playlist.length === 0) {
            container.innerHTML = '<p>Плейлист пуст</p>';
            return;
        }
        
        container.innerHTML = this.playlist.map((track, index) => `
            <div class="playlist-item" style="background: ${index === this.currentTrackIndex ? '#e0e0e0' : 'transparent'}">
                <p>Трек #${track.id}</p>
                <button onclick="player.removeFromPlaylist(${track.id})">Удалить</button>
                <button onclick="player.loadTrack(player.playlist[${index}])">Воспроизвести</button>
            </div>
            <hr>
        `).join('');
    }
    
    onTrackError() {
        console.error('Ошибка загрузки аудиофайла');
        document.getElementById('nowPlaying').innerHTML += '<p style="color: red;">Ошибка загрузки трека</p>';
        
        setTimeout(() => this.nextTrack(), 2000);
    }
}

let player;
window.addEventListener('DOMContentLoaded', () => {
    player = new MusicPlayer();
});

function togglePlayPause() {
    if (player) player.togglePlayPause();
}

function nextTrack() {
    if (player) player.nextTrack();
}

function previousTrack() {
    if (player) player.previousTrack();
}
