#!/usr/bin/env python3
"""Malaysian holiday & timing analysis for outbound trips.

Sub-commands
------------
check    Analyse one trip window: MY public holidays (for the user's state, incl.
         computed replacement days), school-holiday overlap, destination peaks,
         annual leave needed and a fare-pressure score.
windows  Find the best travel windows: either the longest trips for a given
         annual-leave budget, or the cheapest-looking N-day windows.
list     List the holidays that apply to a state in a year.

Examples
--------
  python holidays.py check --state SGR --country JP --start 2027-03-10 --end 2027-03-14
  python holidays.py windows --state SGR --leave 3 --country JP --from 2027-01-01 --to 2027-06-30
  python holidays.py windows --state PNG --days 6 --leave 4 --country KR --json
  python holidays.py list --state KDH --year 2027 --lang en
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta

from common import DATA_DIR, L, WEEKDAYS, load_json, pick

DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

STATE_ALIASES = {
    "johor": "JHR", "jb": "JHR", "johor bahru": "JHR", "柔佛": "JHR", "新山": "JHR",
    "kedah": "KDH", "吉打": "KDH",
    "kelantan": "KTN", "吉兰丹": "KTN",
    "terengganu": "TRG", "登嘉楼": "TRG",
    "melaka": "MLK", "malacca": "MLK", "马六甲": "MLK",
    "negeri sembilan": "NSN", "ns": "NSN", "seremban": "NSN", "森美兰": "NSN",
    "pahang": "PHG", "彭亨": "PHG",
    "penang": "PNG", "pulau pinang": "PNG", "槟城": "PNG",
    "perak": "PRK", "ipoh": "PRK", "霹雳": "PRK",
    "perlis": "PLS", "玻璃市": "PLS",
    "selangor": "SGR", "雪兰莪": "SGR", "pj": "SGR", "petaling jaya": "SGR", "shah alam": "SGR", "subang": "SGR",
    "sabah": "SBH", "kota kinabalu": "SBH", "kk": "SBH", "沙巴": "SBH",
    "sarawak": "SWK", "kuching": "SWK", "砂拉越": "SWK", "古晋": "SWK",
    "kuala lumpur": "KUL", "kl": "KUL", "吉隆坡": "KUL",
    "putrajaya": "PJY", "布城": "PJY",
    "labuan": "LBN", "纳闽": "LBN",
}

LEVEL_POINTS = {"medium": 1, "high": 2, "very_high": 3}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_data():
    return load_json(DATA_DIR / "my_holidays.json"), load_json(DATA_DIR / "destination_peaks.json")


def resolve_state(raw: str, states: dict) -> str:
    key = raw.strip()
    if key.upper() in states:
        return key.upper()
    alias = STATE_ALIASES.get(key.lower())
    if alias:
        return alias
    sys.exit(f"Unknown state '{raw}'. Use one of: {', '.join(states)} (or a name like 'Selangor', 'Penang', 'KL').")


def d(s: str) -> date:
    return date.fromisoformat(s)


def daterange(a: date, b: date):
    cur = a
    while cur <= b:
        yield cur
        cur += timedelta(days=1)


def applies(h: dict, state: str) -> bool:
    if h["states"] == "ALL":
        return state not in h.get("except", [])
    return state in h["states"]


class StateCalendar:
    """Holidays, replacement days and weekends for one Malaysian state."""

    def __init__(self, hdata: dict, state: str):
        self.state = state
        self.info = hdata["states"][state]
        self.weekend = {DOW.index(x) for x in self.info["weekend"]}
        # Rest day whose holidays get a replacement: Sunday (Sat-Sun states) or Friday (Fri-Sat states).
        self.replace_dow = 6 if self.weekend == {5, 6} else 4
        self.group = self.info["school_group"]
        self.holidays: dict[date, list[dict]] = {}
        all_dates = [d(h["date"]) for h in hdata["holidays"]]
        self.coverage = (min(all_dates), max(all_dates)) if all_dates else None
        for h in sorted(hdata["holidays"], key=lambda x: x["date"]):
            if applies(h, state):
                self.holidays.setdefault(d(h["date"]), []).append(h)
        self._add_replacements()
        self.school = [s for s in hdata["school_holidays"] if s["group"] == self.group]

    def _add_replacements(self):
        for day in sorted(list(self.holidays)):
            if day.weekday() != self.replace_dow:
                continue
            for h in list(self.holidays[day]):
                if h.get("replacement"):
                    continue
                nxt = day + timedelta(days=1)
                while nxt.weekday() in self.weekend or nxt in self.holidays:
                    nxt += timedelta(days=1)
                self.holidays.setdefault(nxt, []).append({
                    "date": nxt.isoformat(),
                    "en": f"Replacement holiday for {h['en']}",
                    "zh": f"{h['zh']} 补假",
                    "ms": f"Cuti ganti {h['ms']}",
                    "status": "computed",
                    "replacement": True,
                    "peak": h.get("peak", False),
                })

    def is_off(self, day: date) -> bool:
        return day.weekday() in self.weekend or day in self.holidays

    def in_coverage(self, day: date) -> bool:
        return self.coverage is not None and self.coverage[0] - timedelta(days=60) <= day <= self.coverage[1]

    def school_overlap(self, a: date, b: date):
        out = []
        for s in self.school:
            sa, sb = d(s["start"]), d(s["end"])
            if sa <= b and a <= sb:
                out.append(s)
        return out


def destination_overlap(peaks: dict, country: str | None, a: date, b: date):
    if not country:
        return []
    return [p for p in peaks["periods"]
            if p["country"] == country and d(p["start"]) <= b and a <= d(p["end"])]


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
def analyse(cal: StateCalendar, peaks: dict, country: str | None, a: date, b: date, lang: str) -> dict:
    days = list(daterange(a, b))
    leave_days = [x for x in days if not cal.is_off(x)]
    hols = [(x, h) for x in days for h in cal.holidays.get(x, [])]
    # Holidays just before departure push outbound demand too.
    pre = [(x, h) for x in daterange(a - timedelta(days=2), a - timedelta(days=1))
           for h in cal.holidays.get(x, []) if h.get("peak")]
    school = cal.school_overlap(a, b)
    dest = destination_overlap(peaks, country, a, b)

    score, reasons = 0, []
    if school:
        score += 2
        reasons.append({"zh": "撞到大马学校假期（家庭出游多，机票贵）",
                        "en": "Overlaps Malaysian school holidays (families travel, fares up)",
                        "ms": "Bertembung cuti sekolah (tambang naik)"}[lang])
    if any(h.get("peak") for _, h in hols + pre):
        score += 2
        reasons.append({"zh": "碰上大节日（农历新年/开斋/圣诞/元旦）出国高峰",
                        "en": "Major festival outbound rush (CNY / Raya / Christmas / New Year)",
                        "ms": "Musim perayaan besar (CNY / Raya / Krismas)"}[lang])
    elif hols:
        score += 1
        reasons.append({"zh": "有公共假期，长周末出游的人会多",
                        "en": "Public holiday long weekend - more people flying",
                        "ms": "Cuti umum hujung minggu panjang"}[lang])
    price_dest = [p for p in dest if p["kind"] in ("price", "closure")]
    if price_dest:
        top = max(price_dest, key=lambda p: LEVEL_POINTS[p["level"]])
        score += LEVEL_POINTS[top["level"]]
        reasons.append(({"zh": "当地旺季：", "en": "Destination peak: ", "ms": "Musim puncak destinasi: "}[lang])
                       + pick(top, lang))
    level = "low" if score <= 1 else "medium" if score <= 3 else "high" if score <= 5 else "very_high"

    warnings = []
    if not (cal.in_coverage(a) and cal.in_coverage(b)):
        warnings.append({"zh": "此日期超出内置假期数据范围，请上网查当年的大马假期表。",
                         "en": "Dates fall outside the bundled holiday data - web-search that year's Malaysian holiday list.",
                         "ms": "Tarikh di luar data cuti terbina - semak senarai cuti tahun itu."}[lang])
    if any(h.get("status") == "provisional" for _, h in hols):
        warnings.append({"zh": "部分回教节日日期属预测（看月亮），需以政府宪报为准。",
                         "en": "Some Islamic holiday dates are provisional (moon sighting) - confirm with the gazette.",
                         "ms": "Sesetengah tarikh cuti Islam masih anggaran."}[lang])
    if any(p["kind"] == "closure" for p in dest):
        warnings.append({"zh": "当地节日期间很多店休息，景点和餐厅要逐一确认营业。",
                         "en": "Local festival closures - confirm each shop/attraction is open.",
                         "ms": "Banyak kedai tutup semasa perayaan tempatan."}[lang])

    return {
        "state": cal.state,
        "state_name": pick(cal.info, lang),
        "weekend": cal.info["weekend"],
        "school_group": cal.group,
        "start": a.isoformat(),
        "end": b.isoformat(),
        "total_days": len(days),
        "leave_needed": len(leave_days),
        "leave_dates": [x.isoformat() for x in leave_days],
        "public_holidays": [{"date": x.isoformat(), "weekday": WEEKDAYS[lang][x.weekday()],
                             "name": pick(h, lang), "status": h.get("status")} for x, h in hols],
        "school_holidays": [{"start": s["start"], "end": s["end"], "name": pick(s, lang)} for s in school],
        "destination_events": [{"start": p["start"], "end": p["end"], "name": pick(p, lang),
                                "level": p["level"], "kind": p["kind"]} for p in dest],
        "price_score": score,
        "price_impact": level,
        "reasons": reasons,
        "warnings": warnings,
    }


def find_windows(cal, peaks, country, frm: date, to: date, leave: int | None, days: int | None,
                 top: int, lang: str, min_days: int = 3, max_days: int = 16):
    cands = []
    starts = list(daterange(frm, to))
    for s in starts:
        lengths = [days] if days else range(min_days, max_days + 1)
        for n in lengths:
            e = s + timedelta(days=n - 1)
            if e > to:
                break
            need = sum(1 for x in daterange(s, e) if not cal.is_off(x))
            if leave is not None and need > leave:
                continue
            if not days:
                # Only keep "maximal" windows: can't extend for free on either side.
                if cal.is_off(s - timedelta(days=1)) or cal.is_off(e + timedelta(days=1)):
                    continue
            cands.append((s, e, n, need))
    if not cands:
        return []
    scored = []
    for s, e, n, need in cands:
        a = analyse(cal, peaks, country, s, e, lang)
        scored.append({**a, "efficiency": round(n / max(need, 1), 2)})
    if days:
        scored.sort(key=lambda w: (w["leave_needed"], w["price_score"], w["start"]))
    else:
        scored.sort(key=lambda w: (-w["total_days"], w["leave_needed"], w["price_score"], w["start"]))
    chosen = []
    for w in scored:
        ws, we = d(w["start"]), d(w["end"])
        if any(ws <= d(c["end"]) and d(c["start"]) <= we for c in chosen):
            continue
        chosen.append(w)
        if len(chosen) >= top:
            break
    return chosen


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def print_analysis(a: dict, lang: str):
    from common import IMPACT_LABELS
    print(f"== {a['start']} → {a['end']} ({a['total_days']}d) | {a['state_name']} "
          f"(weekend {'-'.join(a['weekend'])}, school group {a['school_group']})")
    print(f"   {L('leave_needed', lang)}: {a['leave_needed']}  {a['leave_dates']}")
    print(f"   {L('price_impact', lang)}: {L(a['price_impact'], lang, IMPACT_LABELS)} (score {a['price_score']})")
    for h in a["public_holidays"]:
        print(f"   🇲🇾 {h['date']} {h['weekday']}: {h['name']} [{h['status']}]")
    for s in a["school_holidays"]:
        print(f"   🏫 {s['start']}..{s['end']}: {s['name']}")
    for e in a["destination_events"]:
        print(f"   📍 {e['start']}..{e['end']}: {e['name']} ({e['level']}, {e['kind']})")
    for r in a["reasons"]:
        print(f"   • {r}")
    for w in a["warnings"]:
        print(f"   ⚠️  {w}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common_args(sp):
        sp.add_argument("--state", required=True, help="Malaysian state code or name, e.g. SGR, Penang, KL")
        sp.add_argument("--country", help="Destination ISO code: JP KR TH TW VN CN")
        sp.add_argument("--lang", default="zh", choices=["zh", "en", "ms"])
        sp.add_argument("--json", action="store_true", help="Machine-readable output")

    c = sub.add_parser("check")
    common_args(c)
    c.add_argument("--start", required=True)
    c.add_argument("--end", required=True)

    w = sub.add_parser("windows")
    common_args(w)
    w.add_argument("--from", dest="frm", default=None)
    w.add_argument("--to", default=None)
    w.add_argument("--leave", type=int, default=None, help="Max annual-leave days you can take")
    w.add_argument("--days", type=int, default=None, help="Exact trip length in days")
    w.add_argument("--min-days", type=int, default=3)
    w.add_argument("--max-days", type=int, default=16)
    w.add_argument("--top", type=int, default=8)

    li = sub.add_parser("list")
    li.add_argument("--state", required=True)
    li.add_argument("--year", type=int, required=True)
    li.add_argument("--lang", default="zh", choices=["zh", "en", "ms"])
    li.add_argument("--json", action="store_true")

    args = p.parse_args(argv)
    hdata, peaks = load_data()
    state = resolve_state(args.state, hdata["states"])
    cal = StateCalendar(hdata, state)
    country = getattr(args, "country", None)
    country = country.upper() if country else None
    if country and country not in peaks["countries"]:
        print(f"Note: no bundled peak-season data for {country}; web-search its holidays.", file=sys.stderr)

    if args.cmd == "check":
        a, b = d(args.start), d(args.end)
        if b < a:
            sys.exit("--end is before --start")
        res = analyse(cal, peaks, country, a, b, args.lang)
        print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else "", end="")
        if not args.json:
            print_analysis(res, args.lang)
    elif args.cmd == "windows":
        if args.leave is None and args.days is None:
            sys.exit("Give --leave N (leave budget) and/or --days N (exact trip length).")
        frm = d(args.frm) if args.frm else max(date.today(), cal.coverage[0])
        to = d(args.to) if args.to else cal.coverage[1]
        res = find_windows(cal, peaks, country, frm, to, args.leave, args.days, args.top, args.lang,
                           args.min_days, args.max_days)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            if not res:
                print("No window matches. Try a bigger --leave or a wider --from/--to range.")
            for i, wdw in enumerate(res, 1):
                print(f"\n#{i}  efficiency {wdw['efficiency']} days per leave day")
                print_analysis(wdw, args.lang)
    else:
        rows = []
        for day in sorted(cal.holidays):
            if day.year == args.year:
                for h in cal.holidays[day]:
                    rows.append({"date": day.isoformat(), "weekday": WEEKDAYS[args.lang][day.weekday()],
                                 "name": pick(h, args.lang), "status": h.get("status")})
        if args.json:
            print(json.dumps({"state": state, "school": cal.school, "holidays": rows}, ensure_ascii=False, indent=2))
        else:
            for r in rows:
                print(f"{r['date']} {r['weekday']:<4} {r['name']} [{r['status']}]")
            for s in cal.school:
                print(f"🏫 {s['start']}..{s['end']} {pick(s, args.lang)}")


if __name__ == "__main__":
    main()
