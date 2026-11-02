from pipeline import trade


def test_partners_latest_year_sorted():
    text = "yil;ulke;ihracat;ithalat\n2023;A;5;1\n2024;A;10;2\n2024;B;20;3\n"
    out = trade.parse_partners(text)
    assert out["year"] == "2024" and [x["name"] for x in out["items"]] == ["B", "A"]
    assert out["items"][0]["imports"] == 3.0


def test_products_parse():
    out = trade.parse_products("2024;Araçlar;1.234,5\n2024;Makine;2000\n")
    assert out["items"][0] == {"name": "Makine", "exports": 2000.0} and out["items"][1]["exports"] == 1234.5
