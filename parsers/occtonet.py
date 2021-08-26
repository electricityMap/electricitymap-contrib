#!/usr/bin/env python3
# coding=utf-8
import logging
import datetime
import pandas as pd
# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

from io import StringIO

# Abbreviations:
# JP-HKD : Hokkaido
# JP-TH  : Tohoku (incl. Niigata)
# JP-TK  : Tokyo area (Kanto)
# JP-CB  : Chubu
# JP-HR  : Hokuriku
# JP-KN  : Kansai
# JP-CG  : Chugoku
# JP-SK  : Shikoku
# JP-KY  : Kyushu
# JP-ON  : Okinawa


exchange_mapping = {
    'JP-HKD->JP-TH':[1],
    'JP-TH->JP-TK':[2],
    'JP-CB->JP-TK':[3],
    'JP-CB->JP-KN':[4],
    'JP-CB->JP-HR':[5,11],
    'JP-HR->JP-KN':[6],
    'JP-CG->JP-KN':[7],
    'JP-KN->JP-SK':[8],
    'JP-CG->JP-SK':[9],
    'JP-CG->JP-KY':[10]
    }


def fetch_exchange(zone_key1='JP-TH', zone_key2='JP-TK', session=None,
                   target_datetime=None, logger=logging.getLogger(__name__)) -> dict:
    """Requests the last known power exchange (in MW) between two zones."""
    #get target date in time zone Asia/Tokyo
    query_date = arrow.get(target_datetime).to('Asia/Tokyo').strftime('%Y/%m/%d')

    sortedZoneKeys = '->'.join(sorted([zone_key1, zone_key2]))
    exch_id = exchange_mapping[sortedZoneKeys]
    r = session or requests.session()
    # Login to occtonet
    Cookies = get_cookies(r)
    # Get headers for querying exchange
    Headers = get_headers(r, exch_id[0], query_date, Cookies)
    # Add request tokens to headers
    Headers = get_request_token(r, Headers, Cookies)
    # Query data
    df = get_exchange(r, Headers, Cookies)

    # CB-HR -exceptions
    if sortedZoneKeys == 'JP-CB->JP-HR':

        df = df.set_index(['Date', 'Time'])

        Headers = get_headers(r, exch_id[1], query_date, Cookies)
        Headers = get_request_token(r, Headers, Cookies)

        df2 = get_exchange(r, Headers, Cookies)
        df2 = df2.set_index(['Date', 'Time'])

        df = df + df2
        df = df.reset_index()

    # fix occurrences of 24:00hrs
    list24 = list(df.index[df['Time']=='24:00'])
    for idx in list24:
        df.loc[idx, 'Date'] = arrow.get(df.loc[idx, 'Date']).shift(days=1).strftime('%Y/%m/%d')
        df.loc[idx, 'Time'] = '00:00'
    # correct flow direction, if needed
    flows_to_revert = ['JP-CB->JP-TK', 'JP-CG->JP-KN', 'JP-CG->JP-SK']
    if sortedZoneKeys in flows_to_revert:
        df['netFlow'] = -1 * df['netFlow']

    df['source'] = 'occtonet.occto.or.jp'
    df['datetime'] = df.apply(parse_dt, axis=1)

    df['sortedZoneKeys'] = sortedZoneKeys
    df = df[['source', 'datetime', 'netFlow', 'sortedZoneKeys']]

    results = df.to_dict('records')
    for result in results:
        result['datetime'] = result['datetime'].to_pydatetime()
    return results


def fetch_exchange_forecast(zone_key1='JP-TH', zone_key2='JP-TK', session=None,
                            target_datetime=None, logger=logging.getLogger(__name__)) -> list:
    """Gets exchange forecast between two specified zones."""
    #get target date in time zone Asia/Tokyo
    query_date = arrow.get(target_datetime).to('Asia/Tokyo').strftime('%Y/%m/%d')
    # Forecasts ahead of current date are not available
    if query_date > arrow.get().to('Asia/Tokyo').strftime('%Y/%m/%d'):
        raise NotImplementedError(
            "Future dates(local time) not implemented for selected exchange")

    sortedZoneKeys = '->'.join(sorted([zone_key1, zone_key2]))
    exch_id = exchange_mapping[sortedZoneKeys]
    # Login to occtonet
    r = session or requests.session()
    Cookies = get_cookies(r)
    Headers = get_headers(r, exch_id[0], query_date, Cookies)
    # Query data
    Headers = get_request_token(r, Headers, Cookies)
    df = get_exchange_fcst(r, Headers, Cookies)
    # CB-HR -exceptions
    if sortedZoneKeys == 'JP-CB->JP-HR':

        df = df.set_index(['Date', 'Time'])
        Headers = get_headers(r, exch_id[1], query_date, Cookies)
        Headers = get_request_token(r, Headers, Cookies)
        df2 = get_exchange_fcst(r, Headers, Cookies)
        df2 = df2.set_index(['Date', 'Time'])
        df = df + df2
        df = df.reset_index()

    # fix possible occurrences of 24:00hrs
    list24 = list(df.index[df['Time']=='24:00'])
    for idx in list24:
        df.loc[idx, 'Date'] = arrow.get(str(df.loc[idx, 'Date'])).shift(days=1).strftime('%Y/%m/%d')
        df.loc[idx, 'Time'] = '00:00'
    # correct flow direction, if needed
    flows_to_revert = ['JP-CB->JP-TK', 'JP-CG->JP-KN', 'JP-CG->JP-SK']
    if sortedZoneKeys in flows_to_revert:
        df['netFlow'] = -1 * df['netFlow']
    # Add zonekey, source
    df['source'] = 'occtonet.occto.or.jp'
    df['datetime'] = df.apply(parse_dt, axis=1)
    df['sortedZoneKeys'] = sortedZoneKeys
    df = df[['source', 'datetime', 'netFlow', 'sortedZoneKeys']]
    # Format output
    results = df.to_dict('records')
    for result in results:
        result['datetime'] = result['datetime'].to_pydatetime()
    return results


