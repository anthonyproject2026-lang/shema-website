/* ============================================
   SHEMA Website — Interactive Scripts
   Kerala Mural & Kasavu Redesign
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Load Admin Content from LocalStorage ---------- */
  function loadAdminContent() {
    // Hide deleted items
    try {
      const deletedIds = JSON.parse(localStorage.getItem('shema_deleted_items') || '[]');
      deletedIds.forEach(id => {
        const element = document.querySelector(`[data-id="${id}"]`);
        if (element) element.remove();
      });
    } catch (e) {
      console.error('Error hiding deleted items:', e);
    }

    // Load Photos
    const highlightsGrid = document.querySelector('.highlights-grid');
    if (highlightsGrid) {
      try {
        const adminPhotos = JSON.parse(localStorage.getItem('shema_admin_photos') || '[]');
        adminPhotos.forEach(photo => {
          const card = document.createElement('div');
          card.className = 'highlight-card reveal';
          card.setAttribute('data-id', photo.id);
          card.innerHTML = `
            <img src="${photo.url}" alt="${photo.caption}" loading="lazy" />
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

    // Load Events
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
                ${event.location ? `<span class="event-location"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg> ${event.location}</span>` : ''}
              </div>
            </div>
          `;
          eventsGrid.insertBefore(card, eventsGrid.firstChild);
        });
      } catch (e) {
        console.error('Error loading admin events:', e);
      }
    }

    // Load Kerala Heritage Features
    const carouselTrack = document.getElementById('carouselTrack');
    if (carouselTrack) {
      try {
        const adminFeatures = JSON.parse(localStorage.getItem('shema_admin_features') || '[]');
        adminFeatures.forEach(feature => {
          const card = document.createElement('div');
          card.className = 'kerala-card';
          card.setAttribute('data-id', feature.id);
          card.innerHTML = `
            <img src="${feature.image}" alt="${feature.title}" loading="lazy" />
            <div class="kerala-card-overlay">
              <span class="kerala-card-tag">${feature.tag}</span>
              <h3>${feature.title}</h3>
              <p>${feature.description}</p>
            </div>
          `;
          carouselTrack.appendChild(card);
        });
      } catch (e) {
        console.error('Error loading admin features:', e);
      }
    }
  }

  loadAdminContent();

  /* ---------- Navbar scroll effect ---------- */
  const navbar = document.getElementById('navbar');
  const scrollThreshold = 80;

  function updateNavbar() {
    navbar.classList.toggle('scrolled', window.scrollY > scrollThreshold);
  }
  window.addEventListener('scroll', updateNavbar, { passive: true });
  updateNavbar();

  /* ---------- Mobile nav toggle with aria-expanded ---------- */
  const navToggle = document.getElementById('navToggle');
  const navLinks = document.getElementById('navLinks');

  navToggle.addEventListener('click', () => {
    const isOpen = navLinks.classList.toggle('active');
    navToggle.setAttribute('aria-expanded', isOpen);
    const spans = navToggle.querySelectorAll('span');
    if (isOpen) {
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
      navToggle.setAttribute('aria-expanded', 'false');
      const spans = navToggle.querySelectorAll('span');
      spans[0].style.transform = 'none';
      spans[1].style.opacity = '1';
      spans[2].style.transform = 'none';
    });
  });

  /* ---------- Smooth scroll for anchor links ---------- */
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const href = anchor.getAttribute('href');
      if (href === '#') return;
      e.preventDefault();
      const target = document.querySelector(href);
      if (target) {
        const offset = navbar.offsetHeight + 10;
        const targetPosition = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top: targetPosition, behavior: prefersReducedMotion ? 'auto' : 'smooth' });
      }
    });
  });

  /* ---------- Scroll-reveal with IntersectionObserver ---------- */
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

  document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

  /* ---------- Back to top ---------- */
  const backToTop = document.getElementById('backToTop');

  function toggleBackToTop() {
    backToTop.classList.toggle('show', window.scrollY > 500);
  }
  window.addEventListener('scroll', toggleBackToTop, { passive: true });

  backToTop.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: prefersReducedMotion ? 'auto' : 'smooth' });
  });

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
          link.style.color = 'var(--kavi, #C6822B)';
        }
      }
    });
  }
  window.addEventListener('scroll', highlightNavLink, { passive: true });

  /* ============================================
     Kerala Heritage Carousel
     ============================================ */
  const carouselTrack = document.getElementById('carouselTrack');
  const carouselPrev = document.getElementById('carouselPrev');
  const carouselNext = document.getElementById('carouselNext');
  const carouselDots = document.getElementById('carouselDots');
  const carouselPauseBtn = document.getElementById('carouselPauseBtn');

  if (carouselTrack && carouselPrev && carouselNext && carouselDots) {
    const cards = carouselTrack.querySelectorAll('.kerala-card');
    const totalSlides = cards.length;
    let currentSlide = 0;
    let autoPlayInterval = null;
    let isPaused = false;

    // Create dot indicators
    for (let i = 0; i < totalSlides; i++) {
      const dot = document.createElement('button');
      dot.className = 'carousel-dot' + (i === 0 ? ' active' : '');
      dot.setAttribute('aria-label', `Go to slide ${i + 1}`);
      dot.addEventListener('click', () => { goToSlide(i); resetAutoPlay(); });
      carouselDots.appendChild(dot);
    }
    const dots = carouselDots.querySelectorAll('.carousel-dot');

    // Create slide counter with aria-live
    const counterEl = document.createElement('div');
    counterEl.className = 'carousel-counter';
    counterEl.setAttribute('aria-live', 'polite');
    counterEl.textContent = `1 / ${totalSlides}`;
    carouselDots.parentElement.insertBefore(counterEl, carouselPauseBtn);

    function goToSlide(index) {
      if (index < 0) index = totalSlides - 1;
      if (index >= totalSlides) index = 0;
      currentSlide = index;
      carouselTrack.style.transform = `translateX(-${currentSlide * 100}%)`;
      dots.forEach((dot, i) => dot.classList.toggle('active', i === currentSlide));
      counterEl.textContent = `${currentSlide + 1} / ${totalSlides}`;
    }

    carouselPrev.addEventListener('click', () => { goToSlide(currentSlide - 1); resetAutoPlay(); });
    carouselNext.addEventListener('click', () => { goToSlide(currentSlide + 1); resetAutoPlay(); });

    // Keyboard — scoped to when carousel is visible and focused
    const keralaCarousel = document.getElementById('keralaCarousel');
    keralaCarousel.setAttribute('tabindex', '0');
    keralaCarousel.setAttribute('role', 'region');
    keralaCarousel.setAttribute('aria-roledescription', 'carousel');
    keralaCarousel.setAttribute('aria-label', 'Kerala Heritage');

    keralaCarousel.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft') {
        goToSlide(currentSlide - 1); resetAutoPlay();
        e.preventDefault();
      } else if (e.key === 'ArrowRight') {
        goToSlide(currentSlide + 1); resetAutoPlay();
        e.preventDefault();
      }
    });

    // Touch/swipe
    let touchStartX = 0;
    const carouselViewport = document.getElementById('carouselViewport');

    carouselViewport.addEventListener('touchstart', (e) => {
      touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    carouselViewport.addEventListener('touchend', (e) => {
      const diff = touchStartX - e.changedTouches[0].screenX;
      if (Math.abs(diff) > 50) {
        goToSlide(diff > 0 ? currentSlide + 1 : currentSlide - 1);
        resetAutoPlay();
      }
    }, { passive: true });

    // Auto-play — gated behind IntersectionObserver + reduced-motion
    function startAutoPlay() {
      if (prefersReducedMotion || isPaused) return;
      stopAutoPlay();
      autoPlayInterval = setInterval(() => goToSlide(currentSlide + 1), 5000);
    }

    function stopAutoPlay() {
      if (autoPlayInterval) {
        clearInterval(autoPlayInterval);
        autoPlayInterval = null;
      }
    }

    function resetAutoPlay() {
      if (!isPaused) {
        stopAutoPlay();
        startAutoPlay();
      }
    }

    // Only autoplay when carousel is visible
    const carouselObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && !isPaused) {
          startAutoPlay();
        } else {
          stopAutoPlay();
        }
      });
    }, { threshold: 0.3 });
    carouselObserver.observe(keralaCarousel);

    // Pause on hover
    keralaCarousel.addEventListener('mouseenter', stopAutoPlay);
    keralaCarousel.addEventListener('mouseleave', () => { if (!isPaused) startAutoPlay(); });

    // Pause on focus, resume on blur (WCAG 2.2.2)
    keralaCarousel.addEventListener('focusin', stopAutoPlay);
    keralaCarousel.addEventListener('focusout', () => { if (!isPaused) startAutoPlay(); });

    // Pause/Play button (WCAG 2.2.2)
    if (carouselPauseBtn) {
      const pauseIcon = document.getElementById('pauseIcon');
      const playIcon = document.getElementById('playIcon');

      carouselPauseBtn.addEventListener('click', () => {
        isPaused = !isPaused;
        carouselPauseBtn.setAttribute('aria-pressed', isPaused);
        carouselPauseBtn.setAttribute('aria-label', isPaused ? 'Play carousel' : 'Pause carousel');

        if (isPaused) {
          stopAutoPlay();
          if (pauseIcon) pauseIcon.style.display = 'none';
          if (playIcon) playIcon.style.display = 'block';
        } else {
          if (pauseIcon) pauseIcon.style.display = 'block';
          if (playIcon) playIcon.style.display = 'none';
          startAutoPlay();
        }
      });
    }
  }

  /* ============================================
     Video — Auto-stop on end & scroll-out
     ============================================ */
  const videoPlayBtn = document.getElementById('videoPlayBtn');
  const keralaVideo = document.getElementById('keralaVideo');
  const videoOverlay = document.getElementById('videoOverlay');

  if (videoPlayBtn && keralaVideo && videoOverlay) {
    const showOverlay = () => {
      videoOverlay.style.opacity = '1';
      videoOverlay.style.visibility = 'visible';
      keralaVideo.controls = false;
    };

    const hideOverlay = () => {
      videoOverlay.style.opacity = '0';
      videoOverlay.style.visibility = 'hidden';
      keralaVideo.controls = true;
    };

    const playVideo = () => {
      keralaVideo.play().catch(err => console.error('Video play failed:', err));
      hideOverlay();
    };

    videoPlayBtn.addEventListener('click', (e) => { e.stopPropagation(); playVideo(); });
    videoOverlay.addEventListener('click', playVideo);
    keralaVideo.addEventListener('ended', showOverlay);
    keralaVideo.addEventListener('pause', showOverlay);

    keralaVideo.addEventListener('click', () => {
      if (keralaVideo.paused) playVideo();
      else keralaVideo.pause();
    });

    // Auto-pause when scrolled out of view
    const videoObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting && !keralaVideo.paused) {
          keralaVideo.pause();
        }
      });
    }, { threshold: 0.25 });
    videoObserver.observe(keralaVideo);
  }

  console.log('🌿 SHEMA Website loaded successfully');
});
