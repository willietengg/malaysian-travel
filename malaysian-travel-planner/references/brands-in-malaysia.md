# "Does Malaysia have it? Is it worth it?"

## Decision rules

1. **Find out if it exists in Malaysia.** Check the table below. If a row is marked `verify`, or the brand isn't listed, web-search `"<brand> Malaysia outlet"`, `"<brand> 马来西亚 分店"` or `"<brand> buka di Malaysia"`. Prefer news or the brand's own site from the last 12 months. Outlets open and close often.
2. **Set `in_malaysia`:**
   - `yes`: same brand, similar range
   - `partial`: exists but with a much smaller range or a different menu
   - `online`: only via Shopee, Lazada or the official e-shop
   - `no`: not in Malaysia
   - `unknown`: couldn't verify
3. **Compare price when it matters** (fashion, cosmetics, electronics): local price × FX (minus any tax refund) vs the Malaysian price. Say "约便宜 20%（估算）" and never present it as exact.
4. **Set `worth_it`:**

| Situation | Verdict |
|---|---|
| Not in MY, and a signature of the destination | `must` |
| Not in MY, nice but common | `worth` |
| In MY, but the destination has a much bigger range, limited editions, or is ≥20% cheaper after tax refund | `worth` (or `maybe` if the user ranks shopping last) |
| In MY, same range, price gap under ~15% | `skip`: "大马买就好" |
| Food chain that exists in MY | `maybe`. Only go if the menu or taste is different, or it's convenient. Don't spend scarce meal slots on it. |

5. **Adjust for the user's ranking.** If shopping is rank 1, be more generous with `worth`. If it's rank 3, be stricter.

## Seed list

*Last reviewed 2026-11. `verify` = re-check before stating. Pull requests welcome.*

### From Japan

| Brand | In MY | Notes |
|---|---|---|
| Uniqlo | yes | Japan is often cheaper plus tax refund; Japan-only collabs. |
| Muji | yes | Small price gap; usually `skip`. |
| Daiso | yes | MY is a fixed-price store (~RM 6.50) vs ¥110 in Japan; Japan has a larger range. |
| DON DON DONKI | partial | MY stores focus on food. Japan's Don Quijote has cosmetics, drugstore items, electronics and souvenirs. |
| Sushiro | yes | First MY store at Suria KLCC (Feb 2025); more in 1 Utama (2026). The KLCC outlet temporarily closed in Jul 2026 (verify). |
| Ippudo | yes | |
| Yoshinoya | yes | |
| Isetan | yes | KL (verify the current branches). |
| Kinokuniya | yes | Suria KLCC. |
| 100 Hours Curry | yes | First MY outlet in Jul 2026. |
| Ichiran | no | verify |
| Pokémon Center | no | Must for fans. |
| Matsumoto Kiyoshi / Sundrug / Welcia (drugstores) | no | Big savings on Japanese cosmetics and medicine. |
| Loft / Hands | no | verify |
| GU | unknown | verify |

### From Korea

| Brand | In MY | Notes |
|---|---|---|
| Olive Young | partial | No standalone store. Olive Young K-Beauty Edit inside Sephora (from Sep 2026, e.g. Fahrenheit88), plus an official Shopee store. Korea's flagship stores have a far bigger range. |
| Gentle Monster | yes | verify |
| Kyochon | yes | |
| Daiso Korea | no | Different company from Japanese Daiso; cheap Korean beauty and stationery. |
| Musinsa (store) | no | verify |

### From China

| Brand | In MY | Notes |
|---|---|---|
| Haidilao | yes | |
| Mixue | yes | |
| Chagee | yes | |
| Luckin Coffee | yes | |
| Cotti Coffee | yes | |
| Pop Mart | yes | China has more blind-box series and limited editions. |
| Miniso | yes | |
| HEYTEA | yes | verify |

### From Taiwan

| Brand | In MY | Notes |
|---|---|---|
| Din Tai Fung | yes | |
| Chatime | yes | |
| Tiger Sugar | yes | |
| Xing Fu Tang | yes | |
| Shihlin Taiwan Street Snacks | yes | The MY chain tastes different from real night-market food. |
| Eslite | no | verify |

### From Thailand / Vietnam

| Brand | In MY | Notes |
|---|---|---|
| Thai convenience-store snacks (7-Eleven Thailand exclusives) | no | The range is very different from 7-Eleven Malaysia. |
| Big C / Lotus's (Thai hypermarkets) | partial | Lotus's is in MY, but Thai stores carry Thai snacks and souvenirs. |
| Cộng Cà Phê | unknown | verify |
| Phúc Long / Highlands Coffee | no | verify |

## How to phrase it to the user

- 中文: "这家大马已经有了（KLCC、1 Utama），日本比较便宜但不用专程去。"
- EN: "Already in Malaysia (KLCC, 1 Utama). Cheaper in Japan, but not worth a special trip."
- BM: "Sudah ada di Malaysia (KLCC, 1 Utama). Lebih murah di Jepun tetapi tak perlu pergi khas."
