"""Tests for the JSON builder (no network, sample data only)."""

from pipeline import build


def test_levels_cut_at_common_end_month():
    data = {
        "cpi_tr": {"2024-01": 1.0, "2024-02": 2.0, "2024-03": 3.0},
        "usdtry": {"2024-01": 30.0, "2024-02": 31.0},
        "gold_gram_tl": {"2024-01": 2000.0, "2024-02": 2100.0, "2024-03": 2200.0},
    }
    is_sample = {n: False for n in build.SERIES} | {"gold_gram_tl": True}
    out = build.build_levels(data, is_sample, "2024-02")
    assert out["end_month"] == "2024-02"
    assert list(out["series"]["cpi_tr"]) == ["2024-01", "2024-02"]
    assert out["sample"] is True
    assert out["sources"]["gold_gram_tl"]["sample"] is True
    assert "min_wage_net" in out["missing"]


def test_sample_build_flags_everything_as_sample():
    tablo, levels, groups, *_ = build.build(allow_sample=True)
    if not build.RAW.exists():
        assert tablo["sample"] is True and levels["sample"] is True
    assert tablo["end_month"] == levels["end_month"]
    assert {r["id"] for r in tablo["rows"]} >= {"deposit", "usd", "gold"}


def test_generated_at_kept_when_content_unchanged(tmp_path):
    p = tmp_path / "x.json"
    build.write_if_changed(p, {"generated_at": "A", "v": 1})
    second = {"generated_at": "B", "v": 1}
    build.write_if_changed(p, second)
    assert second["generated_at"] == "A"
    third = {"generated_at": "C", "v": 2}
    build.write_if_changed(p, third)
    assert third["generated_at"] == "C"


def test_cpi_groups_output():
    tablo, levels, groups, *_ = build.build(allow_sample=True)
    assert len(groups["groups"]) == 12
    assert groups["end_month"] == tablo["end_month"]
    if not build.WEIGHTS_CSV.exists():
        assert groups["weights_sample"] is True and groups["sample"] is True
    assert abs(sum(g["weight"] for g in groups["groups"]) - 1.0) < 1e-9


def test_group_change_is_12_month_window():
    data = {"cpi_tr": {"2024-01": 100.0, "2025-01": 150.0}}
    for g in build.CPI_GROUPS:
        data[f"cpi_{g['id']}"] = {"2024-01": 100.0, "2025-01": 140.0}
    is_sample = {n: False for n in data}
    out = build.build_cpi_groups(data, is_sample, "2025-01", {g["id"]: 1 / 12 for g in build.CPI_GROUPS}, False)
    assert abs(out["headline_change_12m"] - 0.5) < 1e-12
    assert all(abs(g["change_12m"] - 0.4) < 1e-12 for g in out["groups"])
    assert out["sample"] is False


def test_real_rates_rows():
    data = {
        "cpi_tr": {"2024-01": 100.0, "2025-01": 140.0},
        "deposit_rate": {"2024-01": 0.45, "2025-01": 0.50},
        "credit_rate": {"2024-01": 0.55, "2025-01": 0.60},
    }
    is_sample = {n: False for n in data}
    out = build.build_real_rates(data, is_sample, "2025-01", months=13)
    first = out["rows"][0]
    assert first["month"] == "2025-01"
    assert abs(first["deposit_real_trailing"] - (1.5 / 1.4 - 1)) < 1e-12
    assert abs(first["credit_real_ex_post"] - (1.55 / 1.4 - 1)) < 1e-12
    assert out["rows"][12]["month"] == "2024-01" and out["rows"][12]["cpi_12m"] is None
    assert out["sample"] is False and out["ex_ante"] is None


def test_sources_carry_last_month():
    tablo, *_ = build.build(allow_sample=True)
    for src in tablo["sources"].values():
        assert len(src["last_month"]) == 7 and src["last_month"][4] == "-"


def test_forward_fill_minimum_wage():
    out = build.forward_fill({"2024-01": 17000.0, "2024-04": 20000.0}, "2024-05")
    assert out == {"2024-01": 17000.0, "2024-02": 17000.0, "2024-03": 17000.0,
                   "2024-04": 20000.0, "2024-05": 20000.0}


def test_levels_include_min_wage_when_present():
    data = {
        "cpi_tr": {"2024-01": 1.0, "2024-02": 2.0},
        "usdtry": {"2024-01": 30.0, "2024-02": 31.0},
        "gold_gram_tl": {"2024-01": 2000.0, "2024-02": 2100.0},
        "min_wage_net": {"2024-01": 17002.12},
    }
    out = build.build_levels(data, {n: False for n in data}, "2024-02")
    assert out["series"]["min_wage_net"] == {"2024-01": 17002.12, "2024-02": 17002.12}
    assert out["missing"] == []


