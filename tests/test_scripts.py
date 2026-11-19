"""Smoke tests for the bundled scripts. Run: python -m unittest discover -s tests -v"""
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "malaysian-travel-planner"
SCRIPTS = SKILL / "scripts"
EXAMPLE = SKILL / "examples" / "osaka-kyoto-5d.json"
sys.path.insert(0, str(SCRIPTS))

import holidays  # noqa: E402
from common import balanced_chunks, load_json  # noqa: E402


def run(*args):
    return subprocess.run([sys.executable, *args], cwd=SCRIPTS, capture_output=True, text=True, check=True).stdout


class HolidayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hdata, cls.peaks = holidays.load_data()

    def cal(self, state):
        return holidays.StateCalendar(self.hdata, state)

    def test_data_files_valid(self):
        for h in self.hdata["holidays"]:
            date.fromisoformat(h["date"])
            self.assertTrue(h["states"] == "ALL" or set(h["states"]) <= set(self.hdata["states"]), h)
            for k in ("en", "zh", "ms", "status"):
                self.assertIn(k, h)
        for p in self.peaks["periods"]:
            self.assertLessEqual(date.fromisoformat(p["start"]), date.fromisoformat(p["end"]))
            self.assertIn(p["level"], holidays.LEVEL_POINTS)
            self.assertIn(p["country"], self.peaks["countries"])

    def test_sunday_replacement_sat_sun_state(self):
        # CNY day 2 = Sun 7 Feb 2027 -> Mon 8 Feb replacement in Selangor
        self.assertIn(date(2027, 2, 8), self.cal("SGR").holidays)

    def test_chained_replacement(self):
        # Awal Muharram Sun 6 Jun, Agong Mon 7 Jun -> replacement Tue 8 Jun
        self.assertIn(date(2027, 6, 8), self.cal("KUL").holidays)

    def test_friday_replacement_fri_sat_state(self):
        # Thaipusam Fri 22 Jan 2027 in Kedah -> Sunday 24 Jan
        cal = self.cal("KDH")
        self.assertIn(date(2027, 1, 24), cal.holidays)
        self.assertTrue(cal.is_off(date(2027, 1, 22)))
        self.assertFalse(cal.is_off(date(2027, 1, 31)))  # Sunday is a workday in Kedah

    def test_state_exclusions(self):
        self.assertNotIn(date(2027, 1, 1), self.cal("JHR").holidays)
        self.assertIn(date(2027, 1, 1), self.cal("SGR").holidays)
        self.assertNotIn(date(2027, 10, 28), self.cal("SWK").holidays)

    def test_check_raya_trip(self):
        a = holidays.analyse(self.cal("SGR"), self.peaks, "JP", date(2027, 3, 10), date(2027, 3, 14), "en")
        self.assertEqual(a["leave_needed"], 1)
        self.assertEqual(a["leave_dates"], ["2027-03-12"])
        self.assertIn(a["price_impact"], ("high", "very_high"))
        self.assertTrue(a["school_holidays"])

    def test_windows_respect_leave_budget(self):
        res = holidays.find_windows(self.cal("SGR"), self.peaks, "JP", date(2027, 1, 1), date(2027, 6, 30),
                                    leave=3, days=None, top=5, lang="en")
        self.assertTrue(res)
        for w in res:
            self.assertLessEqual(w["leave_needed"], 3)
        self.assertGreaterEqual(res[0]["total_days"], 9)

    def test_state_alias(self):
        self.assertEqual(holidays.resolve_state("Penang", self.hdata["states"]), "PNG")
        self.assertEqual(holidays.resolve_state("kl", self.hdata["states"]), "KUL")

    def test_cli_json(self):
        out = run("holidays.py", "check", "--state", "Selangor", "--country", "KR",
                  "--start", "2027-09-13", "--end", "2027-09-18", "--json", "--lang", "zh")
        js = json.loads(out)
        self.assertTrue(any("Chuseok" in e["name"] or "中秋" in e["name"] for e in js["destination_events"]))


