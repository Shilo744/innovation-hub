/* ============================================================
   FRAME BRIDGE — shared by every section file.
   Connects a standalone section (running inside an iframe) to
   the parent connector page. Loaded via:
     <script src="_bridge.js" data-frame="about"><\/script>
   Responsibilities:
     • report the section's content height so the parent can
       size the iframe (no nested scrollbars)
     • play reveal animations when the section is shown
     • apply accessibility settings broadcast by the parent
     • forward arrow-key navigation + nav/modal clicks upward
   Safe to open a section file on its own — every parent call
   is guarded, so nothing breaks when there is no parent.
============================================================ */
(function () {
  var ID = (document.currentScript && document.currentScript.dataset.frame) || 'section';
  var inParent = window.parent && window.parent !== window;

  function send(msg) { if (inParent) { try { window.parent.postMessage(msg, '*'); } catch (e) {} } }

  /* ---- height reporting ---- */
  function height() {
    var b = document.body;
    // Measure the body's own content height only. document.documentElement
    // .scrollHeight is clamped to the iframe's current viewport height, so it
    // never reports a value smaller than the frame already is — which stops the
    // frame from shrinking when content gets shorter (e.g. switching to a tab
    // with fewer items), leaving dead space below.
    return Math.max(b ? b.scrollHeight : 0, b ? b.offsetHeight : 0);
  }
  var lastH = 0;
  function report() {
    var h = height();
    if (h && h !== lastH) { lastH = h; send({ t: 'ih:h', id: ID, h: h }); }
  }
  function reportSoon() { requestAnimationFrame(report); setTimeout(report, 120); }

  /* ---- reveal animations (idempotent; never leaves content hidden) ---- */
  function showAll() {
    var els = document.querySelectorAll('.reveal');
    for (var i = 0; i < els.length; i++) els[i].classList.add('in');
    setTimeout(report, 850);
  }
  function playReveals() {
    requestAnimationFrame(showAll);
    setTimeout(showAll, 1200); // safety net: never leave content hidden if 'enter' never arrives
  }

  /* ---- accessibility from parent ---- */
  function applyA11y(d) {
    var b = document.body; if (!b) return;
    b.classList.remove('fs-lg', 'fs-xl'); if (d.fs) b.classList.add(d.fs);
    b.classList.toggle('hc', !!d.hc);
    b.classList.toggle('ul-links', !!d.ul);
    b.classList.toggle('reduce-motion', !!d.rm);
    document.documentElement.style.scrollBehavior = d.rm ? 'auto' : '';
    reportSoon();
  }

  /* ---- receive from parent ---- */
  window.addEventListener('message', function (e) {
    var d = e.data || {};
    if (d.t === 'ih:enter') playReveals();
    if (d.t === 'ih:a11y') applyA11y(d);
    if (d.t === 'ih:measure') report();
  });

  /* ---- forward arrow-key navigation ---- */
  window.addEventListener('keydown', function (e) {
    if (['ArrowDown', 'PageDown', 'ArrowUp', 'PageUp'].indexOf(e.key) === -1) return;
    var tag = document.activeElement && document.activeElement.tagName;
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(tag)) return;
    e.preventDefault();
    send({ t: 'ih:key', key: e.key });
  });

  /* ---- forward nav + modal clicks to the parent ---- */
  document.addEventListener('click', function (e) {
    var s = e.target.closest('[data-scroll]');
    if (s) { send({ t: 'ih:nav', to: s.getAttribute('data-scroll') }); return; }
    var m = e.target.closest('[data-action="open-modal"]');
    if (m) send({ t: 'ih:modal' });
  });

  /* ---- lifecycle ---- */
  function init() {
    report();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(report);
    if (window.ResizeObserver && document.body) {
      try { new ResizeObserver(report).observe(document.body); } catch (e) {}
    }
    window.addEventListener('resize', report);
    window.addEventListener('load', reportSoon);
    send({ t: 'ih:ready', id: ID });
    // The parent fires ih:enter when this section scrolls into view, which
    // plays the reveal with animation. This is the ultimate safety net so
    // content is never left hidden if that signal never arrives.
    setTimeout(showAll, 2500);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();

  /* expose for in-section scripts that change layout (tabs, accordions) */
  window.__frameReport = reportSoon;
})();
