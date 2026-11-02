"""Province ("il") factbook data for the map page.

Observed indicators come from official sources, entered as CSV:
    data/manual/iller/<indicator>.csv   columns: plaka;yil;deger   (header optional)
Derived indicators are computed here; the household wealth figure is a MODEL ESTIMATE
(see reel.engine.province_wealth) whose assumptions the site lets users change.
Missing indicators are filled with flagged SYNTHETIC sample data when --sample is used.
"""

from __future__ import annotations

import csv
import io
import math
from pathlib import Path

from pipeline.manual import MANUAL, parse_number
from reel import engine as e

NAMES = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya", "Artvin", "Aydın", "Balıkesir",
    "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli",
    "Diyarbakır", "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkari",
    "Hatay", "Isparta", "Mersin", "İstanbul", "İzmir", "Kars", "Kastamonu", "Kayseri", "Kırklareli", "Kırşehir",
    "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla", "Muş", "Nevşehir",
    "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas", "Tekirdağ", "Tokat",
    "Trabzon", "Tunceli", "Şanlıurfa", "Uşak", "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman",
    "Kırıkkale", "Batman", "Şırnak", "Bartın", "Ardahan", "Iğdır", "Yalova", "Karabük", "Kilis", "Osmaniye", "Düzce",
]
REGIONS = {  # İBBS Düzey 1
    "İstanbul": [34], "Batı Marmara": [10, 17, 22, 39, 59], "Ege": [3, 9, 20, 35, 43, 45, 48, 64],
    "Doğu Marmara": [11, 14, 16, 26, 41, 54, 77, 81], "Batı Anadolu": [6, 42, 70],
    "Akdeniz": [1, 7, 15, 31, 32, 33, 46, 80], "Orta Anadolu": [38, 40, 50, 51, 58, 66, 68, 71],
    "Batı Karadeniz": [5, 18, 19, 37, 55, 57, 60, 67, 74, 78], "Doğu Karadeniz": [8, 28, 29, 52, 53, 61],
    "Kuzeydoğu Anadolu": [4, 24, 25, 36, 69, 75, 76], "Ortadoğu Anadolu": [12, 13, 23, 30, 44, 49, 62, 65],
    "Güneydoğu Anadolu": [2, 21, 27, 47, 56, 63, 72, 73, 79],
}
REGION_OF = {p: r for r, ps in REGIONS.items() for p in ps}

