from requests import Session
from requests_mock import GET, Adapter

from electricitymap.contrib.lib.types import ZoneKey
from parsers.MN import NDC_GENERATION, fetch_exchange, fetch_production
from parsers.RU import BASE_EXCHANGE_URL


def test_production(snapshot):
    session = Session()
    adapter = Adapter()
    session.mount("https://", adapter)
    mock_file = open("parsers/test/mocks/MN/convertt.php", "rb")
    adapter.register_uri(
        GET,
        NDC_GENERATION,
        content=mock_file.read(),
    )

    production = fetch_production(
        zone_key=ZoneKey("MN"),
        session=session,
    )

    snapshot.assert_match(
        [
            {
                "datetime": element["datetime"].isoformat(),
                "production": element["production"],
                "source": element["source"],
                "zoneKey": element["zoneKey"],
                "sourceType": element["sourceType"].value,
            }
            for element in production
        ]
    )


def test_exchange(snapshot):
    session = Session()
    adapter = Adapter()
    session.mount("https://", adapter)
    mock_file = open("parsers/test/mocks/MN/convertt.php", "rb")
    adapter.register_uri(
        GET,
        NDC_GENERATION,
        content=mock_file.read(),
    )
    mock_file2 = open("parsers/test/mocks/MN/GetData.json", "rb")
    adapter.register_uri(
        GET,
        BASE_EXCHANGE_URL,
        content=mock_file2.read(),
    )
    exchange = fetch_exchange(
        zone_key1=ZoneKey("CN"),
        zone_key2=ZoneKey("MN"),
        session=session,
    )

    snapshot.assert_match(
        [
            {
                "datetime": element["datetime"].isoformat(),
                "source": element["source"],
                "netFlow": element["netFlow"],
                "sortedZoneKeys": element["sortedZoneKeys"],
                "sourceType": element["sourceType"].value,
            }
            for element in exchange
        ]
    )
