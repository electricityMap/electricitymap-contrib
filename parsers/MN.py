#!/usr/bin/env python3

from datetime import datetime
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.parsers.RU import fetch_exchange as ru_fetch_exchange
from parsers.lib.exceptions import ParserException

NDC_API = "https://disnews.energy.mn/convertt.php"
TZ = ZoneInfo("Asia/Ulaanbaatar")  # UTC+8

# https://ndc.energy.mn/ provides a list with icons and numbers next to them,
# where the JSON response from https://disnews.energy.mn/convertt.php is used to
# populate the numbers. Below is a formatted JSON response from 2025-01-13:
#
#     {
#         "date": "2025-01-14 03:00:00",
#         "syssum": "1351.8",
#         "dts": 1061,
#         "sumnar": -0.5,
#         "sumsalhit": 128.6,
#         "energyimport": "162.7",
#         "t": "-20.2",
#         "Songino": "-23.9"
#     }
#
# Notes:
# - dts is assumed to be coal, as coal is reported as the main source of
#   electricity for mongolia.
# - Songino is ignored for now, but it seems to be a specific area of Mongolia.
#   Ideally we'd figure out if we should make use of this value.
# - t is temperature, and ignored.
#
JSON_API_MAPPING = {
    "date": "datetime",
    "syssum": "consumption",
    "energyimport": "import",  # positive = import
    "dts": "coal",
    "sumnar": "solar",
    "sumsalhit": "wind",
}


def _fetch_and_parse(session: Session) -> dict[str, Any]:
    """
    Fetches and parses consumption and production data from a JSON API seen used
    at https://ndc.energy.mn/.
    """
    response: Response = session.get(NDC_API)
    if not response.ok:
        raise ParserException(
            parser="MN.py",
            message=f"Data request did not succeed: {response.status_code}",
        )
    data = response.json()

    # validate that the expected and required keys are present
    received_keys = set(data.keys())
    expected_keys = set(JSON_API_MAPPING.keys())
    if not set(expected_keys).issubset(received_keys):
        missing = expected_keys - received_keys
        raise ParserException(
            parser="MN.py",
            message=f"Fetched JSON didn't include expected keys: {missing}",
        )

    # pick out relevant values into a new dictionary with keys with our names
    result = {JSON_API_MAPPING[k]: data[k] for k in expected_keys}

    # ensure that relevant values are set
    if None in result.values():
        raise ParserException(
            parser="MN.py",
            message=f"Fetched values contain null. Fetched data: {result}.",
        )

    # parse values
    for k, v in result.items():
        if k == "datetime":
            result[k] = datetime.fromisoformat(v).replace(tzinfo=TZ)
        else:
            result[k] = float(v)
    return result


def fetch_production(
    zone_key: ZoneKey = ZoneKey("MN"),
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates.")

    data = _fetch_and_parse(session)

    prod_mix = ProductionMix()
    prod_mix.add_value("coal", data["coal"])
    prod_mix.add_value("solar", data["solar"])
    prod_mix.add_value("wind", data["wind"])

    prod_breakdown_list = ProductionBreakdownList(logger)
    prod_breakdown_list.append(
        datetime=data["datetime"],
        zoneKey=zone_key,
        source="https://ndc.energy.mn/",
        production=prod_mix,
    )

    return prod_breakdown_list.to_list()


def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("MN"),
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates.")

    data = _fetch_and_parse(session)

    consumption_list = TotalConsumptionList(logger)
    consumption_list.append(
        datetime=data["datetime"],
        zoneKey=zone_key,
        consumption=data["consumption"],
        source="https://ndc.energy.mn/",
    )

    return consumption_list.to_list()


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates.")

    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))

    if sorted_zone_keys != "CN->MN":
        raise NotImplementedError(
            "This parser is only able to fetch CN->MN exchange data."
        )

    query_data = query(session, logger, ZoneKey("MN"))

    russia_data = ru_fetch_exchange("MN", "RU-2", session, logger=logger)

    exchange_list = ExchangeList(logger)

    for data in russia_data:
        if (
            data["datetime"] == query_data["time"]
            and data["sortedZoneKeys"] == "MN->RU-2"
            and "netFlow" in data.keys()
        ):
            exchange_list.append(
                datetime=query_data["time"],
                zoneKey=sorted_zone_keys,
                # We calculate the flow with the total imports and the MN->RU-2 exchange, as Mongolia has only two connections
                netFlow=query_data["importMW"] + data["netFlow"],
                source="https://ndc.energy.mn/",
            )

    return exchange_list.to_list()


if __name__ == "__main__":
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_consumption() ->")
    print(fetch_consumption())
