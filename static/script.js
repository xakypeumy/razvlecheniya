// UI Toggle Functions
function toggleSidebar() {
    const appLayout = document.querySelector('.app-layout');
    const sideMenu = document.getElementById('side-menu');
    const mainLogo = document.getElementById('main-logo');
    const miniLogo = document.getElementById('mini-logo');
    const menuToggle = document.getElementById('menu-toggle');

    appLayout.classList.toggle('collapsed');
    sideMenu.classList.toggle('collapsed');

    if (appLayout.classList.contains('collapsed')) {
        mainLogo.style.display = 'none';
        miniLogo.style.display = 'block';
        menuToggle.textContent = '▶';
    } else {
        mainLogo.style.display = 'block';
        miniLogo.style.display = 'none';
        menuToggle.textContent = '◀';
    }

    // Save sidebar state
    localStorage.setItem('sidebarCollapsed', appLayout.classList.contains('collapsed'));
}

function togglePlayer() {
    const appLayout = document.querySelector('.app-layout');
    const playerToggle = document.getElementById('player-toggle');

    appLayout.classList.toggle('player-hidden');

    if (appLayout.classList.contains('player-hidden')) {
        playerToggle.textContent = '▲';
    } else {
        playerToggle.textContent = '▼';
    }

    // Save player state
    localStorage.setItem('playerHidden', appLayout.classList.contains('player-hidden'));
}

// Profile dropdown toggle
document.addEventListener('DOMContentLoaded', function() {
    // Restore UI states
    const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    const playerHidden = localStorage.getItem('playerHidden') === 'true';

    if (sidebarCollapsed) {
        toggleSidebar();
    }

    if (playerHidden) {
        togglePlayer();
    }

    // Restore player state
    const savedIndex = localStorage.getItem('currentIndex');
    if (savedIndex !== null && tracks.length > 0) {
        currentIndex = parseInt(savedIndex);
        playTrack(currentIndex);
    }

    // Close modal on Escape key
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeTrackModal();
        }
    });

    const profileBtn = document.querySelector('.profile-btn');
    if (profileBtn) {
        profileBtn.addEventListener('click', function() {
            const dropdown = this.nextElementSibling;
            dropdown.classList.toggle('show');
        });
    }

    // Close dropdown when clicking outside
    window.addEventListener('click', function(e) {
        if (!e.target.matches('.profile-btn')) {
            const dropdowns = document.querySelectorAll('.dropdown');
            dropdowns.forEach(dropdown => {
                if (dropdown.classList.contains('show')) {
                    dropdown.classList.remove('show');
                }
            });
        }
    });

    // Timeline click
    const timelineBg = document.getElementById('timeline-bg');
    const player = document.getElementById('main-player');
    if (timelineBg && player) {
        let isDraggingTimeline = false;

        const updateTime = (e) => {
            const rect = timelineBg.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const width = rect.width;
            const progress = clickX / width;
            player.currentTime = progress * player.duration;
        };

        timelineBg.addEventListener('mousedown', (e) => {
            isDraggingTimeline = true;
            updateTime(e);
        });

        window.addEventListener('mousemove', (e) => {
            if (isDraggingTimeline) {
                updateTime(e);
            }
        });

        window.addEventListener('mouseup', () => {
            isDraggingTimeline = false;
        });

        timelineBg.addEventListener('click', updateTime); // Keep click for single clicks
    }

    // Volume
    const volumeBg = document.getElementById('volume-bg');
    const volumeFill = document.getElementById('volume-fill');
    if (volumeBg && volumeFill && player) {
        // Set initial volume
        const savedVolume = parseFloat(localStorage.getItem('volume')) || 0.5;
        player.volume = savedVolume;
        volumeFill.style.height = (savedVolume * 100) + '%';

        let isDraggingVolume = false;

        const updateVolume = (e) => {
            const rect = volumeBg.getBoundingClientRect();
            const clickY = e.clientY - rect.top;
            const height = rect.height;
            const volume = 1 - (clickY / height);
            player.volume = Math.max(0, Math.min(1, volume));
            volumeFill.style.height = (volume * 100) + '%';
            localStorage.setItem('volume', volume);
        };

        volumeBg.addEventListener('mousedown', (e) => {
            isDraggingVolume = true;
            updateVolume(e);
        });

        window.addEventListener('mousemove', (e) => {
            if (isDraggingVolume) {
                updateVolume(e);
            }
        });

        window.addEventListener('mouseup', () => {
            isDraggingVolume = false;
        });

        volumeBg.addEventListener('click', updateVolume); // Keep click for single clicks
    }
});

