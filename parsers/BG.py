#!/usr/bin/env python3
# coding=utf-8

import arrow
import requests

TYPE_MAPPING = {                        # Real values around midnight
    u'АЕЦ': 'nuclear',                  # 2000
    u'Кондензационни ТЕЦ': 'coal',      # 1800
    u'Топлофикационни ТЕЦ': 'gas',      # 146
    u'Заводски ТЕЦ': 'gas',             # 147
    u'ВЕЦ': 'hydro',                    # 7
    u'Малки ВЕЦ': 'hydro',              # 74
    u'ВяЕЦ': 'wind',                    # 488
    u'ФЕЦ': 'solar',                    # 0
    u'Био ТЕЦ': 'biomass',              # 29
    u'Био ЕЦ': 'biomass',               # 29
    u'Товар РБ': 'consumption',         # 3175
}


def fetch_production(zone_key='BG', session=None, target_datetime=None, logger=None) -> dict:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    r = session or requests.session()
    url = 'http://www.eso.bg/api/rabota_na_EEC_json.php'
    response = r.get(url).json()

    datapoints = []
    for row in response:
        for k in TYPE_MAPPING.keys():
            if row[0].startswith(k):
                datapoints.append((TYPE_MAPPING[k], row[1]))
                break

    production = {}
    for k, v in datapoints:
        production[k] = production.get(k, 0.0) + v

    data = {
        'zoneKey': zone_key,
        'production': production,
        'storage': {},
        'source': 'eso.bg',
        'datetime': arrow.utcnow().datetime
    }

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
