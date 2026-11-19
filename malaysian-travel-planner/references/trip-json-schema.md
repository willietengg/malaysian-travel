# trip.json schema

One file drives both `make_excel.py` and `make_ppt.py`. Every text field is free text in the user's language. Unknown optional fields can be omitted. A complete example: `examples/osaka-kyoto-5d.json` (inside the skill folder).

```jsonc
{
  "meta": {
    "language": "zh",                       // zh | en | ms  (required)
    "title": "大阪 + 京都 5天4夜",            // required
    "destination_country": "JP",            // ISO code (required)
    "destination_name": "日本",
    "cities": ["大阪", "京都"],
    "start_date": "2027-03-10",             // required, YYYY-MM-DD
    "end_date": "2027-03-14",               // required
    "travelers": {"adults": 2, "children": 1, "seniors": 0, "children_ages": [7]},
    "home_state": "Selangor (SGR)",
    "departure_airport": "KUL",
    "budget_myr_pp": 4000,                  // optional: user's all-in budget per person, checked by check_trip.py
    "generated_on": "2026-11-16",
    "preferences": {
      "ranking": ["food", "attraction", "shopping"],  // order = priority
      "diet": "none",                        // halal | muslim-friendly | no-pork | vegetarian | none
      "pace": "normal",                      // relaxed | normal (alias: balanced) | packed
      "muslim": true                         // optional: Friday prayer + Ramadan/Raya checks
    }
  },
  "fx": {                                    // required
    "currency": "JPY",
    "rate_myr_per_unit": 0.029,              // RM for 1 unit of local currency
    "rate_date": "2026-11-16",
    "source": "open.er-api.com"
  },
  "holiday_analysis": {                      // paste from: holidays.py check ... --trip-json
    "summary": "one-line conclusion",
    "price_impact": "high",                  // low | medium | high | very_high
    "leave_needed": 1,
    "leave_dates": ["2027-03-12"],
    "weekend": ["Sat", "Sun"],               // from holidays.py; Fri-Sat for Kedah/Kelantan/Terengganu (calendar slide)
    "reasons": ["..."],
    "my_holidays": [{"date": "2027-03-10", "weekday": "星期三", "name": "开斋节"}],
    "school_holidays": [{"start": "2027-03-06", "end": "2027-03-14", "name": "..."}],
    "destination_events": [{"start": "...", "end": "...", "name": "...", "level": "high"}],
    "recommendation": "what you advise and why",
    "alternatives": [{"start": "...", "end": "...", "leave_needed": 3, "price_impact": "low", "note": "..."}]
  },
  "flights_note": "Fares are estimates from 2026-11-16, not live quotes.",
  "flights": [{
    "airline": "AirAsia X (D7)", "type": "LCC",       // LCC | FSC | Hybrid
    "route": "KUL ⇄ KIX direct",
    "schedule": "Out 23:55→07:30(+1) / Back 13:30→20:00",
    "duration": "≈6.5h",
    "fare_myr": 1100,                         // base fare per person, return
    "baggage": "7kg cabin only",
    "addons_myr": 290,                        // bag + meals + seat per person
    "notes": "...",
    "recommended": true                       // exactly one
  }],
  "itinerary": [{
    "day": 1, "date": "2027-03-10", "city": "大阪", "theme": "抵达 + 难波",
    "items": [{
      "time": "10:00",
      "name": "黑门市场 Kuromon Market",
      "category": "food",                     // attraction | shopping | food | transport | hotel | flight | other
      "open_hours": "09:00-18:00",
      "closed": "部分摊位星期日休",
      "open_ok": true,                        // true | false | "check"  (omit for transport/hotel)
      "cost_local": 3000,                     // per person, local currency
      "notes": "...",
      "map": "https://maps.google.com/..."    // optional; auto-generated for attraction/shopping/food/prayer; "" = no link
    }]
  }],
  "food": [{
    "name": "章鱼烧", "local_name": "たこ焼き", "where": "道顿堀 Kukuru",
    "price_local": 700,
    "halal": "unknown",                       // halal | muslim-friendly | no-pork | contains-pork | vegetarian | unknown
    "halal_source": "KMF certified · https://...",  // required when halal / muslim-friendly
    "in_malaysia": "partial",                 // yes | no | partial | online | unknown
    "worth_it": "must",                       // must | worth | maybe | skip
    "notes": "..."
  }],
  "shopping": [{
    "name": "Uniqlo", "type": "服装", "in_malaysia": "yes",
    "price_diff": "日本约便宜 15-30%（估算）", "worth_it": "maybe", "notes": "..."
  }],
  "budget": [{
    "category": "hotel",                      // flight | hotel | transport | attraction | food | shopping | other
    "item": "难波商务酒店 双人房",
    "amount": 16000,
    "currency": "local",                      // local | MYR
    "qty": 4,
    "per": "group",                           // person (everyone) | adult (adults + seniors) | child | group
    "notes": "每晚 ¥16,000"
  }],
  "checklist": [{"item": "护照有效期 6 个月以上", "notes": "..."}],   // or plain strings
  "tips": ["..."],
  "sources": [{"title": "...", "url": "https://...", "checked": "2026-11-16"}]
}
```

## Budget maths

`subtotal_RM = (amount if MYR else amount × FX) × qty × N`, where N = all travellers (`person`), adults + seniors (`adult`), children (`child`) or 1 (`group`).

Per-person total = group total ÷ travellers. In Excel these are formulas tied to the named cells `FX`, `PAX`, `ADULTS` and `KIDS` on the Overview sheet.

## Validation

The scripts stop with a clear list of errors if required fields are missing. Fix them and re-run.
