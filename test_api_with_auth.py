#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Test with Authentication
"""

import os
import sys
import json
import requests
from pprint import pprint

# Add the app directory to the path
app_dir = os.path.abspath(os.path.dirname(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# URLs
BASE_URL = "http://localhost:5000"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
PRODUCTS_URL = f"{BASE_URL}/api/inventory/products"
CUSTOMERS_URL = f"{BASE_URL}/api/customers"
STATS_URL = f"{BASE_URL}/api/inventory/stats"

def login_and_get_session():
    """Log in to the application and get a session cookie"""
    print("Logging in...")
    
    # Login credentials - change these to match existing users
    payload = {
        "username": "admin",
        "pin": "1234"
    }
    
    # Create a session
    session = requests.Session()
    
    # Try to login
    try:
        response = session.post(LOGIN_URL, json=payload)
        print(f"Login Status Code: {response.status_code}")
        
        # Print response
        try:
            data = response.json()
            print("Login Response:")
            pprint(data)
        except:
            print(f"Raw response: {response.text}")
        
        if response.status_code == 200:
            print("Login successful. Session established.")
            return session
        else:
            print("Login failed.")
            return None
    except Exception as e:
        print(f"Error during login: {e}")
        return None

def test_api_endpoints(session):
    """Test various API endpoints"""
    if not session:
        print("No session provided. Cannot test endpoints.")
        return
    
    # Test inventory/products endpoint
    print("\n=== Testing Inventory/Products Endpoint ===")
    try:
        response = session.get(PRODUCTS_URL)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success', False)}")
            
            products = data.get('products', [])
            print(f"Products Count: {len(products)}")
            
            if products:
                print("First product:")
                pprint(products[0])
            
            stats = data.get('stats', {})
            print("Stats:")
            pprint(stats)
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error testing products endpoint: {e}")
    
    # Test customers endpoint
    print("\n=== Testing Customers Endpoint ===")
    try:
        response = session.get(CUSTOMERS_URL)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success', False)}")
            
            customers = data.get('customers', [])
            print(f"Customers Count: {len(customers)}")
            
            if customers:
                print("All customers:")
                for customer in customers:
                    print(f"ID: {customer.get('id')}, Name: {customer.get('name')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error testing customers endpoint: {e}")

def main():
    """Main function"""
    print("API Test with Authentication")
    
    # Login and get session
    session = login_and_get_session()
    
    # Test endpoints
    if session:
        test_api_endpoints(session)
    else:
        print("Cannot proceed with API tests without authentication.")

if __name__ == "__main__":
    main()
