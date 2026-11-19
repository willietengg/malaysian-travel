#!/usr/bin/env python3
"""Get the RM exchange rate for a destination currency and convert amounts.

  python fx.py JPY                      # live rate, 1 JPY = ? RM
  python fx.py JPY --amount 12000       # convert ¥12,000 to RM
  python fx.py KRW --rate 0.00318       # offline: use a rate you found by web search
  python fx.py THB --json

Rates are mid-market. Card / money-changer rates are usually 1-3% worse; the
script also prints a "realistic" rate with a configurable buffer (default 2%).
If every provider is blocked (common in sandboxes), web-search
"1 <CUR> to MYR" and re-run with --rate.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import date

PROVIDERS = [
    # (name, url template, extractor -> units of CUR per 1 MYR)
    ("open.er-api.com", "https://open.er-api.com/v6/latest/MYR",
     lambda js, cur: js["rates"][cur]),
    ("frankfurter.app", "https://api.frankfurter.app/latest?from=MYR&to={cur}",
     lambda js, cur: js["rates"][cur]),
    ("fawazahmed0/currency-api", "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/myr.json",
     lambda js, cur: js["myr"][cur.lower()]),
]

SYMBOLS = {"JPY": "¥", "KRW": "₩", "THB": "฿", "TWD": "NT$", "VND": "₫", "CNY": "¥", "MYR": "RM",
           "SGD": "S$", "HKD": "HK$", "USD": "US$", "EUR": "€", "GBP": "£", "AUD": "A$", "IDR": "Rp"}


def fetch_rate(cur: str, timeout: float = 8.0):
    errors = []
    for name, url, extract in PROVIDERS:
        try:
            req = urllib.request.Request(url.format(cur=cur), headers={"User-Agent": "travel-planner-skill/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                js = json.loads(r.read().decode())
            per_myr = float(extract(js, cur))
            if per_myr > 0:
                return 1.0 / per_myr, name
        except Exception as e:  # noqa: BLE001 - try next provider
            errors.append(f"{name}: {e.__class__.__name__}")
    return None, "; ".join(errors)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("currency", help="ISO code, e.g. JPY KRW THB TWD VND CNY")
    p.add_argument("--amount", type=float, help="Amount in the foreign currency to convert to RM")
    p.add_argument("--rate", type=float, help="Manual rate: RM for 1 unit of the currency")
    p.add_argument("--source", help="With --rate: where the rate came from (site name or URL)")
    p.add_argument("--date", help="With --rate: the date of that quote (YYYY-MM-DD)")
    p.add_argument("--buffer", type=float, default=2.0, help="Percent added for card/changer spread (default 2)")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    cur = a.currency.upper()

    if a.rate:
        rate, source = a.rate, a.source or "manual (web search)"
    else:
        rate, source = fetch_rate(cur)
        if rate is None:
            msg = (f"Could not reach any FX provider ({source}).\n"
                   f"Web-search '1 {cur} to MYR' and re-run: python fx.py {cur} --rate <RM per 1 {cur}>")
            if a.json:
                print(json.dumps({"currency": cur, "error": msg}))
            else:
                print(msg, file=sys.stderr)
            sys.exit(2)

    if a.rate and not a.date:
        print("note: pass --date YYYY-MM-DD (the date of that quote) so stale rates can be detected", file=sys.stderr)
    realistic = rate * (1 + a.buffer / 100)
    out = {
        "currency": cur,
        "rate_myr_per_unit": float(f"{rate:.6g}"),
        "units_per_myr": round(1 / rate, 4),
        "realistic_rate_myr_per_unit": float(f"{realistic:.6g}"),
        "buffer_percent": a.buffer,
        # A manual rate is only as fresh as its quote: leave the date empty unless --date is given
        "rate_date": (a.date or "") if a.rate else date.today().isoformat(),
        "source": source,
    }
    if a.amount is not None:
        out["amount"] = a.amount
        out["amount_myr"] = round(a.amount * rate, 2)
        out["amount_myr_realistic"] = round(a.amount * realistic, 2)

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    sym = SYMBOLS.get(cur, cur + " ")
    print(f"1 {cur} = RM {rate:.6f}   |   RM 1 = {sym}{1 / rate:,.2f}   ({source}, {out['rate_date']})")
    print(f"With ~{a.buffer:g}% card/changer spread: 1 {cur} ≈ RM {realistic:.6f}")
    if a.amount is not None:
        print(f"{sym}{a.amount:,.0f} ≈ RM {out['amount_myr']:,.2f} (≈ RM {out['amount_myr_realistic']:,.2f} after spread)")


if __name__ == "__main__":
    main()
