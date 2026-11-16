# Reading the holiday analysis

`scripts/holidays.py` combines four calendars:

1. **Malaysian public holidays for the user's state.** Bundled in `data/my_holidays.json`. Replacement days (cuti ganti) are computed:
   - Sat–Sun states: a holiday on **Sunday** moves to the next working day.
   - Fri–Sat states (Kedah, Kelantan, Terengganu): a holiday on **Friday** moves to the next working day.
2. **KPM school holidays.** Group A = Kedah, Kelantan, Terengganu; Group B = everyone else.
3. **Destination peaks and closures.** Bundled in `data/destination_peaks.json`.
4. **The weekend pattern**, used to count annual-leave days.

## Fare-pressure score

| Signal | Points |
|---|---|
| Overlaps Malaysian school holidays | +2 |
| Major festival (CNY, Hari Raya Aidilfitri, Christmas, New Year) inside the trip or ≤2 days before departure | +2 |
| Otherwise any public holiday (long weekend) | +1 |
| Destination period: medium / high / very high (price or closure kind) | +1 / +2 / +3 |

0–1 = low 🟢 · 2–3 = medium 🟡 · 4–5 = high 🟠 · 6+ = very high 🔴

This is a **heuristic, not a fare quote**. Explain it in plain words: "撞到学校假期 + 开斋节，机票一般会贵很多，建议提早 3–4 个月订或换日期。"

## How to advise

- **Leave-efficiency first, money second** (unless the user said budget matters most). Show the trade-off: "Option A: 1 day leave, high fares. Option B: 3 days leave, low fares."
- **Double peak** (Malaysian holiday + destination peak, e.g. CNY to Taiwan or China, or Raya + sakura): warn strongly. Prices spike and places are crowded or closed.
- **Closures** (Japan 29 Dec–3 Jan, Korea Seollal and Chuseok, Vietnam Tet, China Spring Festival, Taiwan CNY): many family-run restaurants and shops close. Re-check every stop.
- **Weather windows** (typhoon, rainy, very hot) usually mean cheaper fares. Mention both sides.
- **Book-ahead rule of thumb:** high or very high → book 3–4+ months ahead; low → 4–8 weeks is usually fine for short-haul Asia. Present this as a rule of thumb, not a fact.
- The `windows` sub-command finds:
  - `--leave N`: the longest trips using at most N leave days (only "maximal" windows, which can't be extended for free)
  - `--days N`: the N-day windows with the least leave, then the lowest pressure

## Bridging tips to mention when relevant

- Holiday on a Thursday → take Friday off → 4-day weekend for 1 leave day.
- Holiday on a Tuesday → take Monday off.
- CNY and Raya often give 2 consecutive holidays plus a replacement day; check `list` for the user's state.
- State holidays (e.g. Selangor Sultan's Birthday 11 Dec, Penang Heritage Day 7 Jul, Sarawak Day 22 Jul) are hidden gems for people in those states.

## Data freshness

- Bundled data: Nov 2026 → Dec 2027. Islamic dates are **provisional** until gazetted.
- Outside that range, or to double-check: web-search `cuti umum <year> <state>`, `kalendar akademik <year> KPM`, and the official site `kabinet.gov.my` (Hari Kelepasan Am).
- Contributors: update `data/my_holidays.json` each year when the government announces the list (usually around August–September).
