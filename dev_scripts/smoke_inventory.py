import requests, sys, json

BASE = 'http://127.0.0.1:5000'
s = requests.Session()

print('Autologin…', end=' ')
resp = s.get(f'{BASE}/autologin/inventory', allow_redirects=True)
print(resp.status_code)

# 1) Stats
r = s.get(f'{BASE}/api/inventory/stats')
print('stats:', r.status_code, r.text[:200])

# 2) Products
r = s.get(f'{BASE}/api/inventory/products')
print('products:', r.status_code)
try:
    data = r.json()
    products = data.get('products', []) if isinstance(data, dict) else []
except Exception:
    products = []
print('products count:', len(products))

# 3) Low stock
r = s.get(f'{BASE}/api/inventory/low-stock')
print('low-stock:', r.status_code, r.text[:150])

# 4) If we have a product, fetch details and try a dry adjust scenario (set same stock so no change)
if products:
    pid = products[0].get('id')
    print('first product id:', pid)
    r = s.get(f'{BASE}/api/inventory/products/{pid}')
    print('product details:', r.status_code)
    try:
        det = r.json().get('product', {})
        curr = det.get('current_stock', 0)
    except Exception:
        curr = 0
    payload = {
        'product_id': pid,
        'adjustment_type': 'set',
        'quantity': curr,
        'reason': 'smoke_test',
        'notes': 'no-op set to current'
    }
    r = s.post(f'{BASE}/api/inventory/adjust-stock', json=payload)
    print('adjust-stock (no-op):', r.status_code, r.text[:120])

# 5) Inventory count (no adjust)
count_payload = {
    'reference': 'SMOKE-COUNT',
    'notes': 'smoke test',
    'adjust_stock': False,
    'counts': [
        {'product_id': products[0]['id'], 'counted_qty': products[0].get('current_stock', 0)}
    ] if products else []
}
r = s.post(f'{BASE}/api/inventory/inventory-count', json=count_payload)
print('inventory-count:', r.status_code, r.text[:160])

print('DONE')
