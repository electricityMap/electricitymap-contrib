#!/usr/bin/env python3

"""Parser for Moldova."""

from collections import namedtuple
from datetime import datetime
from logging import Logger, getLogger
from operator import attrgetter
from zoneinfo import ZoneInfo

from requests import Session

from parsers.lib.exceptions import ParserException

TZ = ZoneInfo("Europe/Chisinau")

# Supports the following formats:
# - type=csv for zip-data with semicolon-separated-values
# - type=array for a 2D json-array containing an array for each datapoint
# - type=html for a HTML-table (default when no type is given)
archive_base_url = "https://moldelectrica.md/utils/archive2.php?id=table&type=array"

# Fields that can be fetched from archive_url in order.
archive_fields = (
    "datetime",
    "consumption",
    "planned_consumption",
    "production",
    "planned_production",
    "tpp",  # production from thermal power plants
    "hpp",  # production from thermal power plants
    "res",  # production from renewable energy sources
    "exchange_UA_to_MD",
    "planned_exchange_UA_to_MD",
    "exchange_RO_to_MD",
    "planned_exchange_RO_to_MD",
)

# Datapoint in the archive-data.
ArchiveDatapoint = namedtuple("ArchiveDatapoint", archive_fields)

display_url = "http://www.moldelectrica.md/ro/activity/system_state"
data_url = "http://www.moldelectrica.md/utils/load5.php"

# Fields that can be fetched from data_url.
FIELD_LABEL_to_INDEX = {
    # individual plants production data
    "NHE Costeşti": 0,  # hydro [run-of-river]
    "CET Nord": 1,  # gas [CHPP]
    "NHE Dubăsari": 2,  # hydro
    "CET-2 Chişinău": 3,  # gas [CHPP]
    "CET-1 Chişinău": 4,  # gas [CHPP]
    "CERS Moldovenească": 5,  # gas [fuel mix: 99.94% gas, 0.01% coal, 0.05% oil (2020)]
    "Uşi": 6,  # exchange interface [RO]
    "Falciu": 7,  # exchange interface [RO]
    "Isaccea": 8,  # exchange interface [RO]
    # summary table
    "consumption": 9,
    "generation": 10,  # total [see below]
    "gas": 11,
    "hydro": 12,
    "biomass": 13,
    "solar": 14,
    "wind": 15,
    "sold": 16,  # total [see below]
    "exchange MD-UA": 17,
    "exchange MD-RO": 18,
    "utility frequency": 19,
}


# Further information on the equipment used at CERS Moldovenească can be found at:
# http://moldgres.com/o-predpriyatii/equipment
# Further information on the fuel-mix used at CERS Moldovenească can be found at:
# http://moldgres.com/search/%D0%9F%D1%80%D0%BE%D0%B8%D0%B7%D0%B2%D0%BE%D0%B4%D1%81%D1%82%D0%B2%D0%B5%D0%BD%D0%BD%D1%8B%D0%B5%20%D0%BF%D0%BE%D0%BA%D0%B0%D0%B7%D0%B0%D1%82%D0%B5%D0%BB%D0%B8
# (by searching for 'Производственные показатели' aka. 'Performance Indicators')
# Data for the fuel-mix at CERS Moldovenească for the year 2020 can be found at:
# http://moldgres.com/wp-content/uploads/2021/02/proizvodstvennye-pokazateli-zao-moldavskaja-gres-za-2020-god.pdf

# Annual reports from moldelectrica can be found at:
# https://moldelectrica.md/ro/network/annual_report


def template_price_response(zone_key: str, datetime: datetime, price) -> dict:
    return {
        "zoneKey": zone_key,
        "datetime": datetime,
        "currency": "MDL",
        "price": price,
        "source": "moldelectrica.md",
    }


def template_consumption_response(
    zone_key: str, datetime: datetime, consumption
) -> dict:
    return {
        "zoneKey": zone_key,
        "datetime": datetime,
        "consumption": consumption,
        "source": "moldelectrica.md",
    }


def template_production_response(zone_key: str, datetime: datetime, production) -> dict:
    return {
        "zoneKey": zone_key,
        "datetime": datetime,
        "production": production,
        "storage": {},
        "source": "moldelectrica.md",
    }


def template_exchange_response(
    sorted_zone_keys: str, datetime: datetime, netflow
) -> dict:
    return {
        "sortedZoneKeys": sorted_zone_keys,
        "datetime": datetime,
        "netFlow": netflow,
        "source": "moldelectrica.md",
    }


def get_archive_data(
    target_datetime: datetime, session: Session | None = None
) -> list[ArchiveDatapoint]:
    """Returns archive data for the target day as a list of ArchiveDatapoint."""

    archive_date = target_datetime.astimezone(TZ).strftime("%d.%m.%Y")
    archive_url = f"{archive_base_url}&date1={archive_date}&date2={archive_date}"

    s = session or Session()
    data_response = s.get(archive_url, verify=False)
    data = data_response.json()
    try:
        archive_datapoints = [
            ArchiveDatapoint(
                datetime.strptime(entry[0], "%Y-%m-%d %H:%M").replace(tzinfo=TZ),
                *map(float, entry[1:]),
            )
            for entry in data
        ]
        return sorted(archive_datapoints, key=attrgetter("datetime"))
    except Exception as e:
        raise ParserException(
            "MD.py",
            "Not able to parse received data. Check that the specifed URL returns correct data.",
        ) from e