# id: (label, unit, group, source, kind) — kind: observed | derived | estimate
INDICATORS = {
    "population": ("Nüfus", "kişi", "Nüfus ve gelir", "TÜİK, Adrese Dayalı Nüfus Kayıt Sistemi", "observed"),
    "household_size": ("Ortalama hane büyüklüğü", "kişi/hane", "Nüfus ve gelir", "TÜİK", "observed"),
    "gdp_mn_tl": ("GSYH (cari)", "milyon TL", "Nüfus ve gelir", "TÜİK, il bazında GSYH", "observed"),
    "gdp_per_capita_tl": ("Kişi başı GSYH", "TL", "Nüfus ve gelir", "GSYH / nüfus", "derived"),
    "exports_mn_usd": ("İhracat", "milyon $", "Dış ticaret", "TÜİK / TİM — firmanın kayıtlı olduğu ile göre", "observed"),
    "exports_gdp": ("İhracat / GSYH", "%", "Dış ticaret", "ihracat × yıllık ort. USD/TRY / GSYH", "derived"),
    "exports_per_capita": ("Kişi başı ihracat", "$", "Dış ticaret", "ihracat / nüfus", "derived"),
    "insured_employees": ("Sigortalı ücretli çalışan (4/a)", "kişi", "İstihdam", "SGK il bazında sigortalı istatistikleri", "observed"),
    "insured_share": ("Ücretli çalışan / nüfus", "%", "İstihdam", "4/a sigortalı / nüfus", "derived"),
    "companies_active": ("Faal şirket sayısı", "adet", "Şirketler", "TOBB / Ticaret Bakanlığı", "observed"),
    "companies_new": ("Yıl içinde kurulan şirket", "adet", "Şirketler", "TOBB kurulan-kapanan şirket istatistikleri", "observed"),
    "listed_companies": ("Borsada işlem gören şirket", "adet", "Şirketler", "KAP — merkez adresi ilde olan şirketler", "observed"),
    "deposits_mn_tl": ("Banka mevduatı", "milyon TL", "Finans", "BDDK il bazında mevduat", "observed"),
    "loans_mn_tl": ("Banka kredisi", "milyon TL", "Finans", "BDDK il bazında kredi", "observed"),
    "deposits_per_capita": ("Kişi başı mevduat", "TL", "Finans", "mevduat / nüfus", "derived"),
    "loan_deposit": ("Kredi / mevduat", "%", "Finans", "kredi / mevduat", "derived"),
    "m2_price_tl": ("Konut m² satış fiyatı", "TL", "Konut", "Belirlenecek (resmî il bazında seri doğrulanacak)", "observed"),
    "rent_m2_tl": ("Konut m² kira", "TL", "Konut", "Belirlenecek (ilan verisi / BETAM — doğrulanacak)", "observed"),
    "house_sales": ("Konut satış sayısı (yıllık)", "adet", "Konut", "TÜİK konut satış istatistikleri", "observed"),
    "gross_rent_yield": ("Brüt kira getirisi", "%", "Konut", "yıllık kira / satış fiyatı", "derived"),
    "amortization_years": ("Kira ile amortisman süresi", "yıl", "Konut", "satış fiyatı / yıllık kira", "derived"),
    "price_to_wage_years": ("100 m² ev kaç yıllık maaş", "yıl", "Konut", "100 m² fiyat / (ortalama ücret × 12)", "derived"),
    "rent_to_wage": ("100 m² kira / ortalama ücret", "%", "Konut", "aylık kira / aylık ortalama ücret", "derived"),
    "avg_wage_tl": ("Ortalama aylık kazanç (brüt)", "TL", "Gelir", "SGK — prime esas ortalama günlük kazanç × 30", "observed"),
    "income_gini": ("Gelir Gini katsayısı", "katsayı", "Gelir", "TÜİK Gelir ve Yaşam Koşulları — İBBS-2 bölge değeri ile atanır", "observed"),
    "cars": ("Kayıtlı otomobil", "adet", "Gelir", "TÜİK motorlu kara taşıtları", "observed"),
    "cars_per_1000": ("1.000 kişiye otomobil", "adet", "Gelir", "otomobil / nüfus × 1.000", "derived"),
    "sege_score": ("SEGE gelişmişlik skoru", "skor", "Gelişmişlik", "Sanayi ve Teknoloji Bakanlığı, SEGE", "observed"),
    "wealth_per_household": ("Tahmini hane serveti (hane başına)", "TL", "Model tahmini", "Model: konut + mevduat (varsayımlar değiştirilebilir)", "estimate"),
    "wealth_total_bn": ("Tahmini toplam hane serveti", "milyar TL", "Model tahmini", "Model: konut + mevduat", "estimate"),
    "wealth_median_hh": ("Tahmini medyan hane serveti", "TL", "Model tahmini", "Model: ortalama × log-normal medyan/ortalama oranı", "estimate"),
    "wealth_gini": ("Tahmini servet Gini katsayısı", "katsayı", "Model tahmini", "Model: gelir Gini'sinden log-normal varsayım", "estimate"),
    "top10_share": ("En zengin %10'un tahmini servet payı", "%", "Model tahmini", "Model: log-normal varsayım", "estimate"),
    "gold_tonnes": ("Tahmini yastık altı altın", "ton", "Model tahmini", "Model: Türkiye toplamı varsayımı illere dağıtılır", "estimate"),
    "gold_value_bn": ("Tahmini yastık altı altın değeri", "milyar TL", "Model tahmini", "Model: ton × gram altın fiyatı", "estimate"),
    "gold_per_household_g": ("Hane başına tahmini altın", "gram", "Model tahmini", "Model", "estimate"),
}
OBSERVED = [k for k, v in INDICATORS.items() if v[4] == "observed"]

# Default model assumptions (illustrative; users change them on the page).
WEALTH_DEFAULTS = {"ownership_rate": 0.57, "dwelling_m2": 110.0, "household_deposit_share": 0.55, "household_size": 3.2,
                   # Wealth more unequal than income: dispersion multiplier on the income-implied lognormal sigma.
                   "inequality_multiplier": 1.8,
                   # National household gold outside banks (tonnes) — an assumption, no official statistic exists.
                   "gold_total_tonnes": 3500.0, "gold_beta": 0.5}


