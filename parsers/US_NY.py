#!/usr/bin/env python3

"""Real time parser for the state of New York."""

from collections import defaultdict
from datetime import datetime, timedelta
from logging import Logger, getLogger
from operator import itemgetter
from typing import Any
from urllib.error import HTTPError
from zoneinfo import ZoneInfo

import pandas as pd

# Pumped storage is present but is not split into a separate category.
from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import EventSourceType, ProductionMix
from parsers.lib.config import refetch_frequency

# Dual Fuel systems can run either Natural Gas or Oil, they represent
# significantly more capacity in NY State than plants that can only
# burn Natural Gas. When looking up fuel usage for NY in 2016 in
# https://www.eia.gov/electricity/data/state/annual_generation_state.xls
# 100 times more energy came from NG than Oil. That means Oil
# consumption in the Dual Fuel systems is roughly ~1%, and to a first
# approximation it's just Natural Gas.

SOURCE = "nyiso.com"
TIMEZONE = ZoneInfo("America/New_York")
ZONE = "US-NY-NYIS"

mapping = {
    "Dual Fuel": "gas",
    "Natural Gas": "gas",
    "Nuclear": "nuclear",
    "Other Fossil Fuels": "unknown",
    "Other Renewables": "unknown",
    "Wind": "wind",
    "Hydro": "hydro",
}


def read_csv_data(url: str):
    """Gets csv data from a url and returns a dataframe."""

    csv_data = pd.read_csv(url)

    return csv_data


def timestamp_converter(timestamp_string: str) -> datetime:
    """Converts timestamps in nyiso data into aware datetime objects."""
    try:
        dt_naive = datetime.strptime(timestamp_string, "%m/%d/%Y %H:%M:%S")
    except ValueError:
        dt_naive = datetime.strptime(timestamp_string, "%m/%d/%Y %H:%M")
    dt_aware = dt_naive.replace(tzinfo=TIMEZONE)

    return dt_aware


def data_parser(df, logger) -> list[tuple[datetime, ProductionMix]]:
    """
    Takes dataframe and loops over rows to form dictionaries consisting of datetime and generation type.
    Merges these dictionaries using datetime key.

    :return: list of tuples containing datetime and production.
    """

    chunks = []
    for row in df.itertuples():
        piece = {}
        piece["datetime"] = row[1]
        piece[row[3]] = row[4]
        chunks.append(piece)

    # Join dicts on shared 'datetime' keys.
    combine = defaultdict(dict)
    for elem in chunks:
        combine[elem["datetime"]].update(elem)

    ordered = sorted(combine.values(), key=itemgetter("datetime"))

    mapped_generation = []
    for item in ordered:
        mix = ProductionMix()
        dt = timestamp_converter(item.pop("datetime"))
        for key, val in item.items():
            try:
                mix.add_value(mapping[key], val)
            except KeyError:
                logger.warning("Unrecognized production key '%s'", key)

        mapped_generation.append((dt, mix))

    return mapped_generation


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey(ZONE),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known production mix (in MW) of a given zone."""
    if target_datetime is None:
        target_datetime = datetime.now(tz=TIMEZONE)
    else:
        # assume passed in correct timezone
        target_datetime = target_datetime.replace(tzinfo=TIMEZONE)

    if (datetime.now(tz=TIMEZONE) - target_datetime).days > 9:
        raise NotImplementedError(
            "you can get data older than 9 days at the "
            "url http://mis.nyiso.com/public/"
        )

    ny_date = target_datetime.strftime("%Y%m%d")
    mix_url = f"http://mis.nyiso.com/public/csv/rtfuelmix/{ny_date}rtfuelmix.csv"
    try:
        raw_data = read_csv_data(mix_url)
    except HTTPError:
        # this can happen when target_datetime has no data available
        return []

    clean_data = data_parser(raw_data, logger)

    production_breakdowns = ProductionBreakdownList(logger=logger)
    for dt, mix in clean_data:
        production_breakdowns.append(
            zoneKey=zone_key,
            datetime=dt,
            production=mix,
            source=SOURCE,
        )

    return production_breakdowns.to_list()


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known power exchange (in MW) between two zones."""
    url = (
        "http://mis.nyiso.com/public/csv/ExternalLimitsFlows/{}ExternalLimitsFlows.csv"
    )

    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    # In the source CSV, positive is flow into NY, negative is flow out of NY.
    # In Electricity Map, A->B means flow to B is positive.
    if (
        sorted_zone_keys == "US-NEISO->US-NY"
        or sorted_zone_keys == "US-NE-ISNE->US-NY-NYIS"
    ):
        direction = 1
        relevant_exchanges = ["SCH - NE - NY", "SCH - NPX_1385", "SCH - NPX_CSC"]
    elif sorted_zone_keys == "US-NY->US-PJM":
        direction = -1
        relevant_exchanges = [
            "SCH - PJ - NY",
            "SCH - PJM_HTP",
            "SCH - PJM_NEPTUNE",
            "SCH - PJM_VFT",
        ]
    elif sorted_zone_keys == "US-MIDA-PJM->US-NY-NYIS":
        direction = 1
        relevant_exchanges = [
            "SCH - PJ - NY",
            "SCH - PJM_HTP",
            "SCH - PJM_NEPTUNE",
            "SCH - PJM_VFT",
        ]
    elif sorted_zone_keys == "CA-ON->US-NY" or sorted_zone_keys == "CA-ON->US-NY-NYIS":
        direction = 1
        relevant_exchanges = ["SCH - OH - NY"]
    elif sorted_zone_keys == "CA-QC->US-NY" or sorted_zone_keys == "CA-QC->US-NY-NYIS":
        direction = 1
        relevant_exchanges = ["SCH - HQ_CEDARS", "SCH - HQ - NY"]
    else:
        raise NotImplementedError(f"Exchange pair not supported: {sorted_zone_keys}")

    if target_datetime is None:
        target_datetime = datetime.now(tz=TIMEZONE)
    ny_date = target_datetime.strftime("%Y%m%d")
    exchange_url = url.format(ny_date)

    try:
        exchange_data = read_csv_data(exchange_url)
    except HTTPError:
        # this can happen when target_datetime has no data available
        return None

    new_england_exs = exchange_data.loc[
        exchange_data["Interface Name"].isin(relevant_exchanges)
    ]
    consolidated_flows = new_england_exs.reset_index().groupby("Timestamp").sum()

    now = datetime.now(tz=TIMEZONE)

    exchange_5min = ExchangeList(logger)
    for row in consolidated_flows.itertuples():
        flow = float(row[3]) * direction
        # Timestamp for exchange does not include seconds.
        dt = timestamp_converter(row[0] + ":00")

        if (dt > now) and ((dt - now) < timedelta(seconds=300)):
            # NYISO exchanges CSV (and only the exchanges CSV) includes data
            # up to 5 minutes in the future (but only 5 minutes in the future).
            # This also happens on their official website.
            # Electricity Map raises error with data in the future, so skip
            # that datapoint. If it's more than 5 minutes in the future,
            # it's weird/unexpected and thus worthy of failure and logging.
            continue

        exchange_5min.append(
            source=SOURCE, datetime=dt, netFlow=flow, zoneKey=sorted_zone_keys
        )

    return exchange_5min.to_list()


