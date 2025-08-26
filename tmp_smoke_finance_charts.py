import requests

base = 'http://127.0.0.1:5000'
params = {'period': 'month'}
try:
    resp = requests.get(base + '/api/finance/charts', params=params, timeout=10)
    print('status', resp.status_code, resp.headers.get('content-type'))
    print(resp.text[:4000])
except Exception as e:
    print('error', e)
