#!/usr/bin/env python3
"""Build the PowerPoint travel guide from trip.json.

  python make_ppt.py trip.json "Osaka Trip.pptx"
"""
from __future__ import annotations

import sys
from datetime import date

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

from common import (ITEM_CATEGORY_LABELS, fmt_rate, per_multiplier, WEEKDAYS_SHORT, calendar_model, BUDGET_CAT_LABELS, CATEGORY_LABELS, NO_HOURS_CATEGORIES, balanced_chunks, DIET_LABELS, HALAL_LABELS, IMPACT_LABELS, IN_MY_LABELS, PACE_LABELS,
                    WEEKDAYS, WORTH_LABELS, L, fmt_money, load_trip, travelers_count, travelers_text)

NAVY = RGBColor(0x14, 0x21, 0x3D)
NAVY2 = RGBColor(0x2B, 0x3A, 0x67)
GOLD = RGBColor(0xFC, 0xA3, 0x11)
CREAM = RGBColor(0xF7, 0xF5, 0xEF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x22, 0x22, 0x22)
MUTED = RGBColor(0x6B, 0x6B, 0x6B)
RED = RGBColor(0xC1, 0x12, 0x1F)
GREEN_BG = RGBColor(0xE6, 0xF4, 0xEA)
RED_BG = RGBColor(0xFD, 0xEC, 0xEA)
ROW_ALT = RGBColor(0xFA, 0xFA, 0xFA)
LATIN_FONT = "Arial"
EA_FONT = {"zh": "Microsoft YaHei", "en": "Arial", "ms": "Arial"}

W, H = Inches(13.333), Inches(7.5)
MARGIN = Inches(0.6)
ROWS_PER_SLIDE = 8


