"""Which data series the site uses and where each comes from.

`code` is the EVDS series code. Codes marked `verified=False` have NOT been
checked against EVDS yet: run `python -m pipeline.discover` with an API key and
fill them in. Never guess a code.
"""

SERIES = {
    "usdtry": {
        "label": "USD/TRY",
        "source": "TCMB EVDS",
        "code": "TP.DK.USD.A.YTL",   # appears in the evds library's own example
        "verified": False,           # still confirm frequency/aggregation with a real call
        "unit": "TL",
    },
    "eurtry": {
        "label": "EUR/TRY",
        "source": "TCMB EVDS",
        "code": "TP.DK.EUR.A.YTL",   # appears in the evds library's own example
        "verified": False,
        "unit": "TL",
    },
    "cpi_tr": {
        "label": "TÜFE (2003=100)",
        "source": "TÜİK, TCMB EVDS üzerinden",
        "code": None,
        "verified": False,
        "unit": "endeks",
    },
    "deposit_rate": {
        "label": "TL mevduat faizi (ağırlıklı ortalama, yıllık)",
        "source": "TCMB EVDS",
        "code": None,
        "verified": False,
        "unit": "% yıllık",
        "scale": 0.01,   # EVDS/CSV give percent (45.5); the engine wants 0.455
    },
    "credit_rate": {
        "label": "TL ihtiyaç kredisi faizi (ağırlıklı ortalama, yıllık)",
        "source": "TCMB EVDS",
        "code": None,             # consumer (ihtiyaç) loans — households are the audience; find the EVDS code
        "verified": False,
        "unit": "% yıllık",
        "scale": 0.01,
    },
    "gold_gram_tl": {
        "label": "Gram altın",
        "source": "Belirlenecek",
        "code": None,
        "verified": False,
        "unit": "TL",
    },
    "bist100": {
        "label": "BIST 100",
        "source": "Belirlenecek",
        "code": None,
        "verified": False,
        "unit": "endeks",
    },
    "sp500_usd": {
        "label": "S&P 500",
        "source": "Belirlenecek",
        "code": None,
        "verified": False,
        "unit": "USD",
    },
}

# Rows of the "Reel Tablo", in display order. `kind` tells the builder how to
# turn raw series into a TL price level.
ASSETS = [
    {"id": "deposit", "label": "TL Mevduat", "kind": "rate", "series": "deposit_rate"},
    {"id": "credit", "label": "TL Kredi (borç maliyeti)", "kind": "rate", "series": "credit_rate"},
    {"id": "usd", "label": "Dolar", "kind": "tl_level", "series": "usdtry"},
    {"id": "eur", "label": "Euro", "kind": "tl_level", "series": "eurtry"},
    {"id": "gold", "label": "Gram Altın", "kind": "tl_level", "series": "gold_gram_tl"},
    {"id": "bist100", "label": "BIST 100", "kind": "tl_level", "series": "bist100"},
    {"id": "sp500", "label": "S&P 500", "kind": "usd_level", "series": "sp500_usd"},
]

# CPI main expenditure groups (COICOP), used by the personal inflation page.
# Codes are NOT verified: find them with `python -m pipeline.discover "Tüketici Fiyat"`.
# TÜİK may publish a different group structure (e.g. COICOP 2018 with 13 groups);
# confirm against EVDS before filling codes in. Never guess.
CPI_GROUPS = [
    {"id": "food", "label": "Gıda ve alkolsüz içecekler"},
    {"id": "alcohol_tobacco", "label": "Alkollü içecekler ve tütün"},
    {"id": "clothing", "label": "Giyim ve ayakkabı"},
    {"id": "housing", "label": "Konut (kira, aidat, enerji, su)"},
    {"id": "furnishing", "label": "Mobilya ve ev eşyası"},
    {"id": "health", "label": "Sağlık"},
    {"id": "transport", "label": "Ulaştırma"},
    {"id": "communication", "label": "Haberleşme"},
    {"id": "recreation", "label": "Eğlence ve kültür"},
    {"id": "education", "label": "Eğitim"},
    {"id": "restaurants", "label": "Lokanta ve oteller"},
    {"id": "misc", "label": "Çeşitli mal ve hizmetler"},
]

CPI_GROUP_SERIES = {
    f"cpi_{g['id']}": {
        "label": f"TÜFE: {g['label']}",
        "source": "TÜİK, TCMB EVDS üzerinden",
        "code": None,
        "verified": False,
        "unit": "endeks",
    }
    for g in CPI_GROUPS
}

# Official group weights come from TÜİK's annual weight table. Until verified,
# they are read from data/manual/tufe_agirliklari.csv (columns: id,weight) if
# present, otherwise sample weights are used and flagged.
CPI_WEIGHTS_SOURCE = {
    "label": "TÜFE grup ağırlıkları",
    "source": "TÜİK (elle girilen CSV: data/manual/tufe_agirliklari.csv)",
    "code": None,
    "verified": False,
}

