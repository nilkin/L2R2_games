/* L2R2 log — ziyarət və oyun statistikası (server: Google Apps Script → Google Sheets).
   Brauzer məlumatı toplayıb serverə göndərir; loglar serverdə (cədvəldə) saxlanır.
   Quraşdırma: logserver/README.md. Bu fayl ES5-dir (köhnə TV brauzerləri üçün) — let/const/=> yazmayın.

   Oyunlardan çağırış (istəyə bağlı):
     window.L2R2Log && L2R2Log.event('play_start', 'detal');     // oyun başladı
     window.L2R2Log && L2R2Log.event('level_complete', 'detal'); // mərhələ bitdi
     window.L2R2Log && L2R2Log.count('correct');                 // sayğac (+1)
   URL parametrləri: ?nolog=1 (bu cihazı loglama, ?nolog=0 geri qaytarır), ?logdebug=1 (konsolda göstər)
*/
(function () {
  'use strict';

  // Apps Script Web App URL-i (Deploy → Web app → URL). Boşdursa heç nə göndərilmir.
  var ENDPOINT = '';

  var GAMES = [
    [/\/alfa_be\//, 'Hərf Oyunu'],
    [/\/jumping-friends\//, 'Atlayan Dostlar'],
    [/\/reqemler\//, 'Zuzu və Rəqəmlər']
  ];
  var HUB = 'Ana səhifə';
  var SESSION_GAP = 30 * 60 * 1000;

  var w = window, d = document, nav = navigator, ua = nav.userAgent || '', loc = w.location;
  function noop() {}
  var api = { event: noop, count: noop };
  w.L2R2Log = api;

  function now() { return new Date().getTime(); }
  function store(s, k, v) {
    try {
      var st = s === 'l' ? w.localStorage : w.sessionStorage;
      if (v === undefined) return st.getItem(k);
      st.setItem(k, String(v));
    } catch (e) {}
    return null;
  }
  function param(name) {
    var m = new RegExp('[?&]' + name + '=([^&#]*)').exec(loc.search);
    try { return m ? decodeURIComponent(m[1].replace(/\+/g, ' ')) : ''; } catch (e) { return ''; }
  }
  function rid() {
    var s = '', a = 'abcdefghijklmnopqrstuvwxyz0123456789';
    for (var i = 0; i < 10; i++) s += a.charAt(Math.floor(Math.random() * 36));
    return s;
  }
  function cut(s, n) { s = s == null ? '' : String(s); return s.length > n ? s.slice(0, n) : s; }

  // ---------- opt-out / debug ----------
  var nl = param('nolog');
  if (nl === '1' || nl === '0') store('l', 'l2r2_nolog', nl);
  if (store('l', 'l2r2_nolog') === '1') return;
  if (param('logdebug')) store('s', 'l2r2_debug', param('logdebug'));
  var debug = store('s', 'l2r2_debug') === '1';
  var local = loc.protocol === 'file:' || /^(localhost|127\.|192\.168\.|10\.|$)/.test(loc.hostname);

  // ---------- page ----------
  function gameOf(path) {
    for (var i = 0; i < GAMES.length; i++) if (GAMES[i][0].test(path)) return GAMES[i][1];
    return HUB;
  }
  var page = gameOf(loc.pathname);
  var isHub = page === HUB;

  // ---------- who: anonim ziyarətçi + sessiya ----------
  var t0 = now();
  var vid = store('l', 'l2r2_vid'), isNew = !vid;
  if (!vid) {
    vid = rid(); store('l', 'l2r2_vid', vid);
    store('l', 'l2r2_first', new Date().toISOString().slice(0, 10));
  }
  var sid = store('s', 'l2r2_sid');
  var last = +(store('l', 'l2r2_last') || 0);
  var newSession = !sid || t0 - last > SESSION_GAP;
  if (newSession) {
    sid = rid(); store('s', 'l2r2_sid', sid);
    store('l', 'l2r2_visits', +(store('l', 'l2r2_visits') || 0) + 1);
    store('s', 'l2r2_pn', 0);
  }
  var pageNo = +(store('s', 'l2r2_pn') || 0) + 1;
  store('s', 'l2r2_pn', pageNo);
  store('l', 'l2r2_last', t0);

  // ---------- from where ----------
  function refHost() { var m = /^https?:\/\/([^\/?#]+)/i.exec(d.referrer || ''); return m ? m[1].toLowerCase() : ''; }
  function sourceOf() {
    var utm = param('utm_source') || param('src');
    if (utm) return utm;
    var inApp = [[/Instagram/, 'Instagram'], [/FBAN|FBAV|FB_IAB/, 'Facebook'], [/musical_ly|BytedanceWebview|TikTok/i, 'TikTok'], [/Telegram/i, 'Telegram']];
    for (var i = 0; i < inApp.length; i++) if (inApp[i][0].test(ua)) return inApp[i][1];
    var h = refHost();
    if (!h) return 'Birbaşa / mesajlaşma';
    if (h === loc.host.toLowerCase()) {
      var rp = (d.referrer.replace(/^https?:\/\/[^\/]+/i, '') || '/');
      return 'Daxili: ' + gameOf(rp);
    }
    var map = [[/(^|\.)google\./, 'Google'], [/instagram/, 'Instagram'], [/facebook|(^|\.)fb\.|fbcdn/, 'Facebook'],
      [/whatsapp|wa\.me/, 'WhatsApp'], [/(^|\.)t\.me$|telegram/, 'Telegram'], [/youtube|youtu\.be/, 'YouTube'],
      [/tiktok/, 'TikTok'], [/yandex/, 'Yandex'], [/bing\./, 'Bing'], [/(^|\.)t\.co$|twitter|(^|\.)x\.com$/, 'X'],
      [/github/, 'GitHub'], [/linkedin|lnkd\.in/, 'LinkedIn'], [/vk\.com/, 'VK']];
    for (var j = 0; j < map.length; j++) if (map[j][0].test(h)) return map[j][1];
    return h;
  }
  var source = sourceOf();
  var sessionSource = store('s', 'l2r2_ssrc');
  if (newSession || !sessionSource) { sessionSource = source; store('s', 'l2r2_ssrc', source); }
  var utmParts = [param('utm_source'), param('utm_medium'), param('utm_campaign')], utm = '';
  for (var u = 0; u < utmParts.length; u++) if (utmParts[u]) utm += (utm ? ' / ' : '') + utmParts[u];

  // ---------- device ----------
  var ipadOS = /Macintosh/.test(ua) && nav.maxTouchPoints > 1;
  var deviceType =
    /SmartTV|SMART-TV|Tizen|Web0S|WebOS|NetCast|BRAVIA|HbbTV|Android TV|GoogleTV|AFT[A-Z]|CrKey|Roku|VIDAA|Opera TV|AppleTV/i.test(ua) ? 'TV' :
    (/iPad|Tablet|PlayBook|Silk/i.test(ua) || ipadOS || (/Android/i.test(ua) && !/Mobile/i.test(ua))) ? 'Planşet' :
    /Mobi|iPhone|iPod|Android|IEMobile|Opera Mini/i.test(ua) ? 'Telefon' : 'Kompüter';

  var m, os = 'Digər';
  if (/Web0S|webOS/i.test(ua)) os = 'webOS (LG)';
  else if (/Tizen/i.test(ua)) os = 'Tizen (Samsung)';
  else if ((m = /Android\s*([\d.]+)?/i.exec(ua))) os = 'Android ' + (m[1] || '');
  else if ((m = /(?:iPhone|CPU) OS (\d+)/.exec(ua))) os = (/iPad/.test(ua) ? 'iPadOS ' : 'iOS ') + m[1];
  else if (ipadOS) os = 'iPadOS';
  else if ((m = /Windows NT ([\d.]+)/.exec(ua))) os = 'Windows ' + ({ '10.0': '10/11', '6.3': '8.1', '6.2': '8', '6.1': '7' }[m[1]] || m[1]);
  else if (/CrOS/.test(ua)) os = 'ChromeOS';
  else if (/Mac OS X/.test(ua)) os = 'macOS';
  else if (/Linux/.test(ua)) os = 'Linux';

  var browser = 'Digər', BR = [
    [/Instagram/, 'Instagram (daxili)'], [/FBAN|FBAV|FB_IAB/, 'Facebook (daxili)'],
    [/musical_ly|BytedanceWebview|TikTok/i, 'TikTok (daxili)'], [/Telegram/i, 'Telegram (daxili)'],
    [/YaBrowser\/(\d+)/, 'Yandex'], [/SamsungBrowser\/(\d+)/, 'Samsung Internet'], [/OPR\/(\d+)|Opera\/(\d+)/, 'Opera'],
    [/Edg(?:e|A|iOS)?\/(\d+)/, 'Edge'], [/Firefox\/(\d+)|FxiOS\/(\d+)/, 'Firefox'], [/CriOS\/(\d+)/, 'Chrome'],
    [/Chrome\/(\d+)/, 'Chrome'], [/Version\/(\d+)[\d.]* .*Safari/, 'Safari'], [/Safari/, 'Safari']];
  for (var b = 0; b < BR.length; b++) {
    if ((m = BR[b][0].exec(ua))) { browser = BR[b][1] + ((m[1] || m[2]) ? ' ' + (m[1] || m[2]) : ''); break; }
  }
  if (/; wv\)/.test(ua)) browser += ' WebView';

  var model = '';
  if ((m = /Android [\d.]+; (?:[a-z]{2}[-_][a-z]{2}; )?([^;)]+?)(?: Build|\))/i.exec(ua)) && m[1] !== 'K') model = m[1];
  else if (/iPhone/.test(ua)) model = 'iPhone';
  else if (/iPad/.test(ua) || ipadOS) model = 'iPad';
  try {
    if (nav.userAgentData && nav.userAgentData.getHighEntropyValues) {
      nav.userAgentData.getHighEntropyValues(['model', 'platformVersion']).then(function (h) {
        if (h.model) model = h.model;
        var pv = parseInt(h.platformVersion, 10);
        if (/^Windows/.test(os) && pv) os = pv >= 13 ? 'Windows 11' : 'Windows 10';
        if (/^Android/.test(os) && pv) os = 'Android ' + pv;
      }, noop);
    }
  } catch (e) {}

  var tz = '';
  try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) {}
  if (!tz) { var off = -new Date().getTimezoneOffset() / 60; tz = 'UTC' + (off >= 0 ? '+' : '') + off; }
  var REGION = {
    'Asia/Baku': 'Azərbaycan', 'Europe/Istanbul': 'Türkiyə', 'Asia/Istanbul': 'Türkiyə', 'Europe/Moscow': 'Rusiya',
    'Asia/Tbilisi': 'Gürcüstan', 'Asia/Tehran': 'İran', 'Asia/Almaty': 'Qazaxıstan', 'Asia/Tashkent': 'Özbəkistan',
    'Europe/Kiev': 'Ukrayna', 'Europe/Kyiv': 'Ukrayna', 'Europe/London': 'Britaniya', 'Europe/Berlin': 'Almaniya',
    'Europe/Paris': 'Fransa', 'Asia/Dubai': 'BƏƏ', 'America/New_York': 'ABŞ', 'America/Chicago': 'ABŞ',
    'America/Los_Angeles': 'ABŞ', 'America/Toronto': 'Kanada'
  };
  var region = REGION[tz] || '';

  var conn = nav.connection || nav.mozConnection || nav.webkitConnection;
  var screenStr = (w.screen ? w.screen.width + 'x' + w.screen.height : '') + (w.devicePixelRatio ? ' @' + Math.round(w.devicePixelRatio * 100) / 100 : '');
  var touch = ('ontouchstart' in w) || nav.maxTouchPoints > 0;

  // ---------- behaviour ----------
  var interactions = 0, lastInteract = 0, engagedMs = 0, activeMs = 0, visibleSince = t0;
  var visible = d.visibilityState ? d.visibilityState !== 'hidden' : true;
  if (!visible) visibleSince = 0;
  var maxScroll = 0, plays = 0, levels = 0, progress = '', lastEvent = 'page_view', chosen = '';
  var counters = {}, errors = 0, errorMsg = '', loadMs = '';

  function onInteract() { interactions++; lastInteract = now(); }
  function on(el, ev, fn) { try { el.addEventListener(ev, fn, { capture: true, passive: true }); } catch (e) { el.addEventListener(ev, fn, true); } }
  if (w.PointerEvent) on(d, 'pointerdown', onInteract);
  else { on(d, 'touchstart', onInteract); on(d, 'mousedown', function () { if (now() - lastInteract > 800) onInteract(); }); }
  on(d, 'keydown', onInteract);
  on(w, 'scroll', function () {
    var h = Math.max(d.documentElement.scrollHeight, d.body ? d.body.scrollHeight : 0);
    var y = (w.pageYOffset || d.documentElement.scrollTop || 0) + (w.innerHeight || 0);
    if (h) maxScroll = Math.max(maxScroll, Math.min(100, Math.round(y / h * 100)));
  });
  w.addEventListener('error', function (e) { errors++; errorMsg = cut((e && e.message) || 'error', 150); });

  // aktiv oyun vaxtı: ekran görünür və son 15 saniyədə toxunma olub
  setInterval(function () { if (visible && lastInteract && now() - lastInteract < 15000) engagedMs += 5000; }, 5000);

  function flushVisible() { if (visible && visibleSince) { activeMs += now() - visibleSince; visibleSince = now(); } }

  function outcome() {
    if (isHub) {
      if (chosen) return 'Oyun seçdi';
      return interactions ? 'Baxdı, oyun seçmədi' : 'Baxıb çıxdı';
    }
    if (levels) return 'Mərhələ bitirdi';
    if (plays) return 'Oynadı';
    return interactions ? 'Toxundu, oynamadı' : 'Baxıb çıxdı';
  }

  var pv = rid();
  function snapshot(ev, detail) {
    flushVisible();
    var cs = [];
    for (var k in counters) if (counters.hasOwnProperty(k)) cs.push(k + ':' + counters[k]);
    return {
      pv: pv, vid: vid, sid: sid,
      newRet: isNew ? 'Yeni' : 'Qayıdan', visitNo: +(store('l', 'l2r2_visits') || 1), firstSeen: store('l', 'l2r2_first') || '',
      pageNo: pageNo, page: page, outcome: outcome(),
      durationSec: Math.round((now() - t0) / 1000), activeSec: Math.round(activeMs / 1000), engagedSec: Math.round(engagedMs / 1000),
      interactions: interactions, plays: plays, levels: levels, progress: progress, chosen: chosen,
      counters: cs.join(', '), lastEvent: lastEvent, maxScroll: maxScroll,
      source: source, sessionSource: sessionSource, referrer: cut(d.referrer, 200), utm: utm,
      deviceType: deviceType, os: os, browser: browser, model: model, screen: screenStr,
      viewport: (w.innerWidth || '') + 'x' + (w.innerHeight || ''), touch: touch ? 'Bəli' : 'Xeyr',
      lang: nav.language || nav.userLanguage || '', tz: tz, region: region,
      net: conn && conn.effectiveType ? conn.effectiveType : '', loadMs: loadMs,
      errors: errors, errorMsg: errorMsg, ua: cut(ua, 300),
      event: ev, detail: cut(detail, 150)
    };
  }

  var lastLeave = 0, lastPingInteractions = -1;
  function send(ev, detail) {
    store('l', 'l2r2_last', now());
    var p = snapshot(ev, detail);
    if (debug && w.console) console.log('[L2R2Log]', ev, p);
    if (!ENDPOINT || (local && !debug)) return;
    var body = JSON.stringify(p);
    try { if (nav.sendBeacon && nav.sendBeacon(ENDPOINT, body)) return; } catch (e) {}
    try {
      var x = new XMLHttpRequest();
      x.open('POST', ENDPOINT, true);
      x.setRequestHeader('Content-Type', 'text/plain;charset=utf-8');
      x.send(body);
    } catch (e) {}
  }
  function leave() {
    if (now() - lastLeave < 1500) return;
    lastLeave = now();
    send('leave');
  }

  function onVisibility() {
    var v = d.visibilityState !== 'hidden';
    if (v === visible) return;
    if (!v) { flushVisible(); visible = false; leave(); }
    else { visible = true; visibleSince = now(); }
  }
  d.addEventListener('visibilitychange', onVisibility);
  w.addEventListener('pagehide', leave);
  w.addEventListener('beforeunload', leave);

  // hər dəqiqə: yeni toxunma olubsa vəziyyəti yenilə (tab birdən bağlansa da data itməsin)
  setInterval(function () {
    if (visible && interactions !== lastPingInteractions) { lastPingInteractions = interactions; send('ping'); }
  }, 60000);

  // link klikləri: hansı oyunu seçdi, hara çıxdı
  on(d, 'click', function (e) {
    var a = e.target;
    while (a && a.nodeName !== 'A') a = a.parentNode;
    if (!a || !a.href) return;
    if (a.host === loc.host) {
      var g = gameOf(a.pathname.charAt(0) === '/' ? a.pathname : '/' + a.pathname);
      if (g !== page && g !== HUB) { chosen = g; lastEvent = 'click_game'; send('click_game', g); }
    } else if (/^https?:/.test(a.href)) {
      lastEvent = 'click_out'; send('click_out', a.host);
    }
  });

  // ---------- public API ----------
  api.event = function (name, detail) {
    name = cut(name, 40);
    if (name === 'play_start') plays++;
    if (name === 'level_complete' || name === 'game_complete') levels++;
    if (detail != null && detail !== '') progress = cut(detail, 100);
    lastEvent = name;
    send(name, detail);
  };
  api.count = function (name, n) { name = cut(name, 30); counters[name] = (counters[name] || 0) + (n || 1); };

  // ---------- page_view ----------
  function start() {
    try {
      var t = w.performance && w.performance.timing;
      if (t && t.navigationStart && t.domContentLoadedEventEnd) loadMs = t.domContentLoadedEventEnd - t.navigationStart;
    } catch (e) {}
    send('page_view');
  }
  if (d.readyState === 'complete') start();
  else w.addEventListener('load', function () { setTimeout(start, 0); });
})();
