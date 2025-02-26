import re
from json import loads
from pathlib import Path

from requests_mock import GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers.US_PJM import fetch_production, fetch_wind_solar_forecasts

base_path_to_mock = Path("parsers/test/mocks/US_PJM")


def test_production(adapter, session, snapshot):
    settings = Path(base_path_to_mock, "settings.json")
    adapter.register_uri(
        GET,
        "https://dataminer2.pjm.com/config/settings.json",
        json=loads(settings.read_text()),
    )

    data = Path(base_path_to_mock, "gen_by_fuel.json")
    adapter.register_uri(
        GET,
        re.compile(
            r"https://us-ca-proxy-jfnx5klx2a-uw\.a\.run\.app/api/v1/gen_by_fuel.*"
        ),
        json=loads(data.read_text()),
    )

    assert snapshot == fetch_production(
        zone_key=ZoneKey("US-MIDA-PJM"),
        session=session,
    )


def test_fetch_wind_solar_forecasts(adapter, session, snapshot):
    # Mock the settings.json request
    settings = Path(base_path_to_mock, "settings.json")
    adapter.register_uri(
        GET,
        "https://dataminer2.pjm.com/config/settings.json",
        json=loads(settings.read_text()),
    )

    # Mock wind forecast request
    data_wind = Path(
        base_path_to_mock, "pjm_wind_forecast_2025-02-24T00:00:00.0000000.json"
    )
    adapter.register_uri(
        GET,
        re.compile(
            r"https://us-ca-proxy-jfnx5klx2a-uw\.a\.run\.app/api/v1/hourly_wind_power_forecast.*"
        ),
        json=loads(data_wind.read_text()),
    )

    # Mock solar forecast request
    data_solar = Path(
        base_path_to_mock, "pjm_solar_forecast_2025-02-24T00:00:00.0000000.json"
    )
    adapter.register_uri(
        GET,
        re.compile(
            r"https://us-ca-proxy-jfnx5klx2a-uw\.a\.run\.app/api/v1/hourly_solar_power_forecast.*"
        ),
        json=loads(data_solar.read_text()),
    )

    # Run function under test
    assert snapshot == fetch_wind_solar_forecasts(
        zone_key=ZoneKey("US-MIDA-PJM"),
        session=session,
    )
