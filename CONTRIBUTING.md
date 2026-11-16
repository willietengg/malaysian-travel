# Contributing / 贡献指南

Thanks for helping Malaysians travel smarter! 🇲🇾

## Most wanted

1. **Yearly holiday update** (`malaysian-travel-planner/data/my_holidays.json`)
   - The government usually announces next year's holidays around August–September (Prime Minister's Department, BKPP).
   - Add each holiday with `states` (`"ALL"` + optional `except`, or a list of state codes) and `status` (`confirmed` / `provisional`).
   - **Don't add replacement days (cuti ganti).** `holidays.py` computes them.
   - Add KPM school holidays for both Group A (Kedah, Kelantan, Terengganu) and Group B.
   - Update `_last_updated` and `_sources`.

2. **"Does Malaysia have it?" brand table** (`references/brands-in-malaysia.md`)
   - Add the brand, `yes / partial / online / no`, and a short note. Include a source link in your PR description.

3. **New destination**
   - Copy `references/destinations/_template.md` and fill it in from a Malaysian traveller's point of view.
   - Add its peak and closure periods to `data/destination_peaks.json`.
   - Link it from the table in `SKILL.md`.

4. **Translations.** UI labels live in `scripts/common.py` (`zh` / `en` / `ms`).

## Before opening a PR

```bash
pip install openpyxl python-pptx
```
```bash
python -m unittest discover -s tests -v
```

Please cite sources for any fact (entry rules, opening hours, outlet openings) and mark uncertain ones with `(verify)`.
