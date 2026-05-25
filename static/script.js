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

    appLayout.classList.toggle('player-minimized');

    if (playerToggle) {
        if (appLayout.classList.contains('player-minimized')) {
            playerToggle.textContent = '▲';
            playerToggle.title = 'Развернуть плеер';
        } else {
            playerToggle.textContent = '▼';
            playerToggle.title = 'Свернуть плеер';
        }
    }

    // Save player state
    localStorage.setItem('playerMinimized', appLayout.classList.contains('player-minimized'));
}

function initUploadMetadata() {
    const audioInput = document.getElementById('audio-input');
    const previewCard = document.getElementById('preview-card');
    const previewCover = document.getElementById('preview-cover');
    const titleInput = document.getElementById('title-input');
    const artistInput = document.getElementById('artist-input');
    const uploadHint = document.getElementById('upload-hint');

    if (!audioInput) {
        return;
    }

    audioInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (!file) {
            return;
        }

        previewCard.classList.remove('hidden');
        uploadHint.textContent = 'Сканируем метаданные...';
        titleInput.value = '';
        artistInput.value = '';
        previewCover.src = previewCover.dataset.defaultSrc || '/static/logo.png';

        const setFallbackFromFilename = () => {
            const filename = file.name.replace(/\.[^/.]+$/, '').trim();
            const pipeParts = filename.split(/\s*\|\s*/).map(part => part.trim()).filter(Boolean);

            if (pipeParts.length >= 5) {
                titleInput.value = titleInput.value || pipeParts[2];
                artistInput.value = artistInput.value || pipeParts[3];
                return;
            }

            if (pipeParts.length === 4 && /^\d+$/.test(pipeParts[1])) {
                titleInput.value = titleInput.value || pipeParts[2];
                artistInput.value = artistInput.value || pipeParts[3];
                return;
            }

            if (pipeParts.length === 3) {
                titleInput.value = titleInput.value || pipeParts[1];
                artistInput.value = artistInput.value || pipeParts[2];
                return;
            }

            const patterns = [
                /^(?<artist>.+?)\s*[-–—]\s*(?<title>.+)$/,
                /^(?<title>.+?)\s*[-–—]\s*(?<artist>.+)$/,
                /^(?<artist>.+?)\s*\((?<title>.+?)\)$/,
                /^(?<title>.+?)\s*\((?<artist>.+?)\)$/,
                /^(?<artist>.+?)\s*\[(?<title>.+?)\]$/,
                /^(?<title>.+?)\s*\[(?<artist>.+?)\]$/
            ];

            for (const pattern of patterns) {
                const match = filename.match(pattern);
                if (match && match.groups) {
                    artistInput.value = artistInput.value || match.groups.artist.trim();
                    titleInput.value = titleInput.value || match.groups.title.trim();
                    return;
                }
            }

            const fallbackParts = filename.split(/\s*[-–—]\s*/).map(part => part.trim()).filter(Boolean);
            if (fallbackParts.length >= 2) {
                const first = fallbackParts[0];
                const rest = fallbackParts.slice(1).join(' - ');
                if (/^\d+/u.test(first) && rest) {
                    titleInput.value = titleInput.value || first;
                    artistInput.value = artistInput.value || rest;
                } else {
                    artistInput.value = artistInput.value || first;
                    titleInput.value = titleInput.value || rest;
                }
            } else {
                titleInput.value = titleInput.value || filename;
            }
        };

        const readTagValue = (tags, keys) => {
            for (const key of keys) {
                const value = tags[key];
                if (!value) continue;
                if (typeof value === 'string') {
                    return value.trim();
                }
                if (value.data) {
                    return String(value.data).trim();
                }
                if (value.text) {
                    return String(value.text).trim();
                }
            }
            return '';
        };

        const setCoverFromPicture = (picture) => {
            if (!picture || !picture.data) {
                return;
            }

            const format = picture.format || 'image/jpeg';
            const bytes = picture.data instanceof Uint8Array ? picture.data : new Uint8Array(picture.data);
            let binary = '';
            for (let i = 0; i < bytes.length; i++) {
                binary += String.fromCharCode(bytes[i]);
            }
            previewCover.src = `data:${format};base64,${btoa(binary)}`;
        };

        const getTagText = (value) => {
            if (!value && value !== 0) return '';
            if (typeof value === 'string') return value.trim();
            if (typeof value === 'number') return String(value);
            if (Array.isArray(value)) return value.map(getTagText).filter(Boolean).join(', ');
            if (value.data) return String(value.data).trim();
            if (value.text) return String(value.text).trim();
            if (value.value) return getTagText(value.value);
            return '';
        };

        const normalizeTagKey = (key) => String(key).toLowerCase().replace(/[^a-z0-9]/g, '');

        const extractTagValue = (tags, candidates) => {
            const normalizedCandidates = candidates.map(normalizeTagKey);
            for (const [key, value] of Object.entries(tags || {})) {
                const normalizedKey = normalizeTagKey(key);
                if (normalizedCandidates.includes(normalizedKey)) {
                    const text = getTagText(value);
                    if (text) return text;
                }
            }
            return '';
        };

        const applyJsMediaTags = (tag) => {
            const tags = tag.tags || {};
            const title = extractTagValue(tags, ['title', 'tit2', '©nam', 'nam', 'title']);
            const artist = extractTagValue(tags, ['artist', 'tpe1', '©art', 'aart', 'artists', 'albumartist']);

            if (title) titleInput.value = title;
            if (artist) artistInput.value = artist;

            if (tags.picture) {
                setCoverFromPicture(tags.picture);
            } else if (tags.cover && tags.cover.length) {
                setCoverFromPicture(tags.cover[0]);
            }
        };

        const parseWithJsMediaTags = () => {
            return new Promise((resolve) => {
                if (!window.jsmediatags) {
                    return resolve(false);
                }
                try {
                    jsmediatags.read(file, {
                        onSuccess: function(tag) {
                            applyJsMediaTags(tag);
                            resolve(true);
                        },
                        onError: function(error) {
                            console.error('jsmediatags error:', error);
                            resolve(false);
                        }
                    });
                } catch (error) {
                    console.error('jsmediatags exception:', error);
                    resolve(false);
                }
            });
        };

        (async () => {
            const metadataHandled = await parseWithJsMediaTags();
            setFallbackFromFilename();
            if (metadataHandled) {
                uploadHint.textContent = 'Метаданные успешно считаны. Отредактируйте при необходимости.';
            } else {
                uploadHint.textContent = 'Не удалось прочитать метаданные. Использованы данные из имени файла.';
            }
        })();
    });
}

