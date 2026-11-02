"""Regulated-parameter registry ("mevzuat takibi").

data/params/parametreler.json holds rates that law/regulation sets and changes
(KKDF, BSMV, withholding tax, card interest caps, minimum payment ratios...). Each
parameter keeps a dated history; every entry says where it comes from and who checked it.

status:
  verified  — a person read the official text (Resmî Gazete, TCMB, GİB, BDDK) and confirmed it
  candidate — value and official source located, official text not read yet
  example   — illustrative only, no source

Usage:  python -m pipeline.params            # validate + write site/data/mevzuat.json
        python -m pipeline.params --stale    # list parameters overdue for a check (exit 1 if any)
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "data" / "params" / "parametreler.json"
OUT = ROOT / "site" / "data" / "mevzuat.json"
STATUSES = {"verified", "candidate", "example"}
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ParamError(ValueError):
    pass


def load(path: Path = REGISTRY) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(reg: dict) -> None:
    ids = set()
    for p in reg.get("params", []):
        pid = p.get("id")
        if not pid or pid in ids:
            raise ParamError(f"eksik veya tekrar eden id: {pid!r}")
        ids.add(pid)
        for key in ("label", "unit", "group", "history", "check_every_days"):
            if key not in p:
                raise ParamError(f"{pid}: '{key}' eksik")
        if not p["history"]:
            raise ParamError(f"{pid}: geçmiş boş")
        for h in p["history"]:
            if h.get("status") not in STATUSES:
                raise ParamError(f"{pid}: geçersiz durum {h.get('status')!r}")
            for dkey in ("effective_from", "checked_at"):
                v = h.get(dkey)
                if v is not None and not ISO.match(v):
                    raise ParamError(f"{pid}: {dkey} YYYY-AA-GG olmalı, {v!r}")
            if not isinstance(h.get("value"), (int, float)):
                raise ParamError(f"{pid}: değer sayı olmalı")
            if h["status"] == "verified":
                src = h.get("source") or {}
                if not src.get("url") or not h.get("checked_by") or not h.get("checked_at"):
                    raise ParamError(f"{pid}: 'verified' kayıt resmî kaynak bağlantısı, kontrol eden ve tarih ister")


def summarize(reg: dict, today: date | None = None) -> dict:
    """Current value (latest entry in force), upcoming change, staleness, for the site."""
    validate(reg)
    today = today or date.today()
    out = []
    for p in reg["params"]:
        hist = sorted(p["history"], key=lambda h: h["effective_from"] or "0000-00-00")
        in_force = [h for h in hist if not h["effective_from"] or date.fromisoformat(h["effective_from"]) <= today]
        future = [h for h in hist if h["effective_from"] and date.fromisoformat(h["effective_from"]) > today]
        current = in_force[-1] if in_force else None
        checked = max((h["checked_at"] for h in hist if h.get("checked_at")), default=None)
        stale = checked is None or (today - date.fromisoformat(checked)).days > p["check_every_days"]
        out.append({k: p.get(k) for k in ("id", "label", "unit", "group", "used_by", "official_sources", "note")}
                   | {"current": current, "upcoming": future[0] if future else None, "history": hist,
                      "last_checked": checked, "stale": stale, "check_every_days": p["check_every_days"]})
    return {"as_of": today.isoformat(), "params": out}


def main(argv: list[str]) -> int:
    summary = summarize(load())
    if "--stale" in argv:
        stale = [p for p in summary["params"] if p["stale"] or (p["current"] or {}).get("status") != "verified"]
        for p in stale:
            cur = p["current"] or {}
            print(f"- {p['id']}: {cur.get('value')} {p['unit']} [{cur.get('status')}], son kontrol {p['last_checked']}")
        return 1 if stale else 0
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print(f"yazıldı: {OUT.relative_to(ROOT)} ({len(summary['params'])} parametre)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
