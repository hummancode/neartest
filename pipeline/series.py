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
        "label": "TL kredi faizi (ağırlıklı ortalama, yıllık)",
        "source": "TCMB EVDS",
        "code": None,             # which loan type (consumer / commercial) is still to be decided
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

ALL_SERIES = SERIES | CPI_GROUP_SERIES

# Series used only when real data exists (data/raw or data/manual). Never sampled:
# the site shows them as missing instead of inventing numbers.
OPTIONAL_SERIES = {
    "min_wage_net": {
        "label": "Net asgari ücret (aylık, bekâr işçi)",
        "source": "ÇSGB / Resmî Gazete (elle girilir: data/manual/min_wage_net.csv)",
        "code": None,
        "verified": False,
        "unit": "TL",
    },
}
