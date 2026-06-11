/* ============================================
   SHEMA Website — Interactive Scripts
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ---------- Image Fade-In on Load ---------- */
  document.querySelectorAll('img').forEach(img => {
    if (img.complete) {
      img.classList.add('loaded');
    } else {
      img.addEventListener('load', () => img.classList.add('loaded'));
      img.addEventListener('error', () => img.classList.add('loaded')); // show placeholder on error
    }
  });

  /* ---------- Load Admin Content from LocalStorage ---------- */
  function loadAdminContent() {
    // 0. Hide deleted items (both defaults and custom)
    try {
      const deletedIds = JSON.parse(localStorage.getItem('shema_deleted_items') || '[]');
      deletedIds.forEach(id => {
        const element = document.querySelector(`[data-id="${id}"]`);
        if (element) {
          element.remove();
        }
      });
    } catch (e) {
      console.error('Error hiding deleted items:', e);
    }

    // 1. Load Photos
    const highlightsGrid = document.querySelector('.highlights-grid');
    if (highlightsGrid) {
      try {
        const adminPhotos = JSON.parse(localStorage.getItem('shema_admin_photos') || '[]');
        adminPhotos.forEach(photo => {
          const card = document.createElement('div');
          card.className = 'highlight-card reveal';
          card.setAttribute('data-id', photo.id);
          card.innerHTML = `
            <img src="${photo.url}" alt="${photo.caption}" class="loaded" onerror="this.src='images/shema-logo.png'" />
            <div class="highlight-card-info">
              <h3>${photo.caption}</h3>
              <p>${photo.description || ''}</p>
            </div>
          `;
          highlightsGrid.appendChild(card);
        });
      } catch (e) {
        console.error('Error loading admin photos:', e);
      }
    }

    // 2. Load Events
    const eventsGrid = document.getElementById('eventsGrid');
    if (eventsGrid) {
      try {
        const adminEvents = JSON.parse(localStorage.getItem('shema_admin_events') || '[]');
        const MONTHS = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
        
        adminEvents.forEach(event => {
          let month = 'EVT';
          let day = '00';
          if (event.date) {
            const d = new Date(event.date + 'T00:00:00');
            month = MONTHS[d.getMonth()] || 'EVT';
            day = String(d.getDate()).padStart(2, '0');
          }
          
          const card = document.createElement('div');
          card.className = 'event-card reveal';
          card.setAttribute('data-id', event.id);
          card.innerHTML = `
            <div class="event-date-badge">
              <span class="event-month">${month}</span>
              <span class="event-day">${day}</span>
            </div>
            <div class="event-card-content">
              <h3>${event.title}</h3>
              <p>${event.description}</p>
              <div class="event-meta">
                ${event.location ? `<span class="event-location">📍 ${event.location}</span>` : ''}
              </div>
            </div>
          `;
          eventsGrid.insertBefore(card, eventsGrid.firstChild);
        });
      } catch (e) {
        console.error('Error loading admin events:', e);
      }
    }

    // 3. Load Kerala Heritage Features
    const keralaGrid = document.querySelector('.kerala-grid');
    if (keralaGrid) {
      try {
        const adminFeatures = JSON.parse(localStorage.getItem('shema_admin_features') || '[]');
        adminFeatures.forEach(feature => {
          const card = document.createElement('div');
          card.className = 'kerala-card reveal';
          card.setAttribute('data-id', feature.id);
          card.innerHTML = `
            <img src="${feature.image}" alt="${feature.title}" class="loaded" onerror="this.src='images/shema-logo.png'" />
            <div class="kerala-card-overlay">
              <span class="kerala-card-tag">${feature.tag}</span>
              <h3>${feature.title}</h3>
              <p>${feature.description}</p>
            </div>
          `;
          keralaGrid.appendChild(card);
        });
      } catch (e) {
        console.error('Error loading admin features:', e);
      }
    }
  }

  loadAdminContent();

  /* ---------- Preloader ---------- */
  const preloader = document.getElementById('preloader');
  window.addEventListener('load', () => {
    setTimeout(() => preloader.classList.add('hidden'), 800);
  });
  // Fallback: hide preloader after 3s max
  setTimeout(() => preloader.classList.add('hidden'), 3000);

  /* ---------- Navbar scroll effect ---------- */
  const navbar = document.getElementById('navbar');
  const scrollThreshold = 80;

  function updateNavbar() {
    if (window.scrollY > scrollThreshold) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  }
  window.addEventListener('scroll', updateNavbar, { passive: true });
  updateNavbar();

  /* ---------- Mobile nav toggle ---------- */
  const navToggle = document.getElementById('navToggle');
  const navLinks = document.getElementById('navLinks');

  navToggle.addEventListener('click', () => {
    navLinks.classList.toggle('active');
    // Animate hamburger
    const spans = navToggle.querySelectorAll('span');
    if (navLinks.classList.contains('active')) {
      spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
      spans[1].style.opacity = '0';
      spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
    } else {
      spans[0].style.transform = 'none';
      spans[1].style.opacity = '1';
      spans[2].style.transform = 'none';
    }
  });

  // Close mobile nav on link click
  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      navLinks.classList.remove('active');
      const spans = navToggle.querySelectorAll('span');
      spans[0].style.transform = 'none';
      spans[1].style.opacity = '1';
      spans[2].style.transform = 'none';
    });
  });

  /* ---------- Smooth scroll for anchor links ---------- */
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        const offset = navbar.offsetHeight + 10;
        const targetPosition = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top: targetPosition, behavior: 'smooth' });
      }
    });
  });

  /* ---------- Scroll-reveal with IntersectionObserver ---------- */
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target); // stop observing once revealed
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });

  document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

  /* ---------- Counter animation ---------- */
  const counters = document.querySelectorAll('.stat-number[data-count]');
  let countersAnimated = false;

  function animateCounters() {
    if (countersAnimated) return;
    const statsBar = document.querySelector('.stats-bar');
    if (!statsBar) return;

    const rect = statsBar.getBoundingClientRect();
    if (rect.top < window.innerHeight && rect.bottom > 0) {
      countersAnimated = true;
      counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-count'));
        const duration = 2000;
        const increment = target / (duration / 16);
        let current = 0;

        function updateCounter() {
          current += increment;
          if (current < target) {
            counter.textContent = Math.floor(current) + '+';
            requestAnimationFrame(updateCounter);
          } else {
            counter.textContent = target + '+';
          }
        }
        updateCounter();
      });
    }
  }
  window.addEventListener('scroll', animateCounters, { passive: true });
  animateCounters();

  /* ---------- Back to top ---------- */
  const backToTop = document.getElementById('backToTop');
  
  function toggleBackToTop() {
    if (window.scrollY > 600) {
      backToTop.classList.add('show');
    } else {
      backToTop.classList.remove('show');
    }
  }
  window.addEventListener('scroll', toggleBackToTop, { passive: true });
  
  backToTop.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  /* ---------- Kerala cards stagger animation ---------- */
  const keralaCards = document.querySelectorAll('.kerala-card');
  keralaCards.forEach((card, index) => {
    card.style.transitionDelay = `${index * 0.1}s`;
  });

  /* ---------- Culture items stagger ---------- */
  const cultureItems = document.querySelectorAll('.culture-item');
  cultureItems.forEach((item, index) => {
    item.style.transitionDelay = `${index * 0.08}s`;
  });

  /* ---------- Parallax-like subtle effect on hero ---------- */
  const heroBg = document.querySelector('.hero-bg img');
  if (heroBg) {
    window.addEventListener('scroll', () => {
      const scrolled = window.scrollY;
      if (scrolled < window.innerHeight) {
        heroBg.style.transform = `scale(${1 + scrolled * 0.0002}) translateY(${scrolled * 0.3}px)`;
      }
    }, { passive: true });
  }

  /* ---------- Active nav link highlighting ---------- */
  const sections = document.querySelectorAll('section[id]');
  
  function highlightNavLink() {
    const scrollPos = window.scrollY + navbar.offsetHeight + 100;
    
    sections.forEach(section => {
      const top = section.offsetTop;
      const height = section.offsetHeight;
      const id = section.getAttribute('id');
      const link = navLinks.querySelector(`a[href="#${id}"]`);
      
      if (link && scrollPos >= top && scrollPos < top + height) {
        navLinks.querySelectorAll('a').forEach(a => a.style.color = '');
        if (!link.classList.contains('nav-cta')) {
          link.style.color = '#F9A825';
        }
      }
    });
  }
  window.addEventListener('scroll', highlightNavLink, { passive: true });

  /* ---------- Video play button interaction ---------- */
  const videoPlayBtn = document.getElementById('videoPlayBtn');
  const keralaVideo = document.getElementById('keralaVideo');
  const videoOverlay = document.getElementById('videoOverlay');

  if (videoPlayBtn && keralaVideo && videoOverlay) {
    videoPlayBtn.addEventListener('click', () => {
      keralaVideo.play();
      videoOverlay.style.opacity = '0';
      videoOverlay.style.visibility = 'hidden';
      keralaVideo.controls = true;
    });

    keralaVideo.addEventListener('pause', () => {
      videoOverlay.style.opacity = '1';
      videoOverlay.style.visibility = 'visible';
      keralaVideo.controls = false;
    });

    keralaVideo.addEventListener('click', () => {
      if (keralaVideo.paused) {
        keralaVideo.play();
        videoOverlay.style.opacity = '0';
        videoOverlay.style.visibility = 'hidden';
        keralaVideo.controls = true;
      } else {
        keralaVideo.pause();
      }
    });
  }

  /* ---------- Tilt effect on Kerala heritage cards ---------- */
  document.querySelectorAll('.kerala-card').forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      card.style.transform = `perspective(800px) rotateY(${x * 6}deg) rotateX(${-y * 6}deg) scale(1.02)`;
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
    });
  });

  console.log('🌿 SHEMA Website loaded successfully');
});

