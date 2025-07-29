#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct API test script
"""

import os
import sys
import json
import sqlite3
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Application base URL
BASE_URL = "http://localhost:5000"

def test_api_endpoints():
    """Test API endpoints directly"""
    
    # 1. Login first to get session cookie
    logger.info("Testing login...")
    login_payload = {
        "username": "admin",
        "pin": "1234"
    }
    
    session = requests.Session()
    login_response = session.post(f"{BASE_URL}/api/auth/login", json=login_payload)
    logger.info(f"Login response: {login_response.status_code}")
    
    if login_response.status_code != 200:
        logger.error("Login failed. Make sure the application is running.")
        return
    
    login_data = login_response.json()
    logger.info(f"Login result: {json.dumps(login_data)}")
    
    if not login_data.get('success'):
        logger.error("Login failed. Check credentials.")
        return
    
    # 2. Test customers API
    logger.info("\nTesting customers API...")
    customers_response = session.get(f"{BASE_URL}/api/customers")
    customers_data = customers_response.json()
    
    logger.info(f"Customers API response: {json.dumps(customers_data)}")
    
    if customers_data.get('success'):
        logger.info(f"Found {len(customers_data.get('customers', []))} customers:")
        for customer in customers_data.get('customers', []):
            logger.info(f"  ID: {customer.get('id')}, Name: {customer.get('name')}")
    else:
        logger.error("Failed to get customers data")
    
    # 3. Test sales API
    logger.info("\nTesting sales API...")
    sales_response = session.get(f"{BASE_URL}/api/sales")
    sales_data = sales_response.json()
    
    logger.info(f"Sales API response: {json.dumps(sales_data)}")
    
    if sales_data.get('success'):
        logger.info(f"Found {len(sales_data.get('sales', []))} sales:")
        for sale in sales_data.get('sales', []):
            logger.info(f"  ID: {sale.get('id')}, Date: {sale.get('sale_date')}, Customer: {sale.get('customer_name')}, Amount: {sale.get('total_amount')}")
    else:
        logger.error("Failed to get sales data")
    
    # 4. Test inventory API
    logger.info("\nTesting inventory API...")
    inventory_response = session.get(f"{BASE_URL}/api/inventory/products")
    inventory_data = inventory_response.json()
    
    if inventory_data.get('success'):
        logger.info(f"Found {len(inventory_data.get('products', []))} products:")
        for product in inventory_data.get('products', [])[:3]:  # Show just first 3 for brevity
            logger.info(f"  ID: {product.get('id')}, Name: {product.get('name')}, Stock: {product.get('current_stock')}")
        
        if len(inventory_data.get('products', [])) > 3:
            logger.info(f"  ... and {len(inventory_data.get('products', [])) - 3} more products")
    else:
        logger.error("Failed to get inventory data")

def main():
    """Main function"""
    logger.info("Starting direct API tests")
    
    try:
        test_api_endpoints()
    except Exception as e:
        logger.error(f"Error testing API endpoints: {e}")
    
    logger.info("API tests completed")

if __name__ == "__main__":
    main()