def get_cookies(session=None):
    s = session or requests.session()
    s.get('http://occtonet.occto.or.jp/public/dfw/RP11/OCCTO/SD/LOGIN_login')
    return s.cookies


def get_headers(session, exch_id, date, cookies):
    payload = {
            'ajaxToken':'',
            'downloadKey':'',
            'fwExtention.actionSubType':'headerInput',
            'fwExtention.actionType':'reference',
            'fwExtention.formId':'CA01S070P',
            'fwExtention.jsonString':'',
            'fwExtention.pagingTargetTable':'',
            'fwExtention.pathInfo':'CA01S070C',
            'fwExtention.prgbrh':'0',
            'msgArea':'',
            'requestToken':'',
            'requestTokenBk':'',
            'searchReqHdn':'',
            'simFlgHdn':'',
            'sntkTgtRklCdHdn':'',
            'spcDay':date,
            'spcDayHdn':'',
            'tgtRkl':'{:02d}'.format(exch_id),
            'transitionContextKey':'DEFAULT',
            'updDaytime':''
          }
    s = session
    r = s.post('http://occtonet.occto.or.jp/public/dfw/RP11/OCCTO/SD/CA01S070C?fwExtention.pathInfo=CA01S070C&fwExtention.prgbrh=0',
                   cookies=cookies, data=payload)
    headers=r.text
    headers = eval(headers.replace('false', 'False').replace('null', 'None'))
    if headers['root']['errMessage']:
        raise RuntimeError('Headers not available due to {}'.format(headers['root']['errMessage']))
    else:
        payload['msgArea'] = headers['root']['bizRoot']['header']['msgArea']['value']
        payload['searchReqHdn'] = headers['root']['bizRoot']['header']['searchReqHdn']['value']
        payload['spcDayHdn'] = headers['root']['bizRoot']['header']['spcDayHdn']['value']
        payload['updDaytime'] = headers['root']['bizRoot']['header']['updDaytime']['value']
    return payload


def get_request_token(session, payload, cookies):
    s = session
    payload['fwExtention.actionSubType']='ok'
    r = s.post('http://occtonet.occto.or.jp/public/dfw/RP11/OCCTO/SD/CA01S070C?'
               +'fwExtention.pathInfo=CA01S070C&fwExtention.prgbrh=0',
               cookies=cookies, data=payload)
    headers=r.text
    headers = eval(headers.replace('false', 'False').replace('null', 'None'))
    if headers['root']['errFields']:
        raise RuntimeError('Request token not available due to {}'.format(headers['root']['errFields']))
    else:
        payload['downloadKey'] = headers['root']['bizRoot']['header']['downloadKey']['value']
        payload['requestToken'] = headers['root']['bizRoot']['header']['requestToken']['value']
    return payload


def get_exchange(session, payload, cookies):
    s = session
    payload['fwExtention.actionSubType']='download'
    r = s.post('http://occtonet.occto.or.jp/public/dfw/RP11/OCCTO/SD/CA01S070C?'
               +'fwExtention.pathInfo=CA01S070C&fwExtention.prgbrh=0',
               cookies=cookies, data=payload)
    r.encoding = 'shift-jis'
    df = pd.read_csv(StringIO(r.text), delimiter=',')
    df = df[['対象日付', '対象時刻', '潮流実績']]
    df.columns = ['Date', 'Time', 'netFlow']
    df = df.dropna()
    return df


def get_exchange_fcst(session, payload, cookies):
    s = session
    payload['fwExtention.actionSubType']='download'
    r = s.post('http://occtonet.occto.or.jp/public/dfw/RP11/OCCTO/SD/CA01S070C?fwExtention.pathInfo=CA01S070C&fwExtention.prgbrh=0',
                   cookies=cookies, data=payload)
    r.encoding = 'shift-jis'
    df = pd.read_csv(StringIO(r.text), delimiter=',')
    df = df[['対象日付', '対象時刻', '計画潮流(順方向)']]
    df.columns = ['Date', 'Time', 'netFlow']
    df = df.dropna()
    return df


def parse_dt(row):
    return arrow.get(' '.join([row['Date'], row['Time']]).replace('/', '-')).replace(tzinfo='Asia/Tokyo').datetime


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_exchange(JP-CB, JP-HR) ->')
    print(fetch_exchange('JP-CB', 'JP-HR')[-3:])
    print('fetch_exchange(JP-CG, JP-KY) ->')
    print(fetch_exchange('JP-CG', 'JP-KY')[-3:])
    print('fetch_exchange_forecast(JP-CB, JP-HR) ->')
    print(fetch_exchange_forecast('JP-CB', 'JP-HR')[-3:])
    print('fetch_exchange_forecast(JP-CG, JP-KY) ->')
    print(fetch_exchange_forecast('JP-CG', 'JP-KY')[-3:])
