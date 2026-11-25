/* SHEMA website: shared behaviour for every page.
   - forwards old home-page #hashes to their new homes
   - accessible mobile menu (aria-expanded, Escape, focus return)
   - one fade-and-rise reveal, off under prefers-reduced-motion
   - back-to-top after 1.5 screens
   Events (js/events.js) and the 3D lamp (js/lamp.js) live in their own files. */
(function () {
  'use strict';

  var docEl = document.documentElement;
  docEl.classList.add('js');
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  /* ---------- Old #hash forwarding (home page only) ---------- */
  var FORWARD = {
    video: '/kerala.html#journey',
    kerala: '/kerala.html#heritage',
    culture: '/kerala.html#traditions',
    landmarks: '/kerala.html#landmarks',
    products: '/kerala.html#crafts',
    community: '#about',
    highlights: '#photos',
    'leadership-history': '#committee',
    hero: '#top'
  };

  function forwardHash() {
    if (document.body.getAttribute('data-page') !== 'home') return;
    var key = decodeURIComponent(location.hash.slice(1));
    var target = FORWARD[key];
    if (!target) return;
    if (target.charAt(0) === '/') {
      location.replace(target);
      return;
    }
    history.replaceState(null, '', target);
    var el = document.getElementById(target.slice(1));
    if (el) el.scrollIntoView();
  }
  forwardHash();
  window.addEventListener('hashchange', forwardHash);

  /* ---------- Mobile menu ---------- */
  var toggle = document.getElementById('navToggle');
  var links = document.getElementById('navLinks');
  if (toggle && links) {
    var setMenu = function (open, restoreFocus) {
      toggle.setAttribute('aria-expanded', String(open));
      links.classList.toggle('is-open', open);
      if (open) {
        var first = links.querySelector('a');
        if (first) first.focus();
      } else if (restoreFocus) {
        toggle.focus();
      }
    };
    toggle.addEventListener('click', function () {
      setMenu(toggle.getAttribute('aria-expanded') !== 'true', false);
    });
    links.addEventListener('click', function (e) {
      if (e.target.closest('a')) setMenu(false, false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') setMenu(false, true);
    });
    document.addEventListener('click', function (e) {
      if (toggle.getAttribute('aria-expanded') === 'true' && !e.target.closest('.site-nav')) setMenu(false, false);
    });
    var header = toggle.closest('.site-header');
    if (header) {
      header.addEventListener('focusout', function (e) {
        if (toggle.getAttribute('aria-expanded') === 'true' && e.relatedTarget && !header.contains(e.relatedTarget)) {
          setMenu(false, false);
        }
      });
    }
    window.matchMedia('(min-width: 961px)').addEventListener('change', function () { setMenu(false, false); });
  }

  /* ---------- Move focus to in-page targets (skip link, nav) ---------- */
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[href^="#"]');
    if (!a) return;
    var id = a.getAttribute('href').slice(1);
    var target = id && document.getElementById(id);
    if (!target) return;
    if (!target.hasAttribute('tabindex') && !/^(A|BUTTON|INPUT|SELECT|TEXTAREA)$/.test(target.tagName)) {
      target.setAttribute('tabindex', '-1');
    }
    setTimeout(function () { target.focus({ preventScroll: true }); }, 0);
  });

  /* ---------- One reveal: fade and rise 12px, 400ms, once ----------
     Content is never hidden before JS runs; elements already on screen are left alone. */
  if (!reduceMotion.matches && 'IntersectionObserver' in window) {
    var pending = [];
    document.querySelectorAll('.reveal').forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.top > window.innerHeight) pending.push(el);
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-revealing');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px 10% 0px' });
    pending.forEach(function (el) { io.observe(el); });
  }

  /* ---------- Back to top ---------- */
  var toTop = document.getElementById('backToTop');
  if (toTop) {
    var onScroll = function () {
      toTop.classList.toggle('is-visible', window.scrollY > window.innerHeight * 1.5);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    toTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: reduceMotion.matches ? 'auto' : 'smooth' });
      var brand = document.querySelector('.brand');
      if (brand) brand.focus({ preventScroll: true });
    });
  }

  /* ---------- Kerala video: pause when scrolled away ---------- */
  var video = document.getElementById('keralaVideo');
  if (video && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting && !video.paused) video.pause();
      });
    }, { threshold: 0.25 }).observe(video);
  }
})();
