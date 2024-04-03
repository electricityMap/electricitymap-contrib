from importlib import resources
from json import loads

from freezegun import freeze_time
from requests import Session
from requests_mock import GET, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.ENTE import DATA_URL, fetch_exchange, fetch_production


class TestENTE(TestCase):
    def setUp(self):
        self.adapter = Adapter()
        self.session = Session()
        self.session.mount("https://", self.adapter)
        self.adapter.register_uri(
            GET,
            DATA_URL,
            json=loads(
                resources.files("parsers.test.mocks.ENTE")
                .joinpath("response_generic_20240403.json")
                .read_text()
            ),
        )

    @freeze_time("2024-04-03 14:37:00")
    def test_fetch_exchange(self):
        exchange = fetch_exchange(
            zone_key1=ZoneKey("CR"),
            zone_key2=ZoneKey("NI"),
            session=self.session,
        )

        self.assertMatchSnapshot(
            {
                "datetime": exchange["datetime"].isoformat(),
                "sortedZoneKeys": exchange["sortedZoneKeys"],
                "netFlow": exchange["netFlow"],
                "source": exchange["source"],
            }
        )

    def test_fetch_exchange_raises_exception_on_exchange_not_implemented(self):
        with self.assertRaises(
            NotImplementedError,
            msg="This exchange is not implemented.",
        ):
            fetch_exchange(
                zone_key1=ZoneKey("FR"),
                zone_key2=ZoneKey("GB"),
                session=self.session,
            )

    @freeze_time("2024-04-03 14:00:00")
    def test_fetch_production(self):
        production = fetch_production(
            zone_key=ZoneKey("HN"),
            session=self.session,
        )

        self.assertMatchSnapshot(
            {
                "datetime": production["datetime"].isoformat(),
                "zoneKey": production["zoneKey"],
                "production": production["production"],
                "source": production["source"],
            }
        )
