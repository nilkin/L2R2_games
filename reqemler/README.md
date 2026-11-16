# Zuzu və Rəqəmlər 🔢

3–7 yaşlı uşaqlar üçün rəqəm oyunu (AZ / RU / EN). Oxumaq lazım deyil — tapşırıqları Zuzu səsli deyir.

▶️ **Oyna:** https://nilkin.github.io/L2R2_games/reqemler/

## Mərhələlər (hər birində 5 tapşırıq, 1–3 ulduz)
| # | Mexanika | Nə öyrədir |
|---|---|---|
| 1 | 🍓 Zuzunu yedirt (1–3) | saymaq, birə-bir uyğunluq |
| 2 | 🎈 Rəqəmli şarı partlat (1–5) | rəqəmi tanımaq |
| 3 | 🐞 Toxun və say (1–6) | saymaq → rəqəm |
| 4 | 🎲 Dəstəni tap (1–6) | rəqəm → say, bir baxışda tanımaq |
| 5 | 🍪 Zuzunu yedirt + ✔ (3–8) | saymaq və vaxtında dayanmaq |
| 6 | 🎈 Şarlar (0–10) | rəqəmi tanımaq, sıfır |
| 7 | 🧱 Qüllə qur (3–10) | rəqəmə görə say düzəltmək |
| 8 | 🚂 Qatarda çatışmayan rəqəm | ardıcıllıq, irəli və geri sayma |
| 9 | ⚖️ Çox / az, böyük / kiçik | müqayisə |
| 10 | ➕ Ağacdan alma düşür | 10 daxilində toplama |
| 11 | ➖ Zuzu peçenye yeyir | 10 daxilində çıxma (sıfır da) |
| 12 | 🥚 Yumurta qutuları | 11–20, onluq + təklik |
| 13 | 🎈 İkirəqəmli şarlar (20–99) | 47 / 74 / 57 — mərtəbə qiyməti ilə oxumaq |
| 14 | 🧮 Onluq çubuqlar və təkliklər (21–99) | onluqla saymaq: 10, 20, 30… sonra 31, 32… |
| 15 | 🚂 Qatar 10–100 | ardıcıllıq və 10-larla sayma |

🔢 — sərbəst tanışlıq: 0–10 / 0–20 / 0–50 / 0–100 aralığı, ◀ ▶ (±1), ±10, sürətli keçid düymələri.
Ədəd onluq çubuqlar (mavi) və təkliklər (narıncı) ilə göstərilir, rəqəmlər də eyni rənglərdədir: **4**7 = 4 onluq, 7 təklik.

## Səs
Bütün danışıq oyunun içindədir — cihazda Azərbaycan səsi olmasa da hər yerdə eşidilir.

- `audio/az/`, `audio/ru/`, `audio/en/` — hər ifadə üçün qısa MP3 (mono, 40 kbit/s), ~263 klip hər dildə, cəmi ~4,7 MB.
  Səslər: `az-AZ-BanuNeural`, `ru-RU-SvetlanaNeural`, `en-US-AnaNeural` (Microsoft neural TTS, `edge-tts` ilə).
- `audio/manifest.js` — `window.AUD_PACK = {dil: {açar: [mətn, ms]}}`. Fayl adı = açar (`n47.mp3`, `find_t.mp3`...).
- Cümlələr kiçik kliplərdən növbə ilə qurulur, məs. `["n47","find_t"]` → “qırx yeddi | harada?”,
  `["n7","cmp_more_5"]` → “yeddi | beşdən çoxdur!”. Kliplərin əvvəl/sonundakı sükut generasiya zamanı kəsilir.
- Oynatma bir cüt `<audio>` elementi ilə olur (biri oxuyur, digəri növbətini əvvəlcədən yükləyir); ilk toxunuşda
  açılır (iOS qaydaları), `navigator.audioSession.type = 'playback'`. Klip yüklənməzsə — son çarə Web Speech.

### Səsləri yenidən yaratmaq
İfadələrin siyahısı və mətnləri `tools/make_audio.py`-dadır. Mətni dəyişdikdən sonra:
```
python -m venv venv                       # repodan kənarda
venv/Scripts/pip install edge-tts miniaudio lameenc
venv/Scripts/python reqemler/tools/make_audio.py          # yalnız dəyişən / çatışmayan kliplər
venv/Scripts/python reqemler/tools/make_audio.py --force  # hamısı
python reqemler/tools/make_audio.py --check               # yoxlama: siyahı = manifest = fayllar (internetsiz)
```
Skript `audio/<dil>/*.mp3` və `audio/manifest.js` fayllarını yeniləyir, artıq işlənməyən klipləri silir.
Oyunda yeni ifadə əlavə edirsinizsə, onun açarını həm `make_audio.py`-a, həm də `index.html`-dəki `SK` / `L()`-ə yazın.

## Texniki
- `index.html` — HTML/CSS/JS bir faylda, xarici resurs yalnız Google Fonts. Şəkillər SVG / CSS / emoji.
- Səs effektləri WebAudio ilə sintez olunur.
- Dil seçimi hub ilə ortaq `l2r2-lang` açarında; ulduzlar `reqem-prog`-da (köhnə 12 mərhələli irəliləyiş də işləyir).
- Klaviatura / TV pultu: oxlar, Enter, rəqəm düymələri, Esc.
