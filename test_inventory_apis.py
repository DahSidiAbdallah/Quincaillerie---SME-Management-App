#!/usr/bin/env python3
import requests
import json

def test_inventory_apis():
    session = requests.Session()
    
    print('=== Testing Inventory API ===')
    
    # Login first
    login_resp = session.post('http://localhost:5000/login', json={'username': 'admin', 'pin': '1234'})
    print(f'Login Status: {login_resp.status_code}')
    
    # Test inventory stats
    print('\n--- Inventory Stats ---')
    stats_resp = session.get('http://localhost:5000/api/inventory/stats')
    print(f'Status: {stats_resp.status_code}')
    if stats_resp.status_code == 200:
        data = stats_resp.json()
        print('Stats:', json.dumps(data.get('stats', {}), indent=2))
    else:
        print('Error:', stats_resp.text[:200])
    
    # Test inventory products
    print('\n--- Inventory Products ---')
    products_resp = session.get('http://localhost:5000/api/inventory/products')
    print(f'Status: {products_resp.status_code}')
    if products_resp.status_code == 200:
        data = products_resp.json()
        print(f'Success: {data.get("success")}')
        print(f'Products count: {len(data.get("products", []))}')
        if data.get('products'):
            for i, product in enumerate(data['products'][:3]):
                print(f'  {i+1}. {product["name"]} - Stock: {product["current_stock"]}')
        
        # Check if stats are included
        if data.get('stats'):
            print('\nIncluded stats:')
            print(f'  Total products: {data["stats"].get("total", 0)}')
            print(f'  Low stock: {data["stats"].get("low_stock", 0)}')
            print(f'  Inventory value: {data["stats"].get("inventory_value", 0)}')
    else:
        print('Error:', products_resp.text[:200])

if __name__ == "__main__":
    test_inventory_apis()
