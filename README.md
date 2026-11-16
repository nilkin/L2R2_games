# 🎮 L2R2 Oyunlar

Uşaqlar üçün pulsuz brauzer oyunları — hamısı bir yerdə.

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
`index.html`-in başındakı `FORM_ENDPOINT` boşdursa, ideya hazır doldurulmuş GitHub Issue kimi açılır.
E-poçtla qəbul etmək üçün [Formspree](https://formspree.io)-də form yarat və ünvanı ora yaz.

## Tarixçə
`alfa_be` və `jumping-friends` əvvəllər ayrı repolar idi; `git subtree` ilə bütün commit tarixçəsi ilə birləşdirilib.
