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

🔢 — sərbəst tanışlıq: 0–20 rəqəmləri, adı və onluq çərçivə.

## Texniki
- Tək `index.html`, xarici fayl yoxdur (yalnız Google Fonts). Şəkillər SVG / CSS / emoji.
- Danışıq: Web Speech API (`speechSynthesis`). Azərbaycan səsi yoxdursa türk səsi, o da yoxdursa yalnız səs effektləri.
- Səs effektləri WebAudio ilə sintez olunur.
- Dil seçimi hub ilə ortaq `l2r2-lang` açarında; ulduzlar `reqem-prog`-da saxlanılır.
- Klaviatura / TV pultu: oxlar, Enter, rəqəm düymələri, Esc.
