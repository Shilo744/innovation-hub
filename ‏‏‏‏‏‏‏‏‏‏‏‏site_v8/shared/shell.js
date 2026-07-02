/* ============================================================
   SHARED SHELL — injects the nav, accessibility panel, side-dot
   nav, footer and contact modal into every top-level page, then
   wires up all shared chrome behaviour (scroll state, a11y,
   modal, dot-nav, section reveals, arrow-key nav, page-leave
   transition, iframe auto-height bus).

   Each page declares ONLY its own data before loading this file:

     <script>window.IH_PAGE = {
       base: '../',                 // '' for the root page, '../' for a sub-page
       active: 'about',             // which nav item is current
       sections: [{id,label}, ...], // dot-nav + arrow-key targets
       darkIds: ['about-hero']      // section ids that use a dark background
     };</script>
     <script src="../shared/shell.js"></script>

   The nav/footer/modal are injected directly into the document
   (NOT an iframe) so fixed positioning, the scroll effect and the
   dropdown all behave natively.
============================================================ */
(function () {
  var CFG = window.IH_PAGE || {};
  var base = CFG.base || '';
  var active = CFG.active || '';
  var SECTIONS = CFG.sections || [];
  var darkIds = new Set(CFG.darkIds || []);

  var isCompiled = !document.querySelector('script[src*="shell.js"]');
  if (isCompiled) {
    base = '';
  }

  function url(p) {
    if (isCompiled && p) {
      if (p.indexOf('index.html') !== -1) {
        if (p === 'index.html') return 'index.html';
        var parts = p.split('/');
        if (parts.length >= 2) {
          return parts[parts.length - 2] + '.html';
        }
      }
    }
    return base + p;
  }
  var homeHref = (active === 'home') ? '#top' : url('index.html');

  function topLink(key, label, page) {
    return '<li><a href="' + url(page) + '"' + (active === key ? ' class="active"' : '') + '>' + label + '</a></li>';
  }
  function footLink(key, label, page) {
    return '<a href="' + url(page) + '"' + (active === key ? ' class="active"' : '') + '>' + label + '</a>';
  }

  /* ---------- shared contact + program data (single source of truth) ---------- */
  var CONTACT = {
    email: 'Rh.innovationhub@gmail.com',
    phone: '+972 50-976-0346',
    phoneHref: 'tel:+972509760346',
    linkedin: 'https://il.linkedin.com/company/resilience-health-innovation-hub',
    facebook: 'https://www.facebook.com/profile.php?id=61560256910952'
  };
  var EXT = {
    shebaSderot: 'https://www.resiliencetechhub.org/sheba-sderot',
    accelerator: 'https://www.resilience-accelerator.com/',
    immediate: 'https://www.resiliencetechhub.org/blank-7'
  };
  function extLink(href, label) {
    return '<a href="' + href + '" target="_blank" rel="noopener noreferrer">' + label + '</a>';
  }

  /* ---------- markup ---------- */
  var navHTML =
    '<a class="skip-link" href="#ih-main">Skip to main content</a>' +
    '<nav class="nav" id="nav" aria-label="Main navigation">' +
      '<a href="' + homeHref + '" class="brand"><img src="' + url('assets/logo.png') + '" alt="Innovation Hub logo"><span>Innovation Hub</span></a>' +
      '<ul class="nav-links">' +
        '<li><a href="' + homeHref + '"' + (active === 'home' ? ' class="active"' : '') + '>Home</a></li>' +
        topLink('about', 'About', 'about/index.html') +
        '<li><a href="' + url('programs/index.html') + '"' + (active === 'programs' ? ' class="active"' : '') + '>Strategic Pillars <span class="caret">▾</span></a>' +
          '<div class="menu">' +
            '<a href="' + url('programs/index.html') + '">Investments Fund</a>' +
            '<a href="' + url('programs/index.html') + '">R&amp;D</a>' +
            '<a href="' + url('programs/index.html') + '">Venture Creation</a>' +
            '<a href="' + url('programs/index.html') + '">MEITAL Program</a>' +
            extLink(EXT.shebaSderot, 'Sheba to Sderot ↗') +
            extLink(EXT.accelerator, 'Resilience Accelerator ↗') +
            extLink(EXT.immediate, 'Immediate Implementation ↗') +
          '</div>' +
        '</li>' +
        topLink('team', 'Team', 'team/index.html') +
        topLink('events', 'Events', 'events/index.html') +
        topLink('updates', 'Updates', 'updates/index.html') +
        topLink('ecosystem', 'Ecosystem', 'ecosystem/index.html') +
      '</ul>' +
      '<div class="tools">' +
        '<button class="ic" id="a11yBtn" aria-label="Accessibility menu" title="Accessibility">' +
          '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="4" r="2"/><path d="M19 13l-5-1v9M5 13l5-1M9 22V15M15 22l-1-7"/></svg>' +
        '</button>' +
        '<button class="lang" aria-label="עברית" title="Switch to Hebrew">עב</button>' +
        '<button class="cta-nav" data-action="open-modal">Contact Us</button>' +
        '<button class="burger" aria-label="Open menu"><span></span></button>' +
      '</div>' +
    '</nav>';

  var a11yHTML =
    '<aside class="a11y" id="a11yPanel" aria-hidden="true">' +
      '<h4>Accessibility</h4>' +
      '<div class="row"><span>Text size</span><div class="btns">' +
        '<button class="btn-s on" data-fs="">A</button>' +
        '<button class="btn-s" data-fs="fs-lg">A+</button>' +
        '<button class="btn-s" data-fs="fs-xl">A++</button>' +
      '</div></div>' +
      '<div class="row"><span>High contrast</span><button class="btn-s" id="hcBtn">Off</button></div>' +
      '<div class="row"><span>Underline links</span><button class="btn-s" id="ulBtn">Off</button></div>' +
      '<div class="row"><span>Reduce motion</span><button class="btn-s" id="rmBtn">Off</button></div>' +
    '</aside>';

  var dotnavHTML = '<nav class="dotnav" id="dotnav" aria-label="Section navigation"></nav>';

  var footerHTML =
    '<footer class="footer">' +
      '<div class="foot-grid">' +
        '<div>' +
          '<div class="foot-brand"><img src="' + url('assets/logo.png') + '" alt="">Innovation Hub</div>' +
          '<p class="foot-about">A global resilience innovation hub turning the hardest human challenges into the next generation of breakthrough technologies.</p>' +
          '<div class="social">' +
            '<a href="' + CONTACT.linkedin + '" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn" title="LinkedIn"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14M8.34 18.34V10.67H5.67v7.67h2.67M7 9.5a1.55 1.55 0 1 0 0-3.1 1.55 1.55 0 0 0 0 3.1m11.34 8.84v-4.2c0-2.32-1.24-3.4-2.9-3.4-1.34 0-1.94.74-2.27 1.26v-1.07h-2.67v7.67h2.67v-4.28c0-.39.03-.77.14-1.04.31-.77 1.01-1.57 2.19-1.57 1.55 0 2.17 1.18 2.17 2.91v3.98h2.67"/></svg></a>' +
            '<a href="' + CONTACT.facebook + '" target="_blank" rel="noopener noreferrer" aria-label="Facebook" title="Facebook"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M22 12.06C22 6.5 17.52 2 12 2S2 6.5 2 12.06c0 5.02 3.66 9.18 8.44 9.94v-7.03H7.9v-2.9h2.54V9.85c0-2.52 1.5-3.91 3.78-3.91 1.09 0 2.24.2 2.24.2v2.47h-1.26c-1.24 0-1.63.77-1.63 1.57v1.88h2.78l-.45 2.9h-2.33V22c4.78-.76 8.44-4.92 8.44-9.94Z"/></svg></a>' +
            '<a href="' + url('index.html') + '#ecosystem-bridge" aria-label="Watch our video" title="Watch our video"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M21.6 7.2a2.5 2.5 0 0 0-1.76-1.77C18.27 5 12 5 12 5s-6.27 0-7.84.43A2.5 2.5 0 0 0 2.4 7.2 26.2 26.2 0 0 0 2 12a26.2 26.2 0 0 0 .4 4.8 2.5 2.5 0 0 0 1.76 1.77C5.73 19 12 19 12 19s6.27 0 7.84-.43a2.5 2.5 0 0 0 1.76-1.77A26.2 26.2 0 0 0 22 12a26.2 26.2 0 0 0-.4-4.8M10 15V9l5.2 3-5.2 3Z"/></svg></a>' +
            '<a href="mailto:' + CONTACT.email + '" aria-label="Email us" title="Email us"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 7 10 6L22 7"/></svg></a>' +
          '</div>' +
        '</div>' +
        '<div class="foot-col">' +
          '<h5>Explore</h5>' +
          footLink('home', 'Home', 'index.html') +
          footLink('about', 'About', 'about/index.html') +
          footLink('programs', 'Programs', 'programs/index.html') +
          footLink('team', 'Team', 'team/index.html') +
          footLink('events', 'Events', 'events/index.html') +
        '</div>' +
        '<div class="foot-col">' +
          '<h5>Strategic Pillars</h5>' +
          '<a href="' + url('programs/index.html') + '">Investments Fund</a>' +
          '<a href="' + url('programs/index.html') + '">R&amp;D</a>' +
          '<a href="' + url('programs/index.html') + '">Venture Creation</a>' +
          '<a href="' + url('programs/index.html') + '">MEITAL Program</a>' +
          extLink(EXT.accelerator, 'Resilience Accelerator ↗') +
          extLink(EXT.shebaSderot, 'Sheba to Sderot ↗') +
        '</div>' +
        '<div class="foot-col">' +
          '<h5>Contact</h5>' +
          '<a class="foot-contact" href="mailto:' + CONTACT.email + '"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 7 10 6L22 7"/></svg>' + CONTACT.email + '</a>' +
          '<a class="foot-contact" href="' + CONTACT.phoneHref + '"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg>' + CONTACT.phone + '</a>' +
          '<a class="foot-contact" href="https://maps.google.com/?q=RISE.HUB+Sderot" target="_blank" rel="noopener noreferrer"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>Sderot Innovation Wing, Sderot</a>' +
          '<a class="foot-contact" href="https://www.shebaonline.org/" target="_blank" rel="noopener noreferrer"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>Sheba Medical Center, Ramat Gan</a>' +
        '</div>' +
      '</div>' +
      '<div class="foot-bottom">' +
        '<span>© 2026 Innovation Hub. All rights reserved.</span>' +
        '<span class="credit">Designed &amp; developed by <b>Shilo Shvartz</b>, <b>Ori Asher</b>, <b>Shai Ozer</b>, <b>Yosef Ozeri</b></span>' +
      '</div>' +
    '</footer>';

  var modalHTML =
    '<div class="modal-back" id="modal" role="dialog" aria-modal="true" aria-labelledby="modalTitle">' +
      '<div class="modal-card">' +
        '<button class="close" aria-label="Close" data-action="close-modal">×</button>' +
        '<div class="star"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 22 12 18.27 5.82 22 7 14.14l-5-4.87 6.91-1.01L12 2z"/></svg></div>' +
        '<div class="tag">Join the movement</div>' +
        '<h3 id="modalTitle">Join us in redefining the future of <span class="b">resilience innovation.</span></h3>' +
        '<p>We\'re always looking for clinicians, founders, partners and visionaries who share our mission. Get in touch. Let\'s build what comes next together.</p>' +
        '<div class="row">' +
          '<a class="btn-primary" data-action="close-modal" href="mailto:' + CONTACT.email + '?subject=RISE.HUB%20—%20Get%20in%20touch">Get in touch →</a>' +
          '<a class="ghost-btn" href="' + CONTACT.linkedin + '" target="_blank" rel="noopener noreferrer" style="display:inline-flex;align-items:center">Connect on LinkedIn</a>' +
        '</div>' +
      '</div>' +
    '</div>';

  document.body.insertAdjacentHTML('afterbegin', navHTML + a11yHTML + dotnavHTML);
  document.body.insertAdjacentHTML('beforeend', footerHTML + modalHTML);

  /* skip-link target: first content screen */
  var firstScreen = document.querySelector('.screen, main, section');
  if (firstScreen && !document.getElementById('ih-main')) {
    firstScreen.insertAdjacentHTML('beforebegin', '<span id="ih-main" tabindex="-1"></span>');
  }

  /* ---------- page-leave transition for internal navigation ---------- */
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion:reduce)').matches;
  function leave(go) {
    if (reduce) { go(); return; }
    document.body.classList.add('ih-leaving');
    setTimeout(go, 220);
  }
  window.ihLeave = leave;
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a') : null;
    if (!a) return;
    var href = a.getAttribute('href');
    if (!href || href.charAt(0) === '#') return;
    if (a.target && a.target !== '_self') return;
    if (/^(mailto:|tel:|javascript:|https?:)/i.test(href)) return;
    if (href.indexOf('.html') === -1) return;
    e.preventDefault();
    leave(function () { window.location.href = a.href; });
  }, true);
  window.addEventListener('pageshow', function (ev) { if (ev.persisted) document.body.classList.remove('ih-leaving'); });

  /* ---------- iframe registry + messaging ---------- */
  var frames = {};
  document.querySelectorAll('iframe[data-id]').forEach(function (f) { frames[f.dataset.id] = f; });
  function post(frame, msg) { if (frame && frame.contentWindow) { try { frame.contentWindow.postMessage(msg, '*'); } catch (e) {} } }

  /* accessibility state shared with section iframes */
  var a11y = { fs: '', ul: false, rm: false };
  function sendA11yTo(frame) { post(frame, { t: 'ih:a11y', fs: a11y.fs, ul: a11y.ul, rm: a11y.rm }); }
  function broadcastA11y() { Object.keys(frames).forEach(function (k) { sendA11yTo(frames[k]); }); }

  /* resolve a root-relative nav target to this page's depth */
  function resolveTarget(to) {
    var t = to.replace(/^(\.\.\/)+/, '');
    return url(t);
  }

  var visible = new Set();
  addEventListener('message', function (e) {
    var d = e.data || {};
    if (d.t === 'ih:h') { var f = frames[d.id]; if (f && !f.hasAttribute('data-fixed')) f.style.height = d.h + 'px'; }
    else if (d.t === 'ih:ready') { var fr = frames[d.id]; if (fr) { sendA11yTo(fr); if (visible.has(d.id)) post(fr, { t: 'ih:enter' }); } }
    else if (d.t === 'ih:key') { moveSection(d.key); }
    else if (d.t === 'ih:nav') {
      if (d.to.indexOf('.html') !== -1) {
        var target = resolveTarget(d.to);
        ihLeave(function () { window.location.href = target; });
      } else {
        scrollToId(d.to);
      }
    }
    else if (d.t === 'ih:modal') { openModal(); }
  });

  /* ---------- enter/leave reveals ---------- */
  var io = new IntersectionObserver(function (ents) {
    ents.forEach(function (en) {
      var f = en.target.querySelector('iframe'); if (!f) return;
      var id = f.dataset.id;
      if (en.isIntersecting) { if (!visible.has(id)) { visible.add(id); post(f, { t: 'ih:enter' }); } }
      else if (visible.has(id)) { visible.delete(id); post(f, { t: 'ih:leave' }); }
    });
  }, { threshold: 0.01 });
  document.querySelectorAll('.screen').forEach(function (s) { io.observe(s); });

  /* ---------- nav scroll state ---------- */
  var nav = document.getElementById('nav');
  addEventListener('scroll', function () { nav.classList.toggle('scrolled', scrollY > 40); }, { passive: true });

  /* ---------- accessibility panel ---------- */
  var a11yBtn = document.getElementById('a11yBtn');
  var a11yPanel = document.getElementById('a11yPanel');
  a11yBtn.addEventListener('click', function (e) { e.stopPropagation(); var o = a11yPanel.classList.toggle('open'); a11yPanel.setAttribute('aria-hidden', !o); });
  document.addEventListener('click', function (e) { if (!a11yPanel.contains(e.target) && !a11yBtn.contains(e.target)) a11yPanel.classList.remove('open'); });
  document.querySelectorAll('[data-fs]').forEach(function (b) {
    b.addEventListener('click', function () {
      document.body.classList.remove('fs-lg', 'fs-xl');
      if (b.dataset.fs) document.body.classList.add(b.dataset.fs);
      document.querySelectorAll('[data-fs]').forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on');
      a11y.fs = b.dataset.fs; broadcastA11y();
    });
  });
  document.getElementById('hcBtn').addEventListener('click', function (e) { var o = document.body.classList.toggle('hc'); e.target.textContent = o ? 'On' : 'Off'; e.target.classList.toggle('on', o); });
  document.getElementById('ulBtn').addEventListener('click', function (e) { var o = document.body.classList.toggle('ul-links'); e.target.textContent = o ? 'On' : 'Off'; e.target.classList.toggle('on', o); a11y.ul = o; broadcastA11y(); });
  document.getElementById('rmBtn').addEventListener('click', function (e) {
    var o = e.target.classList.toggle('on'); e.target.textContent = o ? 'On' : 'Off';
    document.body.classList.toggle('reduce-motion', o);
    document.documentElement.style.setProperty('scroll-behavior', o ? 'auto' : 'smooth');
    a11y.rm = o; broadcastA11y();
  });

  /* ---------- modal ---------- */
  var modal = document.getElementById('modal');
  function openModal() { modal.classList.add('open'); document.body.classList.add('no-scroll'); }
  function closeModal() { modal.classList.remove('open'); document.body.classList.remove('no-scroll'); }
  document.querySelectorAll('[data-action="open-modal"]').forEach(function (b) { b.addEventListener('click', openModal); });
  document.querySelectorAll('[data-action="close-modal"]').forEach(function (b) { b.addEventListener('click', closeModal); });
  modal.addEventListener('click', function (e) { if (e.target === modal) closeModal(); });
  addEventListener('keydown', function (e) { if (e.key === 'Escape') closeModal(); });

  /* ---------- side dot nav + arrow-key navigation ---------- */
  var els = SECTIONS.map(function (s) { return document.getElementById(s.id); });
  var dotnav = document.getElementById('dotnav');
  dotnav.innerHTML = SECTIONS.map(function (s, i) { return '<button data-i="' + i + '" data-label="' + s.label + '" aria-label="' + s.label + '"></button>'; }).join('');
  var dots = [].slice.call(dotnav.querySelectorAll('button'));
  function scrollToId(id) { var el = document.getElementById(id); if (el) el.scrollIntoView({ behavior: 'smooth' }); }
  dots.forEach(function (d, i) { d.addEventListener('click', function () { if (els[i]) els[i].scrollIntoView({ behavior: 'smooth' }); }); });
  function currentIndex() {
    var mid = scrollY + innerHeight * 0.4; var idx = 0;
    els.forEach(function (el, i) { if (el && el.offsetTop <= mid) idx = i; });
    return idx;
  }
  function syncDots() {
    var idx = currentIndex();
    dots.forEach(function (d, i) { d.classList.toggle('active', i === idx); });
    if (SECTIONS[idx]) dotnav.classList.toggle('on-dark', darkIds.has(SECTIONS[idx].id));
  }
  syncDots();
  addEventListener('scroll', syncDots, { passive: true });
  addEventListener('resize', syncDots, { passive: true });

  var locking = false;
  function moveSection(key) {
    if (locking) return; locking = true; setTimeout(function () { locking = false; }, 650);
    var idx = currentIndex();
    var dir = (key === 'ArrowDown' || key === 'PageDown') ? 1 : -1;
    var next = Math.max(0, Math.min(els.length - 1, idx + dir));
    if (els[next]) els[next].scrollIntoView({ behavior: 'smooth' });
  }
  addEventListener('keydown', function (e) {
    if (['ArrowDown', 'PageDown', 'ArrowUp', 'PageUp'].indexOf(e.key) !== -1) {
      var tag = document.activeElement && document.activeElement.tagName;
      if (/^(INPUT|TEXTAREA|SELECT)$/.test(tag)) return;
      e.preventDefault(); moveSection(e.key);
    }
  });
})();
