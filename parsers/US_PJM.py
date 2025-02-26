"""Parser for the PJM area of the United States (US-MIDA-PJM)."""

import re
from datetime import datetime, time, timedelta, timezone
from itertools import groupby
from logging import Logger, getLogger
from operator import itemgetter
from typing import Any, Literal
from zoneinfo import ZoneInfo

import demjson3 as demjson
from bs4 import BeautifulSoup
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    PriceList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    ProductionMix,
    StorageMix,
)
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

PARSER = "US_PJM.py"
TIMEZONE = ZoneInfo("America/New_York")
ZONE_KEY = ZoneKey("US-MIDA-PJM")
# Used for production and consumption forecast data (https://dataminer2.pjm.com/list)
DATA_MINER_API_ENDPOINT = "https://api.pjm.com/api/v1/"


US_PROXY = "https://us-ca-proxy-jfnx5klx2a-uw.a.run.app"
DATA_PATH = "api/v1"

# Used for price data.
PRICE_API_ENDPOINT = "http://www.pjm.com/markets-and-operations.aspx"
CURRENCY = "USD"

SOURCE = "pjm.com"

ZONE_TO_PJM_INTERFACES = {
    ZoneKey("US-MIDW-MISO"): ["MISO"],  # "MISO LMP"
    # ?: ["DEOK|OVEC"],  # Ohio Valley Electric Corporation (OVEC)
    ZoneKey("US-MIDW-LGEE"): [
        "SOUTH|LGEE"
    ],  # Louisville Gas and Electric Company (LGEE)
    ZoneKey("US-TEN-TVA"): ["SOUTH|TVA"],  # Tennessee Valley Authority (TVA)
    ZoneKey("US-CAR-CPLW"): ["SOUTH|CPLW"],  # CPL Retail Energy West (CPLW)
    ZoneKey("US-CAR-DUK"): ["SOUTH|DUKE"],  # Duke Energy
    ZoneKey("US-CAR-CPLE"): ["SOUTH|CPLE"],  # CPL Retail Energy East (CPLE)
    ZoneKey("US-NY-NYIS"): [
        "NEPTUNE|SAYR",  # NYISO (Neptune)
        "LINDENVFT|LINDEN",  # NYISO (Linden)
        "HUDSONTP|HTP",  # NYISO (Hudson)
        "NYIS|NYIS",  # "NYISO LMP"
    ],
}

FUEL_MAPPING = {
    "Coal": "coal",
    "Gas": "gas",
    "Hydro": "hydro",
    "Multiple Fuels": "unknown",
    "Nuclear": "nuclear",
    "Oil": "oil",
    "Other": "unknown",
    "Other Renewables": "unknown",
    "Solar": "solar",
    "Storage": "battery",
    "Wind": "wind",
}


def _get_api_subscription_key(session: Session) -> str:
    response = session.get("https://dataminer2.pjm.com/config/settings.json")
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Could not get API key: {response.status_code}: {response.text}",
        )
    return response.json()["subscriptionKey"]


def _fetch_api_data(
    kind: Literal[
        "load_frcstd_7_day",
        "gen_by_fuel",
        "hourly_solar_power_forecast",
        "hourly_wind_power_forecast",
    ],
    params: dict,
    session: Session,
) -> dict:
    headers = {
        "Ocp-Apim-Subscription-Key": _get_api_subscription_key(session=session),
        "Accept-Encoding": "identity",
    }
    url = f"{US_PROXY}/{DATA_PATH}/{kind}"
    resp: Response = session.get(
        url=url, params={"host": "https://api.pjm.com", **params}, headers=headers
    )
    if resp.status_code == 200:
        data = resp.json()
        return data
    else:
        raise ParserException(
            PARSER,
            f"{kind} data is not available in the API: {resp.status_code}: {resp.text}",
        )


