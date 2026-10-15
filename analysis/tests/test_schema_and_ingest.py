import pytest

from analysis import schema
from analysis.ingest.cpi import parse_monthly, season_index
from analysis.ingest.transfermarkt import parse_money_eur
from analysis.scripts.fetch_manager_images import is_free


def test_money_parsing_distinguishes_free_from_unknown() -> None:
    assert parse_money_eur("€12.85m") == 12_850_000
    assert parse_money_eur("€3.77bn") == 3_770_000_000
    assert parse_money_eur("€500k") == 500_000
    assert parse_money_eur("free transfer") == 0.0
    assert parse_money_eur("?") is None
    assert parse_money_eur("-") is None
    assert parse_money_eur("Loan fee: €1.00m") is None


def test_cpi_season_index() -> None:
    raw = b'"Title","CPI"\n"2020 JUL","100"\n"2021 JAN","102"\n"2021 JUL","104"\n"2022 JAN","110"\n'
    idx = season_index(parse_monthly(raw)).set_index("season")
    assert idx.loc[2020, "cpi_season"] == 101
    assert abs(idx.loc[2020, "to_latest"] - 110 / 101) < 1e-12


def test_licence_filter() -> None:
    assert is_free("CC BY-SA 4.0") and is_free("CC0") and is_free("Public domain") and is_free("CC BY 2.0")
    assert not is_free("CC BY-NC 2.0") and not is_free("CC BY-ND 4.0") and not is_free("Fair use") and not is_free("")


def test_typescript_generation_covers_every_export() -> None:
    ts = schema.typescript_definitions()
    for td in schema.EXPORTS.values():
        assert f"export interface {td.__name__} {{" in ts
    assert "ga_per90: number | null;" in ts


def test_validate_rejects_missing_and_extra_fields() -> None:
    good = {"generated": "x", "sources": [{"name": "a", "url": "b", "used_for": "c", "coverage": "d", "status": "ok"}]}
    schema.validate(good, schema.SourcesData)
    with pytest.raises(TypeError):
        schema.validate({"generated": "x"}, schema.SourcesData)
    with pytest.raises(TypeError):
        schema.validate({**good, "sources": [{**good["sources"][0], "status": "maybe"}]}, schema.SourcesData)
