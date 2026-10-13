// Header compartido: menú móvil + idioma ES/EN (misma preferencia que la home)
(function () {
  var burger = document.getElementById('fpBurger');
  var menu = document.getElementById('fpMenu');
  if (burger && menu) {
    burger.addEventListener('click', function () { menu.classList.toggle('open'); });
    menu.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { menu.classList.remove('open'); });
    });
  }

  // ---------- Idioma ----------
  var DICT = window.FP_I18N || { toEN: {}, toES: {} };
  var SKIP = { SCRIPT: 1, STYLE: 1, CODE: 1, PRE: 1, TEXTAREA: 1, NOSCRIPT: 1, TEMPLATE: 1 };
  var ATTRS = ['placeholder', 'title', 'aria-label', 'alt'];
  var orig = new WeakMap();   // nodo de texto -> texto original
  var shown = new WeakMap();  // nodo de texto -> último texto que pusimos
  var lang = 'es';
  try { lang = localStorage.getItem('lang') === 'en' ? 'en' : 'es'; } catch (e) {}

  function norm(s) { return s.replace(/\s+/g, ' ').trim(); }
  function lookup(text) {
    var k = norm(text);
    if (!k) return null;
    var map = lang === 'en' ? DICT.toEN : DICT.toES;
    return Object.prototype.hasOwnProperty.call(map, k) ? map[k] : null;
  }
  function skipped(el) {
    for (var n = el; n && n !== document.body; n = n.parentElement) {
      if (SKIP[n.tagName] || n.id === 'fp-chat-root' || (n.hasAttribute && n.hasAttribute('data-no-i18n'))) return true;
    }
    return false;
  }
  function doText(node) {
    if (!node.parentElement || skipped(node.parentElement)) return;
    if (node.parentElement.closest('[data-en]')) return; // lo maneja data-en
    var cur = node.nodeValue;
    if (!orig.has(node) || shown.get(node) !== cur) orig.set(node, cur); // texto nuevo (p. ej. Alpine)
    var base = orig.get(node);
    var t = lookup(base);
    var out = base;
    if (t !== null) {
      var lead = base.match(/^\s*/)[0], tail = base.match(/\s*$/)[0];
      out = lead + t + tail;
    }
    if (node.nodeValue !== out) node.nodeValue = out;
    shown.set(node, out);
  }
  function doAttrs(el) {
    ATTRS.forEach(function (a) {
      if (!el.hasAttribute(a)) return;
      var key = 'fpOrig_' + a.replace('-', '_');
      if (!(key in el.dataset)) el.dataset[key] = el.getAttribute(a);
      var t = lookup(el.dataset[key]);
      el.setAttribute(a, t !== null ? t : el.dataset[key]);
    });
  }
  function doDataEn(el) {
    if (!('es' in el.dataset)) el.dataset.es = el.innerHTML;
    var html = lang === 'en' ? el.dataset.en : el.dataset.es;
    if (el.innerHTML !== html) el.innerHTML = html;
  }
  function walk(root) {
    if (root.nodeType === 3) { doText(root); return; }
    if (root.nodeType !== 1 || skipped(root)) return;
    root.querySelectorAll ? root.querySelectorAll('[data-en]').forEach(doDataEn) : 0;
    if (root.hasAttribute && root.hasAttribute('data-en')) doDataEn(root);
    var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    var n; while ((n = w.nextNode())) doText(n);
    doAttrs(root);
    root.querySelectorAll('[' + ATTRS.join('],[') + ']').forEach(doAttrs);
  }
  var titleOrig = document.title;
  function apply() {
    busy = true;
    document.documentElement.lang = lang;
    var t = lookup(titleOrig); document.title = t !== null ? t : titleOrig;
    walk(document.body);
    document.querySelectorAll('.fp-lang button').forEach(function (b) {
      b.classList.toggle('on', b.getAttribute('data-lang') === lang);
    });
    busy = false;
  }
  var busy = false;
  document.querySelectorAll('.fp-lang button').forEach(function (b) {
    b.addEventListener('click', function () {
      lang = b.getAttribute('data-lang') === 'en' ? 'en' : 'es';
      try { localStorage.setItem('lang', lang); } catch (e) {}
      apply();
    });
  });
  // Contenido que aparece después (Alpine, plantillas): se traduce al vuelo
  var mo = new MutationObserver(function (list) {
    if (busy) return;
    busy = true;
    list.forEach(function (m) {
      if (m.type === 'characterData') doText(m.target);
      else m.addedNodes.forEach(function (n) { walk(n); });
    });
    busy = false;
  });
  function start() {
    apply();
    mo.observe(document.body, { childList: true, subtree: true, characterData: true });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
