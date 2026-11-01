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
    {"id": "usd", "label": "Dolar", "kind": "tl_level", "series": "usdtry"},
    {"id": "eur", "label": "Euro", "kind": "tl_level", "series": "eurtry"},
    {"id": "gold", "label": "Gram Altın", "kind": "tl_level", "series": "gold_gram_tl"},
    {"id": "bist100", "label": "BIST 100", "kind": "tl_level", "series": "bist100"},
    {"id": "sp500", "label": "S&P 500", "kind": "usd_level", "series": "sp500_usd"},
]
