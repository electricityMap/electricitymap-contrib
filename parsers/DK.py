from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger

from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import EventSourceType, ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

EXCHANGE_MAPPING = {
    "DE->DK-DK1": {"id": "ExchangeGermany", "direction": 1, "priceArea": "DK1"},
    "DE->DK-DK2": {"id": "ExchangeGermany", "direction": 1, "priceArea": "DK2"},
    "DK-DK1->DK-DK2": {"id": "ExchangeGreatBelt", "direction": -1, "priceArea": "DK1"},
    "DK-DK1->NL": {"id": "ExchangeNetherlands", "direction": -1, "priceArea": "DK1"},
    "DK-DK1->NO-NO2": {"id": "ExchangeNorway", "direction": -1, "priceArea": "DK1"},
    "DK-DK1->SE-SE3": {"id": "ExchangeSweden", "direction": -1, "priceArea": "DK1"},
    "DK-DK2->SE-SE4": {"id": "ExchangeSweden", "direction": -1, "priceArea": "DK2"},
    "DK-BHM->SE-SE4": {"id": "BornholmSE4", "direction": -1, "priceArea": "DK2"},
}

FORCAST_PARSE_MAPPING = {
    "Offshore Wind": "wind",
    "Onshore Wind": "wind",
    "Solar": "solar",
}

FORCAST_AREA_MAPPING = {
    "DK-DK1": "DK1",
    "DK-DK2": "DK2",
}

EXCHANGE_URL = "https://api.energidataservice.dk/dataset/ElectricityProdex5MinRealtime"
FORECAST_URL = "https://api.energidataservice.dk/dataset/Forecasts_5Min"

SOURCE = "energidataservice.dk"


def fetch_data(
    zone_key: ZoneKey,
    session: Session | None,
    target_datetime: datetime | None,
    logger: Logger,
    is_forecast: bool = False,
) -> dict:
    """
    Helper function to fetch data from the API.
    """
    ses = session or Session()

    if target_datetime and target_datetime.tzinfo:
        # Data source doesn't support timezone aware
        # datetimes.
        target_datetime = target_datetime.replace(tzinfo=None)

    price_area = (
        FORCAST_AREA_MAPPING[zone_key]
        if is_forecast
        else EXCHANGE_MAPPING[zone_key]["priceArea"]
    )

    params = {
        "limit": 500,
        "filter": '{"PriceArea":"DK1"}'
        if price_area == "DK1"
        else '{"PriceArea":"DK2"}',
        "start": target_datetime.strftime("%Y-%m-%d") if target_datetime else None,
        "end": (target_datetime + timedelta(days=1)).strftime("%Y-%m-%d")
        if target_datetime
        else None,
    }
    response: Response = ses.get(
        FORECAST_URL if is_forecast else EXCHANGE_URL,
        params=params,
    )
    if response.ok:
        data = response.json()
        if data["total"] == 0:
            raise ParserException(
                parser="DK.py",
                zone_key=zone_key,
                message=f"No exchange data was returned for {target_datetime.date() or datetime.now().date()}",
            )

        else:
            return data
    else:
        raise ParserException(
            parser="DK.py",
            zone_key=zone_key,
            message=f"No exchange data was returned for {target_datetime.date() or datetime.now().date()}",
        )


def flow(sorted_keys: ZoneKey, datapoint: dict) -> int | float | None:
    """
    Helper function to extract the net flow from a datapoint.
    """
    if sorted_keys == "DK-DK2->SE-SE4":
        # Exchange from Bornholm to Sweden is included in "ExchangeSweden"
        # but Bornholm island is reported separately from DK-DK2 in Electricity Maps
        return (
            datapoint[EXCHANGE_MAPPING["DK-DK2->SE-SE4"]["id"]]
            * EXCHANGE_MAPPING["DK-DK2->SE-SE4"]["direction"]
            - datapoint[EXCHANGE_MAPPING["DK-BHM->SE-SE4"]["id"]]
            * EXCHANGE_MAPPING["DK-BHM->SE-SE4"]["direction"]
            if datapoint[EXCHANGE_MAPPING["DK-BHM->SE-SE4"]["id"]] is not None
            and datapoint[EXCHANGE_MAPPING["DK-DK2->SE-SE4"]["id"]] is not None
            else None
        )
    else:
        return (
            datapoint[EXCHANGE_MAPPING[sorted_keys]["id"]]
            * EXCHANGE_MAPPING[sorted_keys]["direction"]
            if datapoint[EXCHANGE_MAPPING[sorted_keys]["id"]]
            else None
        )


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    sorted_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    data = fetch_data(sorted_keys, session, target_datetime, logger)
    all_exchange_data = ExchangeList(logger)

    if sorted_keys not in EXCHANGE_MAPPING:
        raise ParserException(
            "DK.py",
            sorted_keys,
            "Only able to fetch data for exchanges that are connected to Denmark (DK-DK1, DK-DK2, DK-BHM)",
        )
    else:
        for datapoint in data["records"]:
            all_exchange_data.append(
                zoneKey=sorted_keys,
                datetime=datetime.fromisoformat(datapoint["Minutes5UTC"]).replace(
                    tzinfo=timezone.utc
                ),
                netFlow=flow(sorted_keys, datapoint),
                source=SOURCE,
            )
        return all_exchange_data.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_wind_solar_forecasts(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    data = fetch_data(zone_key, session, target_datetime, logger, True)

    # Production mixs by datetime
    productionMixs = {}
    for datapoint in data["records"]:
        date_time = datetime.fromisoformat(datapoint["Minutes5UTC"]).replace(
            tzinfo=timezone.utc
        )
        if date_time not in productionMixs:
            productionMixs[date_time] = ProductionMix()

        productionMixs[date_time].add_value(
            FORCAST_PARSE_MAPPING[datapoint["ForecastType"]],
            datapoint["ForecastCurrent"],
        )

    forecast = ProductionBreakdownList(logger=logger)
    for date_time, productionMix in productionMixs.items():
        forecast.append(
            zoneKey=zone_key,
            production=productionMix,
            datetime=date_time,
            source=SOURCE,
            sourceType=EventSourceType.forecasted,
        )

    return forecast.to_list()


if __name__ == "__main__":
    print("fetch_exchange(DK-DK1, DE) ->")
    print(fetch_exchange("DK-DK2", "SE-SE4"))

    print("fetch_forecasts(DK-DK1) ->")
    print(fetch_wind_solar_forecasts(ZoneKey("DK-DK1")))