// Play track function
function playTrack(index) {
    const track = tracks[index];
    const player = document.getElementById('main-player');
    const coverImg = document.getElementById('player-cover');
    const titleDiv = document.getElementById('player-title');
    const artistDiv = document.getElementById('player-artist');
    const playBtn = document.getElementById('play-btn');

    player.src = '/uploads/' + track.audio;
    player.load(); // Ensure load
    coverImg.src = track.cover ? '/uploads/' + track.cover : '/static/default.png';
    titleDiv.textContent = track.title;
    artistDiv.textContent = track.artist;
    currentIndex = index;

    player.volume = parseFloat(localStorage.getItem('volume')) || 0.5;

    player.addEventListener('loadedmetadata', () => {
        document.getElementById('duration').textContent = formatTime(player.duration);
        const savedTime = localStorage.getItem('currentTime');
        if (savedTime) {
            player.currentTime = parseFloat(savedTime);
        }
    });

    player.addEventListener('timeupdate', () => {
        const currentTime = document.getElementById('current-time');
        const timelineFill = document.getElementById('timeline-fill');
        currentTime.textContent = formatTime(player.currentTime);
        const progress = (player.currentTime / player.duration) * 100;
        timelineFill.style.width = progress + '%';
        localStorage.setItem('currentTime', player.currentTime);
    });

    player.addEventListener('play', () => {
        localStorage.setItem('isPlaying', 'true');
        playBtn.textContent = '⏸';
    });

    player.addEventListener('pause', () => {
        localStorage.setItem('isPlaying', 'false');
        playBtn.textContent = '▶';
    });

    localStorage.setItem('currentIndex', index);

    // Play if was playing, after canplay
    const wasPlaying = localStorage.getItem('isPlaying') === 'true';
    if (wasPlaying) {
        player.addEventListener('canplay', () => {
            player.play().catch(() => {
                // Autoplay blocked, set to paused
                localStorage.setItem('isPlaying', 'false');
                playBtn.textContent = '▶';
            });
        }, { once: true });
    }

    // Pause on page unload
    window.addEventListener('beforeunload', () => {
        player.pause();
    });
}

// Toggle play/pause
function togglePlayPause() {
    const player = document.getElementById('main-player');
    const playBtn = document.getElementById('play-btn');

    if (player.paused) {
        player.play();
        playBtn.textContent = '⏸';
    } else {
        player.pause();
        playBtn.textContent = '▶';
    }
}

// Placeholder for next/previous (since single track)
function nextTrack() {
    if (tracks.length > 0) {
        currentIndex = (currentIndex + 1) % tracks.length;
        playTrack(currentIndex);
    }
}

function previousTrack() {
    if (tracks.length > 0) {
        currentIndex = (currentIndex - 1 + tracks.length) % tracks.length;
        playTrack(currentIndex);
    }
}

// Format time
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// ===== MODAL FUNCTIONS =====

// Открытие модального окна с информацией о треке
function openTrackModal(index) {
    const track = tracks[index];
    const modal = document.getElementById('track-modal');
    
    // Установка базовой информации
    document.getElementById('modal-title').textContent = track.title;
    document.getElementById('modal-artist').textContent = track.artist;
    document.getElementById('modal-cover').src = track.cover ? '/uploads/' + track.cover : '/static/default.png';
    
    // Очистка информации
    document.getElementById('modal-info').innerHTML = '<p>Загрузка информации...</p>';
    document.getElementById('cover-section').style.display = 'none';
    document.getElementById('modal-badges').innerHTML = '';
    
    // Показываем модальное окно
    modal.classList.add('active');
    
    // Запрашиваем информацию о треке
    fetchTrackInfo(track.artist, track.title, index);
}

// Закрытие модального окна
function closeTrackModal() {
    const modal = document.getElementById('track-modal');
    modal.classList.remove('active');
}

// Воспроизведение трека из модального окна
function playFromModal() {
    const modal = document.getElementById('track-modal');
    if (modal.classList.contains('active')) {
        // Get the currently displayed track info
        const title = document.getElementById('modal-title').textContent;
        const artist = document.getElementById('modal-artist').textContent;
        
        // Find the track index
        for (let i = 0; i < tracks.length; i++) {
            if (tracks[i].title === title && tracks[i].artist === artist) {
                playTrack(i);
                break;
            }
        }
    }
}

// Получение информации о треке от API
async function fetchTrackInfo(artist, title, trackIndex) {
    try {
        const response = await fetch(`/api/track-info?artist=${encodeURIComponent(artist)}&title=${encodeURIComponent(title)}`);
        const data = await response.json();
        
        displayTrackInfo(data, trackIndex);
    } catch (error) {
        console.error('Error fetching track info:', error);
        document.getElementById('modal-info').innerHTML = '<p>Не удалось загрузить информацию о треке.</p>';
    }
}

