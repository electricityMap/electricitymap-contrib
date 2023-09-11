from datetime import datetime
from logging import getLogger
from typing import Dict, Optional, Tuple, Union

from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    PriceList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    ProductionMix,
    StorageMix,
)
from electricitymap.contrib.lib.types import ZoneKey

from .lib.exceptions import ParserException

DOMAIN_MAPPING = {
    "FR-COR": "https://opendata-corse.edf.fr",
    "RE": "https://opendata-reunion.edf.fr",
    "GF": "https://opendata-guyane.edf.fr",
    "MQ": "https://opendata-martinique.edf.fr",
    "GP": "https://opendata-guadeloupe.edf.fr",
}

LIVE_DATASETS = {
    "FR-COR": "production-delectricite-par-filiere-en-temps-reel",
    "GP": "mix-temps-reel-guadeloupe",
    "RE": "prod-electricite-temps-reel",
    "GF": "production-d-electricite-par-filiere-en-temps-reel",
    "MQ": "production-delectricite-par-filiere-en-temps-reel",
}

HISTORICAL_DATASETS = {
    "FR-COR": "production-delectricite-par-filiere",
    "RE": "courbe-de-charge-de-la-production-delectricite-par-filiere",
    "GF": "courbe-de-charge-de-la-production-delectricite-par-filiere",
    "MQ": "courbe-de-charge-de-la-production-delectricite-par-filiere",
    "GP": "courbe-de-charge-de-la-production-delectricite-par-filiere",
}

API_PARAMETER_GROUPS = {
    "production": {
        "biomass": [
            "biomasse",
            "biomasse_mw",
            "biomasse_mwh",
            "bioenergies",
            "bioenergies_mw",
            "bioenergies_mwh",
        ],
        "coal": [
            "charbon",
        ],
        "gas": [
            "thermique_mw",
            "thermique_mwh",
            "turbines_a_combustion",
        ],
        "geothermal": [
            "geothermie",
            "geothermie_mw",
        ],
        "hydro": [
            "hydraulique",
            "hydraulique_mw",
            "hydraulique_mwh",
            "micro_hydro",
            "micro_hydraulique_mw",
        ],
        "oil": ["diesel", "moteur_diesel", "centrale_au_fioul", "moteurs_diesels"],
        "solar": [
            "photovoltaique",
            "photovoltaique0",
            "photovoltaique_mw",
            "photovoltaique_mwh",
            "solaire_mw",
        ],
        "wind": [
            "eolien",
            "eolien_mw",
            "eolien_mwh",
        ],
        "unknown": ["bagasse_charbon_mwh", "charbon_bagasse_mw"],
    },
    "storage": {"battery": ["solde_stockage", "stockage"]},
    "price": {
        "price": ["cout_moyen_de_production_eur_mwh"],
    },
}

PRODUCTION_MAPPING = {
    API_TYPE: type
    for key in ["production"]
    for type, groups in API_PARAMETER_GROUPS[key].items()
    for API_TYPE in groups
}

STORAGE_MAPPING = {
    API_TYPE: type
    for key in ["storage"]
    for type, groups in API_PARAMETER_GROUPS[key].items()
    for API_TYPE in groups
}

PRICE_MAPPING = {
    API_TYPE: type
    for key in ["price"]
    for type, groups in API_PARAMETER_GROUPS[key].items()
    for API_TYPE in groups
}

IGNORED_VALUES = ["jour", "total", "statut", "date", "heure", "liaisons", "tac"]


def generate_url(zone_key, target_datetime):
    return f"{DOMAIN_MAPPING[zone_key]}/api/v2/catalog/datasets/{HISTORICAL_DATASETS[zone_key] if target_datetime else LIVE_DATASETS[zone_key]}/exports/json"


def generate_source(zone_key: ZoneKey):
    # Return the domain name of the source without the protocol
    return DOMAIN_MAPPING[zone_key].split("//")[1]


