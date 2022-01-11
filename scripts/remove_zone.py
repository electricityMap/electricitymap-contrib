#!/usr/bin/env python3
"""
poetry run python scripts/remove_zone.py DK-DK1
"""

import argparse

from utils import LOCALE_FILE_PATHS, ROOT_PATH, JsonFilePatcher, run_shell_command


def remove_zone(zone: str):
    with JsonFilePatcher(ROOT_PATH / "config/exchanges.json") as f:
        for k in list(f.content.keys()):
            if k.startswith(f"{zone}->") or k.endswith(f"->{zone}"):
                del f.content[k]

    with JsonFilePatcher(ROOT_PATH / "config/co2eq_parameters.json") as f:
        for parameter in list(f.content.keys()):
            zone_overrides = f.content[parameter]["zoneOverrides"]
            if zone in zone_overrides:
                del zone_overrides[zone]

    with JsonFilePatcher(ROOT_PATH / "config/zones.json") as f:
        if zone in f.content:
            del f.content[zone]

        # TODO: we could check if part of subZoneNames
        # TODO: we could detect parsers that are only used by this zone
        #       so we can clean those files up.

    for locale_file in LOCALE_FILE_PATHS:
        with JsonFilePatcher(locale_file, indent=4) as f:
            zone_short_name = f.content["zoneShortName"]
            if zone in zone_short_name:
                del zone_short_name[zone]

    geo_json_path = ROOT_PATH / "web/geo/world.geojson"
    with JsonFilePatcher(geo_json_path) as f:
        new_features = [
            f for f in f.content["features"] if f["properties"]["zoneName"] != zone
        ]
        f.content["features"] = new_features

    run_shell_command(f"npx prettier --write {geo_json_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("zone", help="The zone abbreviation (e.g. AT)")
    args = parser.parse_args()
    zone = args.zone

    print(f"Removing {zone}")
    remove_zone(zone)
    print(
        f"NOTE: There is still a bit of cleaning up to do. Try searching for files and references."
    )
    print('Please rerun "yarn update-world" inside the web folder.')


if __name__ == "__main__":
    main()
