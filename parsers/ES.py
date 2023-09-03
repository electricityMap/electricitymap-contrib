#!/usr/bin/env python3

from datetime import datetime, timedelta, timezone
from json import loads
from logging import Logger, getLogger
from typing import Callable, Dict, List, Optional

from arrow import get, utcnow

FUEL_MAPPING = {
    "dem": "demand",
    "nuc": "nuclear",
    "die": "oil",
    "genAux": "oil",
    "gas": "gas",
    "gf": "gas",
    "eol": "wind",
    "cc": "gas",
    "vap": "oil",
    "fot": "solar",
    "sol": "solar",
    "hid": "hydro",
    "car": "coal",
    "resid": "biomass",
    "termRenov": "unknown",
    "cogenResto": "unknown",
    "cogen": "gas",
}

LINK_MAPPING = {
    "cb": "pe_ma",
    "icb": "pe_ma",
    "emm": "ma_me",
    "emi": "ma_ib",
    "eif": "ib_fo",
    "inter": "int",
}

API_CODE_MAPPING = {
    "IberianPeninsula": "DEMANDAQH",
    "Ceuta": "CEUTA5M",
    "Melilla": "MELILLA5M",
    "Mallorca": "MALLORCA5M",
    "Menorca": "MENORCA5M",
    "Ibiza": "IBIZA5M",
    "Formentera": "FORMENTERA5M",
    "GranCanaria": "GCANARIA5M",
    "Gomera": "LA_GOMERA5M",
    "LaPalma": "LA_PALMA5M",
    "Tenerife": "TENERIFE5M",
    "LanzaroteFuerteventura": "LZ_FV5M",
    "ElHierro": "EL_HIERRO5M",
}

ZONE_MAPPING = {
    "IberianPeninsula": "Peninsula",
    "Ceuta": "Peninsula",
    "Melilla": "Peninsula",
    "Mallorca": "Baleares",
    "Menorca": "Baleares",
    "Ibiza": "Baleares",
    "Formentera": "Baleares",
    "GranCanaria": "Canarias",
    "Gomera": "Canarias",
    "LaPalma": "Canarias",
    "Tenerife": "Canarias",
    "LanzaroteFuerteventura": "Canarias",
    "ElHierro": "Canarias",
}
TIMEZONES_MAPPING = {
    "IberianPeninsula": "Europe/Madrid",
    "Ceuta": "Europe/Madrid",
    "Melilla": "Europe/Madrid",
    "Mallorca": "Europe/Madrid",
    "Menorca": "Europe/Madrid",
    "Ibiza": "Europe/Madrid",
    "Formentera": "Europe/Madrid",
    "GranCanaria": "Atlantic/Canary",
    "Gomera": "Atlantic/Canary",
    "LaPalma": "Atlantic/Canary",
    "Tenerife": "Atlantic/Canary",
    "LanzaroteFuerteventura": "Atlantic/Canary",
    "ElHierro": "Atlantic/Canary",
}

# The request library is used to fetch content through HTTP
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.lib.types import ZoneKey

from .lib.config import refetch_frequency
from .lib.exceptions import ParserException

SOURCE = "demanda.ree.es"


ZONE_FUNCTION_MAP: Dict[ZoneKey, Callable] = {
    ZoneKey("ES"): "IberianPeninsula",
    ZoneKey("ES-CE"): "Ceuta",
    ZoneKey("ES-CN-FVLZ"): "LanzaroteFuerteventura",
    ZoneKey("ES-CN-GC"): "GranCanaria",
    ZoneKey("ES-CN-HI"): "ElHierro",
    ZoneKey("ES-CN-IG"): "Gomera",
    ZoneKey("ES-CN-LP"): "LaPalma",
    ZoneKey("ES-CN-TE"): "Tenerife",
    ZoneKey("ES-IB-FO"): "Formentera",
    ZoneKey("ES-IB-IZ"): "Ibiza",
    ZoneKey("ES-IB-MA"): "Mallorca",
    ZoneKey("ES-IB-ME"): "Menorca",
    ZoneKey("ES-ML"): "Melilla",
}

EXCHANGE_FUNCTION_MAP: Dict[str, Callable] = {
    "ES->ES-IB-MA": ZoneKey("ES"),
    "ES-IB-IZ->ES-IB-MA": ZoneKey("ES-IB-MA"),
    "ES-IB-FO->ES-IB-IZ": ZoneKey("ES-IB-FO"),
    "ES-IB-MA->ES-IB-ME": ZoneKey("ES-IB-MA"),
}


