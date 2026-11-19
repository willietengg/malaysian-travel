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
        self.ramadan = [(d(o["start"]), d(o["end"])) for o in hdata.get("observances", []) if o["kind"] == "ramadan"]
        self.raya_day1 = {x for x, hs in self.holidays.items()
                          for h in hs if h.get("en") == "Hari Raya Aidilfitri"}

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

    def in_school_holiday(self, day: date) -> bool:
        return any(d(s["start"]) <= day <= d(s["end"]) for s in self.school)

    def school_days_missed(self, a: date, b: date) -> int:
        """School days (state's working days, not public or school holidays) inside the trip."""
        return sum(1 for x in daterange(a, b) if not self.is_off(x) and not self.in_school_holiday(x))

    def ramadan_days(self, a: date, b: date) -> int:
        return sum(1 for x in daterange(a, b) for rs, re_ in self.ramadan if rs <= x <= re_)

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
def analyse(cal: StateCalendar, peaks: dict, country: str | None, a: date, b: date, lang: str,
            muslim: bool = False, family: bool = False) -> dict:
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
    if school and any(sh.get("status") == "approx" for sh in school):
        warnings.append({"zh": "学校假期日期是非官方整理的，请对照教育部（KPM）日历。",
                         "en": "School-holiday dates are from unofficial sources - confirm with the KPM calendar.",
                         "ms": "Tarikh cuti sekolah daripada sumber tidak rasmi - semak kalendar KPM."}[lang])
    muslim_conflict = 0
    if muslim:
        rd = cal.ramadan_days(a, b)
        if rd:
            muslim_conflict += 1
            warnings.append({"zh": f"有 {rd} 天在斋戒月：要安排封斋饭和开斋时间，部分清真餐厅白天不营业。",
                             "en": f"{rd} day(s) fall in Ramadan: plan sahur/iftar times; some halal restaurants close by day.",
                             "ms": f"{rd} hari dalam bulan Ramadan: rancang sahur/iftar."}[lang])
        if any(a <= x <= b for x in cal.raya_day1):
            muslim_conflict += 2
            warnings.append({"zh": "开斋节第一天在国外，确认是否要在家过节。",
                             "en": "Hari Raya day 1 is spent abroad - check the family is OK celebrating away.",
                             "ms": "Hari Raya pertama di luar negara - pastikan keluarga setuju."}[lang])
    school_missed = cal.school_days_missed(a, b) if family else 0
    if family and school_missed:
        warnings.append({"zh": f"小孩要请 {school_days_txt(school_missed, 'zh')} 上学日的假。",
                         "en": f"Children miss {school_missed} school day(s).",
                         "ms": f"Anak-anak terlepas {school_missed} hari sekolah."}[lang])
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
        "school_days_missed": school_missed,
        "muslim_conflict": muslim_conflict,
        "reasons": reasons,
        "warnings": warnings,
    }


def school_days_txt(n: int, lang: str) -> str:
    return f"{n} 天"


def find_windows(cal, peaks, country, frm: date, to: date, leave: int | None, days: int | None,
                 top: int, lang: str, min_days: int = 3, max_days: int = 16,
                 muslim: bool = False, family: bool = False, allow_overlap: bool = False):
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
        a = analyse(cal, peaks, country, s, e, lang, muslim=muslim, family=family)
        scored.append({**a, "efficiency": round(n / max(need, 1), 2)})

    def penalty(w):
        return w["muslim_conflict"] * 2 + w["school_days_missed"]

    if days:
        scored.sort(key=lambda w: (w["leave_needed"] + penalty(w), w["price_score"], w["start"]))
    else:
        scored.sort(key=lambda w: (-w["total_days"], w["leave_needed"] + penalty(w), w["price_score"], w["start"]))
    chosen = []
    for w in scored:
        ws, we = d(w["start"]), d(w["end"])
        if not allow_overlap and any(ws <= d(c["end"]) and d(c["start"]) <= we for c in chosen):
            continue
        if allow_overlap and any(c["start"] == w["start"] and c["end"] == w["end"] for c in chosen):
            continue
        chosen.append(w)
        if len(chosen) >= top:
            break
    return chosen


