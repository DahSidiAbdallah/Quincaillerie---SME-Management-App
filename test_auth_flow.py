#!/usr/bin/env python3
"""
Test authentication flow for inventory page
"""
import requests
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_auth_flow():
    """Test the complete authentication flow"""
    base_url = 'http://localhost:5000'
    session = requests.Session()
    
    try:
        # Step 1: Check initial auth status
        logger.info("Step 1: Checking initial auth status...")
        auth_response = session.get(f'{base_url}/api/auth/status')
        logger.info(f"Auth status response: {auth_response.status_code}")
        logger.info(f"Response headers: {dict(auth_response.headers)}")
        
        if auth_response.headers.get('content-type', '').startswith('application/json'):
            auth_data = auth_response.json()
            logger.info(f"Auth status data: {json.dumps(auth_data, indent=2)}")
        else:
            logger.warning(f"Auth status returned non-JSON content: {auth_response.text[:200]}...")
        
        # Step 2: Try login
        logger.info("\nStep 2: Attempting login...")
        login_data = {
            'username': 'admin',
            'pin': '1234'
        }
        
        login_response = session.post(
            f'{base_url}/api/auth/login',
            json=login_data,
            headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
        )
        
        logger.info(f"Login response: {login_response.status_code}")
        logger.info(f"Login headers: {dict(login_response.headers)}")
        
        if login_response.headers.get('content-type', '').startswith('application/json'):
            login_result = login_response.json()
            logger.info(f"Login result: {json.dumps(login_result, indent=2)}")
        else:
            logger.warning(f"Login returned non-JSON content: {login_response.text[:200]}...")
        
        # Step 3: Check auth status after login
        logger.info("\nStep 3: Checking auth status after login...")
        auth_response2 = session.get(f'{base_url}/api/auth/status')
        logger.info(f"Auth status response 2: {auth_response2.status_code}")
        
        if auth_response2.headers.get('content-type', '').startswith('application/json'):
            auth_data2 = auth_response2.json()
            logger.info(f"Auth status data 2: {json.dumps(auth_data2, indent=2)}")
        else:
            logger.warning(f"Auth status 2 returned non-JSON content: {auth_response2.text[:200]}...")
        
        # Step 4: Test inventory endpoint
        logger.info("\nStep 4: Testing inventory endpoint...")
        inventory_response = session.get(f'{base_url}/api/inventory/products')
        logger.info(f"Inventory response: {inventory_response.status_code}")
        logger.info(f"Inventory headers: {dict(inventory_response.headers)}")
        
        if inventory_response.headers.get('content-type', '').startswith('application/json'):
            inventory_data = inventory_response.json()
            logger.info(f"Inventory products count: {len(inventory_data.get('products', []))}")
            logger.info(f"Inventory stats: {inventory_data.get('stats', {})}")
        else:
            logger.warning(f"Inventory returned non-JSON content: {inventory_response.text[:200]}...")
        
        # Step 5: Test accessing inventory page directly
        logger.info("\nStep 5: Testing inventory page access...")
        inventory_page_response = session.get(f'{base_url}/inventory')
        logger.info(f"Inventory page response: {inventory_page_response.status_code}")
        logger.info(f"Inventory page headers: {dict(inventory_page_response.headers)}")
        
        if 'Gestion d\'Inventaire' in inventory_page_response.text:
            logger.info("✅ Successfully accessed inventory page")
        else:
            logger.warning("❌ Inventory page content doesn't look right")
            
    except Exception as e:
        logger.error(f"Error during auth flow test: {e}")

if __name__ == '__main__':
    test_auth_flow()
