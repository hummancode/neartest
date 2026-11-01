"""List EVDS series matching keywords, to find and verify codes for series.py.

Usage:  EVDS_API_KEY=... python -m pipeline.discover "Tüketici Fiyat" "Mevduat"
Prints category -> data group -> series code / name / start date.
"""

from __future__ import annotations

import os
import sys


def main(keywords: list[str]) -> int:
    key = os.environ.get("EVDS_API_KEY")
    if not key:
        print("EVDS_API_KEY gerekli.")
        return 1
    from evds import evdsAPI

    api = evdsAPI(key)
    groups = api.get_sub_categories()
    name_col = [c for c in groups.columns if c.startswith("DATAGROUP_NAME")][0]
    for kw in keywords:
        hits = groups[groups[name_col].str.contains(kw, case=False, na=False)]
        print(f"\n=== '{kw}': {len(hits)} veri grubu ===")
        for _, g in hits.head(15).iterrows():
            print(f"\n[{g['DATAGROUP_CODE']}] {g[name_col]}")
            try:
                series = api.get_series(g["DATAGROUP_CODE"])
                print(series.head(20).to_string(index=False))
            except Exception as exc:  # keep going; one bad group should not stop discovery
                print(f"  (seri listesi alınamadı: {exc})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["Tüketici Fiyat", "Mevduat", "Döviz"]))
