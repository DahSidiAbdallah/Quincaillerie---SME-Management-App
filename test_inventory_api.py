#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inventory API Test Script
"""

import os
import sys
import requests
import json
import logging
from flask import Flask, render_template, send_from_directory

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app for serving the test HTML
app = Flask(__name__)

@app.route('/')
def serve_test_page():
    return send_from_directory('.', 'login_test.html')

def test_auth_api():
    """Test authentication API"""
    base_url = "http://localhost:5000"
    
    # Test login
    login_url = f"{base_url}/api/auth/login"
    login_data = {
        "username": "admin",
        "pin": "1234"
    }
    
    try:
        logger.info(f"Trying to log in as {login_data['username']}...")
        login_response = requests.post(login_url, json=login_data)
        logger.info(f"Login response: {login_response.status_code}")
        logger.info(login_response.text)
        
        if login_response.ok:
            # Save cookies for subsequent requests
            cookies = login_response.cookies
            
            # Test auth status
            logger.info("Checking authentication status...")
            status_response = requests.get(f"{base_url}/api/auth/status", cookies=cookies)
            logger.info(f"Auth status response: {status_response.status_code}")
            logger.info(status_response.text)
            
            # Test inventory API
            logger.info("Fetching inventory products...")
            inventory_response = requests.get(f"{base_url}/api/inventory/products", cookies=cookies)
            logger.info(f"Inventory response: {inventory_response.status_code}")
            logger.info(inventory_response.text)
            
            if inventory_response.ok:
                data = inventory_response.json()
                if 'products' in data:
                    logger.info(f"Found {len(data['products'])} products")
                else:
                    logger.warning("No products found in response")
            
        else:
            logger.error("Login failed")
            
    except Exception as e:
        logger.error(f"Error testing API: {e}")

if __name__ == "__main__":
    # If running the script directly, run the tests
    test_auth_api()
    
    # Then serve the test page
    logger.info("Starting test server at http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
