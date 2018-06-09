#!/usr/bin/env python3

import arrow
import requests
import datetime

# Website for reference: http://109.224.53.139:8080/IPS.php
# URL of Iraqi Power System dashboard-API:

url = 'http://109.224.53.139:8080/api.php'


def fetch_production(zone_key='IQ', session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    r = session or requests.session()
    response = r.get(url)
    iraq_json = response.json()
    iraq_data = iraq_json['d']
    iraq_time = iraq_json['lastmodified']

    # Time of dataset shown as "Last Update"
    
    local_date_time = datetime.datetime.strptime(iraq_json['lastmodified'], "%I:%M:%S %p %d-%m-%Y")
    zone_date_time = arrow.Arrow.fromdatetime(local_date_time, 'Asia/Baghdad')

    # Summarized data for Iraq
    
    thermal = iraq_data['d_1218']
    gas = iraq_data['d_1219']
    hydro = iraq_data['d_1220']
    diesel = iraq_data['d_1221'] 
  
    production = {
            'zoneKey': zone_key,
            'datetime': zone_date_time.datetime,
            'production': {
                'gas': gas,
                'hydro': hydro,
                'oil': round(diesel + thermal, 1)
                },
            'storage': {},
            'source': 'Iraqi Power System'
            }

    return production


def fetch_consumption(zone_key = 'IQ', session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')
    
    r = session or requests.session()
    response = r.get(url)
    iraq_json = response.json()
    iraq_consumption = iraq_json['d']['d_1234']
    iraq_time = iraq_json['lastmodified']

    local_date_time = datetime.datetime.strptime(iraq_json['lastmodified'], "%I:%M:%S %p %d-%m-%Y")
    zone_date_time = arrow.Arrow.fromdatetime(local_date_time, 'Asia/Baghdad')
        
    consumption = {
            'zoneKey': zone_key,
            'datetime': zone_date_time.datetime,
            'consumption': iraq_consumption,
            'source': 'Iraqi Power System'
            }

    return consumption
    


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None):
   
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    sortedZoneKeys = '->'.join(sorted([zone_key1, zone_key2]))

    r = session or requests.session()
    response = r.get(url)
    iraq_json = response.json()
    iraq_exch = iraq_json['d']
    iraq_time = iraq_json['lastmodified']

    #    tie_line_mapping = {
    #                'IQ->IR':{'d_1226 = MERSAD',
    #                          'd_1227 = KRKH',
    #                          'd_1228 = KRMS',
    #                          'd_1229 = SBZB'},
    #                'IQ->IQ-KUR':'d_1230 = KURDISTAN'
    #                }
    
    if sortedZoneKeys == 'IQ->IR':
        netflow = -1 * (iraq_exch['d_1226'] +
                        iraq_exch['d_1227'] +
                        iraq_exch['d_1228'] +
                        iraq_exch['d_1229']
                        )
    elif sortedZoneKeys == 'IQ->IQ-KUR':
        netflow = -1 * iraq_exch['d_1230']
    else:
        raise NotImplementedError('This exchange pair is not implemented')

    local_date_time = datetime.datetime.strptime(iraq_time, "%I:%M:%S %p %d-%m-%Y")
    zone_date_time = arrow.Arrow.fromdatetime(local_date_time, 'Asia/Baghdad')

    exchange = {
        'sortedZoneKeys': sortedZoneKeys,
        'datetime': zone_date_time.datetime,
        'netFlow': netflow,
        'source': 'Iraqi Power System'
    }

    return exchange

        
print(fetch_production())
print(fetch_consumption())
print(fetch_exchange('IQ', 'IR'))
print(fetch_exchange('IQ', 'IQ-KUR'))