def test_manual_csv_is_used_and_scaled(tmp_path, monkeypatch):
    # A rate series given in percent in a manual CSV must arrive as a decimal.
    (tmp_path / "deposit_rate.csv").write_text("Tarih;TP_X\n2024-1;45,5\n2024-2;46\n", encoding="utf-8")
    (tmp_path / "deposit_rate.meta.json").write_text('{"source": "TCMB EVDS (web)", "code": "TP.TEST"}', encoding="utf-8")
    monkeypatch.setattr(build, "RAW", tmp_path / "no-raw")
    monkeypatch.setattr(build.manual, "MANUAL", tmp_path)
    monkeypatch.setattr(build, "META", {k: dict(v) for k, v in build.META.items()})
    monkeypatch.setattr(build, "ORIGIN", {})
    data, is_sample = build.load_series(allow_sample=True)
    assert abs(data["deposit_rate"]["2024-01"] - 0.455) < 1e-12
    assert is_sample["deposit_rate"] is False and is_sample["cpi_tr"] is True
    assert build.ORIGIN["deposit_rate"] == "manual"
    assert build.src("deposit_rate", is_sample)["code"] == "TP.TEST"
    assert "min_wage_net" not in data and build.ORIGIN["min_wage_net"] == "missing"


def test_status_lists_every_series_with_origin():
    _, _, _, _, status, *_ = build.build(allow_sample=True)
    names = {r["name"] for r in status["rows"]}
    assert {"cpi_tr", "deposit_rate", "cpi_food", "min_wage_net"} <= names
    assert all(r["origin"] in ("evds", "manual", "sample", "missing") for r in status["rows"])
    assert sum(status["counts"].values()) == len(status["rows"])


def test_paths_end_values_match_reel_tablo():
    tablo, _, _, _, _, paths, *_ = build.build(allow_sample=True)
    for row in tablo["rows"]:
        for w in row["windows"]:
            p = paths["assets"][row["id"]]["windows"][str(w["years"])]
            assert abs(p["real"][-1] / 100 - 1 - w["real_tl"]) < 1e-5
            assert abs(p["usd"][-1] / 100 - 1 - w["usd"]) < 1e-5
            assert len(p["months"]) == 12 * w["years"] + 1


def test_prices_are_contiguous_and_tl_is_flat():
    *_, prices, _ = build.build(allow_sample=True)
    ids = {i["id"] for i in prices["instruments"]}
    assert {"tl", "cpi", "gold", "car", "house_ist"} <= ids
    assert "min_wage" not in ids or "min_wage_net" in build.ORIGIN
    assert set(prices["series"]["tl"]["values"]) == {1.0}
    for sid, s in prices["series"].items():
        last = build.e.shift_month(s["start"], len(s["values"]) - 1)
        assert last == prices["end_month"], sid


def test_housing_gold_return_is_currency_return():
    *_, housing = build.build(allow_sample=True)
    ist = next(c for c in housing["cities"] if c["id"] == "ist")
    w = ist["sources"]["kfe"]["windows"][0]
    assert w["years"] == 1 and w["gold"] is not None
    assert housing["reference"]["deposit_rate"] is not None


def test_housing_adds_betam_when_present():
    *_, base_housing = build.build(allow_sample=True)
    data, is_sample = build.load_series(allow_sample=True)
    data = dict(data)
    data["betam_sale_ist"] = dict(data["house_ist"])        # stand-in values, test only
    data["betam_rent_ist"] = {m: v * 2 for m, v in data["rent_cpi"].items()}
    out = build.build_housing(data, is_sample, base_housing["end_month"])
    ist = next(c for c in out["cities"] if c["id"] == "ist")
    assert set(ist["sources"]) == {"kfe", "betam"}
    assert abs(ist["rent_12m_betam"] - out["reference"]["rent_12m"]) < 1e-12   # x2 scaling cancels
    ank = next(c for c in out["cities"] if c["id"] == "ank")
    assert set(ank["sources"]) == {"kfe"} and ank["rent_12m_betam"] is None


def test_car_new_from_basket(tmp_path, monkeypatch):
    (tmp_path / "car_new_basket.csv").write_text("Ay;Model;Fiyat\n2024-1;A;100\n2024-1;B;200\n2024-2;A;110\n2024-2;B;180\n", encoding="utf-8")
    monkeypatch.setattr(build, "RAW", tmp_path / "no-raw")
    monkeypatch.setattr(build.manual, "MANUAL", tmp_path)
    monkeypatch.setattr(build, "META", {k: dict(v) for k, v in build.META.items()})
    monkeypatch.setattr(build, "ORIGIN", {})
    data, _ = build.load_series(allow_sample=True)
    assert abs(data["car_new"]["2024-02"] - 100 * 0.99 ** 0.5) < 1e-9
    assert build.ORIGIN["car_new"] == "manual"
