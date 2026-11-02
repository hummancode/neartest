"""Manual data import: data/manual/<series>.csv (+ optional <series>.meta.json).

Lets real data flow without the EVDS API: download a series from the EVDS web
interface (or another official source) as CSV and drop it here. Daily rows are
averaged per month, matching the API fetch (aggregation "avg").

CSV: first column a date, second column the value. A header row is optional.
Accepted dates: YYYY-MM, YYYY-M, YYYY/MM, YYYY-MM-DD, MM-YYYY, DD-MM-YYYY, DD.MM.YYYY.
Numbers: "1234.5", "1.234,5", "1,234.5", "45,25" (comma = decimal when alone).

Number heuristic: "1.000" (dots in groups of three, no comma) is read as 1000.
"""

from __future__ import annotations

import csv
import io
import json
import math
import re
from pathlib import Path

MANUAL = Path(__file__).resolve().parent.parent / "data" / "manual"


class ManualDataError(ValueError):
    pass


_DATE_PATTERNS = [
    (re.compile(r"^(\d{4})[-/](\d{1,2})$"), lambda m: (m[1], m[2])),            # 2024-01, 2024-1, 2024/06
    (re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$"), lambda m: (m[1], m[2])),     # 2024-03-15
    (re.compile(r"^(\d{1,2})[-.](\d{4})$"), lambda m: (m[2], m[1])),            # 05-2024
    (re.compile(r"^(\d{1,2})[-./](\d{1,2})[-./](\d{4})$"), lambda m: (m[3], m[2])),  # 15.04.2024, 01-01-2024
]


def parse_month(text: str) -> str | None:
    t = text.strip()
    for pattern, pick in _DATE_PATTERNS:
        m = pattern.match(t)
        if m:
            year, month = pick(m)
            if 1 <= int(month) <= 12:
                return f"{int(year):04d}-{int(month):02d}"
    return None


def parse_number(text: str) -> float:
    t = text.strip().replace(" ", "").replace(" ", "")
    if t == "" or not re.search(r"\d", t):
        return math.nan
    if "," in t and "." in t:
        # Whichever separator comes last is the decimal one.
        if t.rfind(",") > t.rfind("."):
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    elif "," in t:
        if t.count(",") > 1:
            t = t.replace(",", "")
        else:
            t = t.replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+", t):
        t = t.replace(".", "")
    try:
        return float(t)
    except ValueError:
        return math.nan


def parse_csv(text: str) -> dict[str, float]:
    """CSV text -> {"YYYY-MM": monthly average}."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return {}
    sample = "\n".join(lines[:5])
    # Semicolon (EVDS / Turkish Excel) or tab first; plain comma CSV otherwise
    # (decimal-comma numbers must then be quoted).
    delimiter = ";" if ";" in sample else ("\t" if "\t" in sample else ",")
    rows = list(csv.reader(io.StringIO("\n".join(lines)), delimiter=delimiter))
    sums: dict[str, list[float]] = {}
    for i, row in enumerate(rows):
        if len(row) < 2:
            continue
        month = parse_month(row[0])
        if month is None:
            if i == 0:
                continue  # header
            raise ManualDataError(f"satır {i + 1}: tarih okunamadı: {row[0]!r}")
        value = parse_number(row[1])
        if math.isnan(value):
            continue
        sums.setdefault(month, []).append(value)
    return {m: sum(v) / len(v) for m, v in sorted(sums.items())}


def load(name: str, directory: Path | None = None) -> tuple[dict[str, float], dict] | None:
    """Return (series, meta) for data/manual/<name>.csv, or None if absent."""
    directory = directory or MANUAL
    path = directory / f"{name}.csv"
    if not path.exists():
        return None
    series = parse_csv(path.read_text(encoding="utf-8-sig"))
    if not series:
        raise ManualDataError(f"{path}: veri yok")
    meta_path = directory / f"{name}.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    return series, meta