def summary_line(a: dict, lang: str) -> str:
    from common import IMPACT_LABELS
    lvl = L(a["price_impact"], lang, IMPACT_LABELS)
    if lang == "zh":
        return f"{a['start']} 至 {a['end']} 共 {a['total_days']} 天，需请 {a['leave_needed']} 天假；机票价格压力：{lvl}。"
    if lang == "ms":
        return f"{a['start']} hingga {a['end']} ({a['total_days']} hari), perlu {a['leave_needed']} hari cuti; tekanan harga tiket: {lvl}."
    return f"{a['start']} to {a['end']} ({a['total_days']} days) needs {a['leave_needed']} day(s) of annual leave; fare pressure: {lvl}."


def alt_note(w: dict, lang: str) -> str:
    leave = {"zh": f"请 {w['leave_needed']} 天假", "en": f"{w['leave_needed']} leave day(s)",
             "ms": f"{w['leave_needed']} hari cuti"}[lang]
    bits = [leave]
    bits += [h["name"] for h in w["public_holidays"][:2]]
    ev = [e["name"] for e in w["destination_events"]]
    if ev:
        bits.append(ev[0])
    if w.get("school_days_missed"):
        bits.append({"zh": f"小孩缺课 {w['school_days_missed']} 天", "en": f"kids miss {w['school_days_missed']} school day(s)",
                     "ms": f"anak terlepas {w['school_days_missed']} hari sekolah"}[lang])
    if not w["school_holidays"] and not w["public_holidays"]:
        bits.append({"zh": "不撞大马假期", "en": "no Malaysian holiday clash", "ms": "tiada pertembungan cuti"}[lang])
    return " · ".join(bits)


def alternatives_for(cal, peaks, country, a: date, b: date, lang: str, n: int, base_leave: int,
                     muslim: bool = False, family: bool = False):
    days = (b - a).days + 1
    frm, to = a - timedelta(days=45), b + timedelta(days=45)
    if cal.coverage:
        frm, to = max(frm, cal.coverage[0]), min(to, cal.coverage[1])
    cands = find_windows(cal, peaks, country, frm, to, base_leave + 2, days, 40, lang, muslim=muslim, family=family)
    cands = [w for w in cands if not (d(w["start"]) <= b and a <= d(w["end"]))]
    cands.sort(key=lambda w: (w["price_score"] + w["muslim_conflict"] * 2 + w["school_days_missed"],
                              w["leave_needed"], abs((d(w["start"]) - a).days)))
    return cands[:n]


def to_trip_block(res: dict, alts: list, lang: str) -> dict:
    """Convert analyse() output into trip.json's holiday_analysis schema."""
    out = {
        "state": res["state"],
        "summary": summary_line(res, lang),
        "price_impact": res["price_impact"],
        "leave_needed": res["leave_needed"],
        "leave_dates": res["leave_dates"],
        "weekend": res["weekend"],
        "reasons": res["reasons"] + res["warnings"],
        "my_holidays": [{"date": h["date"], "weekday": h["weekday"], "name": h["name"]} for h in res["public_holidays"]],
        "school_holidays": res["school_holidays"],
        "destination_events": [{k: e[k] for k in ("start", "end", "name", "level")} for e in res["destination_events"]],
        "recommendation": "",
        "alternatives": [{"start": w["start"], "end": w["end"], "leave_needed": w["leave_needed"],
                          "price_impact": w["price_impact"], "note": alt_note(w, lang)} for w in alts],
    }
    if res.get("school_days_missed"):
        out["school_days_missed"] = res["school_days_missed"]
    return out