def check_valid_parameters(
    zone_key: ZoneKey,
    session: Optional[Session],
    target_datetime: Optional[datetime],
):
    """Raise an exception if the parameters are not valid for this parser."""
    if "->" not in zone_key and zone_key not in ZONE_FUNCTION_MAP.keys():
        raise ParserException(
            "ES.py",
            f"This parser cannot parse data for zone: {zone_key}",
            zone_key,
        )
    elif "->" in zone_key and zone_key not in EXCHANGE_FUNCTION_MAP.keys():
        zone_key1, zone_key2 = zone_key.split("->")
        raise ParserException(
            "ES.py",
            f"This parser cannot parse data between {zone_key1} and {zone_key2}.",
            zone_key,
        )
    if session is not None and not isinstance(session, Session):
        raise ParserException(
            "ES.py",
            f"Invalid session: {session}",
            zone_key,
        )
    if target_datetime is not None and not isinstance(target_datetime, datetime):
        raise ParserException(
            "ES.py",
            f"Invalid target_datetime: {target_datetime}",
            zone_key,
        )


def fetch_island_data(
    zone_key: ZoneKey,
    session: Session,
    target_datetime: Optional[datetime],
    fuel_mapping: Dict = FUEL_MAPPING,
):
    """Fetch data for the given zone key."""
    timezone = TIMEZONES_MAPPING[ZONE_FUNCTION_MAP[zone_key]]
    if target_datetime is None:
        date = utcnow().to(timezone).format("YYYY-MM-DD")
    else:
        date = target_datetime.strftime("%Y-%m-%d")
    system = ZONE_MAPPING[ZONE_FUNCTION_MAP[zone_key]]
    zone = API_CODE_MAPPING[ZONE_FUNCTION_MAP[zone_key]]
    res = session.get(
        f"https://demanda.ree.es/WSvisionaMoviles{system}Rest/resources/demandaGeneracion{system}?curva={zone}&fecha={date}"
    )
    if not res.ok:
        raise ParserException(
            "ES.py",
            f"Failed fetching data for {zone_key}",
            zone_key,
        )
    json = loads(res.text.replace("null(", "", 1).replace(r");", "", 1))
    data = json["valoresHorariosGeneracion"]
    responses = []
    for value in data:
        ts = value.pop("ts")
        arrow = get(ts + " " + timezone, "YYYY-MM-DD HH:mm ZZZ")
        response = {}
        response["timestamp"] = str(arrow)
        for key in value:
            if key in fuel_mapping:
                if fuel_mapping[key] in response.keys():
                    response[fuel_mapping[key]] += value[key]
                else:
                    response[fuel_mapping[key]] = value[key]
            elif key in LINK_MAPPING:
                if LINK_MAPPING[key] in response.keys():
                    response[LINK_MAPPING[key]] += value[key]
                else:
                    response[LINK_MAPPING[key]] = value[key]
        responses.append(response)
    if responses:
        return responses
    else:
        raise ParserException(
            "ES.py",
            f"Failed fetching data for {zone_key}",
            zone_key,
        )


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: ZoneKey,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    check_valid_parameters(zone_key, session, target_datetime)

    ses = session or Session()
    island_data = fetch_island_data(zone_key, ses, target_datetime)
    consumption = TotalConsumptionList(logger)
    for event in island_data:
        consumption.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(event["timestamp"]).astimezone(
                timezone.utc
            ),
            consumption=event["demand"],
            source="demanda.ree.es",
        )
    return consumption.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    check_valid_parameters(zone_key, session, target_datetime)
    ses = session or Session()
    fuel_mapping = FUEL_MAPPING.copy()

    ## Production mapping override for Canary Islands
    # NOTE the LNG terminals are not built yet, so power generated by "gas" or "cc" in ES-CN domain is actually using oil.
    # Recheck this every 6 months and move to gas key if there has been a change.
    # Last checked: 2022-06-27
    if zone_key.split("-")[1] == "CN":
        fuel_mapping["gas"] = "oil"
        fuel_mapping["cc"] = "oil"

    if zone_key == "ES-IB-ME" or zone_key == "ES-IB-FO":
        fuel_mapping["gas"] = "oil"
    if zone_key == "ES-IB-IZ":
        fuel_mapping["die"] = "gas"

    island_data = fetch_island_data(zone_key, ses, target_datetime, fuel_mapping)
    productionEventList = ProductionBreakdownList(logger)
    for event in island_data:
        production = ProductionMix()
        for mode in [
            "biomass",
            "coal",
            "gas",
            "geothermal",
            "nuclear",
            "oil",
            "solar",
            "wind",
            "unknown",
        ]:
            if mode in event.keys():
                production.add_value(mode, event[mode])
        storage = StorageMix()
        if "hydro" in event.keys():
            storage.hydro = -event["hydro"]
        productionEventList.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(event["timestamp"]).astimezone(
                timezone.utc
            ),
            production=production,
            storage=storage,
            source="demanda.ree.es",
        )

    return productionEventList.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    check_valid_parameters(sorted_zone_keys, session, target_datetime)

    if isinstance(target_datetime, datetime):
        date = target_datetime.strftime("%Y-%m-%d")
    else:
        date = target_datetime

    ses = session or Session()

    responses = fetch_island_data(
        EXCHANGE_FUNCTION_MAP[sorted_zone_keys],
        ses,
        target_datetime,
    )

    exchangeList = ExchangeList(logger)
    for response in responses:
        net_flow: float
        if sorted_zone_keys == "ES-IB-MA->ES-IB-ME":
            net_flow = -1 * response["ma_me"]
        elif sorted_zone_keys == "ES-IB-IZ->ES-IB-MA":
            net_flow = response["ma_ib"]
        elif sorted_zone_keys == "ES-IB-FO->ES-IB-IZ":
            net_flow = -1 * response["ib_fo"]
        else:
            net_flow = response["pe_ma"]

        exchangeList.append(
            zoneKey=sorted_zone_keys,
            datetime=datetime.fromisoformat(response["timestamp"]).astimezone(
                timezone.utc
            ),
            netFlow=net_flow,
            source="demanda.ree.es",
        )

    return exchangeList.to_list()


