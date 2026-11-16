# Flight comparison method

## Always compare

| Group | Carriers | Notes |
|---|---|---|
| Malaysian full-service | **Malaysia Airlines (MH)** | Meals included. Baggage depends on fare family (lowest fares may have no checked bag; check). Enrich points; oneworld. |
| Malaysian low-cost | **AirAsia (AK) / AirAsia X (D7)** | Fares exclude checked bag, meals and seat. Frequent sales. Wide-body D7 flies medium-haul (Japan, Korea); some routes are moving to AK narrow-body, so check. |
| Malaysian hybrid | **Batik Air Malaysia (OD)** | Often includes a checked bag and a snack on international fares (depends on fare). Fewer flights a week on some routes, and schedules get cut. |
| Destination carriers | see the destination file | e.g. JAL/ANA (Japan), Korean Air (Korea), Thai Airways / Thai AirAsia (Thailand), China Airlines / EVA / Starlux (Taiwan), Vietnam Airlines / VietJet (Vietnam), China Southern / China Eastern / Air China / Xiamen Air (China). |

Routes change every season. **Always web-search** "<origin> to <destination> direct flights <month year>" and the airlines' own route news before stating who flies direct.

## True total cost (per person, return)

```
true_total = base fare
           + checked bag (both ways; size it to the user's shopping plan)
           + meals (LCC: ~RM 20–40 per sector; skip if the user doesn't care)
           + seat selection (only if travelling as a group/family who must sit together)
           + extra transfer cost caused by bad timing (e.g. arrival after the last train → taxi)
```

Put base fare in `fare_myr` and the rest in `addons_myr`. The Excel computes `true total = fare + add-ons`.

## Things that matter to Malaysians

- **Shopping trip?** A 20 kg bag one way and 30–40 kg back is common. On LCCs, buy the bag at booking; airport rates are much higher.
- **Red-eye flights** (KUL 23:00–01:00 → arrive 07:00) save a hotel night but cost half of day 1. Plan a light day 1.
- **Return time.** An early-morning return wastes the last day. Afternoon or evening returns allow a last half-day.
- **Departure airport.** Penang, Johor, Kota Kinabalu and Kuching travellers may need to connect via KUL; add domestic legs and minimum connection time. Johor travellers should also compare flying from Singapore (SIN) and count the causeway time and cost.
- **Enrich, AirAsia points, BIG.** Mention them only if the user cares.
- **Sales.** AirAsia big sales and MATTA Fair periods: mention as a tip, never as a guaranteed price.

## Where the user should check live prices

- Google Flights (good for the fare calendar and spotting cheap dates)
- Skyscanner
- airasia.com, malaysiaairlines.com, batikair.com (direct booking avoids OTA fees and makes changes easier)

## Output format (flights[] in trip.json)

```json
{"airline": "AirAsia X (D7)", "type": "LCC", "route": "KUL ⇄ KIX direct",
 "schedule": "Out 23:55→07:30(+1) / Back 13:30→20:00", "duration": "≈6.5h",
 "fare_myr": 1100, "baggage": "7kg cabin only", "addons_myr": 290,
 "notes": "20kg + 2 meals + seat (estimate). Red-eye.", "recommended": true}
```

Mark exactly one option `recommended: true` and say why in `notes` (cheapest true total, best times, or best for families). Put "Fares are estimates from <date>, not live quotes" in `flights_note`.
