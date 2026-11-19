"""Shared helpers: paths, i18n labels, trip.json loading/validation, formatting."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"

LANGS = ("zh", "en", "ms")

# ---------------------------------------------------------------------------
# UI labels used by the Excel / PPT generators.
# ---------------------------------------------------------------------------
LABELS = {
    "overview": {"zh": "总览", "en": "Overview", "ms": "Ringkasan"},
    "itinerary": {"zh": "每日行程", "en": "Itinerary", "ms": "Jadual Harian"},
    "flights": {"zh": "机票对比", "en": "Flights", "ms": "Perbandingan Penerbangan"},
    "food": {"zh": "美食推荐", "en": "Food", "ms": "Makanan"},
    "shopping": {"zh": "购物·大马有没有", "en": "Shopping vs Malaysia", "ms": "Beli-belah vs Malaysia"},
    "budget": {"zh": "预算 (RM)", "en": "Budget (RM)", "ms": "Bajet (RM)"},
    "holidays": {"zh": "假期与时机", "en": "Holidays & Timing", "ms": "Cuti & Masa"},
    "checklist": {"zh": "出发清单", "en": "Checklist", "ms": "Senarai Semak"},
    "tips": {"zh": "小贴士", "en": "Tips", "ms": "Tips"},
    "sources": {"zh": "资料来源", "en": "Sources", "ms": "Sumber"},
    "destination": {"zh": "目的地", "en": "Destination", "ms": "Destinasi"},
    "dates": {"zh": "日期", "en": "Dates", "ms": "Tarikh"},
    "days": {"zh": "天数", "en": "Days", "ms": "Hari"},
    "travelers": {"zh": "人数", "en": "Travellers", "ms": "Pelancong"},
    "adults": {"zh": "大人", "en": "adults", "ms": "dewasa"},
    "children": {"zh": "小孩", "en": "children", "ms": "kanak-kanak"},
    "seniors": {"zh": "长者", "en": "seniors", "ms": "warga emas"},
    "home_state": {"zh": "居住州属", "en": "Home state", "ms": "Negeri"},
    "departure": {"zh": "出发机场", "en": "Departing from", "ms": "Berlepas dari"},
    "fx_rate": {"zh": "汇率（1 单位 = RM）", "en": "FX rate (1 unit = RM)", "ms": "Kadar tukaran (1 unit = RM)"},
    "fx_date": {"zh": "汇率日期", "en": "Rate date", "ms": "Tarikh kadar"},
    "fx_hint": {"zh": "改这个汇率，所有 RM 金额会自动重算", "en": "Edit this rate and every RM amount recalculates", "ms": "Ubah kadar ini dan semua jumlah RM dikira semula"},
    "priority": {"zh": "喜好排序", "en": "Your priorities", "ms": "Keutamaan anda"},
    "diet": {"zh": "饮食", "en": "Diet", "ms": "Pemakanan"},
    "pace": {"zh": "节奏", "en": "Pace", "ms": "Rentak"},
    "total_pp": {"zh": "每人预算", "en": "Budget per person", "ms": "Bajet seorang"},
    "total_group": {"zh": "全团预算", "en": "Group total", "ms": "Jumlah kumpulan"},
    "generated": {"zh": "生成日期", "en": "Generated", "ms": "Dijana"},
    "disclaimer": {
        "zh": "价格、营业时间、签证规定都会变，出发前请再到官网确认。标“估算”的数字不是实时报价。",
        "en": "Prices, opening hours and entry rules change. Re-check official sites before you go. Figures marked 'estimate' are not live quotes.",
        "ms": "Harga, waktu operasi dan syarat masuk boleh berubah. Semak laman rasmi sebelum bertolak. Angka 'anggaran' bukan harga semasa.",
    },
    # column headers
    "day": {"zh": "天", "en": "Day", "ms": "Hari"},
    "date": {"zh": "日期", "en": "Date", "ms": "Tarikh"},
    "weekday": {"zh": "星期", "en": "Weekday", "ms": "Hari"},
    "city": {"zh": "城市", "en": "City", "ms": "Bandar"},
    "time": {"zh": "时间", "en": "Time", "ms": "Masa"},
    "place": {"zh": "地点 / 活动", "en": "Place / activity", "ms": "Tempat / aktiviti"},
    "category": {"zh": "类型", "en": "Type", "ms": "Jenis"},
    "open_hours": {"zh": "营业时间", "en": "Opening hours", "ms": "Waktu buka"},
    "closed": {"zh": "休息日", "en": "Closed on", "ms": "Tutup"},
    "open_check": {"zh": "当天营业?", "en": "Open that day?", "ms": "Buka hari itu?"},
    "cost_local": {"zh": "费用(当地币)", "en": "Cost (local)", "ms": "Kos (tempatan)"},
    "cost_myr": {"zh": "费用(RM)", "en": "Cost (RM)", "ms": "Kos (RM)"},
    "notes": {"zh": "备注", "en": "Notes", "ms": "Catatan"},
    "map": {"zh": "地图", "en": "Map", "ms": "Peta"},
    "airline": {"zh": "航空公司", "en": "Airline", "ms": "Syarikat penerbangan"},
    "type": {"zh": "类型", "en": "Type", "ms": "Jenis"},
    "route": {"zh": "航线", "en": "Route", "ms": "Laluan"},
    "schedule": {"zh": "去 / 回 时间", "en": "Out / back times", "ms": "Masa pergi / balik"},
    "duration": {"zh": "飞行时间", "en": "Flight time", "ms": "Tempoh"},
    "fare": {"zh": "票价", "en": "Fare", "ms": "Tambang"},
    "baggage": {"zh": "行李额", "en": "Baggage", "ms": "Bagasi"},
    "addons": {"zh": "加购", "en": "Add-ons", "ms": "Tambahan"},
    "true_total": {"zh": "真实总价 / 人", "en": "True total / pax", "ms": "Jumlah sebenar / orang"},
    "verdict": {"zh": "结论", "en": "Verdict", "ms": "Keputusan"},
    "name": {"zh": "名称", "en": "Name", "ms": "Nama"},
    "local_name": {"zh": "当地名", "en": "Local name", "ms": "Nama tempatan"},
    "where": {"zh": "推荐去哪吃", "en": "Where", "ms": "Di mana"},
    "price": {"zh": "价位", "en": "Price", "ms": "Harga"},
    "halal": {"zh": "清真/猪肉", "en": "Halal / pork", "ms": "Halal / babi"},
    "in_malaysia": {"zh": "大马有吗", "en": "In Malaysia?", "ms": "Ada di Malaysia?"},
    "worth_it": {"zh": "值不值得", "en": "Worth it?", "ms": "Berbaloi?"},
    "price_diff": {"zh": "价差 vs 大马", "en": "Price vs Malaysia", "ms": "Harga vs Malaysia"},
    "item": {"zh": "项目", "en": "Item", "ms": "Item"},
    "amount": {"zh": "金额", "en": "Amount", "ms": "Jumlah"},
    "currency": {"zh": "币种", "en": "Currency", "ms": "Mata wang"},
    "qty": {"zh": "数量", "en": "Qty", "ms": "Kuantiti"},
    "per": {"zh": "按", "en": "Per", "ms": "Per"},
    "subtotal_myr": {"zh": "小计 RM", "en": "Subtotal RM", "ms": "Subjumlah RM"},
    "total": {"zh": "合计", "en": "Total", "ms": "Jumlah"},
    "done": {"zh": "完成", "en": "Done", "ms": "Siap"},
    "summary": {"zh": "分析结论", "en": "Summary", "ms": "Ringkasan"},
    "my_holidays": {"zh": "大马公共假期（你的州）", "en": "Malaysian public holidays (your state)", "ms": "Cuti umum Malaysia (negeri anda)"},
    "school_holidays": {"zh": "大马学校假期", "en": "Malaysian school holidays", "ms": "Cuti sekolah"},
    "dest_events": {"zh": "当地节日 / 旺季", "en": "Destination events / peak", "ms": "Musim puncak destinasi"},
    "price_impact": {"zh": "机票价格压力", "en": "Fare pressure", "ms": "Tekanan harga tiket"},
    "leave_needed": {"zh": "需要请假", "en": "Annual leave needed", "ms": "Cuti tahunan diperlukan"},
    "recommendation": {"zh": "建议", "en": "Recommendation", "ms": "Cadangan"},
    "alternatives": {"zh": "替代日期", "en": "Alternative dates", "ms": "Tarikh alternatif"},
    "per_person": {"zh": "每人", "en": "per person", "ms": "seorang"},
    "per_group": {"zh": "全团", "en": "group", "ms": "kumpulan"},
    "recommended": {"zh": "推荐", "en": "Recommended", "ms": "Disyorkan"},
    "estimate": {"zh": "估算", "en": "estimate", "ms": "anggaran"},
    "day_n": {"zh": "第 {n} 天", "en": "Day {n}", "ms": "Hari {n}"},
    "contents": {"zh": "目录", "en": "Contents", "ms": "Kandungan"},
    "trip_at_glance": {"zh": "行程一览", "en": "Trip at a glance", "ms": "Sekilas perjalanan"},
    "checked_on": {"zh": "查询日期", "en": "Checked", "ms": "Disemak"},
    "per_adult": {"zh": "每大人", "en": "per adult", "ms": "setiap dewasa"},
    "per_child": {"zh": "每小孩", "en": "per child", "ms": "setiap kanak-kanak"},
    "budget_target": {"zh": "目标预算", "en": "Target", "ms": "Sasaran"},
    "over_budget": {"zh": "超出预算", "en": "over budget", "ms": "melebihi bajet"},
    "within_budget": {"zh": "在预算内", "en": "within budget", "ms": "dalam bajet"},
    "more_in_excel": {"zh": "还有 {n} 项，见 Excel", "en": "+{n} more, see the Excel file", "ms": "+{n} lagi, lihat Excel"},
    "school_days_missed": {"zh": "小孩要请的上学日", "en": "School days missed", "ms": "Hari sekolah terlepas"},
    "halal_source": {"zh": "清真来源", "en": "Halal source", "ms": "Sumber halal"},
    "calendar": {"zh": "出行日历", "en": "Trip calendar", "ms": "Kalendar perjalanan"},
    "cal_trip": {"zh": "出行日", "en": "Trip day", "ms": "Hari perjalanan"},
    "cal_leave": {"zh": "要请假", "en": "Take leave", "ms": "Ambil cuti"},
    "cal_holiday": {"zh": "公共假期", "en": "Public holiday", "ms": "Cuti umum"},
    "cal_weekend": {"zh": "周末", "en": "Weekend", "ms": "Hujung minggu"},
    "cal_school": {"zh": "学校假期", "en": "School holiday", "ms": "Cuti sekolah"},
    "day_cost": {"zh": "当天预计花费", "en": "Estimated spend today", "ms": "Anggaran belanja hari ini"},
    "leave_days_unit": {"zh": "天", "en": "day(s)", "ms": "hari"},
}

# Labels for itinerary items (the ranking uses CATEGORY_LABELS below)
ITEM_CATEGORY_LABELS = {
    "attraction": {"zh": "景点", "en": "Sightseeing", "ms": "Tarikan"},
    "shopping": {"zh": "购物", "en": "Shopping", "ms": "Beli-belah"},
    "food": {"zh": "美食", "en": "Food", "ms": "Makan"},
    "transport": {"zh": "交通", "en": "Transport", "ms": "Pengangkutan"},
    "hotel": {"zh": "住宿", "en": "Hotel", "ms": "Penginapan"},
    "flight": {"zh": "航班", "en": "Flight", "ms": "Penerbangan"},
    "prayer": {"zh": "祷告", "en": "Prayer", "ms": "Solat"},
    "other": {"zh": "其他", "en": "Other", "ms": "Lain-lain"},
}

CATEGORY_LABELS = {
    "attraction": {"zh": "景点", "en": "Sightseeing", "ms": "Tarikan"},
    "shopping": {"zh": "购物+chill", "en": "Shopping + chill", "ms": "Beli-belah + santai"},
    "food": {"zh": "美食hunt", "en": "Food hunt", "ms": "Buru makanan"},
    "transport": {"zh": "交通", "en": "Transport", "ms": "Pengangkutan"},
    "hotel": {"zh": "住宿", "en": "Hotel", "ms": "Penginapan"},
    "flight": {"zh": "航班", "en": "Flight", "ms": "Penerbangan"},
    "other": {"zh": "其他", "en": "Other", "ms": "Lain-lain"},
}

BUDGET_CAT_LABELS = {
    "flight": {"zh": "机票", "en": "Flights", "ms": "Tiket penerbangan"},
    "hotel": {"zh": "住宿", "en": "Accommodation", "ms": "Penginapan"},
    "transport": {"zh": "当地交通", "en": "Local transport", "ms": "Pengangkutan tempatan"},
    "attraction": {"zh": "门票 / 活动", "en": "Tickets / activities", "ms": "Tiket / aktiviti"},
    "food": {"zh": "餐饮", "en": "Food & drinks", "ms": "Makan & minum"},
    "shopping": {"zh": "购物", "en": "Shopping", "ms": "Beli-belah"},
    "other": {"zh": "其他", "en": "Others", "ms": "Lain-lain"},
}

DIET_LABELS = {
    "halal": {"zh": "只吃清真 (Halal)", "en": "Halal only", "ms": "Halal sahaja"},
    "muslim-friendly": {"zh": "穆斯林友好即可", "en": "Muslim-friendly OK", "ms": "Mesra Muslim"},
    "no-pork": {"zh": "不吃猪肉", "en": "No pork", "ms": "Tiada babi"},
    "vegetarian": {"zh": "素食", "en": "Vegetarian", "ms": "Vegetarian"},
    "none": {"zh": "没有限制", "en": "No restriction", "ms": "Tiada sekatan"},
}

HALAL_LABELS = {
    "halal": {"zh": "✅ 清真认证", "en": "✅ Halal certified", "ms": "✅ Halal"},
    "muslim-friendly": {"zh": "🟢 穆斯林友好", "en": "🟢 Muslim-friendly", "ms": "🟢 Mesra Muslim"},
    "no-pork": {"zh": "🟡 无猪肉(非清真)", "en": "🟡 Pork-free (not halal)", "ms": "🟡 Tiada babi (bukan halal)"},
    "contains-pork": {"zh": "🔴 含猪肉", "en": "🔴 Contains pork", "ms": "🔴 Ada babi"},
    "vegetarian": {"zh": "🥬 素食", "en": "🥬 Vegetarian", "ms": "🥬 Vegetarian"},
    "unknown": {"zh": "❔ 需确认", "en": "❔ Check", "ms": "❔ Semak"},
}

IN_MY_LABELS = {
    "yes": {"zh": "有", "en": "Yes", "ms": "Ada"},
    "no": {"zh": "没有", "en": "No", "ms": "Tiada"},
    "partial": {"zh": "有，但款式/菜单不同", "en": "Yes, but different range", "ms": "Ada, tapi berbeza"},
    "online": {"zh": "只有网购", "en": "Online only", "ms": "Dalam talian sahaja"},
    "unknown": {"zh": "需确认", "en": "Check", "ms": "Semak"},
}

WORTH_LABELS = {
    "must": {"zh": "必去", "en": "Must", "ms": "Wajib"},
    "worth": {"zh": "值得", "en": "Worth it", "ms": "Berbaloi"},
    "maybe": {"zh": "有空才去", "en": "If time allows", "ms": "Jika ada masa"},
    "skip": {"zh": "大马买就好", "en": "Skip, buy in MY", "ms": "Beli di Malaysia sahaja"},
}

FOOD_WORTH_LABELS = {**WORTH_LABELS,
                     "skip": {"zh": "大马吃就好", "en": "Skip, have it in MY", "ms": "Makan di Malaysia sahaja"}}

IMPACT_LABELS = {
    "low": {"zh": "低 🟢", "en": "Low 🟢", "ms": "Rendah 🟢"},
    "medium": {"zh": "中 🟡", "en": "Medium 🟡", "ms": "Sederhana 🟡"},
    "high": {"zh": "高 🟠", "en": "High 🟠", "ms": "Tinggi 🟠"},
    "very_high": {"zh": "非常高 🔴", "en": "Very high 🔴", "ms": "Sangat tinggi 🔴"},
}

PACE_LABELS = {
    "relaxed": {"zh": "轻松", "en": "Relaxed", "ms": "Santai"},
    "normal": {"zh": "适中", "en": "Balanced", "ms": "Sederhana"},
    "packed": {"zh": "紧凑", "en": "Packed", "ms": "Padat"},
}

WEEKDAYS = {
    "zh": ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"],
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "ms": ["Isnin", "Selasa", "Rabu", "Khamis", "Jumaat", "Sabtu", "Ahad"],
}


WEEKDAYS_SHORT = {
    "zh": ["一", "二", "三", "四", "五", "六", "日"],
    "en": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
    "ms": ["Is", "Se", "Ra", "Kh", "Ju", "Sa", "Ah"],
}


def calendar_model(trip: dict) -> list[dict]:
    """Months touched by the trip, each a list of weeks of day-dicts (None = padding).

    Day flags: trip, leave, holiday (name), weekend, school."""
    import calendar as _cal
    from datetime import date as _date, timedelta as _td
    meta = trip["meta"]
    ha = trip.get("holiday_analysis") or {}
    start, end = _date.fromisoformat(meta["start_date"]), _date.fromisoformat(meta["end_date"])
    leave = set(ha.get("leave_dates", []))
    hols = {h["date"]: h.get("name", "") for h in ha.get("my_holidays", [])}
    # With the state code (holidays.py --trip-json adds it) also mark holidays outside the trip window
    if ha.get("state"):
        try:
            import holidays as _hol  # lazy: holidays.py imports this module
            hdata = load_json(DATA_DIR / "my_holidays.json")
            cal_ = _hol.StateCalendar(hdata, ha["state"])
            lang = meta.get("language", "en")
            for dd, hs in cal_.holidays.items():
                hols.setdefault(dd.isoformat(), hs[0].get(lang) or hs[0]["en"])
        except (ImportError, OSError, KeyError, ValueError):
            pass
    dows = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekend = {dows.index(x) for x in ha.get("weekend", ["Sat", "Sun"])}
    school = set()
    for sh in ha.get("school_holidays", []):
        a, b = _date.fromisoformat(sh["start"]), _date.fromisoformat(sh["end"])
        while a <= b:
            school.add(a.isoformat())
            a += _td(days=1)
    months, cur = [], _date(start.year, start.month, 1)
    while cur <= end and len(months) < 3:
        weeks = []
        for wk in _cal.Calendar(firstweekday=0).monthdatescalendar(cur.year, cur.month):
            row = []
            for dd in wk:
                if dd.month != cur.month:
                    row.append(None)
                    continue
                iso = dd.isoformat()
                row.append({"date": dd, "trip": start <= dd <= end, "leave": iso in leave,
                            "holiday": hols.get(iso), "weekend": dd.weekday() in weekend, "school": iso in school})
            weeks.append(row)
        months.append({"year": cur.year, "month": cur.month, "weeks": weeks})
        cur = _date(cur.year + (cur.month == 12), cur.month % 12 + 1, 1)
    return months


def L(key: str, lang: str, table: dict | None = None, **fmt) -> str:
    """Look up a label; fall back to English, then the key itself."""
    table = table or LABELS
    entry = table.get(key)
    if entry is None:
        return key
    text = entry.get(lang) or entry.get("en") or key
    return text.format(**fmt) if fmt else text


def pick(obj, lang: str, default: str = "") -> str:
    """Return localized text from either a plain string or a {lang: text} dict."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(lang) or obj.get("en") or next(iter(obj.values()), default)
    return str(obj)