if __name__ == "__main__":
    # Spain
    print("fetch_consumption(ES)")
    print(fetch_consumption(ZoneKey("ES")))
    print("fetch_production(ES)")
    print(fetch_production(ZoneKey("ES")))

    # Autonomous cities
    print("fetch_consumption(ES-CE)")
    print(fetch_consumption(ZoneKey("ES-CE")))
    print("fetch_production(ES-CE)")
    print(fetch_production(ZoneKey("ES-CE")))
    print("fetch_consumption(ES-ML)")
    print(fetch_consumption(ZoneKey("ES-ML")))
    print("fetch_production(ES-ML)")
    print(fetch_production(ZoneKey("ES-ML")))

    # Canary Islands
    print("fetch_consumption(ES-CN-FVLZ)")
    print(fetch_consumption(ZoneKey("ES-CN-FVLZ")))
    print("fetch_production(ES-CN-FVLZ)")
    print(fetch_production(ZoneKey("ES-CN-FVLZ")))
    print("fetch_consumption(ES-CN-GC)")
    print(fetch_consumption(ZoneKey("ES-CN-GC")))
    print("fetch_production(ES-CN-GC)")
    print(fetch_production(ZoneKey("ES-CN-GC")))
    print("fetch_consumption(ES-CN-IG)")
    print(fetch_consumption(ZoneKey("ES-CN-IG")))
    print("fetch_production(ES-CN-IG)")
    print(fetch_production(ZoneKey("ES-CN-IG")))
    print("fetch_consumption(ES-CN-LP)")
    print(fetch_consumption(ZoneKey("ES-CN-LP")))
    print("fetch_production(ES-CN-LP)")
    print(fetch_production(ZoneKey("ES-CN-LP")))
    print("fetch_consumption(ES-CN-TE)")
    print(fetch_consumption(ZoneKey("ES-CN-TE")))
    print("fetch_production(ES-CN-TE)")
    print(fetch_production(ZoneKey("ES-CN-TE")))
    print("fetch_consumption(ES-CN-HI)")
    print(fetch_consumption(ZoneKey("ES-CN-HI")))
    print("fetch_production(ES-CN-HI)")
    print(fetch_production(ZoneKey("ES-CN-HI")))

    # Balearic Islands
    print("fetch_consumption(ES-IB-FO)")
    print(fetch_consumption(ZoneKey("ES-IB-FO")))
    print("fetch_production(ES-IB-FO)")
    print(fetch_production(ZoneKey("ES-IB-FO")))
    print("fetch_consumption(ES-IB-IZ)")
    print(fetch_consumption(ZoneKey("ES-IB-IZ")))
    print("fetch_production(ES-IB-IZ)")
    print(fetch_production(ZoneKey("ES-IB-IZ")))
    print("fetch_consumption(ES-IB-MA)")
    print(fetch_consumption(ZoneKey("ES-IB-MA")))
    print("fetch_production(ES-IB-MA)")
    print(fetch_production(ZoneKey("ES-IB-MA")))
    print("fetch_consumption(ES-IB-ME)")
    print(fetch_consumption(ZoneKey("ES-IB-ME")))
    print("fetch_production(ES-IB-ME)")
    print(fetch_production(ZoneKey("ES-IB-ME")))

    # Exchanges
    print("fetch_exchange(ES, ES-IB-MA)")
    print(fetch_exchange(ZoneKey("ES"), ZoneKey("ES-IB-MA")))
    print("fetch_exchange(ES-IB-MA, ES-IB-ME)")
    print(fetch_exchange(ZoneKey("ES-IB-MA"), ZoneKey("ES-IB-ME")))
    print("fetch_exchange(ES-IB-MA, ES-IB-IZ)")
    print(fetch_exchange(ZoneKey("ES-IB-MA"), ZoneKey("ES-IB-IZ")))
    print("fetch_exchange(ES-IB-IZ, ES-IB-FO)")
    print(fetch_exchange(ZoneKey("ES-IB-IZ"), ZoneKey("ES-IB-FO")))
