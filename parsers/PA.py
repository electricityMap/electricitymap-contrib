#!/usr/bin/env python3
# coding=utf-8

# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests
# The BeautifulSoup library is used to parse HTML
from bs4 import BeautifulSoup


def fetch_production(zone_key='PA', session=None, target_datetime=None, logger=None):
    """Requests the last known production mix (in MW) of a given country

    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'zoneKey': 'FR',
      'datetime': '2017-01-01T00:00:00Z',
      'production': {
          'biomass': 0.0,
          'coal': 0.0,
          'gas': 0.0,
          'hydro': 0.0,
          'nuclear': null,
          'oil': 0.0,
          'solar': 0.0,
          'wind': 0.0,
          'geothermal': 0.0,
          'unknown': 0.0
      },
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
    }
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    #Fetch page and load into BeautifulSoup
    r = session or requests.session()
    url = 'http://sitr.cnd.com.pa/m/pub/gen.html'
    response = r.get(url)
    response.encoding = 'utf-8'
    html_doc = response.text
    soup = BeautifulSoup(html_doc, 'html.parser')

    #Parse production from pie chart
    productions = soup.find('table', {'class': 'sitr-pie-layout'}).find_all('span')
    map_generation = {
      'Hídrica': 'hydro',
      'Eólica': 'wind',
      'Solar': 'solar',
      'Biogas': 'gas',
      'Térmica': 'unknown'
    }
    data = {
        'zoneKey': 'PA',
        'production': {
          #Setting default values here so we can do += when parsing the thermal generation breakdown
          'biomass': 0.0,
          'coal': 0.0,
          'gas': 0.0,
          'hydro': 0.0,
          'nuclear': 0.0,
          'oil': 0.0,
          'solar': 0.0,
          'wind': 0.0,
          'geothermal': 0.0,
          'unknown': 0.0,
        },
        'storage': {},
        'source': 'https://www.cnd.com.pa/',
    }
    for prod in productions:
        prod_data = prod.string.split(' ')
        production_mean = map_generation[prod_data[0]]
        production_value = float(prod_data[1])
        data['production'][production_mean] = production_value

    #Known fossil plants: parse, subtract from "unknown", add to "coal"/"oil"/"gas"
    thermal_production_breakdown = soup.find_all('table', {'class': 'sitr-table-gen'})[1]
    #Make sure the table header is indeed "Térmicas (MW)" (in case the tables are re-arranged)
    thermal_production_breakdown_table_header = thermal_production_breakdown.select('thead > tr > td > span')[0].string
    assert ('Térmicas' in thermal_production_breakdown_table_header), (
      "Exception when extracting thermal generation breakdown for {}: table header does not contain "
      "'Térmicas' but is instead named {}".format(zone_key, thermal_production_breakdown_table_header)
    )
    thermal_production_units = thermal_production_breakdown.select('tbody tr td table.sitr-gen-group tr')
    map_thermal_generation_unit_name_to_fuel_type = {
      'Cativá 1': 'oil',#[1][2]
      'Cativá 2': 'oil',#[1][2]
      'Cativá 3': 'oil',#[1][2]
      'Cativá 4': 'oil',#[1][2]
      'Cativá 5': 'oil',#[1][2]
      'Cativá 6': 'oil',#[1][2]
      'Cativá 7': 'oil',#[1][2]
      'Cativá 8': 'oil',#[1][2]
      'Cativá 9': 'oil',#[1][2]
      'Cativá 10': 'oil',#[1][2]
      'Cobre Panamá 1': 'coal',#[3]
      'Cobre Panamá 2': 'coal',#[3]
      'Costa Norte 1': 'gas',#[4][5]
      'Costa Norte 2': 'gas',#[4][5]
      'Costa Norte 3': 'gas',#[4][5]
      'Costa Norte 4': 'gas',#[4][5]
      #The BLM (Bahía Las Minas) plant has both coal and oil-fired units.[1][2]
      #Because I'm not 100% sure which ones burn oil and which ones coal, I'm leaving these as unknown for now
    }
    #Sources:
    #1. https://www.celsia.com/Portals/0/contenidos-celsia/accionistas-e-inversionistas/perfil-corporativo-US/presentaciones-US/2014/presentacion-morgan-ingles-v2.pdf
    #2. https://www.celsia.com/en/about-celsia/business-model/power-generation/thermoelectric-power-plants
    #3. https://endcoal.org/tracker/
    #4. http://aesmcac.com/aespanamades/en/colon/ "It reuses the heat from the exhaust gas from the gas turbines in order to obtain steam, to be later used by a steam turbine and to save fuel consumption in the production of electricity."
    #5. https://panamcham.com/sites/default/files/el_inicio_del_futuro_del_gas_natural_en_panama.pdf "3 gas turbines and 1 steam (3X1 configuration)" "Technology: Combined Cycle" | This and the previous source taken together seems to imply that the steam turbine is responsible for the second cycle of the CCGT plant, giving confidence that output from all four units should indeed be tallied under "gas". Furthermore, as the plant also has a LNG import facility it is most unlikely the steam turbine would be burning a different fuel such as coal or oil.
    for thermal_production_unit in thermal_production_units:
      unit_name_and_generation = thermal_production_unit.find_all('td')
      unit_name = unit_name_and_generation[0].string
      unit_generation = float(unit_name_and_generation[1].string)
      if(unit_name in map_thermal_generation_unit_name_to_fuel_type):
        unit_fuel_type = map_thermal_generation_unit_name_to_fuel_type[unit_name]
        data['production'][unit_fuel_type] += unit_generation#TODO should we ignore negative "generation"?
        data['production']['unknown'] -= unit_generation

    # Parse the datetime and return a python datetime object
    spanish_date = soup.find('div', {'class': 'sitr-update'}).find('span').string
    date = arrow.get(spanish_date, 'DD-MMMM-YYYY H:mm:ss', locale="es", tzinfo="America/Panama")
    data['datetime'] = date.datetime

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