def fetch_consumption_forecast_7_days(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Gets consumption forecast for specified zone."""

    if target_datetime is not None:
        raise ParserException(
            PARSER, "This parser is not yet able to parse historical data", zone_key
        )

    session = session or Session()
    # startRow must be set if forecast_area is set. RTO_COMBINED is area for whole PJM zone.
    params = {"download": True, "startRow": 1, "forecast_area": "RTO_COMBINED"}
    data = _fetch_api_data(kind="load_frcstd_7_day", params=params, session=session)

    consumption_list = TotalConsumptionList(logger)
    for elem in data:
        utc_datetime = elem["forecast_datetime_beginning_utc"]
        consumption_list.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(utc_datetime).replace(tzinfo=timezone.utc),
            source=SOURCE,
            consumption=elem["forecast_load_mw"],
            sourceType=EventSourceType.forecasted,
        )
    return consumption_list.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Uses PJM API to get generation by fuel.

    We assume that storage is battery storage (see https://learn.pjm.com/energy-innovations/energy-storage)
    """
    target_datetime = (
        datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        if target_datetime is None
        else target_datetime.astimezone(timezone.utc)
    )

    session = session or Session()

    params = {
        "startRow": 1,
        "rowCount": 500,
        "fields": "datetime_beginning_utc,fuel_type,mw",
        "datetime_beginning_utc": target_datetime.strftime("%Y-%m-%dT%H:00:00.0000000"),
    }
    resp_data = _fetch_api_data(kind="gen_by_fuel", params=params, session=session)

    items = resp_data.get("items", [])

    if items == []:
        raise ParserException(
            parser=PARSER,
            message=f"{target_datetime}: Production data is not available in the API",
            zone_key=zone_key,
        )

    production_breakdown_list = ProductionBreakdownList(logger)
    for key, group in groupby(items, itemgetter("datetime_beginning_utc")):
        dt = datetime.fromisoformat(key).replace(tzinfo=timezone.utc)
        production = ProductionMix()
        storage = StorageMix()
        for data in group:
            mode = FUEL_MAPPING[data["fuel_type"]]
            value = data["mw"]
            if mode == "battery":
                storage.add_value(mode, -value)
            else:
                production.add_value(mode, value)
        production_breakdown_list.append(
            zoneKey=zone_key,
            datetime=dt,
            production=production,
            storage=storage,
            source=SOURCE,
        )

    return production_breakdown_list.to_list()


def fetch_wind_solar_forecasts(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Uses PJM API to request the wind and solar forecast (in MW) for a given date in hourly intervals."""

    session = session or Session()

    # Datetime
    target_datetime = (
        datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        if target_datetime is None
        else target_datetime.astimezone(timezone.utc)
    )

    # Config for url
    params = {
        "startRow": 1,
        "rowCount": 10000,
        "datetime_beginning_utc": target_datetime.strftime("%Y-%m-%dT%H:00:00.0000000"),
    }

    resp_data_wind = _fetch_api_data(
        kind="hourly_wind_power_forecast", params=params, session=session
    )
    items_wind = resp_data_wind.get("items", [])

    resp_data_solar = _fetch_api_data(
        kind="hourly_solar_power_forecast", params=params, session=session
    )
    items_solar = resp_data_solar.get("items", [])

    # Combine wind and solar data and sort by datetime_beginning_utc
    items = items_wind + items_solar
    items.sort(key=lambda x: (x["datetime_beginning_utc"], x["evaluated_at_utc"]))
    production_list = ProductionBreakdownList(logger)

    # Group by datetime_beginning_utc and get the last evaluated_at_utc entry for each group
    for datetime_utc, group in groupby(
        items, key=lambda x: x["datetime_beginning_utc"]
    ):
        group_list = list(group)
        wind_entries = [entry for entry in group_list if "wind_forecast_mwh" in entry]
        latest_entry_wind = max(wind_entries, key=lambda x: x["evaluated_at_utc"])
        solar_entries = [entry for entry in group_list if "solar_forecast_mwh" in entry]
        latest_entry_solar = max(solar_entries, key=lambda x: x["evaluated_at_utc"])

        production_mix = ProductionMix()
        production_mix.add_value(
            "solar",
            latest_entry_solar["solar_forecast_mwh"],
            correct_negative_with_zero=True,
        )
        production_mix.add_value(
            "wind",
            latest_entry_wind["wind_forecast_mwh"],
            correct_negative_with_zero=True,
        )

        production_list.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(datetime_utc).replace(tzinfo=timezone.utc),
            production=production_mix,
            source=SOURCE,
            sourceType=EventSourceType.forecasted,
        )

    return production_list.to_list()


def fetch_price(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the last known power price of a given country."""

    if target_datetime is not None:
        raise ParserException(
            PARSER, "This parser is not yet able to parse historical data", zone_key
        )

    session = session or Session()
    now = datetime.now(TIMEZONE)
    response = session.get(PRICE_API_ENDPOINT)
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching production error code: {response.status_code}: {response.text}",
            zone_key,
        )

    soup = BeautifulSoup(response.text, "html.parser")
    price_tag = soup.find("span", class_="rtolmpico")
    price_data = price_tag.find_next("h2")
    price_string = price_data.text.split("$")[1]
    price = float(price_string)

    price_list = PriceList(logger)
    price_list.append(
        zoneKey=zone_key,
        datetime=now.replace(microsecond=0),  # truncate to seconds,
        source=SOURCE,
        price=price,
        currency=CURRENCY,
    )
    return price_list.to_list()


def _get_interface_data(
    interface: str, session: Session
) -> list[tuple[datetime, float]]:
    """Fetches 5min data for any PJM interface in the current day."""

    # For some reason the US-MIDW-MISO data is on a chart at a different url
    if interface == "MISO":
        url = "https://www.pjm.com/Charts/MISO.aspx"
    else:
        url = f"http://www.pjm.com/Charts/InterfaceChartDM2.aspx?open={interface}"

    response = session.get(url)

    soup = BeautifulSoup(response.text, "html.parser")
    scripts = soup.find(
        "script",
        {
            "type": "text/javascript",
            "src": "/assets/js/Highcharts/HighCharts/highcharts.js",
        },
    )
    exchange_script = scripts.find_next_sibling("script")

    # x-axis (time)
    time_pattern = r"var timeArray = (\[(.*)\])"
    time_array = re.search(time_pattern, str(exchange_script)).group(1)
    time_vals = demjson.decode(time_array)

    # y-axis [right] (actual & scheduled load)
    load_pattern = r"var load = (\[(.*)\])"
    load = re.search(load_pattern, str(exchange_script)).group(1)
    load_actual = demjson.decode(load)[0]

    converted_flows = []
    today = datetime.combine(datetime.now(TIMEZONE), time(), tzinfo=TIMEZONE)
    for t, flow in zip(time_vals, load_actual, strict=True):
        # some tail values might be null
        if flow is None:
            continue

        # make sure to use %I and not %H for %p to take effect
        time_of_the_day = datetime.strptime(t, "%I:%M %p").replace(tzinfo=TIMEZONE)
        dt = today.replace(hour=time_of_the_day.hour, minute=time_of_the_day.minute)

        converted_flows.append((dt, float(flow)))

    return converted_flows


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the last known power exchange (in MW) between two zones."""

    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))

    if target_datetime is not None:
        raise ParserException(
            PARSER,
            "This parser is not yet able to parse historical data",
            sorted_zone_keys,
        )

    if not session:
        session = Session()

    # PJM reports exports as negative.
    direction = -1 if sorted_zone_keys.startswith(ZONE_KEY) else 1

    neighbour = zone_key2 if zone_key1 == ZONE_KEY else zone_key1
    interfaces = ZONE_TO_PJM_INTERFACES[neighbour]

    # get flow data from each interface with neighbour and merge
    session = session or Session()
    ungrouped_exchange_lists = []
    for interface in interfaces:
        exchange_list = ExchangeList(logger)

        interface_data = _get_interface_data(interface, session=session)
        for dt, net_flow in interface_data:
            exchange_list.append(
                zoneKey=sorted_zone_keys,
                datetime=dt,
                source=SOURCE,
                netFlow=direction * net_flow,
            )

        ungrouped_exchange_lists.append(exchange_list)

    return ExchangeList.merge_exchanges(ungrouped_exchange_lists, logger).to_list()


if __name__ == "__main__":
    # print("fetch_consumption_forecast_7_days() ->")
    # print(fetch_consumption_forecast_7_days())

    # print("fetch_production() ->")
    # print(fetch_production())

    # print("fetch_price() ->")
    # print(fetch_price())
    """
    for neighbor in [
        "US-CAR-DUK",
        "US-CAR-CPLE",
        "US-CAR-CPLW",
        "US-MIDW-LGEE",
        "US-MIDW-MISO",
        "US-NY-NYIS",
        "US-TEN-TVA",
    ]:
        print(f"fetch_exchange(US-MIDA-PJM, {neighbor}) ->")
        print(fetch_exchange(ZONE_KEY, ZoneKey(neighbor)))
"""
    print("fetch_wind_solar_forecasts() ->")
    print(fetch_wind_solar_forecasts())
