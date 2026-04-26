// Profile dropdown toggle
document.addEventListener('DOMContentLoaded', function() {
    // Restore player state
    const savedIndex = localStorage.getItem('currentIndex');
    if (savedIndex !== null && tracks.length > 0) {
        currentIndex = parseInt(savedIndex);
        playTrack(currentIndex);
    }

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