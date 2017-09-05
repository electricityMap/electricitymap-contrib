from requests import Session
from parsers.lib import web
from parsers.lib import countrycode
from parsers.lib import india


def fetch_consumption(country_code='IN-KA', session=None):
    """Fetch Karnataka consumption"""
    countrycode.assert_country_code(country_code, 'IN-KA')

    html = web.get_response_soup(country_code, 'http://kptclsldc.com/Default.aspx', session)

    india_date_time = india.read_datetime_from_span_id(html, 'Label6', 'DD/MM/YYYY HH:mm')

    demand_value = india.read_value_from_span_id(html, 'Label5')

    data = {
        'countryCode': country_code,
        'datetime': india_date_time.datetime,
        'consumption': demand_value,
        'source': 'kptclsldc.com'
    }

    return data

def fetch_production(country_code='IN-KA', session=None):
    """Fetch Karnataka  production"""
    countrycode.assert_country_code(country_code, 'IN-KA')

    html = web.get_response_soup(country_code, 'http://kptclsldc.com/StateGen.aspx', session)

    india_date_time = india.read_datetime_from_span_id(html, 'lbldate', 'D/M/YYYY h:mm:ss A')

    # RTPS Production: https://en.wikipedia.org/wiki/Raichur_Thermal_Power_Station
    rtps_value = india.read_value_from_span_id(html, 'lblrtptot')

    # BTPS Production: https://en.wikipedia.org/wiki/Bellary_Thermal_Power_station
    btps_value = india.read_value_from_span_id(html, 'lblbtptot')

    # YTPS Production: https://en.wikipedia.org/wiki/Yermarus_Thermal_Power_Station
    ytps_value = india.read_value_from_span_id(html, 'ytptot')

    # UPCL Production: https://en.wikipedia.org/wiki/Udupi_Power_Plant
    upcl_value = india.read_value_from_span_id(html, 'lblupctot')

    # JINDAl Production
    jindal_value = india.read_value_from_span_id(html, 'lbljintot')

    # Coal Production
    coal_value = rtps_value + btps_value + ytps_value + upcl_value + jindal_value

    # Sharavati Production
    sharavati_value = india.read_value_from_span_id(html, 'lblshvytot')

    # Nagjhari Production
    nagjhari_value = india.read_value_from_span_id(html, 'lblngjtot')

    # Varahi Production
    varahi_value = india.read_value_from_span_id(html, 'lblvrhtot')

    # Kodsalli Production
    kodsalli_value = india.read_value_from_span_id(html, 'lblkdsltot')

    # Kadra Production
    kadra_value = india.read_value_from_span_id(html, 'lblkdrtot')

    # GERUSOPPA production
    gerusoppa_value = india.read_value_from_span_id(html, 'lblgrsptot')

    # JOG production
    jog_value = india.read_value_from_span_id(html, 'lbljogtot')

    # LPH Production
    lph_value = india.read_value_from_span_id(html, 'lbllphtot')

    # Supa production
    supa_value = india.read_value_from_span_id(html, 'lblsupatot')

    # SHIMSHA
    shimsha_value = india.read_value_from_span_id(html, 'lblshimtot')

    # SHIVASAMUDRA
    shivasamudra_value = india.read_value_from_span_id(html, 'lblshivtot')

    # MANIDAM
    manidam_value = india.read_value_from_span_id(html, 'lblmanitot')

    # MUNRABAD
    munrabad_value = india.read_value_from_span_id(html, 'lblmbdtot')

    # BHADRA
    bhadra_value = india.read_value_from_span_id(html, 'lblbdratot')

    # GHATAPRABHA
    ghataprabha_value = india.read_value_from_span_id(html, 'lblgtprtot')

    # ALMATTI
    almatti_value = india.read_value_from_span_id(html, 'lblalmttot')

    # Hydro production
    hydro_value = sharavati_value + nagjhari_value + varahi_value + kodsalli_value \
                  + kadra_value + gerusoppa_value + jog_value + lph_value + supa_value \
                  + shimsha_value + shivasamudra_value + manidam_value + munrabad_value \
                  + bhadra_value + ghataprabha_value + almatti_value

    # CGS Production
    # TODO: Search CGS production type
    cgs_value = india.read_value_from_span_id(html, 'lblcgs')

    # NCEP Production
    # TODO: Get NECP production freom http://kptclsldc.com/StateNCEP.aspx
    ncep_value = india.read_value_from_span_id(html, 'lblncep')

    # Unknown production
    unknown_value = cgs_value + ncep_value

    data = {
        'countryCode': country_code,
        'datetime': india_date_time.datetime,
        'production': {
            'biomass': 0.0,
            'coal': round(coal_value, 2),
            'gas': 0.0,
            'hydro': round(hydro_value, 2),
            'nuclear': 0.0,
            'oil': 0.0,
            'solar': None,
            'wind': None,
            'geothermal': 0.0,
            'unknown': round(unknown_value, 2)
        },
        'storage': {
            'hydro': 0.0
        },
        'source': 'kptclsldc.com',
    }

    return data


if __name__ == '__main__':
    session = Session()
    print fetch_production('IN-KA', session)
    print fetch_consumption('IN-KA', session)
