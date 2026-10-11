/*
 * Asistente de contacto de ferdyplacencia.com
 * Chat guiado de 3 pasos que envía el contacto a un webhook de n8n.
 * Sin dependencias. Para cambiar el destino, edita WEBHOOK_URL.
 */
(function () {
  'use strict';

  var WEBHOOK_URL = 'https://n8n.ferdyplacencia.com/webhook/portfolio-lead';
  var AVATAR = '/logo.jpg';
  var WHATSAPP = 'https://wa.me/18096769759';
  var EMAIL = 'ferdyv59@gmail.com';

  if (document.getElementById('fp-chat-root')) return;

  var NEEDS = [
    { id: 'qa', label: 'Pruebas QA para mi app' },
    { id: 'automation', label: 'Automatizar procesos (n8n)' },
    { id: 'ai', label: 'Agente o chatbot con IA' },
    { id: 'job', label: 'Oferta de trabajo' },
    { id: 'other', label: 'Otra cosa' }
  ];

  var PROMPTS = {
    qa: '¿Qué producto quieres probar y qué te preocupa? (web, API, móvil, bugs en producción…)',
    automation: '¿Qué tarea manual te quita más tiempo hoy?',
    ai: '¿Qué te gustaría que hiciera el agente o chatbot?',
    job: 'Cuéntame sobre el puesto: empresa, rol y modalidad.',
    other: 'Cuéntame en una o dos frases qué necesitas.'
  };

  var state = { step: 'need', need: null, message: '', startedAt: Date.now(), sending: false, done: false };

  function store(kind, key, value) {
    try {
      var s = kind === 'session' ? window.sessionStorage : window.localStorage;
      if (value === undefined) return s.getItem(key);
      s.setItem(key, value);
    } catch (e) { return null; }
  }

  var css = [
    '#fp-chat-root{--fp-cyan:#00f2ff;--fp-purple:#9d00ff;--fp-bg:#0f0f14;--fp-surface:#17171f;--fp-line:rgba(255,255,255,.1);--fp-text:#e8eaf0;--fp-muted:#9aa0ad;font-family:Manrope,system-ui,-apple-system,sans-serif;position:fixed;right:20px;bottom:20px;z-index:9999;color:var(--fp-text)}',
    '#fp-chat-root *{box-sizing:border-box}',
    '.fp-launch{width:60px;height:60px;border-radius:50%;border:0;cursor:pointer;display:grid;place-items:center;background:linear-gradient(135deg,var(--fp-cyan),var(--fp-purple));box-shadow:0 10px 30px rgba(0,242,255,.35);transition:transform .2s}',
    '.fp-launch:hover{transform:scale(1.06)}',
    '.fp-launch:focus-visible,.fp-close:focus-visible,.fp-opt:focus-visible,.fp-send:focus-visible{outline:2px solid #fff;outline-offset:3px}',
    '.fp-launch svg{width:26px;height:26px;fill:#06070a}',
    '.fp-teaser{position:absolute;right:72px;bottom:10px;width:max-content;max-width:230px;background:var(--fp-surface);border:1px solid var(--fp-line);padding:10px 14px;border-radius:14px 14px 4px 14px;font-size:13px;line-height:1.4;box-shadow:0 10px 30px rgba(0,0,0,.5);cursor:pointer;animation:fp-in .3s ease}',
    '.fp-panel{position:absolute;right:0;bottom:76px;width:370px;max-width:calc(100vw - 32px);height:540px;max-height:calc(100vh - 110px);display:flex;flex-direction:column;background:var(--fp-bg);border:1px solid rgba(0,242,255,.25);border-radius:20px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.6),0 0 40px rgba(0,242,255,.08);animation:fp-in .25s ease}',
    '.fp-panel[hidden],.fp-teaser[hidden]{display:none}',
    '.fp-head{display:flex;align-items:center;gap:12px;padding:16px;background:linear-gradient(135deg,rgba(0,242,255,.16),rgba(157,0,255,.18));border-bottom:1px solid var(--fp-line)}',
    '.fp-head img{width:40px;height:40px;border-radius:50%;object-fit:cover;border:2px solid rgba(0,242,255,.4);background:#000}',
    '.fp-head h2{margin:0;font-size:15px;font-weight:800;color:#fff}',
    '.fp-head p{margin:2px 0 0;font-size:12px;color:var(--fp-muted)}',
    '.fp-head p::before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;background:#34d399;margin-right:6px;vertical-align:middle}',
    '.fp-close{margin-left:auto;background:none;border:0;color:var(--fp-muted);font-size:22px;line-height:1;cursor:pointer;width:32px;height:32px;border-radius:50%}',
    '.fp-close:hover{background:rgba(255,255,255,.08);color:#fff}',
    '.fp-log{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px;scroll-behavior:smooth}',
    '.fp-msg{max-width:85%;padding:10px 14px;font-size:14px;line-height:1.45;border-radius:16px;white-space:pre-wrap;word-wrap:break-word;animation:fp-in .2s ease}',
    '.fp-bot{align-self:flex-start;background:var(--fp-surface);border:1px solid var(--fp-line);border-bottom-left-radius:4px}',
    '.fp-user{align-self:flex-end;background:linear-gradient(135deg,var(--fp-cyan),#5ab8ff);color:#05060a;font-weight:600;border-bottom-right-radius:4px}',
    '.fp-bot a{color:var(--fp-cyan)}',
    '.fp-opts{display:flex;flex-direction:column;gap:8px;align-self:stretch}',
    '.fp-opt{text-align:left;background:transparent;border:1px solid rgba(0,242,255,.3);color:var(--fp-text);padding:10px 14px;border-radius:12px;font:inherit;font-size:14px;cursor:pointer;transition:background .15s,border-color .15s}',
    '.fp-opt:hover{background:rgba(0,242,255,.08);border-color:var(--fp-cyan)}',
    '.fp-typing{align-self:flex-start;display:flex;gap:4px;padding:12px 14px;background:var(--fp-surface);border:1px solid var(--fp-line);border-radius:16px;border-bottom-left-radius:4px}',
    '.fp-typing span{width:6px;height:6px;border-radius:50%;background:var(--fp-muted);animation:fp-dot 1s infinite}',
    '.fp-typing span:nth-child(2){animation-delay:.15s}.fp-typing span:nth-child(3){animation-delay:.3s}',
    '.fp-form{display:flex;gap:8px;padding:12px;border-top:1px solid var(--fp-line);background:var(--fp-bg)}',
    '.fp-form textarea{flex:1;resize:none;min-height:44px;max-height:110px;padding:11px 12px;border-radius:12px;border:1px solid var(--fp-line);background:var(--fp-surface);color:var(--fp-text);font:inherit;font-size:14px;line-height:1.4}',
    '.fp-form textarea:focus{outline:none;border-color:var(--fp-cyan);box-shadow:0 0 0 3px rgba(0,242,255,.15)}',
    '.fp-form textarea:disabled{opacity:.5}',
    '.fp-send{border:0;border-radius:12px;padding:0 16px;font:inherit;font-weight:800;font-size:14px;cursor:pointer;color:#05060a;background:linear-gradient(135deg,var(--fp-cyan),var(--fp-purple))}',
    '.fp-send:disabled{opacity:.4;cursor:not-allowed}',
    '.fp-hp{position:absolute;left:-9999px;width:1px;height:1px;opacity:0}',
    '.fp-note{font-size:11px;color:var(--fp-muted);text-align:center;padding:0 12px 10px}',
    '@keyframes fp-in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}',
    '@keyframes fp-dot{0%,80%,100%{opacity:.3}40%{opacity:1}}',
    '@media (max-width:480px){#fp-chat-root{right:12px;bottom:12px}.fp-panel{position:fixed;right:8px;left:8px;bottom:84px;width:auto;max-width:none;height:calc(100vh - 100px)}.fp-teaser{max-width:190px}}',
    '@media (prefers-reduced-motion:reduce){#fp-chat-root *{animation:none!important;transition:none!important}}'
  ].join('\n');

  var styleEl = document.createElement('style');
  styleEl.textContent = css;
  document.head.appendChild(styleEl);

  var root = document.createElement('div');
  root.id = 'fp-chat-root';
  root.innerHTML =
    '<div class="fp-teaser" hidden>¿Necesitas QA o automatizar algo? Te ayudo en 2 minutos 👋</div>' +
    '<section class="fp-panel" role="dialog" aria-modal="false" aria-labelledby="fp-title" hidden>' +
      '<header class="fp-head">' +
        '<img alt="" src="' + AVATAR + '">' +
        '<div><h2 id="fp-title">Asistente de Ferdy</h2><p>Respondo en menos de 24 h</p></div>' +
        '<button class="fp-close" type="button" aria-label="Cerrar chat">×</button>' +
      '</header>' +
      '<div class="fp-log" aria-live="polite"></div>' +
      '<form class="fp-form" novalidate>' +
        '<input class="fp-hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">' +
        '<label for="fp-input" class="fp-hp">Mensaje</label>' +
        '<textarea id="fp-input" rows="1" maxlength="600" placeholder="Elige una opción arriba…" disabled></textarea>' +
        '<button class="fp-send" type="submit" disabled>Enviar</button>' +
      '</form>' +
      '<p class="fp-note">Tus datos solo se usan para responderte.</p>' +
    '</section>' +
    '<button class="fp-launch" type="button" aria-label="Abrir chat de contacto" aria-expanded="false">' +
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3C6.5 3 2 6.9 2 11.7c0 2.4 1.1 4.6 3 6.2L4.2 21.4c-.1.4.3.7.7.5l4-2.1c1 .3 2 .4 3.1.4 5.5 0 10-3.9 10-8.7S17.5 3 12 3z"/></svg>' +
    '</button>';
  document.body.appendChild(root);

  var panel = root.querySelector('.fp-panel');
  var teaser = root.querySelector('.fp-teaser');
  var launch = root.querySelector('.fp-launch');
  var closeBtn = root.querySelector('.fp-close');
  var log = root.querySelector('.fp-log');
  var form = root.querySelector('.fp-form');
  var input = root.querySelector('#fp-input');
  var sendBtn = root.querySelector('.fp-send');
  var honeypot = root.querySelector('input[name="website"]');
  var started = false;

  function scrollDown() { log.scrollTop = log.scrollHeight; }

  function addMsg(text, who) {
    var el = document.createElement('div');
    el.className = 'fp-msg ' + (who === 'user' ? 'fp-user' : 'fp-bot');
    el.textContent = text;
    log.appendChild(el);
    scrollDown();
    return el;
  }

  function addHtmlMsg(html) {
    var el = document.createElement('div');
    el.className = 'fp-msg fp-bot';
    el.innerHTML = html;
    log.appendChild(el);
    scrollDown();
  }

  function botSay(text, then) {
    var t = document.createElement('div');
    t.className = 'fp-typing';
    t.setAttribute('aria-label', 'Escribiendo');
    t.innerHTML = '<span></span><span></span><span></span>';
    log.appendChild(t);
    scrollDown();
    setTimeout(function () {
      t.remove();
      addMsg(text, 'bot');
      if (then) then();
    }, 550);
  }

  function setInput(enabled, placeholder) {
    input.disabled = !enabled;
    input.placeholder = placeholder || '';
    sendBtn.disabled = !enabled;
    if (enabled) input.focus();
  }

  function showOptions() {
    var wrap = document.createElement('div');
    wrap.className = 'fp-opts';
    NEEDS.forEach(function (n) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'fp-opt';
      b.textContent = n.label;
      b.addEventListener('click', function () {
        wrap.remove();
        state.need = n.id;
        addMsg(n.label, 'user');
        state.step = 'message';
        botSay(PROMPTS[n.id], function () { setInput(true, 'Escribe tu respuesta…'); });
      });
      wrap.appendChild(b);
    });
    log.appendChild(wrap);
    scrollDown();
    var first = wrap.querySelector('button');
    if (first) first.focus();
  }

  function start() {
    if (started) return;
    started = true;
    state.startedAt = Date.now();
    botSay('¡Hola! Soy el asistente de Ferdy, QA & Automation Engineer.', function () {
      botSay('¿En qué te puedo ayudar?', showOptions);
    });
  }

  function open() {
    panel.hidden = false;
    teaser.hidden = true;
    launch.setAttribute('aria-expanded', 'true');
    store('session', 'fp_chat_seen', '1');
    start();
    if (!input.disabled) input.focus();
  }

  function close() {
    panel.hidden = true;
    launch.setAttribute('aria-expanded', 'false');
    launch.focus();
  }

  function validEmail(v) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v); }

  function fallbackContact() {
    addHtmlMsg('No pude enviar tu mensaje ahora mismo. Escríbeme directo por ' +
      '<a href="' + WHATSAPP + '" target="_blank" rel="noopener">WhatsApp</a> o a ' +
      '<a href="mailto:' + EMAIL + '">' + EMAIL + '</a>.');
  }

  function submitLead(email) {
    state.sending = true;
    setInput(false, 'Enviando…');
    var payload = {
      need: state.need,
      message: state.message,
      email: email,
      page: location.pathname,
      lang: navigator.language || '',
      elapsedMs: Date.now() - state.startedAt,
      website: honeypot.value
    };
    var ctrl = window.AbortController ? new AbortController() : null;
    var timer = setTimeout(function () { if (ctrl) ctrl.abort(); }, 12000);
    fetch(WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: ctrl ? ctrl.signal : undefined
    }).then(function (r) {
      clearTimeout(timer);
      if (!r.ok) throw new Error('HTTP ' + r.status);
      state.done = true;
      botSay('¡Listo! Ferdy recibió tu mensaje y te responde a ' + email + ' en menos de 24 horas.', function () {
        addHtmlMsg('¿Prefieres hablar ya? <a href="' + WHATSAPP + '" target="_blank" rel="noopener">Escríbele por WhatsApp</a>.');
        setInput(false, 'Mensaje enviado ✓');
      });
    }).catch(function () {
      clearTimeout(timer);
      state.sending = false;
      fallbackContact();
      setInput(true, 'tu@correo.com');
    });
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (state.sending || state.done) return;
    var v = input.value.trim();
    if (!v) return;

    if (state.step === 'message') {
      if (v.length < 5) { botSay('Cuéntame un poco más, por favor.'); return; }
      state.message = v;
      addMsg(v, 'user');
      input.value = '';
      state.step = 'email';
      setInput(false);
      botSay('Perfecto. ¿A qué correo te puede responder Ferdy?', function () { setInput(true, 'tu@correo.com'); });
    } else if (state.step === 'email') {
      addMsg(v, 'user');
      input.value = '';
      if (!validEmail(v)) {
        botSay('Ese correo no parece válido. ¿Lo revisas?', function () { setInput(true, 'tu@correo.com'); });
        return;
      }
      submitLead(v);
    }
  });

  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); form.requestSubmit ? form.requestSubmit() : form.dispatchEvent(new Event('submit')); }
  });

  launch.addEventListener('click', function () { panel.hidden ? open() : close(); });
  teaser.addEventListener('click', open);
  closeBtn.addEventListener('click', close);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !panel.hidden) close(); });

  // Invitación discreta una vez por sesión, sin abrir el chat solo.
  if (!store('session', 'fp_chat_seen')) {
    setTimeout(function () { if (panel.hidden) teaser.hidden = false; }, 12000);
  }
})();
