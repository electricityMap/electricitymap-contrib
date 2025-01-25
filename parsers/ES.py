#!/usr/bin/env python3

from datetime import datetime, timedelta
from json import loads
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

# The request library is used to fetch content through HTTP
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

#    Zone name Cheat Sheet

#    ZoneKey("ES"): "IberianPeninsula"
#    ZoneKey("ES-CE"): "Ceuta"
#    ZoneKey("ES-CN-FVLZ"): "LanzaroteFuerteventura"
#    ZoneKey("ES-CN-GC"): "GranCanaria"
#    ZoneKey("ES-CN-HI"): "ElHierro"
#    ZoneKey("ES-CN-IG"): "Gomera"
#    ZoneKey("ES-CN-LP"): "LaPalma"
#    ZoneKey("ES-CN-TE"): "Tenerife"
#    ZoneKey("ES-IB-FO"): "Formentera"
#    ZoneKey("ES-IB-IZ"): "Ibiza"
#    ZoneKey("ES-IB-MA"): "Mallorca"
#    ZoneKey("ES-IB-ME"): "Menorca"
#    ZoneKey("ES-ML"): "Melilla"

PRODUCTION_PARSE_MAPPING = {
    "nuc": "nuclear",  # Nuclear
    "die": "oil",  # Diesel engines
    "genAux": "oil",  # TAuxiliary generation
    "gas": "gas",  # Gas turbine
    "gf": "gas",  # Fuel/gas
    "eol": "wind",  # Wind
    "cc": "gas",  # Combined cycle
    "vap": "oil",  # Vapor turbine
    "fot": "solar",  # Solar PV
    "sol": "solar",  # Solar
    "car": "coal",  # Coal
    "resid": "unknown",  # Wastes
    "termRenov": "geothermal",  # Thermal renewable
    "cogenResto": "unknown",  # Cogeneration and waste
    "tnr": "unknown",  # Other special regime
    "trn": "geothermal",  # Thermal renewable
    "otrRen": "unknown",  # Other renewable
    "cogen": "gas",  # Cogeneration
    "turb": "hydro_storage",  # Pumping Turbine
    "conb": "hydro_storage",  # Pumping consumption
    "residNr": "unknown",  # Non-renewable waste
    "residRen": "biomass",  # Renewable wastes
    "bat": "battery_storage",  # Battery
    "consBat": "battery_storage",  # Batteries consume
    "aut": "unknown",  # Other special regime
    "gnhd": "hydro",  # Hydro
}

ZONE_MAPPING = {
    ZoneKey("ES"): {
        "API_CODE": "DEMANDAAU",
        "SYSTEM": "Peninsula",
        "TZ": "Europe/Madrid",
    },
    ZoneKey("ES-CE"): {
        "API_CODE": "CEUTAAU",
        "SYSTEM": "Peninsula",
        "TZ": "Africa/Ceuta",
    },
    ZoneKey("ES-CN-FVLZ"): {
        "API_CODE": "LZ_FVAU",
        "SYSTEM": "Canarias",
        "TZ": "Atlantic/Canary",
    },
    ZoneKey("ES-CN-GC"): {
        "API_CODE": "GCANARIAAU",
        "SYSTEM": "Canarias",
        "TZ": "Atlantic/Canary",
    },
    ZoneKey("ES-CN-HI"): {
        "API_CODE": "EL_HIERROAU",
        "SYSTEM": "Canarias",
        "TZ": "Atlantic/Canary",
    },
    ZoneKey("ES-CN-IG"): {
        "API_CODE": "LA_GOMERAAU",
        "SYSTEM": "Canarias",
        "TZ": "Atlantic/Canary",
    },
    ZoneKey("ES-CN-LP"): {
        "API_CODE": "LA_PALMAAU",
        "SYSTEM": "Canarias",
        "TZ": "Atlantic/Canary",
    },
    ZoneKey("ES-CN-TE"): {
        "API_CODE": "TENERIFEAU",
        "SYSTEM": "Canarias",
        "TZ": "Atlantic/Canary",
    },
    ZoneKey("ES-IB-FO"): {
        "API_CODE": "FORMENTERAAU",
        "SYSTEM": "Baleares",
        "TZ": "Europe/Madrid",
    },
    ZoneKey("ES-IB-IZ"): {
        "API_CODE": "IBIZAAU",
        "SYSTEM": "Baleares",
        "TZ": "Europe/Madrid",
    },
    ZoneKey("ES-IB-MA"): {
        "API_CODE": "MALLORCAAU",
        "SYSTEM": "Baleares",
        "TZ": "Europe/Madrid",
    },
    ZoneKey("ES-IB-ME"): {
        "API_CODE": "MENORCAAU",
        "SYSTEM": "Baleares",
        "TZ": "Europe/Madrid",
    },
    ZoneKey("ES-ML"): {
        "API_CODE": "MELILLAAU",
        "SYSTEM": "Peninsula",
        "TZ": "Africa/Ceuta",
    },
}

