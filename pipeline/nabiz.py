"""'Ekonomik Nabız' — Türkiye's main economic indicators on one page, described NEUTRALLY.

No good/bad scoring (CLAUDE.md: no political commentary). For each indicator:
latest value, change over a year, position within its own last 10 years (min / median / max and
percentile rank of the latest value), and — where the World Bank comparison has it — Türkiye's rank among
peer economies. Inputs are the site's own JSON outputs, so sample flags carry through unchanged.
"""

from __future__ import annotations

from reel import engine as e

GROUPS = ["Büyüme ve istihdam", "Fiyatlar ve faiz", "Dış denge ve risk", "Kamu maliyesi", "Piyasalar"]
# makro id -> (group, what a higher value means — neutral wording)
MACRO = {
    "gdp_growth": ("Büyüme ve istihdam", "Yüksek değer: ekonomi bir yıl öncesine göre daha hızlı büyüyor."),
    "gdp_usd_pc": ("Büyüme ve istihdam", "Cari dolarla; kur hareketlerinden de etkilenir."),
    "unemployment": ("Büyüme ve istihdam", "İşgücündeki işsizlerin payı."),
    "inflation": ("Fiyatlar ve faiz", "Fiyatların bir yıl önceye göre artış hızı."),
    "policy_rate": ("Fiyatlar ve faiz", "TCMB'nin bir hafta vadeli repo ihale faizi."),
    "real_deposit": ("Fiyatlar ve faiz", "Mevduat faizinin son 12 ay enflasyonuna göre reel hâli; negatif değer, mevduatın enflasyonun gerisinde kaldığını gösterir."),
    "current_account": ("Dış denge ve risk", "Son 12 ayın toplamı; negatif değer döviz girişinden çok çıkış olduğunu gösterir."),
    "reserves": ("Dış denge ve risk", "Merkez Bankası'nın brüt döviz ve altın varlıkları."),
    "cds_5y": ("Dış denge ve risk", "Türkiye'nin 5 yıllık borcu için piyasada ödenen sigorta primi; yüksek değer, piyasanın algıladığı riskin yüksek olduğunu gösterir."),
    "budget_balance_gdp": ("Kamu maliyesi", "Son 12 ayın merkezi yönetim bütçe dengesi, GSYH'ye oranı; negatif değer açık demektir."),
    "usdtry": ("Piyasalar", "Bir doların TL karşılığı."),
    "bist100_usd": ("Piyasalar", "Borsa İstanbul 100 endeksinin dolar karşılığı."),
}
# makro id -> World Bank comparison id (same concept; annual data)
PEER = {"gdp_growth": "gdp_growth", "inflation": "inflation", "unemployment": "unemployment", "gdp_usd_pc": "gdp_pc_usd",
        "current_account": "current_account", "real_deposit": "real_interest"}
PER_YEAR = {"M": 12, "Q": 4, "A": 1}


