#!/usr/bin/env python3


"""Real time parser for the New England ISO (NEISO) area."""

import io
import time
from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    ProductionMix,
    StorageMix,
)
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency

US_NEISO_KEY = ZoneKey("US-NE-ISNE")
SOURCE = "iso-ne.com"

url = "https://www.iso-ne.com/ws/wsclient"

generation_mapping = {
    "Coal": "coal",
    "NaturalGas": "gas",
    "Wind": "wind",
    "Hydro": "hydro",
    "Nuclear": "nuclear",
    "Wood": "biomass",
    "Oil": "oil",
    "Refuse": "biomass",
    "LandfillGas": "biomass",
    "Solar": "solar",
}


def get_json_data(
    target_datetime: datetime | None, params, session: Session | None = None
) -> dict:
    """Fetches json data for requested params and target_datetime using a post request."""

    epoch_time = str(int(time.time()))

    target_datetime = target_datetime or datetime.now(tz=timezone.utc)
    target_ne = target_datetime.astimezone(tz=ZoneInfo("America/New_York"))
    target_ne_day = target_ne.strftime("%m/%d/%Y")

    postdata = {
        "_nstmp_formDate": epoch_time,
        "_nstmp_startDate": target_ne_day,
        "_nstmp_endDate": target_ne_day,
        "_nstmp_twodays": "false",
        "_nstmp_showtwodays": "false",
    }
    postdata.update(params)

    s = session or Session()

    req = s.post(url, data=postdata)
    json_data = req.json()
    raw_data = json_data[0]["data"]

    return raw_data


def production_data_processer(
    zone_key: ZoneKey, raw_data: dict | list, logger: Logger
) -> ProductionBreakdownList:
    """
    Takes raw json data and removes unnecessary keys.
    Separates datetime key and converts to a datetime object.
    """

    other_keys = {"BeginDateMs", "Renewables", "BeginDate", "Other"}
    known_keys = generation_mapping.keys() | other_keys

    unmapped = set()

    production_breakdowns = ProductionBreakdownList(logger)
    counter = 0
    for datapoint in raw_data:
        current_keys = datapoint.keys() | set()
        unknown_keys = current_keys - known_keys
        unmapped = unmapped | unknown_keys

        keys_to_remove = {"BeginDateMs", "Renewables"} | unknown_keys
        for k in keys_to_remove:
            datapoint.pop(k, None)

        time_string = datapoint.pop("BeginDate", None)
        if time_string:
            dt = datetime.fromisoformat(time_string)
        else:
            counter += 1
            logger.warning(
                f"Skipping {zone_key} datapoint missing timestamp.",
                extra={"zone_key": zone_key},
            )
            continue

        # neiso storage flow signs are opposite to EM
        battery_storage = -1 * datapoint.pop("Other", 0.0)
        storage_mix = StorageMix(battery=battery_storage, hydro=None)

        production_mix = ProductionMix()
        for k, v in datapoint.items():
            production_mix.add_value(
                mode=generation_mapping[k], value=v, correct_negative_with_zero=v > -5
            )

        production_breakdowns.append(
            zoneKey=zone_key,
            datetime=dt,
            source=SOURCE,
            production=production_mix,
            storage=storage_mix,
        )

    for key in unmapped:
        logger.warning(
            f"Key '{key}' in {zone_key} is not mapped to type.",
            extra={"zone_key": zone_key},
        )

    if counter > 0:
        logger.warning(
            f"Skipped {counter} {zone_key} datapoints that were missing timestamps.",
            extra={"zone_key": zone_key},
        )

    return production_breakdowns


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = US_NEISO_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known production mix (in MW) of a given country."""

    postdata = {
        "_nstmp_chartTitle": "Fuel+Mix+Graph",
        "_nstmp_requestType": "genfuelmix",
        "_nstmp_fuelType": "all",
        "_nstmp_height": "250",
    }

    production_json = get_json_data(target_datetime, postdata, session)
    production_breakdowns = production_data_processer(zone_key, production_json, logger)

    return production_breakdowns.to_list()


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known power exchange (in MW) between two zones."""
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))

    # For directions, note that ISO-NE always reports its import as negative

    if sorted_zone_keys == "CA-NB->US-NE-ISNE":
        # CA-NB->US-NEISO means import to NEISO should be positive
        multiplier = -1

        postdata = {"_nstmp_zone0": "4010"}  # ".I.SALBRYNB345 1"

    elif sorted_zone_keys == "CA-QC->US-NE-ISNE":
        # CA-QC->US-NEISO means import to NEISO should be positive
        multiplier = -1

        postdata = {
            "_nstmp_zone0": "4012",  # ".I.HQ_P1_P2345 5"
            "_nstmp_zone1": "4013",  # ".I.HQHIGATE120 2"
        }

    elif sorted_zone_keys == "US-NE-ISNE->US-NY-NYIS":
        # US-NEISO->US-NY means import to NEISO should be negative
        multiplier = 1

        postdata = {
            "_nstmp_zone0": "4014",  # ".I.SHOREHAM138 99"
            "_nstmp_zone1": "4017",  # ".I.NRTHPORT138 5"
            "_nstmp_zone2": "4011",  # ".I.ROSETON 345 1"
        }

    else:
        raise Exception(f"Exchange pair not supported: {sorted_zone_keys}")

    postdata["_nstmp_requestType"] = "externalflow"

    exchanges = ExchangeList(logger)
    exchange_data = get_json_data(target_datetime, postdata, session)
    for _, exchange_values in exchange_data.items():
        for datapoint in exchange_values:
            time_string = datapoint.pop("BeginDate", None)
            if time_string:
                dt = datetime.fromisoformat(time_string)
            else:
                logger.warning(
                    f"Skipping {sorted_zone_keys} datapoint missing timestamp.",
                    extra={"zone_key": sorted_zone_keys},
                )
                continue
            exchanges.append(
                zoneKey=sorted_zone_keys,
                datetime=dt,
                netFlow=datapoint["Actual"] * multiplier,
                source=SOURCE,
            )

    # This will merge exchanges with the same datetime
    exchanges = ExchangeList.merge_exchanges([exchanges], logger)

    return exchanges.to_list()


