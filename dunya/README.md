# Bubu və Dünya 🦉

4–6 yaşlı uşaqlar üçün öyrədici oyun (AZ / RU / EN). Mövzular bağçanın orta qrupunun proqramına uyğundur.
Oxumaq lazım deyil: tapşırıqları bayquş Bubu səsli deyir.

▶️ **Oyna:** https://nilkin.github.io/L2R2_games/dunya/

## Mərhələlər (hər birində 5 tapşırıq, 1–3 ulduz)
| # | Mexanika | Nə öyrədir |
|---|---|---|
| 1 | 🎈 Rəngli şarı partlat | 4 əsas rəng |
| 2 | 🔺 Fiquru tap | dairə, kvadrat, üçbucaq, düzbucaqlı |
| 3 | 🐮 Heyvanı tap | ev heyvanları |
| 4 | 🐘 Böyük / kiçik, uzun / qısa | müqayisə |
| 5 | 🔊 Kim belə deyir? | heyvan səsləri |
| 6 | 🎨 Rənglə: düzgün boyanı seç | 8 rəng, əşyaların rəngi |
| 7 | 🧩 Fiqur qutusu (sürüşdür və ya toxun) | fiqurların forması (+ ulduz, ürək) |
| 8 | 🦁 Heyvanı tap | vəhşi heyvanlar |
| 9 | 👀 Bədən üzvləri | göz, burun, qulaq, ağız, əl, ayaq, diş |
| 10 | 🧺 Meyvə səbətə, tərəvəz qazana | qruplaşdırma |
| 11 | ☀️ Fəsli tap | yaz, yay, payız, qış |
| 12 | 🧐 Artıq olanı tap | təsnifat, məntiq |
| 13 | 🔁 Sonra hansı gəlir? | ardıcıllıq (AB, AAB, ABC) |

🔍 **Kəşf et** bölməsi sərbəst tanışlıq üçündür: şəklə toxunanda Bubu onun adını deyir (heyvanlarda səsini də).

Səhv cavabda Bubu uşağı danlamır. O, uşağın nə seçdiyini deyir ("Mavi.") və ya düzgün cavabı izah edir ("Alma meyvədir!"), sonra tapşırığı təkrarlayır.

**Başlanğıc ekranı "Kim oynayır?":** qız və ya oğlan seçilir və ad yazılır. Qız üçün default ad **Emilya**-dır, istəyən dəyişə bilər.
Hər seçim üçün ad ayrıca yadda saxlanır. Linkdə ad da vermək olar: `.../dunya/?ad=Aysel`.
Seçilmiş uşaq cığırda gəzir və qələbə kartında Bubu ilə birlikdə rəqs edir. Ad ekrandakı tərifdə görünür ("Afərin, Emilya!").
Səsli ad yalnız `make_audio.py`-dakı `NAMES` siyahısında olan adlar üçün var (indi yalnız Emilya üçün). Belə adlarda Bubu salamlayanda
və tərifdən sonra adı səsli deyir. Yeni ad əlavə etmək üçün onu `NAMES`-ə yazın və skripti işlədin.

## Dizayn
Dizayn L2R2-nin digər oyunlarına bənzəmir: "stiker kitabı" üslubundadır. Nöqtəli kağız fon, qalın tünd kontur, kəskin kölgə və Fredoka şrifti istifadə olunur.
Mərhələlər dolama cığır üzərindədir. Oyun zamanı Bubu aşağı küncdə (landşaftda solda) durur və komiks buludu ilə danışır.
Mərhələ bitəndə stiker-nişan yapışır.

## Səs
- Bütün ifadələr **yalnız** `tools/make_audio.py`-da yazılıb. Oyun bulud mətnini də `audio/manifest.js`-dən götürür.
- `audio/<dil>/<açar>.mp3`: 208 klip hər dildə, cəmi ~3,8 MB. Səslər: `az-AZ-BanuNeural`, `ru-RU-SvetlanaNeural`, `en-US-AnaNeural` (edge-tts).
- Uşaq səsinə yaxın olsun deyə ton qaldırılıb və pitch-shift tətbiq olunub (`VOICES`-də `pitch` və `shift`). Ayar dəyişəndə skript klipləri avtomatik yenidən yaradır.
- Açarlar: `n_<id>` ad, `q_<id>` "X haradadır?", `qb_<rəng>` şar, `qs_/rs_<heyvan>` səs sualı və cavabı, `pq_/pr_<əşya>` rəngləmə, `r_<id>` meyvə/tərəvəz/fəsil cavabı.

```
python -m venv venv                        # repodan kənarda
venv/Scripts/pip install edge-tts miniaudio lameenc
venv/Scripts/python dunya/tools/make_audio.py          # yalnız dəyişən / çatışmayan kliplər
python dunya/tools/make_audio.py --list                # bütün mətnlər (internetsiz)
python dunya/tools/make_audio.py --check               # siyahı = manifest = fayllar
```

## Texniki
Zuzu ilə eyni quruluşdur: bir `index.html`, şəkillər SVG və emoji ilə çəkilir, səs effektləri WebAudio ilə yaradılır.
Dil seçimi hub ilə ortaq `l2r2-lang` açarında saxlanır. İrəliləyiş `dunya-prog`-da, ad `dunya-name`-də saxlanır.
Klaviatura və TV pultu da işləyir: oxlar, Enter və Esc.
