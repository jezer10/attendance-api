from src.api.v1.timezones import _build_timezone_catalog


def test_timezone_catalog_contains_expected_timezones():
    catalog = _build_timezone_catalog()

    # Known canonical zones should be present.
    assert any("America/Lima" in entry for entry in catalog)
    assert any("Europe/Madrid" in entry for entry in catalog)
    assert "UTC+00:00 UTC" in catalog


def test_timezone_catalog_entries_are_unique_and_formatted():
    catalog = _build_timezone_catalog()
    assert len(catalog) == len(set(catalog))

    sample = catalog[len(catalog) // 2]
    prefix, _, zone_name = sample.partition(" ")
    assert prefix.startswith("UTC")
    assert len(zone_name.strip()) > 0
