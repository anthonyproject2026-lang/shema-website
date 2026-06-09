/* ============================================
   SHEMA Admin Panel — JavaScript
   ============================================ */

(() => {
  'use strict';

  // ---- Config ----
  const ADMIN_PASSWORD = 'shema2025';
  const STORAGE_KEYS = {
    photos: 'shema_admin_photos',
    events: 'shema_admin_events',
    session: 'shema_admin_session'
  };

  // ---- DOM Elements ----
  const loginScreen = document.getElementById('loginScreen');
  const dashboardScreen = document.getElementById('dashboardScreen');
  const loginForm = document.getElementById('loginForm');
  const loginError = document.getElementById('loginError');
  const passwordInput = document.getElementById('adminPassword');
  const togglePwBtn = document.getElementById('togglePw');
  const logoutBtn = document.getElementById('logoutBtn');

  // Photos
  const photoForm = document.getElementById('photoForm');
  const photoUrlInput = document.getElementById('photoUrl');
  const photoCaptionInput = document.getElementById('photoCaption');
  const photoDescInput = document.getElementById('photoDescription');
  const previewPhotoBtn = document.getElementById('previewPhotoBtn');
  const photoPreview = document.getElementById('photoPreview');
  const previewImg = document.getElementById('previewImg');
  const previewCaption = document.getElementById('previewCaption');
  const previewDesc = document.getElementById('previewDesc');
  const photoGrid = document.getElementById('photoGrid');
  const photoCount = document.getElementById('photoCount');

  // Events
  const eventForm = document.getElementById('eventForm');
  const eventTitleInput = document.getElementById('eventTitle');
  const eventDateInput = document.getElementById('eventDate');
  const eventDescInput = document.getElementById('eventDescription');
  const eventLocationInput = document.getElementById('eventLocation');
  const eventImageInput = document.getElementById('eventImage');
  const previewEventBtn = document.getElementById('previewEventBtn');
  const eventPreview = document.getElementById('eventPreview');
  const epMonth = document.getElementById('epMonth');
  const epDay = document.getElementById('epDay');
  const epTitle = document.getElementById('epTitle');
  const epDesc = document.getElementById('epDesc');
  const epLocation = document.getElementById('epLocation');
  const eventGrid = document.getElementById('eventGrid');
  const eventCount = document.getElementById('eventCount');

  // Tabs
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  // Toast
  const toast = document.getElementById('toast');
  const toastMessage = document.getElementById('toastMessage');

  // ---- Helpers ----
  function showToast(msg) {
    toastMessage.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2800);
  }

  function getFromStorage(key) {
    try {
      const data = localStorage.getItem(key);
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  }

  function saveToStorage(key, data) {
    localStorage.setItem(key, JSON.stringify(data));
  }

  function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
  }

  const MONTHS = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];

  function formatDate(dateStr) {
    const d = new Date(dateStr + 'T00:00:00');
    return {
      month: MONTHS[d.getMonth()],
      day: String(d.getDate()).padStart(2, '0'),
      full: d.toLocaleDateString('en-AU', { day: 'numeric', month: 'long', year: 'numeric' })
    };
  }

  // ---- Auth ----
  function checkSession() {
    return sessionStorage.getItem(STORAGE_KEYS.session) === 'true';
  }

  function login() {
    sessionStorage.setItem(STORAGE_KEYS.session, 'true');
    loginScreen.style.display = 'none';
    dashboardScreen.style.display = 'flex';
    renderPhotos();
    renderEvents();
  }

  function logout() {
    sessionStorage.removeItem(STORAGE_KEYS.session);
    dashboardScreen.style.display = 'none';
    loginScreen.style.display = 'flex';
    passwordInput.value = '';
    loginError.textContent = '';
  }

  // Check session on load
  if (checkSession()) {
    login();
  }

  // Login form
  loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const pw = passwordInput.value.trim();
    if (pw === ADMIN_PASSWORD) {
      loginError.textContent = '';
      login();
      showToast('Welcome, Admin! 🎉');
    } else {
      loginError.textContent = 'Incorrect password. Please try again.';
      passwordInput.value = '';
      passwordInput.focus();
      // Shake animation
      loginForm.style.animation = 'none';
      requestAnimationFrame(() => {
        loginForm.style.animation = 'shake 0.4s ease';
      });
    }
  });

  // Toggle password visibility
  togglePwBtn.addEventListener('click', () => {
    const type = passwordInput.type === 'password' ? 'text' : 'password';
    passwordInput.type = type;
  });

  // Logout
  logoutBtn.addEventListener('click', logout);

  // ---- Tabs ----
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;
      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-' + target).classList.add('active');
    });
  });

  // ---- Photos CRUD ----
  function renderPhotos() {
    const photos = getFromStorage(STORAGE_KEYS.photos);
    photoCount.textContent = photos.length;

    if (photos.length === 0) {
      photoGrid.innerHTML = '<p class="empty-state">No photos added yet. Use the form above to add your first photo.</p>';
      return;
    }

    photoGrid.innerHTML = photos.map(photo => `
      <div class="list-item" data-id="${photo.id}">
        <img src="${photo.url}" alt="${photo.caption}" onerror="this.src='images/shema-logo.png'" />
        <div class="list-item-info">
          <strong>${photo.caption}</strong>
          <span>${photo.description || 'No description'}</span>
        </div>
        <button class="delete-btn" onclick="deletePhoto('${photo.id}')" title="Delete photo">
          🗑️
        </button>
      </div>
    `).join('');
  }

  // Make deletePhoto globally accessible
  window.deletePhoto = function(id) {
    let photos = getFromStorage(STORAGE_KEYS.photos);
    photos = photos.filter(p => p.id !== id);
    saveToStorage(STORAGE_KEYS.photos, photos);
    renderPhotos();
    showToast('Photo deleted');
  };

  // Photo preview
  previewPhotoBtn.addEventListener('click', () => {
    const url = photoUrlInput.value.trim();
    const caption = photoCaptionInput.value.trim();
    if (!url) return;

    previewImg.src = url;
    previewCaption.textContent = caption || 'No caption';
    previewDesc.textContent = photoDescInput.value.trim() || '';
    photoPreview.style.display = 'block';
  });

  // Add photo
  photoForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const url = photoUrlInput.value.trim();
    const caption = photoCaptionInput.value.trim();
    const description = photoDescInput.value.trim();

    if (!url || !caption) return;

    const photos = getFromStorage(STORAGE_KEYS.photos);
    photos.push({
      id: generateId(),
      url,
      caption,
      description,
      addedAt: new Date().toISOString()
    });
    saveToStorage(STORAGE_KEYS.photos, photos);

    photoForm.reset();
    photoPreview.style.display = 'none';
    renderPhotos();
    showToast('Photo added successfully! 📸');
  });

  // ---- Events CRUD ----
  function renderEvents() {
    const events = getFromStorage(STORAGE_KEYS.events);
    eventCount.textContent = events.length;

    if (events.length === 0) {
      eventGrid.innerHTML = '<p class="empty-state">No events added yet. Use the form above to create your first event.</p>';
      return;
    }

    eventGrid.innerHTML = events.map(event => {
      const d = formatDate(event.date);
      return `
        <div class="list-item" data-id="${event.id}">
          <div class="list-item-date">
            <span class="li-month">${d.month}</span>
            <span class="li-day">${d.day}</span>
          </div>
          <div class="list-item-info">
            <strong>${event.title}</strong>
            <span>${event.description}</span>
          </div>
          <button class="delete-btn" onclick="deleteEvent('${event.id}')" title="Delete event">
            🗑️
          </button>
        </div>
      `;
    }).join('');
  }

  window.deleteEvent = function(id) {
    let events = getFromStorage(STORAGE_KEYS.events);
    events = events.filter(e => e.id !== id);
    saveToStorage(STORAGE_KEYS.events, events);
    renderEvents();
    showToast('Event deleted');
  };

  // Event preview
  previewEventBtn.addEventListener('click', () => {
    const title = eventTitleInput.value.trim();
    const date = eventDateInput.value;
    const desc = eventDescInput.value.trim();
    const location = eventLocationInput.value.trim();

    if (!title || !date) return;

    const d = formatDate(date);
    epMonth.textContent = d.month;
    epDay.textContent = d.day;
    epTitle.textContent = title;
    epDesc.textContent = desc || 'No description';
    epLocation.textContent = location ? '📍 ' + location : '';
    epLocation.style.display = location ? 'block' : 'none';
    eventPreview.style.display = 'block';
  });

  // Add event
  eventForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const title = eventTitleInput.value.trim();
    const date = eventDateInput.value;
    const description = eventDescInput.value.trim();
    const location = eventLocationInput.value.trim();
    const image = eventImageInput.value.trim();

    if (!title || !date || !description) return;

    const events = getFromStorage(STORAGE_KEYS.events);
    events.push({
      id: generateId(),
      title,
      date,
      description,
      location,
      image,
      addedAt: new Date().toISOString()
    });
    saveToStorage(STORAGE_KEYS.events, events);

    eventForm.reset();
    eventPreview.style.display = 'none';
    renderEvents();
    showToast('Event added successfully! 🎉');
  });

  // ---- Shake animation (for wrong password) ----
  const style = document.createElement('style');
  style.textContent = `
    @keyframes shake {
      0%, 100% { transform: translateX(0); }
      20% { transform: translateX(-10px); }
      40% { transform: translateX(10px); }
      60% { transform: translateX(-6px); }
      80% { transform: translateX(6px); }
    }
  `;
  document.head.appendChild(style);

  console.log('🔐 SHEMA Admin Panel loaded');
})();
