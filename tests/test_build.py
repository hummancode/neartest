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
    assert "asgari_ucret" in out["missing"]


def test_sample_build_flags_everything_as_sample():
    tablo, levels, groups, _ = build.build(allow_sample=True)
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
    tablo, levels, groups, _ = build.build(allow_sample=True)
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
