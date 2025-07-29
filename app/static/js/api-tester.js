/**
 * API Test Helper
 * This script provides helper functions to test API requests from the browser console
 */

// Object to hold our test functions
const APITester = {
    // Base URL for API
    apiUrl: '/api',
    
    // Login with provided credentials
    async login(username = 'admin', pin = '1234') {
        console.log(`🔑 Attempting login as ${username}...`);
        
        try {
            const response = await fetch(`${this.apiUrl}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ username, pin }),
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`Login failed with status ${response.status}`);
            }
            
            const data = await response.json();
            console.log('✅ Login successful:', data);
            return data;
        } catch (error) {
            console.error('❌ Login error:', error);
            return null;
        }
    },
    
    // Check current authentication status
    async checkAuth() {
        console.log('🔍 Checking authentication status...');
        
        try {
            const response = await fetch(`${this.apiUrl}/auth/status`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`Auth check failed with status ${response.status}`);
            }
            
            const data = await response.json();
            console.log(data.authenticated ? '✅ Authenticated' : '❌ Not authenticated', data);
            return data;
        } catch (error) {
            console.error('❌ Auth check error:', error);
            return { authenticated: false };
        }
    },
    
    // Fetch inventory products
    async getProducts() {
        console.log('🛒 Fetching inventory products...');
        
        try {
            const response = await fetch(`${this.apiUrl}/inventory/products`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`Failed to fetch products with status ${response.status}`);
            }
            
            const data = await response.json();
            console.log(`✅ Found ${data.products?.length || 0} products:`, data);
            return data;
        } catch (error) {
            console.error('❌ Product fetch error:', error);
            return null;
        }
    },
    
    // Run a full test sequence
    async runFullTest() {
        console.log('🔄 Running full API test sequence...');
        
        // Step 1: Check if already authenticated
        const authStatus = await this.checkAuth();
        
        // Step 2: Login if needed
        if (!authStatus.authenticated) {
            const loginResult = await this.login();
            if (!loginResult?.success) {
                console.error('❌ Test failed at login step');
                return false;
            }
        }
        
        // Step 3: Fetch products
        const productsResult = await this.getProducts();
        if (!productsResult?.success) {
            console.error('❌ Test failed at products fetch step');
            return false;
        }
        
        console.log('✅ Full test completed successfully!');
        return true;
    }
};

// Log information about how to use this helper
console.log('📢 API Tester loaded. Available commands:');
console.log('  • APITester.login() - Log in as admin');
console.log('  • APITester.checkAuth() - Check authentication status');
console.log('  • APITester.getProducts() - Get inventory products');
console.log('  • APITester.runFullTest() - Run all tests in sequence');
console.log('Example: APITester.runFullTest().then(result => console.log("Test passed:", result))');