class Deck:
    def __init__(self, trip: dict):
        self.trip = trip
        self.meta = trip["meta"]
        self.lang = self.meta["language"]
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = W, H
        self.blank = self.prs.slide_layouts[6]
        self.page = 0

    # ---------- primitives ----------
    def font(self, run, size, bold=False, color=INK, italic=False):
        f = run.font
        f.size = Pt(size)
        f.bold = bold
        f.italic = italic
        f.color.rgb = color
        f.name = LATIN_FONT
        rpr = run._r.get_or_add_rPr()
        for tag in ("a:ea", "a:cs"):
            el = rpr.find(qn(tag))
            if el is None:
                el = rpr.makeelement(qn(tag), {})
                rpr.append(el)
            el.set("typeface", EA_FONT.get(self.lang, LATIN_FONT))

    def text(self, slide, x, y, w, h, text, size=14, bold=False, color=INK, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, italic=False):
        tb = slide.shapes.add_textbox(x, y, w, h)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = Inches(0.05)
        lines = text if isinstance(text, list) else [text]
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            r = p.add_run()
            r.text = str(line)
            self.font(r, size, bold, color, italic)
        return tb

    def rect(self, slide, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE):
        s = slide.shapes.add_shape(shape, x, y, w, h)
        s.fill.solid()
        s.fill.fore_color.rgb = fill
        s.line.fill.background()
        s.shadow.inherit = False
        return s

    def new_slide(self, title: str, subtitle: str = ""):
        s = self.prs.slides.add_slide(self.blank)
        self.page += 1
        bg = s.background.fill
        bg.solid()
        bg.fore_color.rgb = CREAM
        self.rect(s, 0, 0, W, Inches(0.12), NAVY)
        self.text(s, MARGIN, Inches(0.35), W - 2 * MARGIN, Inches(0.7), title, size=28, bold=True, color=NAVY)
        self.rect(s, MARGIN + Inches(0.05), Inches(1.05), Inches(1.0), Inches(0.07), GOLD)
        if subtitle:
            self.text(s, MARGIN, Inches(1.18), W - 2 * MARGIN, Inches(0.45), subtitle, size=13, color=MUTED)
        # footer
        self.text(s, MARGIN, H - Inches(0.45), Inches(9), Inches(0.3), self.meta["title"], size=9, color=MUTED)
        self.text(s, W - MARGIN - Inches(1), H - Inches(0.45), Inches(1), Inches(0.3), str(self.page), size=9,
                  color=MUTED, align=PP_ALIGN.RIGHT)
        return s

    def table(self, slide, headers, rows, widths_in, top=Inches(1.75), font=11, row_fills=None, height=None):
        total_w = sum(widths_in)
        scale = (W - 2 * MARGIN) / Inches(total_w)
        n_rows = len(rows) + 1
        height = height or Inches(0.42) * n_rows
        shape = slide.shapes.add_table(n_rows, len(headers), MARGIN, top, W - 2 * MARGIN, height)
        tbl = shape.table
        # disable banding from default style
        tbl_pr = shape._element.graphic.graphicData.tbl.tblPr
        tbl_pr.set("bandRow", "0")
        tbl_pr.set("firstRow", "0")
        for i, w in enumerate(widths_in):
            tbl.columns[i].width = Emu(int(Inches(w) * scale))
        for c, h in enumerate(headers):
            self._cell(tbl.cell(0, c), h, font, True, WHITE, NAVY2)
        for r, row in enumerate(rows, 1):
            fill = (row_fills[r - 1] if row_fills and row_fills[r - 1] is not None
                    else (ROW_ALT if r % 2 == 0 else WHITE))
            for c, v in enumerate(row):
                self._cell(tbl.cell(r, c), v, font, False, INK, fill)
        return tbl

    def _cell(self, cell, value, size, bold, color, fill):
        cell.fill.solid()
        cell.fill.fore_color.rgb = fill
        cell.margin_left = cell.margin_right = Inches(0.06)
        cell.margin_top = cell.margin_bottom = Inches(0.03)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = ""
        r = p.add_run()
        r.text = "" if value is None else str(value)
        self.font(r, size, bold, color)

    def card(self, slide, x, y, w, h, label, value, accent=GOLD, value_color=NAVY, value_size=26):
        self.rect(slide, x, y, w, h, WHITE, MSO_SHAPE.ROUNDED_RECTANGLE).adjustments[0] = 0.08
        self.rect(slide, x, y + Inches(0.15), Inches(0.08), h - Inches(0.3), accent)
        self.text(slide, x + Inches(0.25), y + Inches(0.15), w - Inches(0.35), Inches(0.4), label, size=12, color=MUTED)
        self.text(slide, x + Inches(0.25), y + Inches(0.5), w - Inches(0.35), h - Inches(0.6), value,
                  size=value_size, bold=True, color=value_color)

    # ---------- slides ----------
    def cover(self):
        s = self.prs.slides.add_slide(self.blank)
        self.page += 1
        bg = s.background.fill
        bg.solid()
        bg.fore_color.rgb = NAVY
        self.rect(s, 0, Inches(5.2), W, Inches(0.08), GOLD)
        m, lang = self.meta, self.lang
        start, end = date.fromisoformat(m["start_date"]), date.fromisoformat(m["end_date"])
        title_size = 44 if len(m["title"]) <= 16 else 36 if len(m["title"]) <= 26 else 30
        self.text(s, Inches(0.9), Inches(1.4), Inches(11.5), Inches(1.8), m["title"], size=title_size, bold=True,
                  color=WHITE, anchor=MSO_ANCHOR.BOTTOM)
        sub = (f"{start.isoformat()} ({WEEKDAYS[lang][start.weekday()]}) → {end.isoformat()} "
               f"({WEEKDAYS[lang][end.weekday()]})  ·  {travelers_text(m, lang)}")
        self.text(s, Inches(0.9), Inches(3.3), Inches(11.5), Inches(0.6), sub, size=20, color=GOLD)
        cities = " · ".join(m.get("cities", []))
        if cities:
            self.text(s, Inches(0.9), Inches(3.95), Inches(11.5), Inches(0.6), cities, size=18, color=WHITE)
        self.text(s, Inches(0.9), Inches(5.55), Inches(11.5), Inches(0.9), L("disclaimer", lang), size=11,
                  color=RGBColor(0xBB, 0xC3, 0xD6), italic=True)
        self.text(s, Inches(0.9), Inches(6.6), Inches(11.5), Inches(0.4),
                  f"🇲🇾 Malaysian Travel Planner · {L('generated', lang)} {m.get('generated_on', date.today().isoformat())}",
                  size=10, color=RGBColor(0x8A, 0x96, 0xB4))

    def glance(self):
        t, m, lang = self.trip, self.meta, self.lang
        s = self.new_slide(L("trip_at_glance", lang))
        start, end = date.fromisoformat(m["start_date"]), date.fromisoformat(m["end_date"])
        ha = t.get("holiday_analysis") or {}
        total_group = self.budget_total()
        pax = travelers_count(m)
        cw, ch, gap, y = Inches(2.85), Inches(1.45), Inches(0.2), Inches(1.6)
        cards = [
            (L("days", lang), f"{(end - start).days + 1}"),
            (L("leave_needed", lang), f"{ha.get('leave_needed', '-')} {L('leave_days_unit', lang)}"),
            (L("total_pp", lang), fmt_money(total_group / pax) if total_group else "-"),
            (L("price_impact", lang), L(ha.get("price_impact", "low"), lang, IMPACT_LABELS)),
        ]
        over = self.over_budget()
        for i, (lab, val) in enumerate(cards):
            self.card(s, MARGIN + i * (cw + gap), y, cw, ch, lab, val,
                      value_color=RED if (i == 2 and over) else NAVY, value_size=24,
                      accent=RED if (i == 2 and over) else GOLD)
        prefs = m.get("preferences", {})
        ranking = prefs.get("ranking", [])
        medals = ["🥇", "🥈", "🥉"]
        y2 = Inches(3.35)
        self.text(s, MARGIN, y2, Inches(5.8), Inches(0.4), L("priority", lang), size=16, bold=True, color=NAVY)
        lines = [f"{medals[i] if i < 3 else '•'} {L(k, lang, CATEGORY_LABELS)}" for i, k in enumerate(ranking)]
        lines += ["", f"{L('diet', lang)}: {L(prefs.get('diet', 'none'), lang, DIET_LABELS)}",
                  f"{L('pace', lang)}: {L(prefs.get('pace', 'normal'), lang, PACE_LABELS)}"]
        self.text(s, MARGIN, y2 + Inches(0.45), Inches(5.8), Inches(2.8), lines, size=15)
        fx = t["fx"]
        rate = float(fx["rate_myr_per_unit"])
        right = [
            f"💱 {fmt_rate(rate, fx['currency'])}",
            f"    ({fx.get('rate_date', '')}, {fx.get('source', '')})",
            "",
        ]
        rec = next((f for f in t.get("flights", []) if f.get("recommended")), None)
        if rec:
            right.append(f"✈️ {L('recommended', lang)}: {rec.get('airline')} — "
                         f"{fmt_money((rec.get('fare_myr') or 0) + (rec.get('addons_myr') or 0))} / pax")
        right += [f"🛫 {L('departure', lang)}: {m.get('departure_airport', '')}",
                  f"🏠 {L('home_state', lang)}: {m.get('home_state', '')}",
                  f"👥 {L('total_group', lang)}: {fmt_money(total_group)}"]
        self.text(s, Inches(6.9), y2, Inches(5.8), Inches(0.4), L("summary", lang), size=16, bold=True, color=NAVY)
        self.text(s, Inches(6.9), y2 + Inches(0.45), Inches(5.8), Inches(2.8), right, size=14)

    def holidays(self):
        ha = self.trip.get("holiday_analysis")
        if not ha:
            return
        lang = self.lang
        s = self.new_slide(L("holidays", lang), ha.get("summary", ""))
        left_w = Inches(5.2)
        self.card(s, MARGIN, Inches(1.8), left_w, Inches(1.2), L("price_impact", lang),
                  L(ha.get("price_impact", "low"), lang, IMPACT_LABELS), accent=RED, value_size=22)
        reasons = ["• " + r for r in ha.get("reasons", [])]
        rec = ha.get("recommendation", "")
        body = reasons + (["", f"👉 {rec}"] if rec else [])
        self.text(s, MARGIN, Inches(3.15), left_w, Inches(3.6), body, size=13)
        rows = []
        for h in ha.get("my_holidays", []):
            rows.append(["🇲🇾", f"{h.get('date')} {h.get('weekday', '')}", h.get("name", "")])
        for sh in ha.get("school_holidays", []):
            rows.append(["🏫", f"{sh.get('start')} → {sh.get('end')}", sh.get("name", "")])
        for e in ha.get("destination_events", []):
            rows.append(["📍", f"{e.get('start')} → {e.get('end')}", e.get("name", "")])
        alts = ha.get("alternatives", [])
        for a in alts[:3]:
            rows.append(["💡", f"{a.get('start')} → {a.get('end')}",
                         f"{L('alternatives', lang)}: {a.get('note', '')} ({L(a.get('price_impact', 'low'), lang, IMPACT_LABELS)})"])
        if len(rows) > 10:
            extra = len(rows) - 9
            rows = rows[:9] + [["…", "", L("more_in_excel", lang, n=extra)]]
        if rows:
            x0 = MARGIN + left_w + Inches(0.3)
            # table helper spans full width; build a narrower one manually
            shape = s.shapes.add_table(len(rows[:10]) + 1, 3, x0, Inches(1.8), W - MARGIN - x0,
                                       Inches(0.4) * (len(rows[:10]) + 1))
            tbl = shape.table
            tbl_pr = shape._element.graphic.graphicData.tbl.tblPr
            tbl_pr.set("bandRow", "0")
            tbl_pr.set("firstRow", "0")
            ws = [0.5, 2.3, 3.9]
            tot = sum(ws)
            for i, w in enumerate(ws):
                tbl.columns[i].width = Emu(int((W - MARGIN - x0) * w / tot))
            for c, h in enumerate(["", L("date", lang), L("name", lang)]):
                self._cell(tbl.cell(0, c), h, 11, True, WHITE, NAVY2)
            for r, row in enumerate(rows[:10], 1):
                fill = RED_BG if row[0] == "🏫" else GREEN_BG if row[0] == "💡" else (ROW_ALT if r % 2 == 0 else WHITE)
                for c, v in enumerate(row):
                    self._cell(tbl.cell(r, c), v, 11, False, INK, fill)

    def calendar(self):
        if not self.trip.get("holiday_analysis"):
            return
        lang = self.lang
        months = calendar_model(self.trip)
        if not months:
            return
        s = self.new_slide(L("calendar", lang))
        n = len(months)
        gap = Inches(0.4)
        cal_w = min(Inches(5.8), (W - 2 * MARGIN - gap * (n - 1)) / n)
        cell = int(cal_w / 7)
        blue = RGBColor(0x2F, 0x6F, 0xDE)
        hol_bg = RGBColor(0xFD, 0xE2, 0xE1)
        trip_bg = RGBColor(0xFF, 0xF1, 0xCC)
        pink = RGBColor(0xF4, 0x8F, 0xB1)
        for mi, m in enumerate(months):
            x0 = MARGIN + mi * (cal_w + gap)
            y0 = Inches(1.45)
            title = f"{m['year']} 年 {m['month']} 月" if lang == "zh" else f"{date(m['year'], m['month'], 1):%B %Y}"
            self.text(s, x0, y0, cal_w, Inches(0.4), title, size=16, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
            y = y0 + Inches(0.45)
            for i, wd in enumerate(WEEKDAYS_SHORT[lang]):
                self.text(s, x0 + i * cell, y, cell, Inches(0.3), wd, size=11, bold=True, color=MUTED,
                          align=PP_ALIGN.CENTER)
            y += Inches(0.32)
            row_h = Inches(0.62)
            for week in m["weeks"]:
                for i, dd in enumerate(week):
                    if dd is None:
                        continue
                    cx = x0 + i * cell
                    fill = WHITE
                    if dd["trip"]:
                        fill = blue if dd["leave"] else hol_bg if dd["holiday"] else trip_bg
                    box = self.rect(s, cx + Inches(0.03), y + Inches(0.03), cell - Inches(0.06), row_h - Inches(0.06),
                                    fill, MSO_SHAPE.ROUNDED_RECTANGLE)
                    box.adjustments[0] = 0.12
                    if dd["trip"]:
                        box.line.color.rgb = GOLD
                        box.line.width = Pt(2.25)
                    color = WHITE if (dd["trip"] and dd["leave"]) else RED if dd["holiday"] else \
                        MUTED if dd["weekend"] else INK
                    self.text(s, cx, y + Inches(0.06), cell, Inches(0.35), str(dd["date"].day), size=14,
                              bold=dd["trip"] or bool(dd["holiday"]), color=color, align=PP_ALIGN.CENTER)
                    if dd["school"]:
                        self.rect(s, cx + Inches(0.12), y + row_h - Inches(0.16), cell - Inches(0.24), Inches(0.06), pink)
                y += row_h
        ha = self.trip["holiday_analysis"]
        if n == 1:
            px = MARGIN + cal_w + Inches(0.6)
            pw = W - MARGIN - px
            self.rect(s, px, Inches(1.5), pw, Inches(4.6), WHITE)
            self.rect(s, px, Inches(1.5), Inches(0.08), Inches(4.6), GOLD)
            lines = []
            for h in ha.get("my_holidays", []):
                lines.append(f"🇲🇾 {h['date'][5:]} {h.get('weekday', '')}  {h.get('name', '')}")
            for sh in ha.get("school_holidays", []):
                lines.append(f"🏫 {sh['start'][5:]} → {sh['end'][5:]}  {sh.get('name', '')}")
            for e in ha.get("destination_events", []):
                lines.append(f"📍 {e['start'][5:]} → {e['end'][5:]}  {e.get('name', '')}")
            if ha.get("leave_dates"):
                lines.append(f"🗓️ {L('leave_needed', lang)}: " + ", ".join(x[5:] for x in ha["leave_dates"]))
            for a in ha.get("alternatives", [])[:3]:
                lines.append(f"💡 {a['start'][5:]} → {a['end'][5:]}  {a.get('note', '')}")
            self.text(s, px + Inches(0.3), Inches(1.65), pw - Inches(0.45), Inches(0.4), L("summary", lang), size=15,
                      bold=True, color=NAVY)
            self.text(s, px + Inches(0.3), Inches(2.1), pw - Inches(0.45), Inches(3.9), lines or ["—"], size=12)
        # legend
        ly = H - Inches(1.05)
        items = [(trip_bg, L("cal_trip", lang)), (blue, L("cal_leave", lang)), (hol_bg, L("cal_holiday", lang)),
                 (WHITE, L("cal_weekend", lang)), (pink, L("cal_school", lang))]
        lx = MARGIN
        for col, lab in items:
            sw = self.rect(s, lx, ly + Inches(0.08), Inches(0.3), Inches(0.22) if col != pink else Inches(0.08), col)
            if col in (trip_bg, WHITE):
                sw.line.color.rgb = GOLD if col == trip_bg else MUTED
            self.text(s, lx + Inches(0.38), ly, Inches(1.9), Inches(0.4), lab, size=12, color=INK)
            lx += Inches(2.3)
        if ha.get("leave_dates") and n > 1:
            self.text(s, MARGIN, ly + Inches(0.4), W - 2 * MARGIN, Inches(0.35),
                      f"{L('leave_needed', lang)}: " + ", ".join(ha["leave_dates"]), size=11, color=MUTED)

    def flights(self):
        fl = self.trip.get("flights", [])
        if not fl:
            return
        lang = self.lang
        s = self.new_slide(L("flights", lang), self.trip.get("flights_note", ""))
        heads = [L("airline", lang), L("type", lang), L("schedule", lang), L("baggage", lang),
                 L("fare", lang), L("addons", lang), L("true_total", lang), L("notes", lang)]
        rows, fills = [], []
        for f in fl:
            total = (f.get("fare_myr") or 0) + (f.get("addons_myr") or 0)
            rows.append([("⭐ " if f.get("recommended") else "") + str(f.get("airline", "")), f.get("type", ""),
                         f.get("schedule", ""), f.get("baggage", ""), fmt_money(f.get("fare_myr")),
                         fmt_money(f.get("addons_myr") or 0), fmt_money(total), f.get("notes", "")])
            fills.append(GREEN_BG if f.get("recommended") else None)
        self.table(s, heads, rows, [1.7, 0.8, 2.0, 1.6, 1.0, 1.1, 1.2, 3.0],
                   font=12, row_fills=fills)

    def days(self):
        lang = self.lang
        for day in self.trip.get("itinerary", []):
            items = day["items"]
            dt = day.get("date", "")
            wd = WEEKDAYS[lang][date.fromisoformat(dt).weekday()] if dt else ""
            chunks = balanced_chunks(items, ROWS_PER_SLIDE) or [[]]
            cur = self.trip["fx"]["currency"]
            rate = float(self.trip["fx"]["rate_myr_per_unit"])
            day_local = sum(float(it["cost_local"]) for it in items
                            if isinstance(it.get("cost_local"), (int, float)))
            for ci, chunk in enumerate(chunks):
                title = f"{L('day_n', lang, n=day['day'])} · {day.get('city', '')}"
                if len(chunks) > 1:
                    title += f" ({ci + 1}/{len(chunks)})"
                s = self.new_slide(title, f"{dt} {wd}  ·  {day.get('theme', '')}")
                heads = [L("time", lang), L("place", lang), L("category", lang), L("open_hours", lang),
                         L("open_check", lang), L("notes", lang)]
                rows, fills = [], []
                for it in chunk:
                    ok = it.get("open_ok")
                    mark = "✅" if ok is True else "❌" if ok is False else "❔"
                    if it.get("category") in NO_HOURS_CATEGORIES and "open_ok" not in it:
                        mark = "—"
                    rows.append([it.get("time", ""), it.get("name", ""),
                                 L(it.get("category", "other"), lang, ITEM_CATEGORY_LABELS),
                                 " / ".join(x for x in [it.get("open_hours", ""),
                                                         (L("closed", lang) + ": " + it["closed"]) if it.get("closed") else ""] if x),
                                 mark, it.get("notes", "")])
                    fills.append(RED_BG if ok is False else None)
                self.table(s, heads, rows, [1.0, 2.6, 1.3, 2.4, 0.9, 4.2], font=12, row_fills=fills)
                if ci == len(chunks) - 1 and day_local:
                    self.rect(s, MARGIN, H - Inches(1.15), W - 2 * MARGIN, Inches(0.55), WHITE)
                    self.rect(s, MARGIN, H - Inches(1.15), Inches(0.08), Inches(0.55), GOLD)
                    self.text(s, MARGIN + Inches(0.25), H - Inches(1.1), W - 2 * MARGIN - Inches(0.4), Inches(0.45),
                              f"💰 {L('day_cost', lang)}: {day_local:,.0f} {cur} ≈ {fmt_money(day_local * rate, decimals=0)} "
                              f"({L('per_person', lang)})", size=14, bold=True, color=NAVY, anchor=MSO_ANCHOR.MIDDLE)

    def paged_table(self, title_key, heads, rows, widths, fills=None, subtitle="", rows_per=ROWS_PER_SLIDE, font=12):
        chunks = balanced_chunks(list(range(len(rows))), rows_per)
        for pi, idx in enumerate(chunks):
            title = L(title_key, self.lang)
            if len(chunks) > 1:
                title += f" ({pi + 1}/{len(chunks)})"
            s = self.new_slide(title, subtitle)
            self.table(s, heads, [rows[i] for i in idx], widths, font=font,
                       row_fills=[fills[i] for i in idx] if fills else None)

    def food(self):
        lang, cur = self.lang, self.trip["fx"]["currency"]
        rate = float(self.trip["fx"]["rate_myr_per_unit"])
        rows, fills = [], []
        for f in self.trip.get("food", []):
            p = f.get("price_local")
            price = f"{p:,.0f} {cur} ≈ {fmt_money(p * rate)}" if isinstance(p, (int, float)) else (p or "")
            rows.append([f.get("name", ""), f.get("local_name", ""), f.get("where", ""), price,
                         L(f.get("halal", "unknown"), lang, HALAL_LABELS),
                         L(f.get("in_malaysia", "unknown"), lang, IN_MY_LABELS), f.get("notes", "")])
            fills.append(GREEN_BG if f.get("worth_it") == "must" else None)
        heads = [L("name", lang), L("local_name", lang), L("where", lang), L("price", lang), L("halal", lang),
                 L("in_malaysia", lang), L("notes", lang)]
        self.paged_table("food", heads, rows, [1.6, 1.4, 2.2, 1.8, 1.5, 1.4, 3.0], fills)

    def shopping(self):
        lang = self.lang
        rows, fills = [], []
        for x in self.trip.get("shopping", []):
            rows.append([x.get("name", ""), x.get("type", ""), L(x.get("in_malaysia", "unknown"), lang, IN_MY_LABELS),
                         x.get("price_diff", ""), L(x.get("worth_it", "maybe"), lang, WORTH_LABELS), x.get("notes", "")])
            fills.append(GREEN_BG if x.get("worth_it") == "must" else RGBColor(0xEE, 0xEE, 0xEE)
                         if x.get("worth_it") == "skip" else None)
        heads = [L("name", lang), L("type", lang), L("in_malaysia", lang), L("price_diff", lang),
                 L("worth_it", lang), L("notes", lang)]
        self.paged_table("shopping", heads, rows, [2.0, 1.5, 1.6, 1.8, 1.3, 4.6], fills)

    def budget_rows(self):
        rate = float(self.trip["fx"]["rate_myr_per_unit"])
        out = []
        for b in self.trip.get("budget", []):
            amt = b.get("amount") or 0
            amt = float(amt) if isinstance(amt, (int, float)) else 0.0
            myr = amt if b.get("currency") == "MYR" else amt * rate
            mult = per_multiplier(b.get("per", "person"), self.meta)
            out.append((b, myr * float(b.get("qty", 1)) * mult))
        return out

    def budget_total(self):
        return sum(v for _, v in self.budget_rows())

    def over_budget(self) -> bool:
        target = self.meta.get("budget_myr_pp")
        total = self.budget_total()
        return isinstance(target, (int, float)) and total / travelers_count(self.meta) > target

    def budget(self):
        rows_raw = self.budget_rows()
        if not rows_raw:
            return
        lang, cur = self.lang, self.trip["fx"]["currency"]
        pax = travelers_count(self.meta)
        # aggregate per category
        cats: dict[str, float] = {}
        for b, v in rows_raw:
            cats[b.get("category", "other")] = cats.get(b.get("category", "other"), 0) + v
        total = sum(cats.values())
        if total <= 0:
            return
        s = self.new_slide(L("budget", lang), fmt_rate(float(self.trip["fx"]["rate_myr_per_unit"]), cur))
        over = self.over_budget()
        target = self.meta.get("budget_myr_pp")
        label = L("total_pp", lang)
        if isinstance(target, (int, float)):
            label += f"  ·  {L('budget_target', lang)} {fmt_money(target)}"
        self.card(s, MARGIN, Inches(1.8), Inches(3.6), Inches(1.4), label, fmt_money(total / pax),
                  accent=RED if over else GOLD, value_color=RED if over else NAVY, value_size=30)
        if isinstance(target, (int, float)):
            self.text(s, MARGIN, Inches(4.95), Inches(3.6), Inches(0.4),
                      ("⚠️ " + L("over_budget", lang)) if over else ("✅ " + L("within_budget", lang)),
                      size=13, bold=True, color=RED if over else RGBColor(0x2A, 0x9D, 0x8F))
        self.card(s, MARGIN, Inches(3.4), Inches(3.6), Inches(1.4), L("total_group", lang), fmt_money(total),
                  value_size=26)
        # category bars
        x0, y0, bar_w = Inches(4.7), Inches(1.85), Inches(4.2)
        top = max(cats.values()) or 1
        for i, (k, v) in enumerate(sorted(cats.items(), key=lambda kv: -kv[1])):
            y = y0 + i * Inches(0.62)
            self.text(s, x0, y, Inches(1.8), Inches(0.45), L(k, lang, BUDGET_CAT_LABELS), size=13, bold=True)
            self.rect(s, x0 + Inches(1.9), y + Inches(0.08), int(bar_w * (v / top)) or 1, Inches(0.3), GOLD)
            self.text(s, x0 + Inches(1.95) + int(bar_w * (v / top)), y + Inches(0.02), Inches(2.0), Inches(0.4),
                      f"{fmt_money(v)} ({v / total:.0%})", size=12, color=MUTED)
        # detail table on next slide(s)
        heads = [L("category", lang), L("item", lang), L("amount", lang), L("qty", lang), L("per", lang),
                 L("subtotal_myr", lang), L("notes", lang)]
        rows = []
        for b, v in rows_raw:
            amt = b.get("amount")
            amt_s = fmt_money(amt) if b.get("currency") == "MYR" else f"{float(amt or 0):,.0f} {cur}"
            rows.append([L(b.get("category", "other"), lang, BUDGET_CAT_LABELS), b.get("item", ""), amt_s,
                         b.get("qty", 1), L("per_" + b.get("per", "person").replace("group", "group"), lang),
                         fmt_money(v), b.get("notes", "")])
        self.paged_table("budget", heads, rows, [1.4, 2.6, 1.6, 0.6, 1.1, 1.4, 3.4], rows_per=11, font=11)

    def checklist(self):
        t, lang = self.trip, self.lang
        items = t.get("checklist", [])
        tips = t.get("tips", [])
        if not items and not tips:
            return
        lines = []
        for i in items:
            if isinstance(i, dict):
                lines.append("☐ " + i.get("item", "") + (f"  — {i['notes']}" if i.get("notes") else ""))
            else:
                lines.append("☐ " + i)
        item_pages = balanced_chunks(lines, 11) or [[]]
        tip_pages = balanced_chunks(["• " + x for x in tips], 7) or [[]]
        n = max(len(item_pages), len(tip_pages))
        half = Inches(5.9)
        for pi in range(n):
            title = L("checklist", lang) + " & " + L("tips", lang) + (f" ({pi + 1}/{n})" if n > 1 else "")
            s = self.new_slide(title)
            if pi < len(item_pages):
                self.text(s, MARGIN, Inches(1.6), half, Inches(5.2), item_pages[pi], size=12)
            if pi < len(tip_pages) and tip_pages[pi]:
                self.rect(s, MARGIN + half + Inches(0.3), Inches(1.6), W - 2 * MARGIN - half - Inches(0.3), Inches(5.2), WHITE)
                self.text(s, MARGIN + half + Inches(0.5), Inches(1.7), W - 2 * MARGIN - half - Inches(0.6), Inches(0.4),
                          "💡 " + L("tips", lang), size=16, bold=True, color=NAVY)
                self.text(s, MARGIN + half + Inches(0.5), Inches(2.2), W - 2 * MARGIN - half - Inches(0.6), Inches(4.5),
                          tip_pages[pi], size=12)

    def sources(self):
        src = self.trip.get("sources", [])
        if not src:
            return
        lines = [f"• {x.get('title', '')} — {x.get('url', '')} ({x.get('checked', '')})" for x in src]
        pages = balanced_chunks(lines, 14)
        for pi, chunk in enumerate(pages):
            title = L("sources", self.lang) + (f" ({pi + 1}/{len(pages)})" if len(pages) > 1 else "")
            s = self.new_slide(title, L("disclaimer", self.lang))
            self.text(s, MARGIN, Inches(1.8), W - 2 * MARGIN, Inches(5), chunk, size=11, color=MUTED)

    def build(self, out):
        self.cover()
        self.glance()
        self.holidays()
        self.calendar()
        self.flights()
        self.days()
        self.food()
        self.shopping()
        self.budget()
        self.checklist()
        self.sources()
        self.prs.save(out)
        print(f"Saved {out} ({self.page} slides)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python make_ppt.py trip.json output.pptx")
    Deck(load_trip(sys.argv[1])).build(sys.argv[2])