def fetch_wind_solar_forecasts(
    zone_key: ZoneKey = US_NEISO_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests wind and solar power forecast in MW for 7 days"""

    # Datetime
    target_datetime = (
        datetime.now(timezone.utc)
        if target_datetime is None
        else target_datetime.astimezone(timezone.utc)
    )
    target_datetime = target_datetime.astimezone(tz=ZoneInfo("America/New_York"))
    if (
        target_datetime.hour <= 10
    ):  # the data is updated every day at approximately 10:00:00-05:00
        target_datetime = target_datetime - timedelta(days=1)
    target_datetime_string = target_datetime.strftime("%Y%m%d")

    # Request url
    session = session or Session()
    merged_data = None
    for data_type in ["solar", "wind"]:
        # Get cookies by accessing the forecast pages
        session.get(
            "https://www.iso-ne.com/isoexpress/web/reports/operations/-/tree/seven-day-"
            + data_type
            + "-power-forecast"
        )
        response = session.get(
            "https://www.iso-ne.com/transform/csv/"
            + data_type[0]
            + "phf?start="
            + target_datetime_string
        )

        # Get dataframe
        df = pd.read_csv(
            io.StringIO(response.content.decode("utf8")),
            skiprows=[0, 1, 2, 3, 4, 5],
            skipfooter=1,
            engine="python",
        ).drop_duplicates()

        df = df.drop(columns=["D", "Date"])

        data = df.melt(
            id_vars=["Hour Ending"],
            var_name="Date",
            value_name=data_type,
        ).dropna(subset=[data_type])

        if merged_data is None:
            # For the first iteration (solar), just store the data
            merged_data = data
        else:
            # For the second iteration (wind), merge with the first data
            merged_data = pd.merge(
                merged_data, data, on=["Hour Ending", "Date"], how="outer"
            )

    # Combine Date and Hour Ending into a datetime iso column
    merged_data["datetime"] = pd.to_datetime(
        merged_data["Date"]
        + " "
        + (merged_data["Hour Ending"] - 1).astype(str)
        + ":00",
        format="%m/%d/%Y %H:%M",
    )
    merged_data["datetime_iso"] = merged_data["datetime"].dt.strftime(
        "%Y-%m-%dT%H:%M:%S"
    )
    data_final = merged_data[["datetime_iso", "solar", "wind"]]

    # All events with a datetime and a production breakdown
    all_production_events = data_final.copy()
    production_list = ProductionBreakdownList(logger)
    for _index, event in all_production_events.iterrows():
        event_datetime = datetime.fromisoformat(event["datetime_iso"]).astimezone(
            tz=ZoneInfo("America/New_York")
        )
        production_mix = ProductionMix()
        production_mix.add_value(
            "solar", event["solar"], correct_negative_with_zero=True
        )
        production_mix.add_value("wind", event["wind"], correct_negative_with_zero=True)
        production_list.append(
            zoneKey=zone_key,
            datetime=event_datetime,
            production=production_mix,
            source=SOURCE,
            sourceType=EventSourceType.forecasted,
        )
    return production_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    from pprint import pprint

    """
    print("fetch_production() ->")
    pprint(fetch_production())

    print(
        'fetch_production(target_datetime=datetime.fromisoformat("2017-12-31T12:00:00+00:00")) ->'
    )
    pprint(
        fetch_production(
            target_datetime=datetime.fromisoformat("2017-12-31T12:00:00+00:00")
        )
    )

    print(
        'fetch_production(target_datetime=datetime.fromisoformat("2007-03-13T12:00:00+00:00")) ->'
    )
    pprint(
        fetch_production(
            target_datetime=datetime.fromisoformat("2007-03-13T12:00:00+00:00")
        )
    )

    print(f'fetch_exchange("{US_NEISO_KEY}", "CA-QC") ->')
    pprint(fetch_exchange(US_NEISO_KEY, ZoneKey("CA-QC")))

    print(
        f'fetch_exchange("{US_NEISO_KEY}", "CA-QC", target_datetime=datetime.fromisoformat("2017-12-31T12:00:00+00:00")) ->'
    )
    pprint(
        fetch_exchange(
            US_NEISO_KEY,
            ZoneKey("CA-QC"),
            target_datetime=datetime.fromisoformat("2017-12-31T12:00:00+00:00"),
        )
    )

    print(
        f'fetch_exchange("{US_NEISO_KEY}", "CA-QC", target_datetime=datetime.fromisoformat("2007-03-13T12:00:00+00:00")) ->'
    )
    pprint(
        fetch_exchange(
            US_NEISO_KEY,
            ZoneKey("CA-QC"),
            target_datetime=datetime.fromisoformat("2007-03-13T12:00:00+00:00"),
        )
    )
    """

    print("fetch_wind_solar_forecasts()")
    pprint(fetch_wind_solar_forecasts())