def parse_province_csv(text: str) -> dict[int, tuple[str, float]]:
    """plaka;yil;deger CSV -> {plaka: (year, value)}; the latest year wins per province."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return {}
    delim = ";" if ";" in lines[0] else ("\t" if "\t" in lines[0] else ",")
    out: dict[int, tuple[str, float]] = {}
    for i, row in enumerate(csv.reader(io.StringIO("\n".join(lines)), delimiter=delim)):
        if len(row) < 3:
            continue
        try:
            plaka = int(row[0].strip())
        except ValueError:
            if i == 0:
                continue
            raise ValueError(f"satır {i + 1}: plaka okunamadı: {row[0]!r}")
        if not 1 <= plaka <= 81:
            raise ValueError(f"satır {i + 1}: plaka 1–81 olmalı: {plaka}")
        year, value = row[1].strip(), parse_number(row[2])
        if math.isnan(value):
            continue
        if plaka not in out or year >= out[plaka][0]:
            out[plaka] = (year, value)
    return out


def _noise(plaka: int, k: int) -> float:
    x = math.sin(plaka * 12.9898 + k * 78.233) * 43758.5453
    return x - math.floor(x)


BIG = {34: 16.0, 6: 5.5, 35: 4.3, 16: 3.1, 7: 2.6, 42: 2.2, 1: 2.2, 27: 2.1, 63: 2.1, 41: 2.0, 33: 1.8, 21: 1.7, 31: 1.6}


def sample_provinces() -> dict[str, dict[int, tuple[str, float]]]:
    """SYNTHETIC province values. NOT real; for layout only."""
    out: dict[str, dict[int, tuple[str, float]]] = {k: {} for k in OBSERVED}
    for p in range(1, 82):
        size = BIG.get(p, 0.35 + 0.9 * _noise(p, 1))
        dev = min(1.0, 0.35 + 0.08 * size + 0.35 * _noise(p, 2)) * (0.75 if REGION_OF[p] in ("Güneydoğu Anadolu", "Ortadoğu Anadolu", "Kuzeydoğu Anadolu") else 1.0)
        pop = 1_000_000 * size * (0.85 + 0.3 * _noise(p, 3))
        gdp_pc = 180_000 + 420_000 * dev
        vals = {
            "population": pop,
            "household_size": 2.8 + 2.4 * (1 - dev) * _noise(p, 4) + (1.0 if REGION_OF[p] == "Güneydoğu Anadolu" else 0),
            "gdp_mn_tl": pop * gdp_pc / 1e6,
            "exports_mn_usd": pop * gdp_pc / 1e6 / 40 * (0.05 + 0.5 * dev * _noise(p, 5)),
            "insured_employees": pop * (0.10 + 0.25 * dev),
            "companies_active": pop * (0.004 + 0.02 * dev),
            "companies_new": pop * (0.0003 + 0.0015 * dev),
            "listed_companies": round(max(0.0, (size - 0.8) * 9 * dev * _noise(p, 6))),
            "deposits_mn_tl": pop * gdp_pc / 1e6 * (0.35 + 0.45 * dev),
            "loans_mn_tl": pop * gdp_pc / 1e6 * (0.40 + 0.40 * _noise(p, 7)),
            "m2_price_tl": 15_000 + 45_000 * dev * (0.7 + 0.6 * _noise(p, 8)),
            "sege_score": -1.5 + 4.0 * dev + 0.4 * _noise(p, 9),
            "rent_m2_tl": (15_000 + 45_000 * dev * (0.7 + 0.6 * _noise(p, 8))) * (0.0045 + 0.002 * _noise(p, 10)),
            "house_sales": pop * (0.010 + 0.006 * _noise(p, 11)),
            "avg_wage_tl": 28_000 + 30_000 * dev * (0.8 + 0.4 * _noise(p, 12)),
            "income_gini": 0.36 + 0.08 * _noise(p // 3, 13),
            "cars": pop * (0.08 + 0.22 * dev),
        }
        for k, v in vals.items():
            out[k][p] = ("2024", round(v, 2))
    return out


def _avg_fx(usdtry: dict[str, float], year: str) -> float | None:
    vals = [v for m, v in usdtry.items() if m.startswith(year + "-")]
    return sum(vals) / len(vals) if len(vals) == 12 else None


def parse_bist_list(text: str) -> dict[int, list[dict]]:
    """plaka;kod;unvan;sektor -> {plaka: [{code, name, sector}]} (companies by registered head office)."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return {}
    delim = ";" if ";" in lines[0] else ("\t" if "\t" in lines[0] else ",")
    out: dict[int, list[dict]] = {}
    for i, row in enumerate(csv.reader(io.StringIO("\n".join(lines)), delimiter=delim)):
        if len(row) < 3:
            continue
        try:
            plaka = int(row[0].strip())
        except ValueError:
            if i == 0:
                continue
            raise ValueError(f"satır {i + 1}: plaka okunamadı")
        out.setdefault(plaka, []).append({"code": row[1].strip(), "name": row[2].strip(),
                                          "sector": row[3].strip() if len(row) > 3 else ""})
    return {p: sorted(v, key=lambda x: x["code"]) for p, v in out.items()}