def fetch_consumption_forecast(
    zone_key: ZoneKey = ZoneKey(ZONE),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the load forecast (in MW) for a given date in hourly intervals."""
    session = session or Session()

    # Datetime
    if target_datetime is None:
        target_datetime = datetime.now(tz=TIMEZONE)
    else:
        # assume passed in correct timezone
        target_datetime = target_datetime.replace(tzinfo=TIMEZONE)

    if (
        datetime.now(tz=TIMEZONE) - target_datetime
    ).days > 9:  # TODO: If datetime is previous to 9 days, it need to be implemented
        raise NotImplementedError(
            "you can get data older than 9 days at the "
            "url http://mis.nyiso.com/public/"
        )
    ny_date = target_datetime.strftime("%Y%m%d")

    # Request to the url
    target_url = f"http://mis.nyiso.com/public/csv/isolf/{ny_date}isolf.csv"
    df = pd.read_csv(target_url)

    # Add events consumption_list
    all_consumption_events = (
        df.copy()
    )  # all events with a datetime and a generation value
    consumption_list = TotalConsumptionList(logger)
    for _index, event in all_consumption_events.iterrows():
        event_datetime = timestamp_converter(event["Time Stamp"])
        consumption_list.append(
            zoneKey=zone_key,
            datetime=event_datetime,
            consumption=event["NYISO"],
            source=SOURCE,
            sourceType=EventSourceType.forecasted,
        )
    return consumption_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    from pprint import pprint

    """
    print("fetch_production() ->")
    pprint(fetch_production())

    print("fetch_production(target_datetime=datetime(2018, 3, 13, 12, 0)) ->")
    pprint(fetch_production(target_datetime=datetime(2018, 3, 13, 12, 0)))

    print("fetch_production(target_datetime=datetime(2007, 3, 13, 12)) ->")
    pprint(fetch_production(target_datetime=datetime(2007, 3, 13, 12)))

    print("fetch_exchange(US-NY, US-NEISO)")
    pprint(fetch_exchange("US-NY", "US-NEISO"))

    print('fetch_exchange("US-NY", "CA-QC")')
    pprint(fetch_exchange("US-NY", "CA-QC"))

    print(
        'fetch_exchange("US-NY", "CA-QC", target_datetime=datetime(2018, 3, 13, 12, 0))'
    )
    pprint(
        fetch_exchange("US-NY", "CA-QC", target_datetime=datetime(2018, 3, 13, 12, 0))
    )

    print(
        'fetch_exchange("US-NY", "CA-QC", target_datetime=datetime(2007, 3, 13, 12)))'
    )
    pprint(fetch_exchange("US-NY", "CA-QC", target_datetime=datetime(2007, 3, 13, 12)))
    """

    print("fetch_consumption_forecast() ->")
    pprint(fetch_consumption_forecast())
