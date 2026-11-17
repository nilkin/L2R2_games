/**
 * L2R2 log server — Google Apps Script (Web App).
 * log.js-dən gələn məlumatı Google Sheets-ə yazır:
 *   "Ziyarətlər" — hər səhifə baxışı = 1 sətir (oyunçu çıxanda yenilənir: müddət, nəticə, mərhələ...)
 *   "Hadisələr"  — xam hadisə jurnalı (page_view, play_start, level_complete, click_game ...)
 *   "Xülasə"     — avtomatik hesabatlar (setup() yaradır)
 * Quraşdırma: logserver/README.md
 */

var TZ = 'Asia/Baku';
var VISITS = 'Ziyarətlər', EVENTS = 'Hadisələr', SUMMARY = 'Xülasə';

// [açar, sütun başlığı] — açar log.js-dəki snapshot sahəsidir
var COLS = [
  ['pv', 'Baxış ID'],
  ['time', 'Vaxt'],
  ['updated', 'Son yenilənmə'],
  ['vid', 'Ziyarətçi ID'],
  ['newRet', 'Yeni / Qayıdan'],
  ['visitNo', 'Neçənci gəliş'],
  ['firstSeen', 'İlk gəliş'],
  ['sid', 'Sessiya ID'],
  ['pageNo', 'Sessiyada səhifə №'],
  ['page', 'Səhifə / Oyun'],
  ['outcome', 'Nəticə'],
  ['durationSec', 'Müddət (san)'],
  ['activeSec', 'Ekranda (san)'],
  ['engagedSec', 'Aktiv oyun (san)'],
  ['interactions', 'Toxunma / klik'],
  ['plays', 'Oyun başladı (dəfə)'],
  ['levels', 'Bitirilən mərhələ'],
  ['progress', 'Son irəliləyiş'],
  ['chosen', 'Seçdiyi oyun'],
  ['counters', 'Sayğaclar'],
  ['lastEvent', 'Son hadisə'],
  ['maxScroll', 'Scroll %'],
  ['source', 'Haradan (bu səhifə)'],
  ['sessionSource', 'Haradan (ilk giriş)'],
  ['referrer', 'Referrer'],
  ['utm', 'UTM'],
  ['deviceType', 'Cihaz'],
  ['os', 'Əməliyyat sistemi'],
  ['browser', 'Brauzer'],
  ['model', 'Model'],
  ['screen', 'Ekran'],
  ['viewport', 'Pəncərə'],
  ['touch', 'Toxunma ekranı'],
  ['lang', 'Dil'],
  ['tz', 'Saat qurşağı'],
  ['region', 'Ölkə (təxmini)'],
  ['net', 'Şəbəkə'],
  ['loadMs', 'Yüklənmə (ms)'],
  ['errors', 'JS xəta sayı'],
  ['errorMsg', 'Son JS xətası'],
  ['ua', 'User-Agent']
];
var EV_COLS = ['Vaxt', 'Baxış ID', 'Ziyarətçi ID', 'Sessiya ID', 'Səhifə / Oyun', 'Hadisə', 'Detal', 'Cihaz', 'Haradan'];
var SKIP_EVENTS = { leave: 1, ping: 1 };   // bunlar yalnız "Ziyarətlər" sətrini yeniləyir

function doGet() {
  return ContentService.createTextOutput('L2R2 log server işləyir ✔');
}

function doPost(e) {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(20000)) return ContentService.createTextOutput('busy');
  try {
    var d = JSON.parse(e.postData.contents);
    if (!d || !d.pv || !d.vid) return ContentService.createTextOutput('bad');
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var vs = sheet_(ss, VISITS, COLS.map(function (c) { return c[1]; }));
    var es = sheet_(ss, EVENTS, EV_COLS);
    var t = new Date();

    // Ziyarətlər: pv üzrə upsert
    var row = COLS.map(function (c) {
      if (c[0] === 'time' || c[0] === 'updated') return t;
      return clean_(d[c[0]]);
    });
    var hit = vs.getRange('A:A').createTextFinder(String(d.pv)).matchEntireCell(true).findNext();
    if (hit) {
      row[1] = vs.getRange(hit.getRow(), 2).getValue() || t;   // ilk vaxtı saxla
      vs.getRange(hit.getRow(), 1, 1, row.length).setValues([row]);
    } else {
      vs.appendRow(row);
    }

    // Hadisələr
    var ev = clean_(d.event);
    if (ev && !SKIP_EVENTS[ev]) {
      es.appendRow([t, clean_(d.pv), clean_(d.vid), clean_(d.sid), clean_(d.page), ev, clean_(d.detail), clean_(d.deviceType), clean_(d.source)]);
    }
    return ContentService.createTextOutput('ok');
  } catch (err) {
    return ContentService.createTextOutput('err');
  } finally {
    lock.releaseLock();
  }
}

function clean_(v) {
  if (v === null || v === undefined) return '';
  if (typeof v === 'number' || typeof v === 'boolean') return v;
  var s = String(v).slice(0, 500);
  return /^[=+\-@]/.test(s) ? "'" + s : s;   // formula injection-dan qorunma
}