// Profile dropdown toggle
document.addEventListener('DOMContentLoaded', function() {
    // Restore UI states
    const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    const playerMinimized = localStorage.getItem('playerMinimized') === 'true';

    if (sidebarCollapsed) {
        toggleSidebar();
    }

    if (playerMinimized) {
        togglePlayer();
    }

    initUploadMetadata();

    const mainPlayer = document.getElementById('main-player');

    // Restore player state only when the player exists
    const savedIndex = localStorage.getItem('currentIndex');
    if (mainPlayer && savedIndex !== null && tracks.length > 0) {
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
    if (!player || !track) {
        return;
    }
    const coverImg = document.getElementById('player-cover');
    const titleDiv = document.getElementById('player-title');
    const artistDiv = document.getElementById('player-artist');
    const playBtn = document.getElementById('play-btn');

    const audioSrc = track.audio_file || track.audio;
    if (!audioSrc) {
        return;
    }
    player.src = '/uploads/' + audioSrc;
    player.load(); // Ensure load
    if (coverImg) {
        coverImg.src = track.cover_file ? '/uploads/' + track.cover_file : '/static/logo.png';
    }
    if (titleDiv) {
        titleDiv.textContent = track.name || track.title || 'Название';
    }
    if (artistDiv) {
        artistDiv.textContent = track.author || track.artist || 'Исполнитель';
    }
    currentIndex = index;

    player.volume = parseFloat(localStorage.getItem('volume')) || 0.5;

    player.addEventListener('loadedmetadata', () => {
        const durationEl = document.getElementById('duration');
        const miniDurationEl = document.getElementById('mini-duration');
        const formattedDuration = formatTime(player.duration);
        if (durationEl) durationEl.textContent = formattedDuration;
        if (miniDurationEl) miniDurationEl.textContent = formattedDuration;
        const savedTime = localStorage.getItem('currentTime');
        if (savedTime) {
            player.currentTime = parseFloat(savedTime);
        }
    });

    player.addEventListener('timeupdate', () => {
        const currentTime = document.getElementById('current-time');
        const miniCurrentTime = document.getElementById('mini-current-time');
        const timelineFill = document.getElementById('timeline-fill');
        const formattedTime = formatTime(player.currentTime);
        if (currentTime) currentTime.textContent = formattedTime;
        if (miniCurrentTime) miniCurrentTime.textContent = formattedTime;
        const progress = (player.currentTime / player.duration) * 100;
        if (timelineFill) timelineFill.style.width = progress + '%';
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
    if (!track || !modal) {
        return;
    }
    const title = track.name || track.title || 'Название';
    const artist = track.author || track.artist || 'Исполнитель';

    // Установка базовой информации
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-artist').textContent = artist;
    document.getElementById('modal-cover').src = track.cover_file ? '/uploads/' + track.cover_file : '/static/logo.png';
    
    // Очистка информации
    document.getElementById('modal-info').innerHTML = '<p>Загрузка информации...</p>';
    document.getElementById('cover-section').style.display = 'none';
    document.getElementById('modal-badges').innerHTML = '';
    
    // Показываем модальное окно
    modal.classList.add('active');
    
    // Запрашиваем информацию о треке
    fetchTrackInfo(artist, title, index);
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
            const trackTitle = tracks[i].name || tracks[i].title;
            const trackArtist = tracks[i].author || tracks[i].artist;
            if (trackTitle === title && trackArtist === artist) {
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