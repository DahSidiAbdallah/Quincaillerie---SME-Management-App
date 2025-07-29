import requests
import json
import sys
import os

"""
Test script for the inventory API endpoint
Usage: python api_test_inventory.py

This script will:
1. Login to get a session cookie
2. Make a request to the inventory products API
3. Display the results
"""

BASE_URL = "http://localhost:5000"  # Update if your app runs on a different port

def test_inventory_api():
    print("Testing Inventory API...")
    
    # Step 1: Login to get a session cookie
    login_url = f"{BASE_URL}/api/auth/login"
    login_data = {
        "username": "admin",  # Replace with your test username
        "pin": "1234"  # Replace with your test PIN
    }
    
    print(f"\n1. Logging in to {login_url}...")
    try:
        login_response = requests.post(
            login_url, 
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed with status code: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
            
        print(f"✅ Login successful: {login_response.status_code}")
        
        # Extract cookies from login response
        cookies = login_response.cookies
        print(f"Cookies received: {[f'{c.name}={c.value}' for c in cookies]}")
        
    except Exception as e:
        print(f"❌ Error during login: {str(e)}")
        return
    
    # Step 2: Make a request to the inventory products API
    inventory_url = f"{BASE_URL}/api/inventory/products"
    
    print(f"\n2. Fetching inventory from {inventory_url}...")
    try:
        # Make request with cookies from login
        inventory_response = requests.get(
            inventory_url,
            cookies=cookies,
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json"
            }
        )
        
        # Print response details
        print(f"Response Status: {inventory_response.status_code}")
        print(f"Response Headers: {dict(inventory_response.headers)}")
        
        if inventory_response.status_code != 200:
            print(f"❌ Inventory API request failed with status code: {inventory_response.status_code}")
            print(f"Response: {inventory_response.text[:500]}...")
            return
            
        # Try to parse JSON response
        try:
            data = inventory_response.json()
            print("\n3. Response Data:")
            print(f"Success: {data.get('success', False)}")
            print(f"Message: {data.get('message', 'No message')}")
            
            products = data.get('products', [])
            print(f"Products count: {len(products)}")
            
            if products and len(products) > 0:
                print("\nFirst 3 products:")
                for i, product in enumerate(products[:3]):
                    print(f"  Product {i+1}: {product.get('name')} (ID: {product.get('id')})")
            
            # Pretty print the full response
            print("\nFull Response (formatted):")
            print(json.dumps(data, indent=2))
            
        except json.JSONDecodeError:
            print("❌ Response is not valid JSON:")
            print(inventory_response.text[:500])
            
    except Exception as e:
        print(f"❌ Error fetching inventory: {str(e)}")

if __name__ == "__main__":
    test_inventory_api()
