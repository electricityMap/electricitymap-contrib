from __future__ import annotations

from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import List, Optional, Union

# The arrow library is used to handle datetimes
import arrow
from bs4 import BeautifulSoup

# The request library is used to fetch content through HTTP
from requests import Session

# please try to write PEP8 compliant code (use a linter). One of PEP8's
# requirement is to limit your line length to 79 characters.


translate_table_gen = {
    "TPP": "coal",  # coal
    "CCGT": "gas",  # gas and steem gas
    "NPP": "nuclear",  # Nuclear
    "HPP": "hydro",  # Water
    "PsPP": "hydro",  # Pump Water storage
    "AltPP": "biomass",  # Alternative
    "ApPP": "unknown",  # factory
    "PVPP": "solar",  # photovoltaic
    "WPP": "wind",  # wind
    "unknown": "unknown",
}
translate_table_dist = {
    "SEPS": "SVK",
    "APG": "AT",
    "PSE": "PL",
    "TenneT": "DE",
    "50HzT": "DE",
}
url = "https://wwwtest.ceps.cz/_layouts/CepsData.asmx"


def get_mapper(xmlload):
    series = xmlload.find("series")
    mapping = {}
    for tag in series:
        generator = tag["name"].replace(" [MW]", "")
        mapping[generator] = tag["id"]

    return mapping


def make_request(session, payload, zone_key):
    headers = {
        "Content-Type": "application/soap+xml; charset=utf-8",
        "Content-Length": "1",
    }

    r = session or Session()
    res = r.post(url, headers=headers, data=payload)
    assert res.status_code == 200, (
        "Exception when fetching production for "
        "{}: error when calling url={}".format(zone_key, url)
    )

    return res


def fetch_production(
    zone_key: str = "CZ",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> Union[List[dict], dict]:

    if not target_datetime:
        target_datetime = datetime.now().replace(minute=0, second=0, microsecond=0)
    from_datetime = target_datetime - timedelta(hours=1)

    payload = """<?xml version="1.0" encoding="utf-8"?>
            <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
              <soap12:Body>
                <Generation xmlns="https://www.ceps.cz/CepsData/">
                  <dateFrom>{0}</dateFrom>
                  <dateTo>{1}</dateTo>
                  <agregation>{2}</agregation>
                  <function>{3}</function>
                  <version>{4}</version>
                  <para1>{5}</para1>
                </Generation>
              </soap12:Body>
            </soap12:Envelope>""".format(
        from_datetime.isoformat(), target_datetime.isoformat(), "QH", "AVG", "RT", "all"
    )

    content = make_request(session, payload, zone_key).content
    xml = BeautifulSoup(content, "xml")
    mapper = get_mapper(xml)

    data_tag = xml.find("data")
    data_list = []

    for values in data_tag:
        data = {
            "zoneKey": zone_key,
            "production": {},
            "storage": {},
            "source": url,
            "datetime": datetime.fromisoformat(values["date"]).isoformat(),
        }

        for k, v in mapper.items():
            generator = translate_table_gen[k]
            if k != "PsPP":
                data["production"][generator] = float(values[v])
            else:
                data["storage"][generator] = float(values[v])

        data_list.append(data)

    return data_list


def fetch_exchange(
    zone_key1: str = "CZ",
    zone_key2: str = "DE",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
    mode: Optional[str] = "Actual",
):
    if not target_datetime:
        target_datetime = datetime.now().replace(minute=0, second=0, microsecond=0)
    from_datetime = target_datetime - timedelta(hours=1)

    payload = """<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <CrossborderPowerFlows xmlns="https://www.ceps.cz/CepsData/">
      <dateFrom>{0}</dateFrom>
      <dateTo>{1}</dateTo>
      <agregation>{2}</agregation>
      <function>{3}</function>
      <version>{4}</version>
    </CrossborderPowerFlows>
  </soap12:Body>
</soap12:Envelope>""".format(
        from_datetime.isoformat(), target_datetime.isoformat(), "QH", "AVG", "RT"
    )

    content = make_request(session, payload, zone_key1).content
    xml = BeautifulSoup(content, "xml")
    mapper = get_mapper(xml)

    data_tag = xml.find("data")
    data_list = []

    for values in data_tag:
        data = {
            "sortedZoneKeys": f"{zone_key1}->{zone_key2}",
            "datetime": datetime.fromisoformat(values["date"]).isoformat(),
            "netFlow": 0.0,
            "source": url,
        }

        for k, v in mapper.items():
            country = "".join(
                [c for key, c in translate_table_dist.items() if key in k and mode in k]
            )
            if country != "" and country in (zone_key1, zone_key2):
                data["netFlow"] += float(values[v])

        data_list.append(data)

    return data_list


def fetch_exchange_forecast():
    fetch_exchange("CZ", "DE", mode="Planned")


def fetch_price(
    zone_key: str = "CZ",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):

    if not target_datetime:
        target_datetime = arrow.now().replace(minute=0, second=0)
    from_datetime = target_datetime.shift(days=-5)

    payload = """<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <OfferPrices xmlns="https://www.ceps.cz/CepsData/">
      <dateFrom>{0}</dateFrom>
      <dateTo>{1}</dateTo>
      <version>{2}</version>
      <param1>(3)</param1>
    </OfferPrices>
  </soap12:Body>
</soap12:Envelope>""".format(
        from_datetime, target_datetime, "RT", "all"
    )

    xml = BeautifulSoup(make_request(session, payload, zone_key).content, "xml")
    mapper = get_mapper(xml)

    data_tag = xml.find("data")
    data_list = []


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    # print("fetch_production() ->")
    # print(fetch_production())
    # print("fetch_price() ->")
    # print(fetch_price())
    # print("fetch_exchange_planned() ->")
    # print(fetch_exchange_planned())
    print("fetch_exchange('CZ', 'DE') ->")
    print(fetch_exchange('AT', 'CZ'))
