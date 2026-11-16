# 🎮 L2R2 Oyunlar

Uşaqlar üçün brauzer oyunları — hamısı bir yerdə.

▶️ **Oyna:** https://nilkin.github.io/L2R2_games/

| Oyun | Qovluq | Link |
|---|---|---|
| Hərf Oyunu 🎈 | [`alfa_be/`](alfa_be/) | https://nilkin.github.io/L2R2_games/alfa_be/ |
| Atlayan Dostlar 🦗🐸🐰🐧 | [`jumping-friends/`](jumping-friends/) | https://nilkin.github.io/L2R2_games/jumping-friends/ |

## Struktur
```
index.html          ← mərkəzi səhifə (oyun kartları + ideya forması)
alfa_be/            ← hər oyun öz qovluğunda, öz index.html-i ilə
jumping-friends/
```

## Yeni oyun əlavə etmək
1. Yeni qovluq yarat, məs. `yeni-oyun/`, və oyunu `yeni-oyun/index.html`-ə qoy.
   Fayllara nisbi yolla müraciət et (`audio/x.mp3`, `/audio/x.mp3` yox).
2. Kökdəki `index.html`-də `.games` blokunda mövcud kartı (`<a class="game" ...>`) kopyala,
   `href="yeni-oyun/"` et, şəkli və mətni dəyiş. Mətnlər üçün `T.az / T.ru / T.en`-ə açar əlavə et.
3. Bu cədvələ sətir əlavə et, commit + push — bir neçə dəqiqəyə saytda olur.

## İdeya forması
İdeyalar **WhatsApp**-a gəlir: "WhatsApp-a göndər" basılanda WhatsApp ideya mətni hazır yazılmış halda açılır,
ziyarətçi sadəcə göndər düyməsini basır. Nömrə `index.html`-in başındakı `WHATSAPP_NUMBER`-dədir.
`WHATSAPP_NUMBER` boşdursa `FORM_ENDPOINT` (məs. [Formspree](https://formspree.io)), o da boşdursa GitHub Issue istifadə olunur.

## Tarixçə
`alfa_be` və `jumping-friends` əvvəllər ayrı repolar idi; `git subtree` ilə bütün commit tarixçəsi ilə birləşdirilib.