def get_data(session: Session | None = None) -> list:
    """Returns data as a list of floats."""
    s = session or Session()

    # In order for data_url to return data, cookies from display_url must be obtained then reused.
    _response = s.get(display_url, verify=False)
    data_response = s.get(data_url, verify=False)
    raw_data = data_response.text
    try:
        data = [float(i) if i else None for i in raw_data.split(",")]
    except Exception as e:
        raise ParserException(
            "MD.py",
            "Not able to parse received data. Check that the specifed URL returns correct data.",
        ) from e

    return data


def fetch_price(
    zone_key: str = "MD",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """
    Returns the static price of electricity (0.145 MDL per kWh) as specified here:
    https://moldelectrica.md/ro/activity/tariff
    It is defined by the following government-agency decision,
    which is still in effect at the time of writing this (July 2021):
    http://lex.justice.md/viewdoc.php?action=view&view=doc&id=360109&lang=1
    """
    if target_datetime:
        raise NotImplementedError(
            "This parser is not yet able to parse past dates for price"
        )

    dt = datetime.now(tz=TZ)
    return template_price_response(zone_key, dt, 145.0)


def fetch_consumption(
    zone_key: str = "MD",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    """Requests the consumption (in MW) of a given country."""
    if target_datetime:
        archive_data = get_archive_data(target_datetime, session=session)

        datapoints = []
        for entry in archive_data:
            datapoint = template_consumption_response(
                zone_key, entry.datetime, entry.consumption
            )
            datapoints.append(datapoint)
        return datapoints
    else:
        field_values = get_data(session)

        consumption = field_values[FIELD_LABEL_to_INDEX["consumption"]]

        dt = datetime.now(tz=TZ)

        datapoint = template_consumption_response(zone_key, dt, consumption)

        return datapoint


def fetch_production(
    zone_key: str = "MD",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    """Requests the production mix (in MW) of a given country."""
    if target_datetime:
        archive_data = get_archive_data(target_datetime, session=session)
        datapoints = []
        for entry in archive_data:
            production = {
                "solar": None,
                "wind": None,
                "biomass": 0.0,
                "nuclear": 0.0,
                "gas": 0.0,
                "hydro": 0.0,
            }

            production["gas"] += entry.tpp
            production["hydro"] += entry.hpp
            # Renewables (solar + biogas + wind) make up a small part of the energy produced.
            # The exact mix of renewable enegry sources is unknown,
            # so everything is attributed to biomass.
            production["biomass"] += entry.res

            datapoint = template_production_response(
                zone_key, entry.datetime, production
            )
            datapoints.append(datapoint)
        return datapoints
    else:
        field_values = get_data(session)

        production = {
            "solar": field_values[FIELD_LABEL_to_INDEX["solar"]],
            "wind": field_values[FIELD_LABEL_to_INDEX["wind"]],
            "biomass": field_values[FIELD_LABEL_to_INDEX["biomass"]],
            "nuclear": 0.0,
            "gas": field_values[FIELD_LABEL_to_INDEX["gas"]],
            "hydro": field_values[FIELD_LABEL_to_INDEX["hydro"]],
        }

        dt = datetime.now(tz=TZ)

        datapoint = template_production_response(zone_key, dt, production)

        return datapoint


def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    """Requests the last known power exchange (in MW) between two countries."""
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    if target_datetime:
        archive_data = get_archive_data(target_datetime, session=session)

        datapoints = []
        for entry in archive_data:
            if sorted_zone_keys == "MD->UA":
                netflow = -1 * entry.exchange_UA_to_MD
            elif sorted_zone_keys == "MD->RO":
                netflow = -1 * entry.exchange_RO_to_MD
            else:
                raise NotImplementedError("This exchange pair is not implemented")

            datapoint = template_exchange_response(
                sorted_zone_keys, entry.datetime, netflow
            )
            datapoints.append(datapoint)
        return datapoints
    else:
        field_values = get_data(session)

        if sorted_zone_keys == "MD->UA":
            netflow = field_values[FIELD_LABEL_to_INDEX["exchange MD-UA"]]
        elif sorted_zone_keys == "MD->RO":
            netflow = field_values[FIELD_LABEL_to_INDEX["exchange MD-RO"]]
        else:
            raise NotImplementedError("This exchange pair is not implemented")

        dt = datetime.now(tz=TZ)

        datapoint = template_exchange_response(sorted_zone_keys, dt, netflow)

        return datapoint


if __name__ == "__main__":
    # Main method, never used by the Electricity Map backend, but handy for testing.

    print("fetch_price() ->")
    print(fetch_price())

    for target_datetime in (None, datetime.fromisoformat("2021-07-25T15:00+00:00")):
        print(f"For target_datetime {target_datetime}:")

        print("fetch_consumption() ->")
        print(fetch_consumption(target_datetime=target_datetime))

        print("fetch_production() ->")
        print(fetch_production(target_datetime=target_datetime))

        print("fetch_exchange(MD, UA) ->")
        print(fetch_exchange("MD", "UA", target_datetime=target_datetime))
        print("fetch_exchange(MD, RO) ->")
        print(fetch_exchange("MD", "RO", target_datetime=target_datetime))

        print("------------")
