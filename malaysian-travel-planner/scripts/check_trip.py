#!/usr/bin/env python3
"""Sanity-check a trip.json BEFORE generating the Excel / PPT.

  python check_trip.py trip.json          # human-readable report, exit 1 on errors
  python check_trip.py trip.json --json   # machine-readable

Catches the mistakes an AI planner most often makes:
  * FX rate inverted or wildly off (e.g. 34.5 instead of 0.029 for JPY)
  * a stop scheduled on a weekday its own `closed` field says it is shut
  * unresolved `open_ok: false` stops
  * food that contradicts the traveller's diet (pork for halal / no-pork users)
  * itinerary dates outside the trip or out of order
  * flights: fewer than 3 options, or not exactly one recommended
  * budget over the traveller's stated RM budget
  * missing sources / stale FX date
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date

from common import load_trip, travelers_count

# Plausible RM-per-unit ranges (wide on purpose; only catches inverted / garbage rates).
FX_RANGES = {
    "JPY": (0.015, 0.06), "KRW": (0.0015, 0.006), "THB": (0.08, 0.25), "TWD": (0.08, 0.25),
    "VND": (0.0001, 0.0003), "CNY": (0.4, 1.0), "SGD": (2.5, 4.5), "IDR": (0.0001, 0.0005),
    "HKD": (0.35, 0.8), "MOP": (0.35, 0.8), "EUR": (3.5, 7.0), "GBP": (4.0, 8.0), "USD": (3.0, 6.0),
    "AUD": (2.0, 4.5), "NZD": (1.8, 4.0), "NOK": (0.25, 0.7), "SEK": (0.25, 0.7), "DKK": (0.4, 1.0),
    "ISK": (0.02, 0.06), "CHF": (3.5, 7.0), "PHP": (0.05, 0.12), "INR": (0.03, 0.08), "TRY": (0.08, 0.4),
    "AED": (0.8, 1.6), "SAR": (0.8, 1.6), "KHR": (0.0007, 0.0015), "LAK": (0.00015, 0.0004),
    "MMK": (0.0015, 0.004), "BND": (2.5, 4.5), "MYR": (1.0, 1.0),
}

WEEKDAY_PATTERNS = [
    # index 0 = Monday
    (0, r"星期一|周一|週一|礼拜一|禮拜一|\bmon(day)?s?\b|\bisnin\b|月曜"),
    (1, r"星期二|周二|週二|礼拜二|禮拜二|\btue(s|sday)?s?\b|\bselasa\b|火曜"),
    (2, r"星期三|周三|週三|礼拜三|禮拜三|\bwed(nesday)?s?\b|\brabu\b|水曜"),
    (3, r"星期四|周四|週四|礼拜四|禮拜四|\bthu(r|rs|rsday)?s?\b|\bkhamis\b|木曜"),
    (4, r"星期五|周五|週五|礼拜五|禮拜五|\bfri(day)?s?\b|\bjumaat\b|金曜"),
    (5, r"星期六|周六|週六|礼拜六|禮拜六|\bsat(urday)?s?\b|\bsabtu\b|土曜"),
    (6, r"星期日|星期天|周日|週日|礼拜天|禮拜天|\bsun(day)?s?\b|\bahad\b|日曜"),
]
PARTIAL_HINT = re.compile(r"部分|some|sesetengah|irregular|不定|不少|many|kadang", re.I)

DIET_CONFLICTS = {
    "halal": {"error": {"contains-pork"}, "warn": {"no-pork", "unknown"}},
    "muslim-friendly": {"error": {"contains-pork"}, "warn": {"unknown"}},
    "no-pork": {"error": {"contains-pork"}, "warn": set()},
    "vegetarian": {"error": {"contains-pork"}, "warn": {"halal", "muslim-friendly", "no-pork", "unknown"}},
}

HOURS_CATEGORIES = {"attraction", "shopping", "food"}


def closed_weekdays(text: str) -> set[int]:
    if not text:
        return set()
    return {idx for idx, pat in WEEKDAY_PATTERNS if re.search(pat, text, re.I)}


def check(trip: dict, today: date | None = None) -> tuple[list[str], list[str]]:
    today = today or date.today()
    errors, warns = [], []
    meta, fx = trip["meta"], trip["fx"]
    start, end = date.fromisoformat(meta["start_date"]), date.fromisoformat(meta["end_date"])
    if end < start:
        errors.append(f"meta.end_date {end} is before start_date {start}")

    # ---- FX ----
    cur, rate = fx["currency"].upper(), float(fx["rate_myr_per_unit"])
    rng = FX_RANGES.get(cur)
    if rng and not (rng[0] <= rate <= rng[1]):
        inv = 1 / rate if rate else 0
        hint = " (looks inverted: you may have used units-per-RM)" if rng[0] <= inv <= rng[1] else ""
        errors.append(f"fx.rate_myr_per_unit={rate} is outside the plausible RM range {rng} for {cur}{hint}")
    if fx.get("rate_date"):
        try:
            age = (today - date.fromisoformat(fx["rate_date"])).days
            if age > 14:
                warns.append(f"FX rate is {age} days old ({fx['rate_date']}); refresh with fx.py")
        except ValueError:
            warns.append(f"fx.rate_date '{fx['rate_date']}' is not YYYY-MM-DD")

    # ---- itinerary ----
    prev = None
    for day in trip.get("itinerary", []):
        label = f"Day {day.get('day')}"
        ds = day.get("date")
        d = None
        if not ds:
            warns.append(f"{label}: no date, so opening days can't be checked")
        else:
            d = date.fromisoformat(ds)
            if not (start <= d <= end):
                errors.append(f"{label}: date {d} is outside the trip {start}..{end}")
            if prev and d <= prev:
                errors.append(f"{label}: date {d} is not after the previous day {prev}")
            prev = d
        for it in day.get("items", []):
            name = it.get("name", "?")
            cat = it.get("category", "other")
            ok = it.get("open_ok")
            if ok is False:
                errors.append(f"{label} '{name}': open_ok is false (closed that day). Move it or replace it")
            if cat in HOURS_CATEGORIES and "open_ok" not in it:
                warns.append(f"{label} '{name}': open_ok not set; check opening days/hours")
            if d is not None:
                hit = d.weekday() in closed_weekdays(it.get("closed", ""))
                if hit and ok is not False:
                    msg = (f"{label} ({d:%a}) '{name}': its 'closed' note says '{it['closed']}' "
                           f"but it is scheduled on that weekday")
                    (warns if PARTIAL_HINT.search(it.get("closed", "")) else errors).append(msg)
    days_in_trip = (end - start).days + 1
    if trip.get("itinerary") and len(trip["itinerary"]) != days_in_trip:
        warns.append(f"itinerary has {len(trip['itinerary'])} days but the trip spans {days_in_trip} days")

    # ---- flights ----
    flights = trip.get("flights", [])
    if len(flights) < 3:
        warns.append(f"only {len(flights)} flight option(s); compare at least 3 (MH, AirAsia, Batik, local carrier)")
    recs = [f for f in flights if f.get("recommended")]
    if flights and len(recs) != 1:
        errors.append(f"exactly one flight must be recommended (found {len(recs)})")
    for f in flights:
        if not isinstance(f.get("fare_myr"), (int, float)):
            warns.append(f"flight '{f.get('airline')}': fare_myr is not a number")

    # ---- food vs diet ----
    diet = (meta.get("preferences") or {}).get("diet", "none")
    rules = DIET_CONFLICTS.get(diet)
    if rules:
        for fd in trip.get("food", []):
            h = fd.get("halal", "unknown")
            if h in rules["error"]:
                errors.append(f"food '{fd.get('name')}' is '{h}' but the traveller's diet is '{diet}'")
            elif h in rules["warn"]:
                warns.append(f"food '{fd.get('name')}' is '{h}' for a '{diet}' traveller; confirm or replace")
        for day in trip.get("itinerary", []):
            for it in day.get("items", []):
                if it.get("category") == "food" and diet in ("halal", "muslim-friendly", "no-pork") and \
                        re.search(r"pork|豚|猪|豬|babi|tonkotsu|samgyeopsal|bacon|ham\b|char siu|叉烧", it.get("name", "") + " " + it.get("notes", ""), re.I) \
                        and not re.search(r"no[- ]pork|不含猪|无猪|tanpa babi|avoid|避开|不吃", it.get("notes", ""), re.I):
                    warns.append(f"Day {day.get('day')} '{it.get('name')}': mentions pork for a '{diet}' traveller")

    # ---- budget ----
    pax = travelers_count(meta)
    total = 0.0
    for b in trip.get("budget", []):
        amt = float(b.get("amount") or 0)
        myr = amt if b.get("currency") == "MYR" else amt * rate
        total += myr * float(b.get("qty", 1)) * (pax if b.get("per", "person") == "person" else 1)
    target = meta.get("budget_myr_pp")
    if isinstance(target, (int, float)) and total:
        pp = total / pax
        if pp > target * 1.1:
            warns.append(f"budget RM {pp:,.0f}/person is over the stated RM {target:,.0f} (+{pp / target - 1:.0%})")
    if not trip.get("budget"):
        warns.append("budget is empty")

    # ---- misc ----
    if not trip.get("sources"):
        warns.append("no sources listed; add the URLs you checked (with dates)")
    if not trip.get("holiday_analysis"):
        warns.append("holiday_analysis missing; run holidays.py check --trip-json")
    return errors, warns


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("trip")
    p.add_argument("--json", action="store_true")
    p.add_argument("--today", help="override today's date (YYYY-MM-DD), for tests")
    a = p.parse_args(argv)
    trip = load_trip(a.trip)
    errors, warns = check(trip, date.fromisoformat(a.today) if a.today else None)
    if a.json:
        print(json.dumps({"ok": not errors, "errors": errors, "warnings": warns}, ensure_ascii=False, indent=2))
    else:
        for e in errors:
            print(f"❌ {e}")
        for w in warns:
            print(f"⚠️  {w}")
        print(f"\n{len(errors)} error(s), {len(warns)} warning(s)" + ("" if errors else " — OK to generate"))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
