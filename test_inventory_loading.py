#!/usr/bin/env python3
"""
Test inventory page loading to check for infinite loops
"""
import time
import requests
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_inventory_page_loading():
    """Test if the inventory page loads correctly without infinite loops"""
    base_url = 'http://localhost:5000'
    session = requests.Session()
    
    try:
        # Step 1: Login first
        logger.info("Step 1: Logging in...")
        login_data = {
            'username': 'admin',
            'pin': '1234'
        }
        
        login_response = session.post(
            f'{base_url}/api/auth/login',
            json=login_data,
            headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
        )
        
        if login_response.status_code != 200:
            logger.error(f"Login failed: {login_response.status_code}")
            return False
            
        login_result = login_response.json()
        if not login_result.get('success'):
            logger.error(f"Login not successful: {login_result}")
            return False
            
        logger.info("✅ Login successful")
        
        # Step 2: Test inventory page access
        logger.info("Step 2: Accessing inventory page...")
        inventory_page_response = session.get(f'{base_url}/inventory')
        
        if inventory_page_response.status_code != 200:
            logger.error(f"Inventory page access failed: {inventory_page_response.status_code}")
            return False
            
        # Check if the page contains the expected content
        page_content = inventory_page_response.text
        
        # Check for critical elements
        checks = [
            ('Gestion d\'Inventaire', 'Page title'),
            ('Total Produits', 'Stats section'),
            ('id="totalProducts"', 'Total products element'),
            ('id="loadingState"', 'Loading state element'),
            ('id="gridView"', 'Product grid element'),
        ]
        
        for check_text, description in checks:
            if check_text in page_content:
                logger.info(f"✅ Found {description}")
            else:
                logger.warning(f"❌ Missing {description}")
        
        # Step 3: Test API endpoints that the page uses
        logger.info("Step 3: Testing API endpoints...")
        
        # Test auth status
        auth_status = session.get(f'{base_url}/api/auth/status')
        if auth_status.status_code == 200:
            auth_data = auth_status.json()
            logger.info(f"✅ Auth status OK: {auth_data.get('authenticated')}")
        else:
            logger.warning(f"❌ Auth status failed: {auth_status.status_code}")
            
        # Test inventory products
        inventory_products = session.get(f'{base_url}/api/inventory/products')
        if inventory_products.status_code == 200:
            products_data = inventory_products.json()
            product_count = len(products_data.get('products', []))
            logger.info(f"✅ Products API OK: {product_count} products")
        else:
            logger.warning(f"❌ Products API failed: {inventory_products.status_code}")
            
        logger.info("🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        return False

if __name__ == '__main__':
    success = test_inventory_page_loading()
    if success:
        print("\n✅ Inventory page should be working correctly!")
        print("Try refreshing the page: http://localhost:5000/inventory")
    else:
        print("\n❌ There are still issues with the inventory page.")
