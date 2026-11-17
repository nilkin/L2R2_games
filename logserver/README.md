# 📊 L2R2 Log — ziyarət və oyun statistikası

```
Brauzer (log.js) ──POST──▶ Google Apps Script (server, Code.gs) ──▶ Google Sheets (loglar burada)
```

Loglar **serverdə** saxlanır: Google Cədvəlində. Brauzer yalnız məlumatı toplayıb göndərir.

## Quraşdırma (təxminən 5 dəqiqə, bir dəfəlik)

1. [sheets.new](https://sheets.new) ilə yeni Google Cədvəl yaradın və adını qoyun (məs. `L2R2 Log`).
2. **Uzantılar → Apps Script** açın. Oradakı kodu silib [`Code.gs`](Code.gs)-in məzmununu yapışdırın, sonra 💾 Saxla.
3. Yuxarıdakı funksiya siyahısından `setup` seçib **▶ Run** basın. Google icazə istəyəcək: hesabınızı seçin, sonra
   *Advanced → Go to … (unsafe) → Allow*. Bu sizin öz skriptinizdir. Cədvəldə `Xülasə`, `Ziyarətlər`, `Hadisələr` vərəqləri yaranır.
4. **Deploy → New deployment →** ⚙️ **Web app**:
   - *Execute as*: **Me**
   - *Who has access*: **Anyone**

   **Deploy** basın və **Web app URL**-ni kopyalayın (`https://script.google.com/macros/s/…/exec`).
5. Kökdəki [`log.js`](../log.js)-də `var ENDPOINT = '';` sətrinə bu URL-i yazın, sonra commit + push edin.
6. Yoxlama: URL-i brauzerdə açın, `L2R2 log server işləyir ✔` görünməlidir. Sonra saytı telefonda açın, bir dəqiqə sonra cədvəldə sətir görünəcək.

> `Code.gs`-i sonradan dəyişsəniz: **Deploy → Manage deployments → ✏️ → Version: New version → Deploy**. URL eyni qalır.

## Cədvəldə nə var

**Xülasə** (avtomatik hesabatlar): oyun üzrə baxış, oyuna başlama, mərhələ, orta müddət · unikal ziyarətçi ·
nəticə (oynadı / baxıb çıxdı) · cihaz · haradan gəliblər · yeni/qayıdan · ƏS · brauzer · ölkə · günlük.

**Ziyarətlər**: hər səhifə açılışı bir sətirdir. Oyunçu çıxanda həmin sətir yenilənir.

| Sual | Sütunlar |
|---|---|
| **Kim?** | Ziyarətçi ID (anonim, cihaza bağlı), Yeni / Qayıdan, Neçənci gəliş, İlk gəliş, Sessiya ID |
| **Hansı oyun?** | Səhifə / Oyun, Seçdiyi oyun (ana səhifədə hansı karta basıb) |
| **Nə etdi?** | **Nəticə**, Oyun başladı (dəfə), Bitirilən mərhələ, Son irəliləyiş, Sayğaclar (`düz:12, səhv:3`) |
| **Nə qədər?** | Müddət, Ekranda (tab görünən vaxt), Aktiv oyun (son 15 san-də toxunma olan vaxt), Toxunma / klik |
| **Haradan?** | Haradan (bu səhifə), Haradan (ilk giriş), Referrer, UTM |
| **Cihaz?** | Cihaz (Telefon / Planşet / Kompüter / TV), ƏS, Brauzer, Model, Ekran, Pəncərə, Toxunma ekranı |
| **Harada?** | Dil, Saat qurşağı, Ölkə (saat qurşağından təxmini) |
| **Texniki** | Şəbəkə (4g/3g), Yüklənmə (ms), JS xəta sayı, Son JS xətası, User-Agent |

**Nəticə** sütununun mənaları:
- Oyunda: `Baxıb çıxdı` (heç toxunmayıb), `Toxundu, oynamadı`, `Oynadı`, `Mərhələ bitirdi`
- Ana səhifədə: `Baxıb çıxdı`, `Baxdı, oyun seçmədi`, `Oyun seçdi`

**Hadisələr**: xam jurnal. Hadisələr bunlardır: `page_view`, `play_start`, `level_complete`, `game_complete`, `click_game`, `click_out`, `idea_sent`.

## Faydalı

- **Mənbəni dəqiq bilmək üçün** linki paylaşanda UTM əlavə edin. WhatsApp və Telegram referrer göndərmir:
  `https://nilkin.github.io/L2R2_games/?utm_source=whatsapp&utm_campaign=mekteb1`
- **Öz cihazınızı loglamamaq üçün** saytı bir dəfə `?nolog=1` ilə açın. Geri qaytarmaq üçün `?nolog=0`.
- **Test**: `?logdebug=1` göndərilən məlumatı brauzer konsolunda göstərir. `localhost`-da loglar yalnız bu rejimdə göndərilir.
- **Yeni oyunda**: `<head>`-ə `<script src="../log.js"></script>` əlavə edin. İstəsəniz oyun kodunda bunları çağırın:
  ```js
  window.L2R2Log && L2R2Log.event('play_start', 'Mərhələ 1');
  window.L2R2Log && L2R2Log.event('level_complete', 'Mərhələ 1: 3⭐');
  window.L2R2Log && L2R2Log.count('düz');
  ```
  Çağırmasanız da səhifə açılışı, müddət, toxunmalar, cihaz və mənbə yazılır.

## Məxfilik
Uşaq saytıdır, ona görə ad, IP və dəqiq yer **yazılmır**. Ziyarətçi ID təsadüfi yaradılır və yalnız həmin cihazın brauzerində qalır.
Ölkə saat qurşağından təxmin edilir.