def leave_hacks(hdata, peaks, states: list[str], year: int, max_leave: int, lang: str):
    """Every 'maximal' break in a year that bridges a public holiday, for 1..max_leave leave days.

    Kept when it gives at least 3 more days off than the leave spent (i.e. a holiday is doing work)."""
    out = {}
    frm, to = date(year, 1, 1), date(year, 12, 31)
    for st in states:
        cal = StateCalendar(hdata, st)
        rows = []
        for s0 in daterange(frm, to):
            if cal.is_off(s0 - timedelta(days=1)):
                continue  # not maximal on the left
            for n in range(3, 17):
                e0 = s0 + timedelta(days=n - 1)
                if e0 > to + timedelta(days=10):
                    break
                need = sum(1 for x in daterange(s0, e0) if not cal.is_off(x))
                if need > max_leave:
                    break
                if cal.is_off(e0 + timedelta(days=1)) or n < need + 3:
                    continue
                if not any(x in cal.holidays for x in daterange(s0, e0)):
                    continue
                w = analyse(cal, peaks, None, s0, e0, lang)
                w["efficiency"] = round(n / max(need, 1), 2)
                rows.append(w)
        # Worth it: at least 1 leave day and >= 2.5 days off per leave day
        rows = [w for w in rows if w["leave_needed"] >= 1 and w["efficiency"] >= 2.5]
        # Same holiday cluster: keep the longest break per leave count ...
        best = {}
        for w in rows:
            key = (tuple(h["date"] for h in w["public_holidays"]), w["leave_needed"])
            if key not in best or w["total_days"] > best[key]["total_days"]:
                best[key] = w
        # ... and drop options beaten by spending less leave for as many days
        kept = [w for w in best.values()
                if not any(o is not w and o["public_holidays"] == w["public_holidays"]
                           and o["leave_needed"] < w["leave_needed"] and o["total_days"] >= w["total_days"]
                           for o in best.values())]
        out[st] = sorted(kept, key=lambda w: (w["start"], w["leave_needed"]))
    return out


