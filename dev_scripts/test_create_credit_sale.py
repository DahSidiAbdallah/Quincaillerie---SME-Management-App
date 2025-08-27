import requests
from datetime import datetime, timedelta

BASE = 'http://127.0.0.1:5000'

s = requests.Session()
# Login
r = s.post(f'{BASE}/api/auth/login', json={'username':'admin','pin':'1234'})
print('login', r.status_code, r.text)

# Get a product id
r = s.get(f'{BASE}/api/inventory/products')
products = r.json().get('products', []) if r.ok else []
if not products:
    print('no products, cannot create sale')
    raise SystemExit(1)
product = products[0]
print('using product', product.get('id'), product.get('name'))

# Create a credit sale with due date tomorrow
tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
items = [{'product_id': product['id'], 'quantity': 1, 'unit_price': product.get('sale_price') or product.get('price') or 100}]

data = {
    'sale_items': items,
    'total_amount': items[0]['unit_price'] * items[0]['quantity'],
    'paid_amount': 0,  # credit
    'payment_method': 'credit',
    'credit_due_date': tomorrow,
    'customer_name': 'Test Buyer',
    'customer_phone': '000'
}

r = s.post(f'{BASE}/api/sales/sales', json=data)
print('create sale', r.status_code, r.text)

# Fetch recent sales and find our Test Buyer entry
r = s.get(f'{BASE}/api/sales?limit=10')
print('sales list', r.status_code)
if r.ok:
    sales = r.json().get('sales', [])
    for sitem in sales:
        if sitem.get('customer_name') == 'Test Buyer':
            print('found', sitem['id'], 'status=', sitem.get('status'))
            break
    else:
        print('not found in recent sales')
else:
    print('failed to fetch sales')
