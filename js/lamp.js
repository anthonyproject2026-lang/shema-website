/* "Light the lamp": interactive 3D nilavilakku (model built in Blender, tools/blender/build_lamp.py).
   - Nothing 3D is downloaded until activation:
       data-activate="click"   (home page)  -> on "Light the lamp" / "Explore in 3D"
       data-activate="visible" (kerala.html) -> when within 400px of the viewport (click if Save-Data)
   - Viewer: Google <model-viewer> 4.4.0 (Apache-2.0), vendored, loaded with Subresource Integrity.
   - No JS / no WebGL: the Blender still and the numbered notes remain (they are plain HTML).
   - prefers-reduced-motion: flames never flicker, camera moves are instant. */
(function () {
  'use strict';

  var MV_SRC = '/vendor/model-viewer-4.4.0/model-viewer.min.js';
  var MV_SRI = 'sha384-wjsPzEO+lXOf7d9csIDfAQpPt2OKuUU3m0K9qsdKIuzX4N8czSF6hdh23eAbZa3p';
  var MODEL = '/assets/3d/lamp.glb';
  var DEFAULT_ORBIT = '25deg 72deg 3.4m';
  var DEFAULT_TARGET = '0m 0.34m 0m';
  var DEFAULT_FOV = '30deg';
  var ALT = '3D model of a brass nilavilakku, a traditional Kerala oil lamp, standing on a circular pookalam flower carpet, with an Onam sadhya on a banana leaf and a chenda drum beside it.';

  /* glTF coordinates in metres (x right, y up, z towards the viewer). */
  var HOTSPOTS = [
    { id: 'flame', n: 1, label: 'The flame', pos: '0m 0.69m 0.22m', normal: '0m 0.5m 0.87m', orbit: '0deg 68deg 2.1m', target: '0m 0.62m 0.1m' },
    { id: 'brass', n: 2, label: 'Bell metal and brass', pos: '0.04m 0.38m 0.04m', normal: '0.7m 0m 0.7m', orbit: '30deg 80deg 2.0m', target: '0m 0.4m 0m' },
    { id: 'pookalam', n: 3, label: 'Pookalam', pos: '0.35m 0.02m 0.35m', normal: '0m 1m 0m', orbit: '35deg 40deg 2.6m', target: '0.1m 0m 0.1m' },
    { id: 'sadhya', n: 4, label: 'Onam Sadhya', pos: '-0.71m 0.04m 0.56m', normal: '0m 1m 0m', orbit: '-55deg 50deg 1.9m', target: '-0.6m 0.05m 0.45m' },
    { id: 'chenda', n: 5, label: 'Chenda', pos: '0.66m 0.58m -0.55m', normal: '0m 1m 0m', orbit: '130deg 60deg 2.3m', target: '0.55m 0.3m -0.45m' }
  ];

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var scriptPromise = null;

  function hasWebGL() {
    try {
      var c = document.createElement('canvas');
      return !!(window.WebGLRenderingContext && (c.getContext('webgl2') || c.getContext('webgl')));
    } catch (e) {
      return false;
    }
  }

  /* model-viewer bundles three.js's meshopt decoder, which tries to compile its WebAssembly as soon as the
     module loads. Our model does not use meshopt (it is KHR_mesh_quantization only, no decoder needed),
     and the site CSP deliberately does not allow WebAssembly, so that unused start-up promise is rejected.
     Swallow only that specific rejection so it is not reported as an uncaught error. */
  window.addEventListener('unhandledrejection', function (e) {
    var r = e.reason;
    if (r && /WebAssembly/.test(String(r.message || r)) && scriptPromise) e.preventDefault();
  });

  function loadViewerScript() {
    if (scriptPromise) return scriptPromise;
    scriptPromise = new Promise(function (resolve, reject) {
      if (window.customElements && customElements.get('model-viewer')) return resolve();
      var s = document.createElement('script');
      s.type = 'module';
      s.src = MV_SRC;
      s.integrity = MV_SRI;
      s.crossOrigin = 'anonymous';
      s.onload = function () { customElements.whenDefined('model-viewer').then(resolve, reject); };
      s.onerror = function () { reject(new Error('model-viewer failed to load')); };
      document.head.appendChild(s);
    });
    return scriptPromise;
  }

  function icon(path) {
    return '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + path + '</svg>';
  }

  var ICONS = {
    flame: icon('<path d="M12 3c2 3 5 5 5 9a5 5 0 0 1-10 0c0-2 1-3 2-4 0 2 1 3 2 3 0-3-1-5 1-8z"/>'),
    left: icon('<path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/>'),
    right: icon('<path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 4v5h-5"/>'),
    zin: icon('<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3M11 8v6M8 11h6"/>'),
    zout: icon('<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3M8 11h6"/>'),
    reset: icon('<path d="M3 12a9 9 0 1 0 9-9"/><path d="M3 3v6h6"/><circle cx="12" cy="12" r="2"/>'),
    cube: icon('<path d="M12 2l9 5v10l-9 5-9-5V7z"/><path d="M12 22V12M21 7l-9 5-9-5"/>')
  };

  function button(cls, iconSvg, label, extra) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'tb-btn ' + cls;
    b.innerHTML = iconSvg + '<span class="tb-label">' + label + '</span>';
    Object.keys(extra || {}).forEach(function (k) { b.setAttribute(k, extra[k]); });
    return b;
  }

  function Lamp(section) {
    this.section = section;
    this.stage = section.querySelector('.lamp-viewer');
    this.still = section.querySelector('.lamp-still');
    this.toolbar = section.querySelector('.lamp-toolbar');
    this.status = section.querySelector('.lamp-status');
    this.notes = section.querySelectorAll('.lamp-note');
    this.viewer = null;
    this.flame = null;
    this.lit = false;
    this.wantLit = false;
    this.state = 'idle';
    this.mode = section.getAttribute('data-activate') || 'click';
    if (this.mode === 'visible' && navigator.connection && navigator.connection.saveData) this.mode = 'click';
    this.buildIdleToolbar();
    if (this.mode === 'visible') this.watch();
  }

  Lamp.prototype.announce = function (text) {
    if (!this.status) return;
    this.status.textContent = '';
    var s = this.status;
    setTimeout(function () { s.textContent = text; }, 30);
  };

  Lamp.prototype.buildIdleToolbar = function () {
    var self = this;
    this.toolbar.hidden = false;
    this.toolbar.replaceChildren();
    this.lightBtn = button('tb-light', ICONS.flame, 'Light the lamp', { 'aria-pressed': 'false' });
    this.lightBtn.addEventListener('click', function () {
      if (self.state === 'ready') self.setLit(!self.lit);
      else { self.wantLit = true; self.activate(); }
    });
    this.toolbar.appendChild(this.lightBtn);
    if (this.mode === 'click') {
      var explore = button('tb-explore', ICONS.cube, 'Explore in 3D');
      explore.addEventListener('click', function () { self.activate(true); });
      this.toolbar.appendChild(explore);
      this.exploreBtn = explore;
    }
  };

  Lamp.prototype.watch = function () {
    var self = this;
    if (!('IntersectionObserver' in window)) return this.activate();
    var io = new IntersectionObserver(function (entries) {
      if (entries.some(function (e) { return e.isIntersecting; })) {
        io.disconnect();
        self.activate();
      }
    }, { rootMargin: '400px 0px' });
    io.observe(this.section);
  };

  Lamp.prototype.setBusy = function (busy) {
    this.section.setAttribute('aria-busy', busy ? 'true' : 'false');
    if (this.lightBtn && this.state === 'loading') {
      this.lightBtn.querySelector('.tb-label').textContent = busy ? 'Loading…' : 'Light the lamp';
    }
  };

  Lamp.prototype.activate = function (focusViewer) {
    var self = this;
    if (this.state !== 'idle') return;
    this.state = 'loading';
    this.setBusy(true);
    loadViewerScript().then(function () {
      self.createViewer(focusViewer);
    }).catch(function () { self.fail(); });
  };

  Lamp.prototype.fail = function () {
    this.state = 'failed';
    this.setBusy(false);
    if (this.viewer) this.viewer.remove();
    this.section.classList.remove('is-3d');
    this.toolbar.hidden = true;
    var msg = document.createElement('p');
    msg.className = 'lamp-error';
    msg.textContent = 'The 3D view could not be loaded. The notes below cover the same content.';
    this.stage.after(msg);
  };

  Lamp.prototype.createViewer = function (focusViewer) {
    var self = this;
    var mv = document.createElement('model-viewer');
    var attrs = {
      src: MODEL, alt: ALT, 'camera-controls': '', 'disable-zoom': '', 'disable-pan': '', 'disable-tap': '',
      'touch-action': 'pan-y', 'interaction-prompt': 'none', 'camera-orbit': DEFAULT_ORBIT,
      'camera-target': DEFAULT_TARGET, 'field-of-view': DEFAULT_FOV, 'min-camera-orbit': 'auto 25deg 1.6m',
      'max-camera-orbit': 'auto 88deg 4.6m', 'tone-mapping': 'neutral', exposure: '1', 'shadow-intensity': '0.6',
      'shadow-softness': '1', loading: 'eager', reveal: 'auto', 'animation-name': 'Flicker',
      'aria-describedby': this.section.querySelector('.lamp-describe p').id
    };
    if (reduceMotion.matches) attrs['interpolation-decay'] = '0';
    Object.keys(attrs).forEach(function (k) { mv.setAttribute(k, attrs[k]); });
    mv.className = 'lamp-mv';

    HOTSPOTS.forEach(function (h) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'hotspot';
      b.slot = 'hotspot-' + h.id;
      b.setAttribute('data-position', h.pos);
      b.setAttribute('data-normal', h.normal);
      b.setAttribute('data-visibility-attribute', 'visible');
      b.setAttribute('aria-label', h.n + '. ' + h.label);
      b.textContent = String(h.n);
      b.addEventListener('click', function () { self.focusHotspot(h, true); });
      mv.appendChild(b);
    });

    mv.addEventListener('load', function () { self.onLoad(focusViewer); });
    mv.addEventListener('error', function () { self.fail(); });
    this.viewer = mv;
    this.stage.appendChild(mv);
    this.section.classList.add('is-3d');
  };

  Lamp.prototype.onLoad = function (focusViewer) {
    var self = this;
    var mv = this.viewer;
    this.state = 'ready';
    this.setBusy(false);
    try {
      this.flame = mv.model.getMaterialByName('Flame');
      this.flame.setAlphaMode('BLEND');
    } catch (e) {
      this.flame = null;
    }
    this.setLit(this.wantLit, !this.wantLit);
    this.buildFullToolbar();
    this.notes.forEach(function (note) {
      var b = note.querySelector('.lamp-show');
      if (!b) return;
      b.hidden = false;
      b.addEventListener('click', function () {
        var h = HOTSPOTS.filter(function (x) { return x.id === b.getAttribute('data-hotspot'); })[0];
        if (h) self.focusHotspot(h, false);
      });
    });
    this.section.classList.add('is-ready');
    if (focusViewer) {
      var inner = mv.shadowRoot && mv.shadowRoot.querySelector('.userInput');
      (inner || mv).focus();
    }
  };

  Lamp.prototype.buildFullToolbar = function () {
    var self = this;
    if (this.exploreBtn) this.exploreBtn.remove();
    this.lightBtn.querySelector('.tb-label').textContent = this.lit ? 'Put out the lamp' : 'Light the lamp';
    var add = function (cls, ic, label, fn) {
      var b = button(cls, ic, label);
      b.addEventListener('click', fn);
      self.toolbar.appendChild(b);
      return b;
    };
    add('tb-left', ICONS.left, 'Rotate left', function () { self.orbitBy(-30, 1); });
    add('tb-right', ICONS.right, 'Rotate right', function () { self.orbitBy(30, 1); });
    add('tb-zin', ICONS.zin, 'Zoom in', function () { self.orbitBy(0, 0.85); });
    add('tb-zout', ICONS.zout, 'Zoom out', function () { self.orbitBy(0, 1.15); });
    add('tb-reset', ICONS.reset, 'Reset view', function () { self.reset(); });
  };

  Lamp.prototype.jump = function () {
    if (reduceMotion.matches && this.viewer.jumpCameraToGoal) this.viewer.jumpCameraToGoal();
  };

  Lamp.prototype.orbitBy = function (deg, scale) {
    var o = this.viewer.getCameraOrbit();
    var radius = Math.min(4.6, Math.max(1.6, o.radius * scale));
    this.viewer.cameraOrbit = (o.theta + deg * Math.PI / 180) + 'rad ' + o.phi + 'rad ' + radius + 'm';
    this.jump();
  };

  Lamp.prototype.reset = function () {
    this.viewer.cameraOrbit = DEFAULT_ORBIT;
    this.viewer.cameraTarget = DEFAULT_TARGET;
    this.viewer.fieldOfView = DEFAULT_FOV;
    this.notes.forEach(function (n) { n.removeAttribute('aria-current'); });
    this.jump();
  };

  Lamp.prototype.focusHotspot = function (h, fromHotspot) {
    this.viewer.cameraOrbit = h.orbit;
    this.viewer.cameraTarget = h.target;
    this.jump();
    var current = null;
    this.notes.forEach(function (n) {
      var on = n.getAttribute('data-hotspot') === h.id;
      if (on) { n.setAttribute('aria-current', 'true'); current = n; } else n.removeAttribute('aria-current');
    });
    if (current && fromHotspot && window.matchMedia('(max-width: 900px)').matches) {
      current.scrollIntoView({ block: 'nearest', behavior: reduceMotion.matches ? 'auto' : 'smooth' });
    }
    this.announce(h.n + '. ' + h.label);
  };

  Lamp.prototype.setLit = function (lit, silent) {
    var mv = this.viewer;
    this.lit = lit;
    if (this.flame) {
      this.flame.pbrMetallicRoughness.setBaseColorFactor(lit ? [0.9, 0.67, 0.25, 1] : [0.9, 0.67, 0.25, 0]);
      this.flame.setEmissiveFactor(lit ? [0.87, 0.4, 0.03] : [0, 0, 0]);
    }
    mv.exposure = lit ? 1.15 : 1;
    this.section.classList.toggle('is-lit', lit);
    if (lit && !reduceMotion.matches) mv.play({ repetitions: Infinity });
    else mv.pause();
    this.lightBtn.setAttribute('aria-pressed', String(lit));
    this.lightBtn.querySelector('.tb-label').textContent = lit ? 'Put out the lamp' : 'Light the lamp';
    if (!silent) this.announce(lit ? 'The lamp is lit.' : 'The lamp is out.');
  };

  function init() {
    if (!hasWebGL()) return;
    document.querySelectorAll('[data-lamp]').forEach(function (section) { section.lampViewer = new Lamp(section); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
