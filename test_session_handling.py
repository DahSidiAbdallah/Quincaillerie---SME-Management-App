#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Test Script for Inventory Session Handling
This script tests the login flow and ensures inventory products are accessible
"""

import requests
import json
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Base URL for our application
BASE_URL = "http://localhost:5000"

def test_login_and_inventory():
    """Test the login flow and fetch inventory products"""
    
    # Create a session to persist cookies
    session = requests.Session()
    
    # Step 1: Test the login
    logger.info("STEP 1: Testing login...")
    login_url = f"{BASE_URL}/api/auth/login"
    login_data = {
        "username": "admin",
        "pin": "1234"
    }
    
    login_response = session.post(
        login_url,
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    logger.info(f"Login response status code: {login_response.status_code}")
    try:
        login_json = login_response.json()
        logger.info(f"Login response: {json.dumps(login_json, indent=2)}")
        
        if not login_json.get('success'):
            logger.error("Login failed!")
            return False
            
        logger.info(f"Login successful for user: {login_json['user']['username']}")
    except Exception as e:
        logger.error(f"Error parsing login response: {e}")
        return False
    
    # Step 2: Check auth status
    logger.info("\nSTEP 2: Checking authentication status...")
    auth_status_url = f"{BASE_URL}/api/auth/status"
    
    auth_status_response = session.get(auth_status_url)
    logger.info(f"Auth status response code: {auth_status_response.status_code}")
    
    try:
        auth_status_json = auth_status_response.json()
        logger.info(f"Auth status response: {json.dumps(auth_status_json, indent=2)}")
        
        if not auth_status_json.get('authenticated'):
            logger.error("Not authenticated according to status check!")
            return False
            
        logger.info(f"Authenticated as: {auth_status_json['user']['username']}")
    except Exception as e:
        logger.error(f"Error parsing auth status response: {e}")
        return False
    
    # Step 3: Fetch inventory products
    logger.info("\nSTEP 3: Fetching inventory products...")
    inventory_url = f"{BASE_URL}/api/inventory/products"
    
    # Show the cookies we have
    logger.info(f"Cookies in session: {session.cookies.get_dict()}")
    
    inventory_response = session.get(inventory_url)
    logger.info(f"Inventory response status code: {inventory_response.status_code}")
    
    if inventory_response.status_code == 401:
        logger.error("Unauthorized! Session cookies not working correctly.")
        return False
    
    try:
        inventory_json = inventory_response.json()
        product_count = len(inventory_json.get('products', []))
        logger.info(f"Found {product_count} products")
        
        if product_count > 0:
            # Show the first product as a sample
            logger.info(f"Sample product: {json.dumps(inventory_json['products'][0], indent=2)}")
            
        logger.info(f"Stats: {json.dumps(inventory_json.get('stats', {}), indent=2)}")
        return True
    except Exception as e:
        logger.error(f"Error parsing inventory response: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting comprehensive session test...")
    success = test_login_and_inventory()
    
    if success:
        logger.info("\n✅ TEST PASSED: Login and inventory fetch successful!")
    else:
        logger.error("\n❌ TEST FAILED: Issues with login or inventory fetch")