def fetch_data(
    zone_key: ZoneKey,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
) -> Tuple[list, str]:
    ses = session or Session()

    DATE_STRING_MAPPING = {
        "FR-COR": "date_heure" if target_datetime else "date",
        "RE": "date_heure" if target_datetime else "date",
        "GF": "date",
        "MQ": "date_heure" if target_datetime else "date",
        "GP": "date",
    }

    if target_datetime and zone_key not in HISTORICAL_DATASETS.keys():
        raise ParserException(
            "FR_O.py",
            f"Historical data not implemented for {zone_key} in this parser.",
            zone_key,
        )
    elif target_datetime is None and zone_key not in LIVE_DATASETS.keys():
        raise ParserException(
            "FR_O.py",
            f"Live data not implemented for {zone_key} in this parser.",
            zone_key,
        )

    URL_QUERIES: Dict[str, Union[str, None]] = {
        #   "refine": "statut:Validé" if target_datetime else None,
        "timezone": "UTC",
        "order_by": f"{DATE_STRING_MAPPING[zone_key]} desc",
        "refine": f"{DATE_STRING_MAPPING[zone_key]}:{target_datetime.strftime('%Y')}"
        if target_datetime
        else None,
    }

    url = generate_url(zone_key, target_datetime)
    response: Response = ses.get(url, params=URL_QUERIES)
    data: Union[dict, list, None] = response.json()
    if data == []:
        raise ParserException(
            "FR_O.py",
            f"No data available for {zone_key} for {target_datetime.strftime('%Y')}"
            if target_datetime
            else f"No live data available for {zone_key}.",
            zone_key,
        )
    elif isinstance(data, dict):
        if data.get("errorcode") == "10002":
            raise ParserException(
                "FR_O.py",
                f"Rate limit exceeded. Please try again later after: {data.get('reset_time')}",
            )
        elif data.get("error_code") == "ODSQLError":
            raise ParserException(
                "FR_O.py",
                "Query malformed. Please check the parameters. If this was previously working there has likely been a change in the API.",
            )
    if not isinstance(data, list):
        raise ParserException(
            "FR_O.py",
            f"Unexpected data format for {zone_key} for {target_datetime.strftime('%Y')}"
            if target_datetime
            else f"Unexpected data format for {zone_key}.",
            zone_key,
        )
    return data, DATE_STRING_MAPPING[zone_key]


def fetch_production(
    zone_key: ZoneKey,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger=getLogger(__name__),
):
    production_objects, date_string = fetch_data(zone_key, session, target_datetime)

    production_breakdown_list = ProductionBreakdownList(logger=logger)
    for production_object in production_objects:
        production = ProductionMix()
        storage = StorageMix()
        for mode_key in production_object:
            if mode_key in PRODUCTION_MAPPING:
                production.add_value(
                    PRODUCTION_MAPPING[mode_key],
                    production_object[mode_key],
                    correct_negative_with_zero=True,
                )
            elif mode_key in STORAGE_MAPPING:
                storage.add_value(
                    STORAGE_MAPPING[mode_key], -production_object[mode_key]
                )
            elif mode_key in IGNORED_VALUES:
                pass
            else:
                logger.warning(
                    f"Unknown mode_key: '{mode_key}' encountered for {zone_key}."
                )

        production_breakdown_list.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(production_object[date_string]),
            production=production,
            storage=storage,
            source=generate_source(zone_key),
            sourceType=EventSourceType.estimated
            if production_object.get("statut") == "Estimé"
            else EventSourceType.measured,
        )
    return production_breakdown_list.to_list()


def fetch_price(
    zone_key: ZoneKey,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger=getLogger(__name__),
):
    data_objects, date_string = fetch_data(zone_key, session, target_datetime)

    price_list = PriceList(logger=logger)
    for data_object in data_objects:
        price: Union[float, int, None] = None
        for mode_key in data_object:
            if mode_key in PRICE_MAPPING:
                price = data_object[mode_key]
                break
        if price is not None:
            price_list.append(
                zoneKey=zone_key,
                currency="EUR",
                datetime=datetime.fromisoformat(data_object[date_string]),
                source=generate_source(zone_key),
                price=price,
            )
    return price_list.to_list()
