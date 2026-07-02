/* ============================================
   SHEMA Admin Panel — JavaScript
   ============================================ */

(() => {
  'use strict';

  // ---- Config ----
  // TODO: Replace with real authentication (Firebase Auth / Netlify Identity)
  // Password removed from client-side code for security
  const ADMIN_PASSWORD = '';
  const STORAGE_KEYS = {
    photos: 'shema_admin_photos',
    events: 'shema_admin_events',
    features: 'shema_admin_features',
    committee: 'shema_admin_committee',
    deletedItems: 'shema_deleted_items',
    session: 'shema_admin_session'
  };

  // ---- Defaults ----
  const DEFAULT_COMMITTEE = [
    { id: 'default_committee_1', name: 'Antony Jones', role: 'President', image: '/.netlify/images?url=/images/committee-antony.jpg&w=400&fm=webp', isDefault: true },

    { id: 'default_committee_4', name: 'Anu Joby', role: 'Secretary', image: '/.netlify/images?url=/images/committee-anu.png&w=400&fm=webp', isDefault: true },
    { id: 'default_committee_5', name: 'Arun Thampi', role: 'Treasurer', image: '/.netlify/images?url=/images/committee-arun.png&w=400&fm=webp', isDefault: true }
  ];

  const DEFAULT_PHOTOS = [
    {
      id: 'default_photo_1',
      url: 'images/event-mayor.jpg',
      caption: 'SHEMA Cultural Evening',
      description: 'With Cr Shane Sali, Mayor — Greater Shepparton City Council',
      isDefault: true
    },
    {
      id: 'default_photo_2',
      url: 'images/event-lamp.jpg',
      caption: 'Traditional Lamp Lighting',
      description: 'Nilavilakku ceremony — an auspicious beginning to every Kerala celebration',
      isDefault: true
    }
  ];

  const DEFAULT_EVENTS = [
    {
      id: 'default_event_1',
      title: 'Onam Celebration 2025',
      date: '2025-09-14',
      description: 'Join us for the grand Onam celebration featuring traditional Sadhya feast, cultural performances, Pookalam competition and family fun activities.',
      location: 'Shepparton Community Hall',
      isDefault: true
    },
    {
      id: 'default_event_2',
      title: 'Vishu Celebration 2026',
      date: '2026-04-14',
      description: 'Welcome the Kerala New Year with Vishukkani, Sadya and traditional games. A day of new beginnings and community togetherness.',
      location: 'Shepparton Civic Centre',
      isDefault: true
    },
    {
      id: 'default_event_3',
      title: 'Christmas & Year-End Gathering',
      date: '2025-12-21',
      description: 'Celebrate the festive season with the SHEMA community. Enjoy food, music, kids\' activities and a warm community gathering to close the year.',
      location: 'Victoria Park Lake',
      isDefault: true
    }
  ];

  const DEFAULT_FEATURES = [
    { id: 'default_feature_1', tag: 'Performing Art', title: 'Kathakali', description: "The classical dance-drama of Kerala, known for its elaborate costumes, vivid face makeup, and powerful storytelling rooted in Hindu mythology.", image: 'images/kathakali.png', isDefault: true },
    { id: 'default_feature_2', tag: 'Ritual Art', title: 'Theyyam', description: "An ancient ritual art form from North Malabar, where performers are believed to become possessed by divine spirits, adorned with stunning headgear and body paint.", image: 'images/theyyam.png', isDefault: true },
    { id: 'default_feature_3', tag: 'Tradition', title: 'Vallam Kali', description: "The iconic snake boat races of Kerala, where massive chundan vallams race through the backwaters in a breathtaking display of teamwork and tradition.", image: 'images/boat-race.png', isDefault: true },
    { id: 'default_feature_4', tag: 'Landscape', title: 'Backwaters & Houseboats', description: "Kerala's iconic network of serene lagoons, canals and lakes, best experienced on traditional kettuvallam houseboats gliding through palm-fringed waters.", image: 'images/kerala-backwaters.png', isDefault: true },
    { id: 'default_feature_5', tag: 'Nature', title: 'Munnar & Western Ghats', description: "Rolling emerald tea plantations, misty mountain peaks, and pristine forests that make Kerala's Western Ghats a UNESCO-worthy natural treasure.", image: 'images/munnar.png', isDefault: true },
    { id: 'default_feature_6', tag: 'Cuisine', title: 'Onam Sadhya', description: "The grand vegetarian feast of Kerala, served on a banana leaf with up to 26 dishes — a culinary tradition that embodies the spirit of Onam festival.", image: 'images/onam-sadhya.png', isDefault: true },
    { id: 'default_feature_7', tag: 'Martial Art', title: 'Kalaripayattu', description: "One of the oldest martial arts in the world, originating in Kerala. Practitioners train in traditional kalaris, mastering strikes, kicks and weaponry.", image: 'images/kalaripayattu.png', isDefault: true },
    { id: 'default_feature_8', tag: 'Festival', title: 'Temple Festivals', description: "Grand celebrations featuring caparisoned elephants, traditional percussion ensembles, colourful parasols, and spectacular fireworks at Kerala's sacred temples.", image: 'images/temple-festival.png', isDefault: true },
    { id: 'default_feature_9', tag: 'Heritage', title: 'Chinese Fishing Nets', description: "The iconic cantilevered fishing nets of Fort Kochi, introduced by Chinese traders centuries ago — now a symbol of Kerala's multicultural maritime history.", image: 'images/chinese-fishing-nets.png', isDefault: true },
    { id: 'default_feature_10', tag: 'Wellness', title: 'Ayurveda', description: "Kerala is the heartland of Ayurveda — the ancient Indian system of holistic medicine using herbal remedies, therapeutic oils and time-honoured healing practices.", image: 'images/ayurveda.png', isDefault: true }
  ];

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

  // Features (Kerala Heritage)
  const featureForm = document.getElementById('featureForm');
  const featureTitleInput = document.getElementById('featureTitle');
  const featureTagInput = document.getElementById('featureTag');
  const featureDescInput = document.getElementById('featureDescription');
  const featureImageInput = document.getElementById('featureImage');
  const previewFeatureBtn = document.getElementById('previewFeatureBtn');
  const featurePreview = document.getElementById('featurePreview');
  const fpImg = document.getElementById('fpImg');
  const fpTag = document.getElementById('fpTag');
  const fpTitle = document.getElementById('fpTitle');
  const fpDesc = document.getElementById('fpDesc');
  const featureGrid = document.getElementById('featureGrid');
  const featureCount = document.getElementById('featureCount');

  // Committee
  const committeeForm = document.getElementById('committeeForm');
  const committeeNameInput = document.getElementById('committeeName');
  const committeeRoleInput = document.getElementById('committeeRole');
  const committeeImageInput = document.getElementById('committeeImage');
  const committeeGrid = document.getElementById('committeeGrid');
  const committeeCount = document.getElementById('committeeCount');

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
    renderFeatures();
    renderCommittee();
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
    const deletedItems = getFromStorage(STORAGE_KEYS.deletedItems);
    const customPhotos = getFromStorage(STORAGE_KEYS.photos);
    
    const defaultPhotosToShow = DEFAULT_PHOTOS.filter(p => !deletedItems.includes(p.id));
    const allPhotos = [...defaultPhotosToShow, ...customPhotos];
    
    photoCount.textContent = allPhotos.length;

    if (allPhotos.length === 0) {
      photoGrid.innerHTML = '<p class="empty-state">No photos added yet. Use the form above to add your first photo.</p>';
      return;
    }

    photoGrid.innerHTML = allPhotos.map(photo => `
      <div class="list-item" data-id="${photo.id}">
        <img src="${photo.url}" alt="${photo.caption}" onerror="this.src='images/shema-logo.png'" />
        <div class="list-item-info">
          <strong>${photo.caption} ${photo.isDefault ? '<span class="badge badge-default">Default</span>' : '<span class="badge badge-added">Added</span>'}</strong>
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
    if (confirm('Are you sure you want to delete this photo?')) {
      if (id.startsWith('default_')) {
        const deleted = getFromStorage(STORAGE_KEYS.deletedItems);
        if (!deleted.includes(id)) {
          deleted.push(id);
          saveToStorage(STORAGE_KEYS.deletedItems, deleted);
        }
      } else {
        let photos = getFromStorage(STORAGE_KEYS.photos);
        photos = photos.filter(p => p.id !== id);
        saveToStorage(STORAGE_KEYS.photos, photos);
      }
      renderPhotos();
      showToast('Photo deleted');
    }
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
    const deletedItems = getFromStorage(STORAGE_KEYS.deletedItems);
    const customEvents = getFromStorage(STORAGE_KEYS.events);
    
    const defaultEventsToShow = DEFAULT_EVENTS.filter(e => !deletedItems.includes(e.id));
    const allEvents = [...defaultEventsToShow, ...customEvents];
    
    eventCount.textContent = allEvents.length;

    if (allEvents.length === 0) {
      eventGrid.innerHTML = '<p class="empty-state">No events added yet. Use the form above to create your first event.</p>';
      return;
    }

    eventGrid.innerHTML = allEvents.map(event => {
      const d = formatDate(event.date);
      return `
        <div class="list-item" data-id="${event.id}">
          <div class="list-item-date">
            <span class="li-month">${d.month}</span>
            <span class="li-day">${d.day}</span>
          </div>
          <div class="list-item-info">
            <strong>${event.title} ${event.isDefault ? '<span class="badge badge-default">Default</span>' : '<span class="badge badge-added">Added</span>'}</strong>
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
    if (confirm('Are you sure you want to delete this event?')) {
      if (id.startsWith('default_')) {
        const deleted = getFromStorage(STORAGE_KEYS.deletedItems);
        if (!deleted.includes(id)) {
          deleted.push(id);
          saveToStorage(STORAGE_KEYS.deletedItems, deleted);
        }
      } else {
        let events = getFromStorage(STORAGE_KEYS.events);
        events = events.filter(e => e.id !== id);
        saveToStorage(STORAGE_KEYS.events, events);
      }
      renderEvents();
      showToast('Event deleted');
    }
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

  // ---- Features (Kerala Heritage) CRUD ----
  function renderFeatures() {
    const deletedItems = getFromStorage(STORAGE_KEYS.deletedItems);
    const customFeatures = getFromStorage(STORAGE_KEYS.features);
    
    const defaultFeaturesToShow = DEFAULT_FEATURES.filter(f => !deletedItems.includes(f.id));
    const allFeatures = [...defaultFeaturesToShow, ...customFeatures];
    
    featureCount.textContent = allFeatures.length;

    if (allFeatures.length === 0) {
      featureGrid.innerHTML = '<p class="empty-state">No heritage cards found. Use the form above to add one.</p>';
      return;
    }

    featureGrid.innerHTML = allFeatures.map(feature => `
      <div class="list-item" data-id="${feature.id}">
        <img src="${feature.image}" alt="${feature.title}" onerror="this.src='images/shema-logo.png'" />
        <div class="list-item-info">
          <strong>${feature.title} ${feature.isDefault ? '<span class="badge badge-default">Default</span>' : '<span class="badge badge-added">Added</span>'}</strong>
          <span class="feature-tag-badge">${feature.tag}</span>
          <span>${feature.description}</span>
        </div>
        <button class="delete-btn" onclick="deleteFeature('${feature.id}')" title="Delete heritage card">
          🗑️
        </button>
      </div>
    `).join('');
  }

  window.deleteFeature = function(id) {
    if (confirm('Are you sure you want to delete this heritage card?')) {
      if (id.startsWith('default_')) {
        const deleted = getFromStorage(STORAGE_KEYS.deletedItems);
        if (!deleted.includes(id)) {
          deleted.push(id);
          saveToStorage(STORAGE_KEYS.deletedItems, deleted);
        }
      } else {
        let features = getFromStorage(STORAGE_KEYS.features);
        features = features.filter(f => f.id !== id);
        saveToStorage(STORAGE_KEYS.features, features);
      }
      renderFeatures();
      showToast('Heritage card deleted');
    }
  };

  // Feature preview
  previewFeatureBtn.addEventListener('click', () => {
    const title = featureTitleInput.value.trim();
    const tag = featureTagInput.value.trim();
    const desc = featureDescInput.value.trim();
    const url = featureImageInput.value.trim();

    if (!title || !tag || !desc || !url) return;

    fpImg.src = url;
    fpTag.textContent = tag;
    fpTitle.textContent = title;
    fpDesc.textContent = desc;
    featurePreview.style.display = 'block';
  });

  // Add feature
  featureForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const title = featureTitleInput.value.trim();
    const tag = featureTagInput.value.trim();
    const description = featureDescInput.value.trim();
    const image = featureImageInput.value.trim();

    if (!title || !tag || !description || !image) return;

    const features = getFromStorage(STORAGE_KEYS.features);
    features.push({
      id: generateId(),
      title,
      tag,
      description,
      image,
      addedAt: new Date().toISOString()
    });
    saveToStorage(STORAGE_KEYS.features, features);

    featureForm.reset();
    featurePreview.style.display = 'none';
    renderFeatures();
    showToast('Heritage card added successfully! 🎨');
  });

  // ---- Committee CRUD ----
  function renderCommittee() {
    const deletedItems = getFromStorage(STORAGE_KEYS.deletedItems);
    const customCommittee = getFromStorage(STORAGE_KEYS.committee);
    
    const defaultCommitteeToShow = DEFAULT_COMMITTEE.filter(c => !deletedItems.includes(c.id));
    const allCommittee = [...defaultCommitteeToShow, ...customCommittee];
    
    committeeCount.textContent = allCommittee.length;

    if (allCommittee.length === 0) {
      committeeGrid.innerHTML = '<p class="empty-state">No committee members added yet.</p>';
      return;
    }

    committeeGrid.innerHTML = allCommittee.map(member => `
      <div class="list-item" data-id="${member.id}">
        <img src="${member.image}" alt="${member.name}" onerror="this.src='images/shema-logo.png'" style="width:50px;height:50px;object-fit:cover;border-radius:50%;" />
        <div class="list-item-info">
          <strong>${member.name} ${member.isDefault ? '<span class="badge badge-default">Default</span>' : '<span class="badge badge-added">Added</span>'}</strong>
          <span>${member.role}</span>
        </div>
        <button class="delete-btn" onclick="deleteCommittee('${member.id}')" title="Delete member">
          🗑️
        </button>
      </div>
    `).join('');
  }

  window.deleteCommittee = function(id) {
    if (confirm('Are you sure you want to delete this committee member?')) {
      if (id.startsWith('default_')) {
        const deleted = getFromStorage(STORAGE_KEYS.deletedItems);
        if (!deleted.includes(id)) {
          deleted.push(id);
          saveToStorage(STORAGE_KEYS.deletedItems, deleted);
        }
      } else {
        let committee = getFromStorage(STORAGE_KEYS.committee);
        committee = committee.filter(c => c.id !== id);
        saveToStorage(STORAGE_KEYS.committee, committee);
      }
      renderCommittee();
      showToast('Committee member deleted');
    }
  };

  // Add committee member
  committeeForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = committeeNameInput.value.trim();
    const role = committeeRoleInput.value.trim();
    const image = committeeImageInput.value.trim();

    if (!name || !role || !image) return;

    const committee = getFromStorage(STORAGE_KEYS.committee);
    committee.push({
      id: generateId(),
      name,
      role,
      image,
      addedAt: new Date().toISOString()
    });
    saveToStorage(STORAGE_KEYS.committee, committee);

    committeeForm.reset();
    renderCommittee();
    showToast('Committee member added successfully! 👥');
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