def load_json(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


REQUIRED_META = ("language", "title", "destination_country", "start_date", "end_date")


def load_trip(path: str | Path) -> dict:
    """Load trip.json and fail loudly with actionable messages."""
    trip = load_json(path)
    errors = []
    meta = trip.get("meta")
    if not isinstance(meta, dict):
        errors.append("missing 'meta' object")
        meta = {}
    for key in REQUIRED_META:
        if not meta.get(key):
            errors.append(f"meta.{key} is required")
    if meta.get("language") and meta["language"] not in LANGS:
        errors.append(f"meta.language must be one of {LANGS}")
    fx = trip.get("fx") or {}
    if not fx.get("currency"):
        errors.append("fx.currency is required (e.g. 'JPY')")
    if not isinstance(fx.get("rate_myr_per_unit"), (int, float)):
        errors.append("fx.rate_myr_per_unit must be a number (RM for 1 unit of local currency)")
    for d in trip.get("itinerary", []):
        if "day" not in d or "items" not in d:
            errors.append(f"itinerary entry needs 'day' and 'items': {d.get('day')}")
    for b in trip.get("budget", []):
        if b.get("currency", "local") not in ("local", "MYR"):
            errors.append(f"budget.currency must be 'local' or 'MYR': {b.get('item')}")
        if b.get("per", "person") not in PER_VALUES:
            errors.append(f"budget.per must be one of {PER_VALUES}: {b.get('item')}")
    if errors:
        sys.exit("trip.json is invalid:\n  - " + "\n  - ".join(errors))
    normalize_trip(trip)
    return trip


PER_VALUES = ("person", "adult", "child", "group")
KNOWN_KEYS = {"meta", "fx", "holiday_analysis", "flights_note", "flights", "itinerary", "food", "shopping",
              "budget", "checklist", "tips", "sources"}


def normalize_trip(trip: dict) -> None:
    """Accept common aliases so nothing silently disappears from the outputs."""
    ha = trip.get("holiday_analysis")
    if isinstance(ha, dict):
        if "public_holidays" in ha and "my_holidays" not in ha:
            ha["my_holidays"] = ha.pop("public_holidays")
            print("note: holiday_analysis.public_holidays renamed to my_holidays", file=sys.stderr)
        if "warnings" in ha:
            ha["reasons"] = list(ha.get("reasons", [])) + [w for w in ha.pop("warnings") if w not in ha.get("reasons", [])]
    prefs = trip["meta"].setdefault("preferences", {})
    if prefs.get("pace") == "balanced":
        prefs["pace"] = "normal"
    unknown = set(trip) - KNOWN_KEYS
    if unknown:
        print(f"note: unknown top-level keys ignored: {sorted(unknown)}", file=sys.stderr)


def travelers_count(meta: dict) -> int:
    t = meta.get("travelers") or {}
    n = int(t.get("adults", 0)) + int(t.get("children", 0)) + int(t.get("seniors", 0))
    return max(n, 1)


def per_multiplier(per: str, meta: dict) -> int:
    """How many people a budget line applies to. adult = adults + seniors."""
    t = meta.get("travelers") or {}
    if per == "group":
        return 1
    if per == "adult":
        return int(t.get("adults", 0)) + int(t.get("seniors", 0))
    if per == "child":
        return int(t.get("children", 0))
    return travelers_count(meta)


SINGULAR_EN = {"adults": "adult", "children": "child", "seniors": "senior"}


def travelers_text(meta: dict, lang: str) -> str:
    t = meta.get("travelers") or {}
    parts = []
    for k in ("adults", "children", "seniors"):
        n = t.get(k)
        if not n:
            continue
        word = SINGULAR_EN[k] if (lang == "en" and int(n) == 1) else L(k, lang)
        text = f"{n} {word}"
        if k == "children" and t.get("children_ages"):
            text += f" ({', '.join(str(a) for a in t['children_ages'])})"
        parts.append(text)
    return ", ".join(parts) or "1"


def fmt_rate(rate: float, cur: str) -> str:
    """'1 KRW = RM 0.00306 · RM 1 = 326.80 KRW' with sensible precision for any currency."""
    from math import floor, log10
    digits = max(2, 3 - int(floor(log10(abs(rate)))) - 1) if rate else 2
    inv = 1 / rate if rate else 0
    inv_s = f"{inv:,.0f}" if inv >= 1000 else f"{inv:,.2f}"
    return f"1 {cur} = RM {rate:.{digits}f}  ·  RM 1 = {inv_s} {cur}"


NO_HOURS_CATEGORIES = ("transport", "hotel", "flight")


def balanced_chunks(items: list, max_per: int) -> list[list]:
    """Split into the fewest pages of <= max_per rows, spread evenly (no 1-row orphan page)."""
    if not items:
        return []
    pages = -(-len(items) // max_per)
    size = -(-len(items) // pages)
    return [items[i:i + size] for i in range(0, len(items), size)]


def fmt_money(value, currency: str = "RM", decimals: int | None = None) -> str:
    if value is None or value == "":
        return ""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    if decimals is None:
        decimals = 0 if abs(v) >= 100 or v == int(v) else 2
    s = f"{v:,.{decimals}f}"
    return f"{currency} {s}" if currency else s