// Отображение информации о треке в модальном окне
function displayTrackInfo(data, trackIndex) {
    const infoDiv = document.getElementById('modal-info');
    const coverSection = document.getElementById('cover-section');
    const geniusSection = document.getElementById('genius-section');
    const lastfmSection = document.getElementById('lastfm-section');
    const similarSection = document.getElementById('similar-section');
    const badgesDiv = document.getElementById('modal-badges');
    
    // Очищаем предыдущие значки
    badgesDiv.innerHTML = '';
    
    let infoHtml = '';
    
    // Базовая информация
    infoHtml += `<p><strong>Название:</strong> <span>${data.title || 'Не определено'}</span></p>`;
    infoHtml += `<p><strong>Исполнитель:</strong> <span>${data.artist || 'Не определено'}</span></p>`;
    
    if (data.length) {
        const minutes = Math.floor(data.length / 60000);
        const seconds = Math.floor((data.length % 60000) / 1000);
        infoHtml += `<p><strong>Длительность:</strong> <span>${minutes}:${seconds.toString().padStart(2, '0')}</span></p>`;
    }
    
    if (data.mbid) {
        infoHtml += `<p><strong>MusicBrainz ID:</strong> <span>${data.mbid.substring(0, 8)}...</span></p>`;
    }
    
    infoDiv.innerHTML = infoHtml;
    
    // Добавляем значки
    if (data.is_cover) {
        const badge = document.createElement('span');
        badge.className = 'badge';
        badge.textContent = '🎵 Кавер';
        badgesDiv.appendChild(badge);
    }
    
    // Показываем информацию о кавере, если это кавер
    if (data.is_cover) {
        coverSection.style.display = 'block';
        
        const coverHtml = `
            <p><strong>Это кавер:</strong> <span>Да</span></p>
            ${data.original_title ? `<p><strong>Оригинальное название:</strong> <span>${data.original_title}</span></p>` : ''}
            ${data.original_artist ? `<p><strong>Оригинальный исполнитель:</strong> <span>${data.original_artist}</span></p>` : ''}
        `;
        
        document.getElementById('cover-info').innerHTML = coverHtml;
    } else {
        coverSection.style.display = 'none';
    }
    
    // Показываем текст песни
    if (data.lyrics_text) {
        geniusSection.style.display = 'block';
        
        let geniusHtml = `<h3>Текст песни</h3>`;
        geniusHtml += `<div class="lyrics-text">${data.lyrics_text.replace(/\n/g, '<br>')}</div>`;
        
        if (data.lyrics_url) {
            geniusHtml += `<p><a href="${data.lyrics_url}" target="_blank" class="info-link">Поиск в Google →</a></p>`;
        }
        if (data.genius_url) {
            geniusHtml += `<p><a href="${data.genius_url}" target="_blank" class="info-link">Перейти на Genius →</a></p>`;
        }
        
        document.getElementById('genius-info').innerHTML = geniusHtml;
    } else if (data.genius_url) {
        geniusSection.style.display = 'block';
        
        let geniusHtml = `<h3>Информация о песне</h3>`;
        geniusHtml += `<p><a href="${data.genius_url}" target="_blank" class="info-link">Перейти на Genius →</a></p>`;
        
        document.getElementById('genius-info').innerHTML = geniusHtml;
    } else {
        geniusSection.style.display = 'none';
    }
    
    // Показываем статистику Last.fm
    if (data.lastfm) {
        lastfmSection.style.display = 'block';
        
        let lastfmHtml = '';
        if (data.lastfm.playcount) {
            lastfmHtml += `<p><strong>Прослушиваний:</strong> <span>${formatNumber(parseInt(data.lastfm.playcount))}</span></p>`;
        }
        if (data.lastfm.listeners) {
            lastfmHtml += `<p><strong>Слушателей:</strong> <span>${formatNumber(parseInt(data.lastfm.listeners))}</span></p>`;
        }
        if (data.lastfm.url) {
            lastfmHtml += `<a href="${data.lastfm.url}" target="_blank" class="info-link">Перейти на Last.fm →</a>`;
        }
        if (data.lastfm.tags && data.lastfm.tags.length > 0) {
            lastfmHtml += `<div class="tags-container" style="margin-top: 10px;">`;
            data.lastfm.tags.forEach(tag => {
                lastfmHtml += `<span class="tag">${tag}</span>`;
            });
            lastfmHtml += `</div>`;
        }
        
        document.getElementById('lastfm-info').innerHTML = lastfmHtml;
    } else {
        lastfmSection.style.display = 'none';
    }
    
    // Показываем похожие треки
    if (data.similar && data.similar.length > 0) {
        similarSection.style.display = 'block';
        
        let similarHtml = '';
        data.similar.slice(0, 8).forEach(track => {
            similarHtml += `
                <div class="similar-track-item">
                    <div class="similar-track-header">
                        <span class="similar-track-name">${track.name}</span>
                        <span class="similar-track-match">${Math.round(track.match)}%</span>
                    </div>
                    <div class="similar-track-artist">${track.artist}</div>
                </div>
            `;
        });
        
        document.getElementById('similar-tracks').innerHTML = similarHtml;
    } else {
        similarSection.style.display = 'none';
    }
}

// Форматирование больших чисел
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// Обновление функции playTrack для открытия модала при клике
// (переопределяем поведение клика на карточку трека)