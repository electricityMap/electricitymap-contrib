from datetime import datetime
from logging import getLogger
from typing import Dict, Union

from bs4 import BeautifulSoup
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey

logger = getLogger(__name__)
MODE_MAPPING = {
    '"Wind Onshore"': "wind",
    '"Wind Offshore"': "wind",
    '"Solar"': "solar",
    '"Other renewable"': "unknown",
    '"Other"': "unknown",
    '"Nuclear"': "nuclear",
    '"Hydro Run-of-river and poundage"': "hydro",
    '"Fossil Hard coal"': "coal",
    '"Fossil Gas"': "gas",
    '"Biomass"': "biomass",
    '"Hydro Pumped Storage"': "hydro storage",
}

SOURCE = "bmreports.com"


def fetch_production_capacity(
    zone_key: ZoneKey, target_datetime: datetime, session: Session
) -> Union[Dict, None]:
    url = f"https://www.bmreports.com/bmrs/?q=ajax/year/B1410/{target_datetime.year}/"
    r: Response = session.get(url)

    if not r.ok:
       raise
        soup = BeautifulSoup(r.text, "lxml")
        items = soup.find_all("item")
        capacity = {}
        for item in items:
            mode = item.find("powersystemresourcetype").string
            mode = MODE_MAPPING[mode]
            if mode in capacity:
                capacity[mode]["value"] += int(item.find("quantity").string)
            else:
                capacity[mode] = {
                    "datetime": target_datetime.strftime("%Y-%m-%d"),
                    "value": int(item.find("quantity").string),
                    "source": SOURCE,
                }
        logger.info(
            f"Fetched capacity for {zone_key} on {target_datetime.date()}: \n{capacity}"
        )
        return capacity
    else:
        logger.error(f"GB: No capacity data available for year {target_datetime.year}")


if __name__ == "__main__":
    fetch_production_capacity("GB", datetime(2023, 1, 1), Session())
