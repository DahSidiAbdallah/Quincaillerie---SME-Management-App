#!/usr/bin/env python3
import requests
import json

def test_dashboard_apis():
    session = requests.Session()
    
    print('=== Testing Dashboard APIs ===')
    
    # Login first
    login_resp = session.post('http://localhost:5000/login', json={'username': 'admin', 'pin': '1234'})
    print(f'Login Status: {login_resp.status_code}')
    
    # Test top products
    print('\n--- Top Products ---')
    top_resp = session.get('http://localhost:5000/api/dashboard/top-products')
    print(f'Status: {top_resp.status_code}')
    
    if top_resp.status_code == 200:
        data = top_resp.json()
        print('Success:', data.get('success'))
        print('Full response:', json.dumps(data, indent=2))
        
        if data.get('products'):
            print(f'Products count: {len(data["products"])}')
            for i, product in enumerate(data['products'][:3]):
                print(f'  {i+1}. {product["name"]} - {product["total_sales"]} MRU ({product["quantity_sold"]} units)')
    else:
        print('Error response:', top_resp.text)
    
    # Test sales chart
    print('\n--- Sales Chart ---')
    chart_resp = session.get('http://localhost:5000/api/dashboard/sales-chart')
    print(f'Status: {chart_resp.status_code}')
    
    if chart_resp.status_code == 200:
        data = chart_resp.json()
        print('Success:', data.get('success'))
        print('Full response:', json.dumps(data, indent=2))
        
        if data.get('daily'):
            print('Daily labels:', data['daily']['labels'])
            print('Daily data:', data['daily']['data'])
            print('Has non-zero data:', any(x > 0 for x in data['daily']['data']))
    else:
        print('Error response:', chart_resp.text)

if __name__ == "__main__":
    test_dashboard_apis()
