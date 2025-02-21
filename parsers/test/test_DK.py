from datetime import datetime
from importlib import resources
from json import loads

import pytest
from requests_mock import GET

from parsers import DK


@pytest.fixture(autouse=True)
def mock_response(adapter):
    adapter.register_uri(
        GET,
        DK.EXCHANGE_URL,
        json=loads(
            resources.files("parsers.test.mocks.DK")
            .joinpath("ElectricityProdex5MinRealtime.json")
            .read_text()
        ),
    )

    adapter.register_uri(
        GET,
        DK.FORECAST_URL,
        json=loads(
            resources.files("parsers.test.mocks.DK")
            .joinpath("Forecasts_5Min.json")
            .read_text()
        ),
    )


def test_fetch_exchange(session, snapshot):
    target_datetime = datetime(2025, 2, 21)

    assert snapshot == DK.fetch_exchange(
        "DK-DK2",
        "SE-SE4",
        session=session,
        target_datetime=target_datetime,
    )


def test_fetch_forecast(session, snapshot):
    target_datetime = datetime(2025, 2, 21)

    assert snapshot == DK.fetch_wind_solar_forecasts(
        "DK-DK1",
        session=session,
        target_datetime=target_datetime,
    )