EXCHANGE_MAPPING = {
    ZoneKey("ES->ES-IB-MA"): {
        "zone_ref": ZoneKey("ES-IB-MA"),
        "codes": ["cb"],
        "coef": 1,
    },
    ZoneKey("ES-IB-IZ->ES-IB-MA"): {
        "zone_ref": ZoneKey("ES-IB-MA"),
        "codes": ["emi"],
        "coef": 1,
    },
    ZoneKey("ES-IB-FO->ES-IB-IZ"): {
        "zone_ref": ZoneKey("ES-IB-FO"),
        "codes": ["eif"],
        "coef": -1,
    },
    ZoneKey("ES-IB-MA->ES-IB-ME"): {
        "zone_ref": ZoneKey("ES-IB-MA"),
        "codes": ["emm"],
        "coef": -1,
    },
    ZoneKey("AD->ES"): {
        "zone_ref": ZoneKey("ES"),
        "codes": ["expAnd", "impAnd"],
        "coef": 1,
    },
    ZoneKey("ES->MA"): {
        "zone_ref": ZoneKey("ES"),
        "codes": ["expMar", "impMar"],
        "coef": -1,
    },
    ZoneKey("ES->PT"): {
        "zone_ref": ZoneKey("ES"),
        "codes": ["expPor", "impPor"],
        "coef": -1,
    },
    ZoneKey("ES->FR"): {
        "zone_ref": ZoneKey("ES"),
        "codes": ["expFra", "impFra"],
        "coef": -1,
    },
}

SOURCE = "demanda.ree.es"


def check_valid_parameters(
    zone_key: ZoneKey,
    session: Session | None,
    target_datetime: datetime | None,
):
    """Raise an exception if the parameters are not valid for this parser."""
    if "->" not in zone_key and zone_key not in ZONE_MAPPING:
        raise ParserException(
            "ES.py",
            f"This parser cannot parse data for zone: {zone_key}",
            zone_key,
        )
    elif "->" in zone_key and zone_key not in EXCHANGE_MAPPING:
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


def check_known_key(key: str, logger: Logger):
    """Check if the given key is already known and log a warning if not."""
    if (
        key not in sum([v["codes"] for v in EXCHANGE_MAPPING.values()], [])
        and key not in PRODUCTION_PARSE_MAPPING
        and key
        not in {
            "dem",  # Demand
            "hid",  # Hydro => sum of hydro
            "ts",  # Timestamp
            "efl",  # Fuerteventura-Lanzarote link => not used
            "expTot",  # Exportation Total
            "impTot",  # Importation Total
            "dif",  # ?
            "solFot",  # Solar PV => include in solar
            "solTer",  # Solar thermal => include in solar
            "inter",  # Int. exchanges
            "icb",  # Balear link => include in cb (Balearic-Peninsula link)
        }
    ):
        logger.warning(f'Key "{key}" could not be parsed!')


