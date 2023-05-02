#!/usr/bin/env python3

# The arrow library is used to handle datetimes
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

import arrow
import pandas as pd
import pytz
from requests import Response, Session

from electricitymap.contrib.config import ZONES_CONFIG, ZoneKey
from electricitymap.contrib.lib.models.event_lists import TotalConsumptionList
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

# More info:
# https://www.bchydro.com/energy-in-bc/our_system/transmission/transmission-system/actual-flow-data.html

HISTORICAL_LOAD_REPORTS = "https://www.bchydro.com/content/dam/BCHydro/customer-portal/documents/corporate/suppliers/transmission-system/balancing_authority_load_data/Historical%20Transmission%20Data/BalancingAuthorityLoad{0}.xls"
TIMEZONE = pytz.timezone(ZONES_CONFIG.get(ZoneKey("CA-BC")).get("timezone"))
PUBLICATION_DELAY = timedelta(days=31)


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: ZoneKey,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    r = session or Session()
    consumption_list = TotalConsumptionList(logger)
    if target_datetime is None:
        start_date = datetime.now(tz=TIMEZONE) - PUBLICATION_DELAY - timedelta(days=1)
        end_date = datetime.now(tz=TIMEZONE)
    else:
        start_date = target_datetime - timedelta(days=1)
        end_date = target_datetime
    # If the range spans multiple years, we need to fetch each year separately.
    for year in range(start_date.year, end_date.year + 1):
        url = HISTORICAL_LOAD_REPORTS.format(year)
        response: Response = r.get(url)
        if not response.ok:
            raise ParserException(
                "CA_BC.py",
                "Could not fetch load report for year {0}".format(year),
                zone_key,
            )
        df = pd.read_excel(response.content, skiprows=3)
        df = df.rename(columns={"Date ?": "Date"})
        # The first hour of each day is set at 1 and the last at 24 so we need to subtract 1
        # to correctly align dates and hours.
        # Due to DST there might be some missing hours, we use shift_backward to fill them with the previous hour.
        df["datetime"] = pd.to_datetime(
            df["Date"] + " " + (df["HE"] - 1).astype("str"), format="%m/%d/%Y %H"
        ).dt.tz_localize(TIMEZONE, nonexistent="shift_backward")
        df = df.set_index("datetime")
        selected_times = df[start_date:end_date]
        for row in selected_times.iterrows():
            consumption_list.append(
                zoneKey=zone_key,
                datetime=row[0].to_pydatetime(),
                source="bchydro.com",
                consumption=row[1]["Control Area Load"],
            )
    return consumption_list.to_list()


def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known power exchange (in MW) between two countries."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    r = session or Session()
    url = "https://www.bchydro.com/bctc/system_cms/actual_flow/latest_values.txt"
    response = r.get(url)
    obj = response.text.split("\r\n")[1].replace("\r", "").split(",")

    datetime = arrow.get(
        arrow.get(obj[0], "DD-MMM-YY HH:mm:ss").datetime, TIMEZONE
    ).datetime

    sortedZoneKeys = "->".join(sorted([zone_key1, zone_key2]))

    if sortedZoneKeys == "CA-BC->US-BPA" or sortedZoneKeys == "CA-BC->US-NW-BPAT":
        netFlow = float(obj[1])
    elif sortedZoneKeys == "CA-AB->CA-BC":
        netFlow = -1 * float(obj[2])
    else:
        raise NotImplementedError("This exchange pair is not implemented")

    return {
        "datetime": datetime,
        "sortedZoneKeys": sortedZoneKeys,
        "netFlow": netFlow,
        "source": "bchydro.com",
    }


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_exchange(CA-BC, US-BPA) ->")
    print(fetch_exchange("CA-BC", "US-BPA"))
    print("fetch_exchange(CA-AB, CA-BC) ->")
    print(fetch_exchange("CA-AB", "CA-BC"))
    print("fetch_consumption(CA-BC) ->")
    print(
        fetch_consumption(
            ZoneKey("CA-BC"), target_datetime=datetime(2023, 3, 1, 0, 0, 0, 0, TIMEZONE)
        )
    )
