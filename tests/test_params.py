"""Regulated-parameter registry (mevzuat takibi)."""

from datetime import date

import pytest

from pipeline import params as P


def _reg(*history, every=30):
    return {"params": [{"id": "x", "label": "X", "unit": "%", "group": "G", "used_by": ["/kredi"],
                        "check_every_days": every, "official_sources": [], "history": list(history)}]}


def _entry(value, frm, status="candidate", checked="2026-10-01", url="https://www.resmigazete.gov.tr/x", by="test"):
    return {"value": value, "effective_from": frm, "status": status, "checked_at": checked, "checked_by": by,
            "source": {"title": "RG", "url": url}, "note": ""}


def test_current_is_latest_effective_entry():
    reg = _reg(_entry(10, "2023-01-01"), _entry(15, "2023-07-07"), _entry(20, "2027-01-01"))
    out = P.summarize(reg, today=date(2026, 11, 2))
    x = out["params"][0]
    assert x["current"]["value"] == 15            # 2027 entry not yet in force
    assert x["upcoming"]["value"] == 20


def test_stale_when_not_checked_recently():
    reg = _reg(_entry(15, "2023-07-07", checked="2026-08-01"), every=30)
    assert P.summarize(reg, today=date(2026, 11, 2))["params"][0]["stale"] is True
    reg = _reg(_entry(15, "2023-07-07", checked="2026-10-20"), every=30)
    assert P.summarize(reg, today=date(2026, 11, 2))["params"][0]["stale"] is False


def test_verified_requires_official_source_and_checker():
    with pytest.raises(P.ParamError):
        P.validate(_reg(_entry(15, "2023-07-07", status="verified", url="")))
    with pytest.raises(P.ParamError):
        P.validate(_reg(_entry(15, "2023-07-07", status="verified", by="")))
    P.validate(_reg(_entry(15, "2023-07-07", status="verified")))


def test_rejects_bad_status_and_dates():
    with pytest.raises(P.ParamError):
        P.validate(_reg(_entry(15, "2023-07-07", status="sanırım")))
    with pytest.raises(P.ParamError):
        P.validate(_reg(_entry(15, "07.07.2023")))


def test_unknown_effective_date_is_allowed_for_candidates():
    reg = _reg(_entry(15, None))
    x = P.summarize(reg, today=date(2026, 11, 2))["params"][0]
    assert x["current"]["value"] == 15


def test_real_registry_is_valid():
    P.validate(P.load())


def test_tariff_values_validated():
    from pipeline.params import _valid_value
    assert _valid_value(15) and _valid_value([[100, 0.1], [None, 0.2]])
    assert not _valid_value([[100, 0.1], [50, 0.2], [None, 0.3]])     # thresholds must increase
    assert not _valid_value([[100, 0.1], [200, 0.2]])                 # last bracket must be open-ended
    assert not _valid_value(True) and not _valid_value("15")