class TripJsonAndHacksTests(unittest.TestCase):
    def test_trip_json_block(self):
        out = run("holidays.py", "check", "--state", "SGR", "--country", "JP", "--start", "2027-03-10",
                  "--end", "2027-03-14", "--trip-json", "--lang", "en")
        ha = json.loads(out)["holiday_analysis"]
        for k in ("summary", "price_impact", "leave_needed", "leave_dates", "weekend", "my_holidays",
                  "school_holidays", "alternatives"):
            self.assertIn(k, ha)
        self.assertEqual(len(ha["alternatives"]), 3)
        for a in ha["alternatives"]:
            self.assertFalse(a["start"] <= "2027-03-14" and "2027-03-10" <= a["end"], "alternative overlaps trip")

    def test_hacks_quality(self):
        hdata, peaks = holidays.load_data()
        res = holidays.leave_hacks(hdata, peaks, ["SGR"], 2027, 4, "en")["SGR"]
        self.assertTrue(res)
        for w in res:
            self.assertGreaterEqual(w["leave_needed"], 1)
            self.assertGreaterEqual(w["efficiency"], 2.5)
            self.assertTrue(w["public_holidays"])
        starts = {(w["start"], w["end"]) for w in res}
        self.assertIn(("2027-10-28", "2027-10-31"), starts)  # Deepavali Thu + Fri leave

    def test_hacks_markdown(self):
        out = run("holidays.py", "hacks", "--year", "2027", "--state", "KDH", "--lang", "en")
        self.assertIn("Kedah", out)
        self.assertIn("Fri-Sat", out)


class CheckTripTests(unittest.TestCase):
    def setUp(self):
        self.trip = load_json(EXAMPLE)

    def check(self, trip):
        import check_trip
        return check_trip.check(trip, date(2026, 11, 19))

    def test_example_is_clean(self):
        errors, _ = self.check(self.trip)
        self.assertEqual(errors, [])

    def test_inverted_fx(self):
        self.trip["fx"]["rate_myr_per_unit"] = 34.5
        errors, _ = self.check(self.trip)
        self.assertTrue(any("inverted" in e for e in errors), errors)

    def test_closed_weekday_conflict(self):
        item = self.trip["itinerary"][1]["items"][1]  # Thursday 2027-03-11
        item["closed"] = "Closed on Thursdays"
        item["open_ok"] = True
        errors, _ = self.check(self.trip)
        self.assertTrue(any("Thu" in e and "closed" in e for e in errors), errors)

    def test_diet_conflict(self):
        self.trip["meta"]["preferences"]["diet"] = "halal"
        errors, warns = self.check(self.trip)
        self.assertTrue(any("contains-pork" in e for e in errors))

    def test_one_recommended_flight(self):
        for f in self.trip["flights"]:
            f["recommended"] = True
        errors, _ = self.check(self.trip)
        self.assertTrue(any("exactly one flight" in e for e in errors))

    def test_over_budget(self):
        self.trip["meta"]["budget_myr_pp"] = 2000
        _, warns = self.check(self.trip)
        self.assertTrue(any("over the stated" in w for w in warns))


class CalendarTests(unittest.TestCase):
    def test_calendar_model(self):
        from common import calendar_model
        months = calendar_model(load_json(EXAMPLE))
        self.assertEqual(len(months), 1)
        days = [d for wk in months[0]["weeks"] for d in wk if d]
        self.assertEqual(len(days), 31)
        trip = [d for d in days if d["trip"]]
        self.assertEqual(len(trip), 5)
        self.assertEqual([d["date"].day for d in trip if d["leave"]], [12])
        self.assertEqual([d["date"].day for d in trip if d["holiday"]], [10, 11])


class FxTests(unittest.TestCase):
    def test_manual_rate(self):
        js = json.loads(run("fx.py", "JPY", "--rate", "0.03", "--amount", "10000", "--json"))
        self.assertAlmostEqual(js["amount_myr"], 300.0)
        self.assertAlmostEqual(js["units_per_myr"], 33.3333, places=3)


class OutputTests(unittest.TestCase):
    def test_generate_excel_and_ppt(self):
        from openpyxl import load_workbook
        from pptx import Presentation
        with tempfile.TemporaryDirectory() as tmp:
            x, p = Path(tmp) / "t.xlsx", Path(tmp) / "t.pptx"
            run("make_excel.py", str(EXAMPLE), str(x))
            run("make_ppt.py", str(EXAMPLE), str(p))
            wb = load_workbook(x)
            self.assertIn("FX", wb.defined_names)
            self.assertIn("PAX", wb.defined_names)
            self.assertGreaterEqual(len(wb.worksheets), 8)
            prs = Presentation(p)
            trip = load_json(EXAMPLE)
            self.assertGreaterEqual(len(prs.slides), 5 + len(trip["itinerary"]))

    def test_invalid_trip_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text(json.dumps({"meta": {"language": "zh"}}), encoding="utf-8")
            r = subprocess.run([sys.executable, "make_excel.py", str(bad), str(Path(tmp) / "o.xlsx")],
                               cwd=SCRIPTS, capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("fx.currency", r.stderr)

    def test_balanced_chunks(self):
        self.assertEqual([len(c) for c in balanced_chunks(list(range(9)), 8)], [5, 4])
        self.assertEqual([len(c) for c in balanced_chunks(list(range(8)), 8)], [8])
        self.assertEqual(balanced_chunks([], 8), [])


if __name__ == "__main__":
    unittest.main()