# Prices for the "X priced in Y" chart tool and the housing page. Codes NOT verified.
# Cars: no official TL price series exists; TÜİK's CPI sub-index for cars is the only
# official measure (quality-adjusted index, not list prices). Never scrape listing sites.
MARKET_SERIES = {
    "car_cpi": {
        "label": "TÜFE: Otomobil alt endeksi",
        "source": "TÜİK, TCMB EVDS üzerinden",
        "code": None,
        "verified": False,
        "unit": "endeks",
    },
    "rent_cpi": {
        "label": "TÜFE: Gerçek kira alt endeksi",
        "source": "TÜİK, TCMB EVDS üzerinden",
        "code": None,
        "verified": False,
        "unit": "endeks",
    },
    **{
        f"house_{key}": {
            "label": f"Konut Fiyat Endeksi — {name}",
            "source": "TCMB Konut Fiyat Endeksi (KFE), EVDS",
            "code": None,
            "verified": False,
            "unit": "endeks",
        }
        for key, name in (("tr", "Türkiye"), ("ist", "İstanbul"), ("ank", "Ankara"), ("izm", "İzmir"))
    },
}

# Macro indicators for the dashboard (Makro Pano) and co-movement tool. Codes NOT verified.
# kind: "rate" (%, bps, signed balances -> changes in points) or "level" (-> % changes).
# freq: "M" monthly, "Q" quarterly (keyed by quarter-end month), "A" annual (keyed YYYY-12).
# Values are stored in display units (4.5 = %4,5; 350 = 350 bps).
MACRO_SERIES = {
    "gdp_growth": {"label": "GSYH büyümesi (reel, yıllık)", "unit": "%", "kind": "rate", "freq": "Q",
                   "group": "Büyüme", "source": "TÜİK, TCMB EVDS üzerinden", "code": None, "verified": False},
    "gdp_usd_pc": {"label": "Kişi başı GSYH", "unit": "$", "kind": "level", "freq": "A",
                   "group": "Büyüme", "source": "TÜİK", "code": None, "verified": False},
    "unemployment": {"label": "İşsizlik oranı", "unit": "%", "kind": "rate", "freq": "M",
                     "group": "İstihdam", "source": "TÜİK, TCMB EVDS üzerinden", "code": None, "verified": False},
    "current_account": {"label": "Cari denge (12 aylık toplam)", "unit": "milyar $", "kind": "rate", "freq": "M",
                        "group": "Dış denge", "source": "TCMB ödemeler dengesi, EVDS", "code": None, "verified": False},
    "reserves": {"label": "TCMB brüt rezervleri", "unit": "milyar $", "kind": "level", "freq": "M",
                 "group": "Dış denge", "source": "TCMB, EVDS", "code": None, "verified": False},
    "policy_rate": {"label": "Politika faizi", "unit": "%", "kind": "rate", "freq": "M",
                    "group": "Para politikası", "source": "TCMB, EVDS", "code": None, "verified": False},
    "cds_5y": {"label": "Türkiye 5 yıllık CDS primi", "unit": "bp", "kind": "rate", "freq": "M",
               "group": "Risk", "source": "Lisanslı veri — elle girilir (data/manual/cds_5y.csv)", "code": None,
               "verified": False},
    "budget_balance_gdp": {"label": "Bütçe dengesi / GSYH (12 aylık)", "unit": "%", "kind": "rate", "freq": "Q",
                           "group": "Kamu maliyesi", "source": "Hazine ve Maliye Bakanlığı, TÜİK", "code": None,
                           "verified": False},
}

CITIES = [
    {"id": "ist", "label": "İstanbul", "series": "house_ist", "betam_sale": "betam_sale_ist", "betam_rent": "betam_rent_ist"},
    {"id": "ank", "label": "Ankara", "series": "house_ank", "betam_sale": "betam_sale_ank", "betam_rent": "betam_rent_ank"},
    {"id": "izm", "label": "İzmir", "series": "house_izm", "betam_sale": "betam_sale_izm", "betam_rent": "betam_rent_izm"},
    {"id": "tr", "label": "Türkiye", "series": "house_tr", "betam_sale": "betam_sale_tr", "betam_rent": "betam_rent_tr"},
]

ALL_SERIES = SERIES | CPI_GROUP_SERIES | MARKET_SERIES | MACRO_SERIES

# Series used only when real data exists (data/raw or data/manual). Never sampled:
# the site shows them as missing instead of inventing numbers.
OPTIONAL_SERIES = {
    # New-car list prices from official dealer price lists. Either an index CSV
    # (data/manual/car_new.csv) or a basket of model prices
    # (data/manual/car_new_basket.csv: month;model;price) turned into a chained
    # Jevons index by the builder. Our own price tracker, not an official statistic.
    "car_new": {
        "label": "0 km otomobil liste fiyatı endeksi (resmi bayi fiyat listeleri)",
        "source": "Markaların resmi fiyat listeleri, elle derlenen sepet (data/manual/car_new_basket.csv)",
        "code": None,
        "verified": False,
        "unit": "endeks",
    },
    # BETAM (Bahçeşehir Üniversitesi) housing sale / rent indices from its monthly
    # reports, entered by hand. Check BETAM's terms and cite it when published.
    **{
        f"betam_{kind}_{key}": {
            "label": f"BETAM {'satılık' if kind == 'sale' else 'kiralık'} konut endeksi — {name}",
            "source": "BETAM konut piyasası raporları (elle girilir)",
            "code": None,
            "verified": False,
            "unit": "endeks veya TL/m²",
        }
        for kind in ("sale", "rent")
        for key, name in (("tr", "Türkiye"), ("ist", "İstanbul"), ("ank", "Ankara"), ("izm", "İzmir"))
    },
    "min_wage_net": {
        "label": "Net asgari ücret (aylık, bekâr işçi)",
        "source": "ÇSGB / Resmî Gazete (elle girilir: data/manual/min_wage_net.csv)",
        "code": None,
        "verified": False,
        "unit": "TL",
    },
}
