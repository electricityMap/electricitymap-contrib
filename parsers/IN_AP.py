from requests import Session
from arrow import get
from parsers import countrycode
from parsers import web


def read_date_time(html):
    """Read date time from html code"""
    date_time_span = html.find('span', {'id': 'lblPowerStatusDate'})
    india_date_time = date_time_span.text + ' Asia/Kolkata'
    return get(india_date_time, 'DD-MM-YYYY HH:mm ZZZ')


def fetch_production(country_code='IN-AP', session=None):
    """Fetch Andhra Pradesh  production"""
    countrycode.assert_country_code(country_code, 'IN-AP')

    html = web.get_response_soup(country_code,
                                 'http://www.core.ap.gov.in/CMDashBoard/UserInterface/Power/PowerReport.aspx', session)
    india_date = read_date_time(html)

    hydro_value = html.find('span', {'id': 'lblHydel'}).text
    gas_value = html.find('span', {'id': 'lblGas'}).text
    wind_value = html.find('span', {'id': 'lblWind'}).text
    solar_value = html.find('span', {'id': 'lblSolar'}).text

    # All thermal centrals are considered coal based production
    # https://en.wikipedia.org/wiki/Power_sector_of_Andhra_Pradesh
    thermal_value = html.find('span', {'id': 'lblThermal'}).text

    cgs_value = html.find('span', {'id': 'lblCGS'}).text
    ipp_value = html.find('span', {'id': 'lblIPPS'}).text

    data = {
        'countryCode': country_code,
        'datetime': india_date.datetime,
        'production': {
            'biomass': 0.0,
            'coal': float(thermal_value),
            'gas': float(gas_value),
            'hydro': float(hydro_value),
            'nuclear': 0.0,
            'oil': 0.0,
            'solar': float(solar_value),
            'wind': float(wind_value),
            'geothermal': 0.0,
            'unknown': round(float(cgs_value) + float(ipp_value), 2)
        },
        'storage': {
            'hydro': 0.0
        },
        'source': 'core.ap.gov.in',
    }

    return data


def fetch_consumption(country_code='IN-AP', session=None):
    """Fetch Andhra Pradesh consumption"""
    countrycode.assert_country_code(country_code, 'IN-AP')

    html = web.get_response_soup(country_code,
                                 'http://www.core.ap.gov.in/CMDashBoard/UserInterface/Power/PowerReport.aspx', session)
    india_date = read_date_time(html)

    demand_value = html.find('span', {'id': 'lblGridDemand'}).text

    data = {
        'countryCode': country_code,
        'datetime': india_date.datetime,
        'consumption': float(demand_value),
        'source': 'core.ap.gov.in'
    }

    return data


if __name__ == '__main__':
    session = Session()
    print fetch_production('IN-AP', session)
    print fetch_consumption('IN-AP', session)

