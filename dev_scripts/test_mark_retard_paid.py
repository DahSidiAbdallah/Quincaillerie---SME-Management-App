import requests

BASE = 'http://127.0.0.1:5000'

s = requests.Session()
# Login
r = s.post(f'{BASE}/api/auth/login', json={'username':'admin','pin':'1234'})
print('login', r.status_code, r.text)

# Find a sale with status 'retard'
r = s.get(f'{BASE}/api/sales?limit=100')
if not r.ok:
    print('failed to fetch sales'); raise SystemExit(1)
sales = r.json().get('sales', [])
ret = None
for sale in sales:
    if sale.get('status') == 'retard':
        ret = sale
        break

print('found', ret and ret.get('id'))
if not ret:
    print('no retard sale found; exiting')
    raise SystemExit(0)

# Mark it paid
sale_id = ret['id']
r = s.put(f'{BASE}/api/sales/sales/{sale_id}/status', json={'status':'paid'})
print('mark paid', r.status_code, r.text)

# Verify
r = s.get(f'{BASE}/api/sales/{sale_id}')
print('fetch detail', r.status_code, r.text)