def _peer(countries: dict, cid: str) -> dict | None:
    ind = next((i for i in countries.get("indicators", []) if i["id"] == cid), None)
    if not ind or "TUR" not in ind["series"]:
        return None
    tur = ind["series"]["TUR"]
    if not tur:
        return None
    year = tur[-1][0]
    vals = {iso: dict(pts).get(year) for iso, pts in ind["series"].items()}
    vals = {k: v for k, v in vals.items() if v is not None}
    order = sorted(vals, key=lambda k: -vals[k])
    names = {c["iso"]: c["name"] for c in countries.get("countries", [])}
    return {"label": ind["label"], "unit": ind["unit"], "year": year, "value": vals["TUR"], "rank": order.index("TUR") + 1,
            "n": len(order), "median": sorted(vals.values())[len(vals) // 2], "highest": names.get(order[0], order[0]),
            "sample": bool(ind.get("sample", countries.get("sample")))}


def build_nabiz(macro: dict, countries: dict, extras: list[dict] | None = None) -> dict:
    cards = []
    for ind in macro.get("indicators", []):
        if ind["id"] not in MACRO or not ind.get("points"):
            continue
        group, reading = MACRO[ind["id"]]
        k = PER_YEAR.get(ind.get("freq", "M"), 12)
        pts = ind["points"]
        window = pts[-10 * k:]
        vals = [v for _, v in window]
        stats = e.window_stats(vals)
        prev = pts[-1 - k][1] if len(pts) > k else None
        card = {"id": ind["id"], "label": ind["label"], "unit": ind["unit"], "group": group, "reading": reading,
                "period": pts[-1][0], "value": pts[-1][1], "freq": ind.get("freq", "M"),
                "change_1y": (pts[-1][1] - prev) if prev is not None else None,
                "change_1y_pct": (100 * (pts[-1][1] / prev - 1)) if prev not in (None, 0) and ind["unit"] not in ("%", "bp") else None,
                "window": {"from": window[0][0], "to": window[-1][0], **stats},
                "spark": [[d, round(v, 4)] for d, v in window], "sample": bool(ind.get("sample", macro.get("sample"))),
                "source": ind.get("source", "")}
        if ind["id"] in PEER:
            card["peer"] = _peer(countries, PEER[ind["id"]])
        cards.append(card)
    for x in extras or []:
        cards.append(x)
    return {"groups": GROUPS + (["Gerçek veriyle"] if extras else []), "cards": cards,
            "sample": any(c["sample"] for c in cards), "end_month": macro.get("end_month")}


def series_card(*, cid: str, label: str, unit: str, group: str, reading: str, points: list, per_year: int,
                source: str, sample: bool = False) -> dict | None:
    """Same card shape for any [[period, value], ...] series (used for the real-data indicators)."""
    if len(points) < 2:
        return None
    window = points[-10 * per_year:]
    stats = e.window_stats([v for _, v in window])
    prev = points[-1 - per_year][1] if len(points) > per_year else None
    return {"id": cid, "label": label, "unit": unit, "group": group, "reading": reading, "period": points[-1][0],
            "value": points[-1][1], "freq": {12: "M", 4: "Q", 2: "S", 1: "A"}.get(per_year, "M"),
            "change_1y": points[-1][1] - prev if prev is not None else None,
            "change_1y_pct": 100 * (points[-1][1] / prev - 1) if prev not in (None, 0) and unit not in ("%",) else None,
            "window": {"from": window[0][0], "to": window[-1][0], **stats},
            "spark": [[d, round(v, 4)] for d, v in window], "sample": sample, "source": source}


def real_extras(bigmac: dict | None, house: dict | None, commodities: dict | None) -> list[dict]:
    G = "Gerçek veriyle"
    out = []
    tr = next((c for c in (house or {}).get("countries", []) if c["code"] == "TR"), None)
    if tr:
        out.append(series_card(cid="house_real", label="Reel konut fiyatı (2010 = 100)", unit="endeks", group=G, points=tr["series"], per_year=4,
                               reading="Konut fiyatlarının TÜFE'ye göre seyri; 100 = 2010 ortalaması.", source="BIS / TCMB KFE"))
    s = (commodities or {}).get("series", {})
    if "gold" in s:
        out.append(series_card(cid="gold", label="Altın (ons)", unit="$", group=G, points=s["gold"]["points"], per_year=12,
                               reading="Dünya piyasasında ons altının dolar fiyatı (aylık ortalama).", source=s["gold"]["source"]))
    if "brent" in s:
        out.append(series_card(cid="brent", label="Brent petrol (varil)", unit="$", group=G, points=s["brent"]["points"], per_year=12,
                               reading="Enerji ithalatı faturasını etkileyen petrol fiyatı.", source=s["brent"]["source"]))
    bm = (bigmac or {}).get("history", {}).get("TUR")
    if bm:
        pts = [[p[0][:7], round(100 * p[4], 3)] for p in bm["points"]]
        out.append(series_card(cid="bigmac", label="Big Mac endeksi: TL (dolara karşı)", unit="%", group=G, points=pts, per_year=2,
                               reading="Pozitif: Big Mac Türkiye'de dolar cinsinden ABD'den pahalı. Kaba bir satın alma gücü ölçüsüdür.", source="The Economist"))
    return [x for x in out if x]