def build_provinces(usdtry: dict[str, float], allow_sample: bool, directory: Path | None = None,
                    gold_gram_tl: float | None = None, gold_sample: bool = True) -> dict:
    directory = directory or (MANUAL / "iller")
    synthetic = sample_provinces() if allow_sample else {}
    data, sample_flag = {}, {}
    for k in OBSERVED:
        path = directory / f"{k}.csv"
        if path.exists():
            data[k], sample_flag[k] = parse_province_csv(path.read_text(encoding="utf-8-sig")), False
        elif allow_sample:
            data[k], sample_flag[k] = synthetic[k], True
        else:
            data[k], sample_flag[k] = {}, False

    bist_path = directory / "bist_sirketler.csv"
    bist = parse_bist_list(bist_path.read_text(encoding="utf-8-sig")) if bist_path.exists() else {}

    provinces = []
    for p in range(1, 82):
        v = {k: data[k].get(p) for k in OBSERVED}
        out = {k: {"value": x[1], "year": x[0], "sample": sample_flag[k]} for k, x in v.items() if x}

        def d(key, value, year, *deps):
            out[key] = {"value": value, "year": year, "sample": any(sample_flag[x] for x in deps)}

        pop = v["population"]
        if pop and v["gdp_mn_tl"]:
            d("gdp_per_capita_tl", v["gdp_mn_tl"][1] * 1e6 / pop[1], v["gdp_mn_tl"][0], "gdp_mn_tl", "population")
        if v["exports_mn_usd"] and v["gdp_mn_tl"] and v["exports_mn_usd"][0] == v["gdp_mn_tl"][0]:
            fx = _avg_fx(usdtry, v["exports_mn_usd"][0])
            if fx:
                d("exports_gdp", 100 * v["exports_mn_usd"][1] * fx / v["gdp_mn_tl"][1], v["exports_mn_usd"][0], "exports_mn_usd", "gdp_mn_tl")
        if pop and v["exports_mn_usd"]:
            d("exports_per_capita", v["exports_mn_usd"][1] * 1e6 / pop[1], v["exports_mn_usd"][0], "exports_mn_usd", "population")
        if pop and v["insured_employees"]:
            d("insured_share", 100 * v["insured_employees"][1] / pop[1], v["insured_employees"][0], "insured_employees", "population")
        if pop and v["deposits_mn_tl"]:
            d("deposits_per_capita", v["deposits_mn_tl"][1] * 1e6 / pop[1], v["deposits_mn_tl"][0], "deposits_mn_tl", "population")
        if v["deposits_mn_tl"] and v["loans_mn_tl"] and v["deposits_mn_tl"][1] > 0:
            d("loan_deposit", 100 * v["loans_mn_tl"][1] / v["deposits_mn_tl"][1], v["loans_mn_tl"][0], "loans_mn_tl", "deposits_mn_tl")
        if v["m2_price_tl"] and v["rent_m2_tl"] and v["avg_wage_tl"]:
            a = e.housing_affordability(m2_price=v["m2_price_tl"][1], rent_m2=v["rent_m2_tl"][1],
                                        monthly_wage=v["avg_wage_tl"][1], dwelling_m2=100)
            deps = ("m2_price_tl", "rent_m2_tl", "avg_wage_tl")
            d("gross_rent_yield", 100 * a["gross_yield"], v["rent_m2_tl"][0], "m2_price_tl", "rent_m2_tl")
            d("amortization_years", a["amortization_years"], v["rent_m2_tl"][0], "m2_price_tl", "rent_m2_tl")
            d("price_to_wage_years", a["price_to_annual_wage"], v["avg_wage_tl"][0], *deps)
            d("rent_to_wage", 100 * a["rent_to_wage"], v["avg_wage_tl"][0], *deps)
        if pop and v["cars"]:
            d("cars_per_1000", 1000 * v["cars"][1] / pop[1], v["cars"][0], "cars", "population")
        if bist:
            out["listed_companies"] = {"value": len(bist.get(p, [])), "year": "liste", "sample": False}
        if pop and v["deposits_mn_tl"] and v["m2_price_tl"]:
            hs = v["household_size"][1] if v["household_size"] else WEALTH_DEFAULTS["household_size"]
            w = e.province_wealth(population=pop[1], deposits_tl=v["deposits_mn_tl"][1] * 1e6, m2_price=v["m2_price_tl"][1],
                                  household_size=hs, ownership_rate=WEALTH_DEFAULTS["ownership_rate"],
                                  dwelling_m2=WEALTH_DEFAULTS["dwelling_m2"],
                                  household_deposit_share=WEALTH_DEFAULTS["household_deposit_share"])
            deps = ("population", "deposits_mn_tl", "m2_price_tl")
            d("wealth_per_household", w["per_household"], v["deposits_mn_tl"][0], *deps)
            d("wealth_total_bn", w["total"] / 1e9, v["deposits_mn_tl"][0], *deps)
            if v["income_gini"]:
                ineq = e.wealth_inequality(income_gini=v["income_gini"][1], multiplier=WEALTH_DEFAULTS["inequality_multiplier"])
                d("wealth_gini", ineq["wealth_gini"], v["income_gini"][0], "income_gini")
                d("top10_share", 100 * ineq["top10_share"], v["income_gini"][0], "income_gini")
                d("wealth_median_hh", w["per_household"] * ineq["median_to_mean"], v["deposits_mn_tl"][0], *deps, "income_gini")
        provinces.append({"plaka": p, "name": NAMES[p - 1], "region": REGION_OF[p], "values": out,
                          "companies": bist.get(p, [])})

    # Household gold: national total (assumption) split by households x wealth^beta.
    with_w = [x for x in provinces if "wealth_per_household" in x["values"]]
    if with_w:
        hh = [x["values"]["population"]["value"] / (x["values"]["household_size"]["value"] if "household_size" in x["values"]
                                                    else WEALTH_DEFAULTS["household_size"]) for x in with_w]
        alloc = e.gold_allocation(hh, [x["values"]["wealth_per_household"]["value"] for x in with_w],
                                  beta=WEALTH_DEFAULTS["gold_beta"], total=WEALTH_DEFAULTS["gold_total_tonnes"])
        for x, h, t in zip(with_w, hh, alloc):
            smp = x["values"]["wealth_per_household"]["sample"]
            x["values"]["gold_tonnes"] = {"value": t, "year": "varsayım", "sample": smp}
            x["values"]["gold_per_household_g"] = {"value": t * 1e6 / h, "year": "varsayım", "sample": smp}
            if gold_gram_tl:
                x["values"]["gold_value_bn"] = {"value": t * 1e6 * gold_gram_tl / 1e9, "year": "varsayım", "sample": smp or gold_sample}

    return {
        "indicators": [{"id": k, "label": l, "unit": u, "group": g, "source": s, "kind": kind,
                        "sample": (sample_flag.get(k, False) if kind == "observed" else None)}
                       for k, (l, u, g, s, kind) in INDICATORS.items()],
        "wealth_defaults": WEALTH_DEFAULTS,
        "gold_gram_tl": gold_gram_tl,
        "has_company_list": bool(bist),
        "sample": any(sample_flag.values()),
        "provinces": provinces,
    }