def hacks_markdown(result: dict, hdata: dict, year: int, lang: str) -> str:
    from common import IMPACT_LABELS
    head = {"zh": f"# {year} 请假攻略（按州）\n\n用最少年假换最长连假。由 `holidays.py hacks` 自动生成；回教节日属预测，以宪报为准。\n",
            "en": f"# {year} leave hacks by state\n\nLongest breaks for the fewest annual-leave days. Generated by `holidays.py hacks`; Islamic dates are provisional.\n",
            "ms": f"# Tip cuti {year} mengikut negeri\n\nCuti panjang dengan cuti tahunan paling sedikit. Dijana oleh `holidays.py hacks`.\n"}[lang]
    cols = {"zh": "| 日期 | 放几天 | 请几天假 | 性价比 | 学校假期? | 包含的假期 |\n|---|---|---|---|---|---|",
            "en": "| Dates | Days off | Leave | Ratio | School hols? | Holidays inside |\n|---|---|---|---|---|---|",
            "ms": "| Tarikh | Hari cuti | Cuti diambil | Nisbah | Cuti sekolah? | Cuti umum |\n|---|---|---|---|---|---|"}[lang]
    lines = [head]
    for st, rows in result.items():
        info = hdata["states"][st]
        lines.append(f"\n## {pick(info, lang)} ({st}) — weekend {'-'.join(info['weekend'])}\n")
        lines.append(cols)
        for w in rows:
            hol = "、".join(dict.fromkeys(h["name"] for h in w["public_holidays"])) if lang == "zh" else \
                ", ".join(dict.fromkeys(h["name"] for h in w["public_holidays"]))
            school = "✅" if w["school_holidays"] else "—"
            lines.append(f"| {w['start']} → {w['end']} | {w['total_days']} | {w['leave_needed']} | "
                         f"{w['efficiency']}x | {school} | {hol} |")
    return "\n".join(lines) + "\n"


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
        sp.add_argument("--muslim", action="store_true", help="Flag Ramadan days and Hari Raya day 1 abroad")
        sp.add_argument("--family", action="store_true", help="Children in school: count school days missed")

    c = sub.add_parser("check")
    common_args(c)
    c.add_argument("--start", required=True)
    c.add_argument("--end", required=True)
    c.add_argument("--trip-json", action="store_true",
                   help="Print a ready-to-paste holiday_analysis block for trip.json")
    c.add_argument("--alternatives", type=int, default=3, help="With --trip-json: how many alternative windows")

    w = sub.add_parser("windows")
    common_args(w)
    w.add_argument("--from", dest="frm", default=None)
    w.add_argument("--to", default=None)
    w.add_argument("--leave", type=int, default=None, help="Max annual-leave days you can take")
    w.add_argument("--days", type=int, default=None, help="Exact trip length in days")
    w.add_argument("--min-days", type=int, default=3)
    w.add_argument("--max-days", type=int, default=16)
    w.add_argument("--top", type=int, default=8)
    w.add_argument("--allow-overlap", action="store_true", help="Show overlapping variants (different start days)")

    hk = sub.add_parser("hacks", help="Best leave-bridging windows for a whole year")
    hk.add_argument("--year", type=int, required=True)
    hk.add_argument("--state", default="ALL", help="State code/name, comma-separated list, or ALL")
    hk.add_argument("--max-leave", type=int, default=4)
    hk.add_argument("--lang", default="zh", choices=["zh", "en", "ms"])
    hk.add_argument("--json", action="store_true")
    hk.add_argument("--out", help="Write Markdown to this file")

    li = sub.add_parser("list")
    li.add_argument("--state", required=True)
    li.add_argument("--year", type=int, required=True)
    li.add_argument("--lang", default="zh", choices=["zh", "en", "ms"])
    li.add_argument("--json", action="store_true")

    args = p.parse_args(argv)
    hdata, peaks = load_data()
    if args.cmd == "hacks":
        states = list(hdata["states"]) if args.state.upper() == "ALL" else \
            [resolve_state(x, hdata["states"]) for x in args.state.split(",")]
        res = leave_hacks(hdata, peaks, states, args.year, args.max_leave, args.lang)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return
        md = hacks_markdown(res, hdata, args.year, args.lang)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"Saved {args.out}")
        else:
            print(md)
        return
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
        res = analyse(cal, peaks, country, a, b, args.lang, muslim=args.muslim, family=args.family)
        if args.trip_json:
            alts = alternatives_for(cal, peaks, country, a, b, args.lang, args.alternatives,
                                    res["leave_needed"], args.muslim, args.family) if args.alternatives else []
            print(json.dumps({"holiday_analysis": to_trip_block(res, alts, args.lang)}, ensure_ascii=False, indent=2))
        elif args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print_analysis(res, args.lang)
    elif args.cmd == "windows":
        if args.leave is None and args.days is None:
            sys.exit("Give --leave N (leave budget) and/or --days N (exact trip length).")
        frm = d(args.frm) if args.frm else max(date.today(), cal.coverage[0])
        to = d(args.to) if args.to else cal.coverage[1]
        res = find_windows(cal, peaks, country, frm, to, args.leave, args.days, args.top, args.lang,
                           args.min_days, args.max_days, args.muslim, args.family, args.allow_overlap)
        if len(res) < args.top:
            note = f"Only {len(res)} window(s) found"
            if args.days:
                floor = find_windows(cal, peaks, country, frm, to, None, args.days, 1, args.lang)
                if floor:
                    note += f"; a {args.days}-day trip in this range needs at least {floor[0]['leave_needed']} leave day(s)"
            if not args.allow_overlap:
                note += ". Overlapping variants are hidden; add --allow-overlap to see them"
            print(note + ".", file=sys.stderr)
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
