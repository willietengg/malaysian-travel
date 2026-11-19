# Interview question bank

Ask in short rounds. Skip what the user has already told you. Use a clickable-option tool if the platform has one. Otherwise print numbered questions with lettered options and tell the user they can reply like `1B 2A 3C`. An open "Other / 其他 / Lain-lain" answer is always allowed.

## Round 0: Language

| | 中文 | English | Bahasa Melayu |
|---|---|---|---|
| Q | 你想用什么语言？ | Which language? | Bahasa pilihan? |
| A | 中文 | English | Bahasa Melayu |

## Round 1: Logistics

1. **Destination / 目的地 / Destinasi**
   - Country + cities, or "help me choose" (帮我选 / Tolong cadangkan).
   - If they want help choosing, ask about budget, length and season, then shortlist 2–3 countries using the holiday analysis and FX.

2. **Dates / 日期 / Tarikh**
   - A. Fixed dates → ask for them
   - B. Flexible within a month → which month?
   - C. Help me find the best window for my leave (帮我找最划算的请假时段 / Cari tarikh paling jimat cuti)

3. **Length / 天数 / Tempoh:** A. 3–4 days B. 5–6 days C. 7–9 days D. 10+ days

4. **Travellers / 人数 / Pelancong:** adults, children (ages), seniors. Mention that children and seniors change the pace and hotel choice.
   - Children in school? "OK to miss school days, or only during school holidays?" → use `holidays.py --family`.
   - Ages matter: child fares and tickets, and age-based entry rules (e.g. Korea K-ETA exempts ≤17 and ≥65).

5. **Malaysian state / 州属 / Negeri**
   Needed for state holidays, the weekend pattern (Kedah, Kelantan and Terengganu rest Fri–Sat) and the school-holiday group.
   Options: Selangor, KL / Putrajaya, Penang, Johor, Perak, Sabah, Sarawak, Other.

6. **Departure airport / 出发机场 / Lapangan terbang:** A. KUL (KLIA T1/T2) B. PEN C. BKI D. KCH E. JHB (or fly from SIN) F. Other

7. **Annual leave available / 可以请几天假 / Cuti tahunan:** A. 0–1 B. 2–3 C. 4–5 D. 6+ E. Not working / student / retired

8. **Budget per person (RM, all-in) / 每人预算 / Bajet seorang:** A. < RM 2,000 B. RM 2,000–4,000 C. RM 4,000–7,000 D. RM 7,000+ E. Not sure, show me options

## Round 2: Style

9. **Rank these three / 排序 / Susun keutamaan** (most important first):
   - 🏛️ 景点 Sightseeing / Tarikan
   - 🛍️ 城市购物 + chill Shopping + chill / Beli-belah + santai
   - 🍜 美食 hunt Food hunt / Buru makanan

   Store this as `meta.preferences.ranking`, e.g. `["food","attraction","shopping"]`. Time split ≈ 50 / 30 / 20 %.

10. **Diet / 饮食 / Pemakanan:** A. Halal only B. Muslim-friendly OK C. No pork D. Vegetarian E. No restriction
    → `halal | muslim-friendly | no-pork | vegetarian | none`
    - If A or B: "Do you want Friday prayer and prayer times in the plan?" and "Would you rather be home for Hari Raya?" → set `meta.preferences.muslim: true`, use `holidays.py --muslim`.

11. **Pace / 节奏 / Rentak:** A. Relaxed (3–4 stops a day) B. Balanced (5–6) C. Packed (7+)

12. **Flights / 航班偏好 / Penerbangan:**
    A. Cheapest total
    B. Comfort (full-service, better times)
    C. No preference
    Follow-up: "Will you shop a lot? (need checked baggage)" A. Yes, big haul B. Some C. Carry-on only

13. **Hotel / 住宿 / Penginapan:**
    A. Budget / hostel
    B. 3★ business hotel
    C. 4★+
    D. Apartment / Airbnb (family)

## Optional, only if relevant

- Special occasion (honeymoon, birthday)?
- Mobility needs (wheelchair, stroller, elderly knees: avoid stairs-heavy spots)?
- Must-do items already in mind (USJ, Disney, specific restaurant)?
- Driving abroad (needs an International Driving Permit from JPJ)?

## After the interview

Repeat the key facts back in 3–4 lines, e.g. "雪兰莪 · 2 大人 · 3 月 5 天 · 可请 3 天假 · 每人 RM 4,000 · 美食>景点>购物 · 不吃猪肉". Then start Step 2. Don't ask "shall I proceed?" unless something is truly ambiguous.
