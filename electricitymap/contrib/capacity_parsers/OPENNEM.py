from datetime import datetime

import pandas as pd
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from parsers.OPENNEM import SOURCE, ZONE_KEY_TO_REGION

"""Disclaimer: only works for real-time data. There is retired capacity included but we do not have the information on when the capacity was retired."""

REGION_MAPPING = {
    ZONE_KEY_TO_REGION[key]: key for key in ZONE_KEY_TO_REGION
}  # NT only has solar capacity so it will be excluded

FUEL_MAPPING = {
    "wind": "wind",
    "solar_rooftop": "solar",
    "battery_charging": "battery storage",
    "solar_utility": "solar",
    "coal_black": "coal",
    "battery_discharging": "battery storage",
    "pumps": "hydro storage",
    "gas_steam": "gas",
    "gas_ocgt": "gas",
    "hydro": "hydro",
    "coal_brown": "coal",
    "distillate": "oil",
    "bioenergy_biogas": "biomass",
    "gas_ccgt": "gas",
    "gas_wcmg": "gas",
    "gas_recip": "gas",
    "bioenergy_biomass": "biomass",
}


def get_opennem_capacity_data() -> dict:
    url = "https://api.opennem.org.au/facility/"
    r: Response = Session().get(url)
    data = r.json()
    capacity_df = pd.json_normalize(data)

    capacity_df = capacity_df.loc[capacity_df["dispatch_type"] == "GENERATOR"]
    capacity_df = capacity_df.loc[capacity_df["status.code"] == "operating"]
    capacity_df = capacity_df[
        ["network_region", "capacity_registered", "fueltech.code", "created_at"]
    ]
    capacity_df = capacity_df.rename(
        columns={
            "network_region": "zone_key",
            "capacity_registered": "value",
            "fueltech.code": "mode",
            "created_at": "datetime",
        }
    )

    capacity_df["datetime"] = capacity_df["datetime"].apply(
        lambda x: pd.to_datetime(x, utc=True).replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
    )
    return capacity_df


def filter_capacity_data_by_datetime(
    data: pd.DataFrame, target_datetime: datetime
) -> pd.DataFrame:
    df = data.copy()
    max_datetime = df["datetime"].max()
    min_datetime = df["datetime"].min()

    if target_datetime >= max_datetime:
        df = df.copy()
    elif target_datetime <= min_datetime:
        df = df.loc[
            df["datetime"] == min_datetime
        ].copy()  # we backfill the capacity data using the first data point
    else:
        df = df.loc[df["datetime"] <= target_datetime]
    return df


def fetch_production_capacity_for_all_zones(target_datetime: datetime):
    capacity_df = get_opennem_capacity_data()

    capacity_df = filter_capacity_data_by_datetime(capacity_df, target_datetime)

    capacity_df["zone_key"] = capacity_df["zone_key"].map(REGION_MAPPING)
    capacity_df["mode"] = capacity_df["mode"].map(FUEL_MAPPING)

    capacity_df = (
        capacity_df.groupby(["zone_key", "mode"])[["value"]].sum().reset_index()
    )

    capacity = {}
    for zone in capacity_df["zone_key"].unique():
        zone_capacity_df = capacity_df.loc[capacity_df["zone_key"] == zone]
        zone_capacity = {}
        for idx, data in zone_capacity_df.iterrows():
            zone_capacity[data["mode"]] = {
                "datetime": target_datetime.strftime("%Y-%m-%d"),
                "value": round(data["value"], 2),
                "source": SOURCE,
            }
        capacity[zone] = zone_capacity
    return capacity


def fetch_production_capacity(zone_key: ZoneKey, target_datetime: datetime):
    capacity = fetch_production_capacity_for_all_zones(target_datetime)[zone_key]
    if capacity:
        print(f"Updated capacity for {zone_key} in {target_datetime}: \n{capacity}")
        return capacity
    else:
        raise ValueError(f"No capacity data for {zone_key} in {target_datetime}")


def get_solar_capacity_au_nt(target_datetime: datetime):

    capacity_df = get_opennem_capacity_data()
    capacity_df = filter_capacity_data_by_datetime(capacity_df, target_datetime)

    capacity_df = capacity_df.loc[capacity_df["zone_key"] == "NT1"]
    capacity_df["zone_key"] = "AU-NT"

    capacity_df["mode"] = capacity_df["mode"].map(FUEL_MAPPING)

    capacity_df = (
        capacity_df.groupby(["zone_key", "mode"])[["value"]].sum().reset_index()
    )

    capacity = {}
    for idx, data in capacity_df.iterrows():
        capacity[data["mode"]] = {
            "datetime": target_datetime.strftime("%Y-%m-%d"),
            "value": round(data["value"], 2),
            "source": SOURCE,
        }
    return capacity