function sheet_(ss, name, headers) {
  var sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    sh.getRange(1, 1, 1, headers.length).setValues([headers]).setFontWeight('bold').setBackground('#fff3c4');
    sh.setFrozenRows(1);
  }
  return sh;
}

function col_(key) {
  for (var i = 0; i < COLS.length; i++) if (COLS[i][0] === key) return letter_(i + 1);
  throw new Error('sütun yoxdur: ' + key);
}
function letter_(n) {
  var s = '';
  while (n > 0) { var r = (n - 1) % 26; s = String.fromCharCode(65 + r) + s; n = Math.floor((n - 1) / 26); }
  return s;
}

/** Bir dəfə redaktordan işə salın: vərəqləri, saat qurşağını və "Xülasə" hesabatlarını yaradır. */
function setup() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  ss.setSpreadsheetTimeZone(TZ);
  sheet_(ss, VISITS, COLS.map(function (c) { return c[1]; }));
  sheet_(ss, EVENTS, EV_COLS);

  var sh = ss.getSheetByName(SUMMARY) || ss.insertSheet(SUMMARY, 0);
  sh.clear();
  var R = "'" + VISITS + "'!A:" + letter_(COLS.length);
  var A = col_('pv'), T = col_('time'), V = col_('vid'), P = col_('page'), O = col_('outcome'),
      DU = col_('durationSec'), EN = col_('engagedSec'), PL = col_('plays'), LV = col_('levels'),
      DT = col_('deviceType'), SS = col_('sessionSource'), OS = col_('os'), BR = col_('browser'), RG = col_('region'), NR = col_('newRet');

  var blocks = [
    ['📊 Oyun üzrə: baxış, oyun, mərhələ, orta müddət',
      '=QUERY(' + R + ',"select ' + P + ', count(' + A + '), sum(' + PL + '), sum(' + LV + '), avg(' + DU + '), avg(' + EN + ') where ' + A + ' is not null group by ' + P +
      ' order by count(' + A + ') desc label count(' + A + ') \'Baxış\', sum(' + PL + ') \'Oyun başladı\', sum(' + LV + ') \'Mərhələ\', avg(' + DU + ') \'Orta müddət (san)\', avg(' + EN + ') \'Orta aktiv oyun (san)\'",1)'],
    ['👤 Unikal ziyarətçi (oyun üzrə)',
      '=QUERY(QUERY(' + R + ',"select ' + P + ', ' + V + ', count(' + A + ') where ' + A + ' is not null group by ' + P + ', ' + V + '",1),"select Col1, count(Col2) group by Col1 label count(Col2) \'Unikal ziyarətçi\'",1)'],
    ['🎯 Nəticə: kim oynadı, kim baxıb çıxdı',
      '=QUERY(' + R + ',"select ' + P + ', count(' + A + ') where ' + A + ' is not null group by ' + P + ' pivot ' + O + '",1)'],
    ['📱 Cihaz növü',
      '=QUERY(' + R + ',"select ' + P + ', count(' + A + ') where ' + A + ' is not null group by ' + P + ' pivot ' + DT + '",1)'],
    ['🔗 Haradan gəliblər (ilk giriş)',
      '=QUERY(' + R + ',"select ' + SS + ', count(' + A + ') where ' + A + ' is not null group by ' + SS + ' order by count(' + A + ') desc label count(' + A + ') \'Baxış\'",1)'],
    ['🆕 Yeni / qayıdan',
      '=QUERY(' + R + ',"select ' + NR + ', count(' + A + ') where ' + A + ' is not null group by ' + NR + ' label count(' + A + ') \'Baxış\'",1)'],
    ['💻 Əməliyyat sistemi',
      '=QUERY(' + R + ',"select ' + OS + ', count(' + A + ') where ' + A + ' is not null group by ' + OS + ' order by count(' + A + ') desc label count(' + A + ') \'Baxış\'",1)'],
    ['🌐 Brauzer',
      '=QUERY(' + R + ',"select ' + BR + ', count(' + A + ') where ' + A + ' is not null group by ' + BR + ' order by count(' + A + ') desc label count(' + A + ') \'Baxış\'",1)'],
    ['🗺️ Ölkə (saat qurşağından)',
      '=QUERY(' + R + ',"select ' + RG + ', count(' + A + ') where ' + A + ' is not null group by ' + RG + ' order by count(' + A + ') desc label count(' + A + ') \'Baxış\'",1)'],
    ['📅 Günlük (son günlər yuxarıda)',
      '=QUERY(' + R + ',"select toDate(' + T + '), count(' + A + ') where ' + A + ' is not null group by toDate(' + T + ') pivot ' + P + ' order by toDate(' + T + ') desc",1)']
  ];

  // bloklar iki sütunda, hər biri 16 sətir yer tutur
  blocks.forEach(function (b, i) {
    var r = 1 + Math.floor(i / 2) * 16, c = i % 2 === 0 ? 1 : 10;
    sh.getRange(r, c).setValue(b[0]).setFontWeight('bold').setFontSize(12);
    sh.getRange(r + 1, c).setFormula(b[1]);
  });
  sh.setFrozenRows(0);
  SpreadsheetApp.flush();
}