def get_ree_data(
    zone_key: ZoneKey, session: Session, target_datetime: datetime | None, tz: str
) -> dict:
    if target_datetime is None:
        date = datetime.now(tz=ZoneInfo(tz)).strftime("%Y-%m-%d")
    else:
        date = target_datetime.strftime("%Y-%m-%d")
    system = ZONE_MAPPING[zone_key]["SYSTEM"]
    zone = ZONE_MAPPING[zone_key]["API_CODE"]
    res = session.get(
        f"https://demanda.ree.es/WSvisionaMoviles{system}Rest/resources/demandaGeneracion{system}?curva={zone}&fecha={date}"
    )
    if not res.ok:
        raise ParserException(
            "ES.py",
            f"Failed fetching data for {zone_key}",
            zone_key,
        )
    # The response is not rely a JSON, but a JSON-like string starting with "'null(" and ending with ");" or ")"
    json = loads(res.text[5:-2]) if res.text[-1] == ";" else loads(res.text[5:-1])

    return json["valoresHorariosGeneracion"]


def parse_date(str_date, tz):
     return datetime.fromisoformat(str_date).replace(tzinfo=ZoneInfo(tz))


def fetch_and_preprocess_data(
    zone_key: ZoneKey,
    session: Session,
    logger: Logger,
    target_datetime: datetime | None,
):
    """Fetch data for the given zone key."""
    tz = ZONE_MAPPING[zone_key]["TZ"]
    data = get_ree_data(zone_key, session, target_datetime, tz)
    for value in data:
        # Add timezone info to time object
        value["ts"] = parse_date(value["ts"], tz)

        for key in value:
            check_known_key(key, logger)
    if data:
        return data
    else:
        raise ParserException(
            "ES.py",
            f"Failed fetching data for {zone_key}",
            zone_key,
        )


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    check_valid_parameters(zone_key, session, target_datetime)

    ses = session or Session()
    data = fetch_and_preprocess_data(zone_key, ses, logger, target_datetime)
    consumption = TotalConsumptionList(logger)
    for event in data:
        consumption.append(
            zoneKey=zone_key,
            datetime=event["ts"],
            consumption=event["dem"],
            source="demanda.ree.es",
        )
    return consumption.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    check_valid_parameters(zone_key, session, target_datetime)
    ses = session or Session()
    data_mapping = PRODUCTION_PARSE_MAPPING.copy()

    data = fetch_and_preprocess_data(zone_key, ses, logger, target_datetime)
    productionEventList = ProductionBreakdownList(logger)
    for event in data:
        storage = StorageMix()
        production = ProductionMix()
        for key in event:
            if key in data_mapping:
                if data_mapping[key].endswith("_storage"):
                    storage.add_value(data_mapping[key].split("_")[0], -event[key])
                else:
                    production.add_value(data_mapping[key], event[key])

        productionEventList.append(
            zoneKey=zone_key,
            datetime=event["ts"],
            production=production,
            storage=storage,
            source="demanda.ree.es",
        )

    return productionEventList.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    check_valid_parameters(sorted_zone_keys, session, target_datetime)
    ses = session or Session()

    data = fetch_and_preprocess_data(
        EXCHANGE_MAPPING[sorted_zone_keys]["zone_ref"],
        ses,
        logger,
        target_datetime,
    )

    exchangeList = ExchangeList(logger)
    for event in data:
        net_flow = 0.0
        for key in event:
            if key in EXCHANGE_MAPPING[sorted_zone_keys]["codes"]:
                net_flow = (
                    net_flow + EXCHANGE_MAPPING[sorted_zone_keys]["coef"] * event[key]
                )

        exchangeList.append(
            zoneKey=sorted_zone_keys,
            datetime=event["ts"],
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
    print("fetch_exchange(ES, MA)")
    print(fetch_exchange(ZoneKey("ES"), ZoneKey("MA")))
    print("fetch_exchange(ES, AD)")
    print(fetch_exchange(ZoneKey("ES"), ZoneKey("AD")))
    print("fetch_exchange(ES, FR)")
    print(fetch_exchange(ZoneKey("ES"), ZoneKey("FR")))
    print("fetch_exchange(ES, PT)")
    print(fetch_exchange(ZoneKey("ES"), ZoneKey("PT")))
