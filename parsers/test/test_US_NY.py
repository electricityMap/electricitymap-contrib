#!/usr/bin/env python3

"""Tests for US_NY.py"""

from freezegun import freeze_time

from electricitymap.contrib.lib.types import ZoneKey
from parsers import US_NY

MOCK_CSV_DATA = "parsers/test/mocks/US_NY/20250219isolf.csv"


def test_snapshot_fetch_consumption_forecast(adapter, session, snapshot):
    adapter.register_uri(
        "GET",
        "http://mis.nyiso.com/public/csv/isolf/20250219isolf.csv",
        text=MOCK_CSV_DATA,
    )

    with freeze_time("2025-02-19 00:00:00"):
        result = US_NY.fetch_consumption_forecast(
            zone_key=ZoneKey("US-NY-NYIS"),
            session=session,
        )

    # Assert the structure matches the snapshot
    assert snapshot == result
