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
    tablo, levels = build.build(allow_sample=True)
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
