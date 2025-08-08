/**
 * Inventory Loading Diagnostics Script
 * This script helps debug infinite loading and button issues on the inventory page
 */

console.log('🔧 Inventory Diagnostics Script loaded');

// Diagnostic functions
window.inventoryDiagnostics = {
    
    // Test the inventory API endpoint directly
    async testInventoryAPI() {
        console.log('🧪 Testing inventory API endpoint...');
        
        try {
            const response = await fetch('/api/inventory/products', {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });
            
            console.log('📡 API Response status:', response.status);
            console.log('📡 API Response headers:', Object.fromEntries([...response.headers.entries()]));
            
            if (!response.ok) {
                console.error('❌ API Response not OK:', response.status, response.statusText);
                if (response.status === 401) {
                    console.error('🔒 Authentication required - user not logged in');
                }
                return { success: false, error: `HTTP ${response.status}` };
            }
            
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.error('❌ Response is not JSON:', contentType);
                const text = await response.text();
                console.log('📄 Response text:', text.substring(0, 500));
                return { success: false, error: 'Non-JSON response' };
            }
            
            const data = await response.json();
            console.log('✅ API Success:', data);
            
            return { success: true, data };
            
        } catch (error) {
            console.error('❌ API Test failed:', error);
            return { success: false, error: error.message };
        }
    },
    
    // Check if all required DOM elements exist
    checkDOMElements() {
        console.log('🔍 Checking required DOM elements...');
        
        const requiredElements = [
            'loadingState',
            'productsContainer', 
            'gridView',
            'emptyState',
            'searchInput',
            'categoryFilter',
            'stockFilter',
            'totalProducts',
            'inStockProducts', 
            'lowStockProducts',
            'stockValue'
        ];
        
        const results = {};
        
        requiredElements.forEach(id => {
            const element = document.getElementById(id);
            const exists = !!element;
            results[id] = {
                exists,
                element: element,
                visible: exists ? !element.classList.contains('hidden') : false
            };
            
            console.log(`${exists ? '✅' : '❌'} ${id}:`, exists ? 'Found' : 'Missing');
        });
        
        return results;
    },
    
    // Check for JavaScript errors on the page
    checkJavaScriptErrors() {
        console.log('🔍 Checking for JavaScript errors...');
        
        // Set up error listener
        const originalOnError = window.onerror;
        const errors = [];
        
        window.onerror = function(message, source, lineno, colno, error) {
            errors.push({
                message,
                source,
                lineno,
                colno,
                error: error ? error.toString() : null,
                timestamp: new Date().toISOString()
            });
            
            console.error('⚠️ JavaScript Error captured:', {
                message, source, lineno, colno, error
            });
            
            if (originalOnError) {
                return originalOnError.apply(this, arguments);
            }
        };
        
        return errors;
    },
    
    // Test the loadProducts function if it exists
    async testLoadProductsFunction() {
        console.log('🔍 Testing loadProducts function...');
        
        if (typeof window.loadProducts === 'function') {
            console.log('✅ loadProducts function found');
            try {
                await window.loadProducts();
                console.log('✅ loadProducts executed successfully');
                return { success: true };
            } catch (error) {
                console.error('❌ loadProducts failed:', error);
                return { success: false, error: error.message };
            }
        } else if (typeof window.loadProductsWithAuth === 'function') {
            console.log('✅ loadProductsWithAuth function found');
            try {
                await window.loadProductsWithAuth();
                console.log('✅ loadProductsWithAuth executed successfully');
                return { success: true };
            } catch (error) {
                console.error('❌ loadProductsWithAuth failed:', error);
                return { success: false, error: error.message };
            }
        } else {
            console.error('❌ No loadProducts or loadProductsWithAuth function found');
            return { success: false, error: 'Function not found' };
        }
    },
    
    // Check network requests in the Network tab
    monitorNetworkRequests() {
        console.log('📡 Starting network request monitoring...');
        
        const originalFetch = window.fetch;
        const requests = [];
        
        window.fetch = function(...args) {
            const url = args[0];
            const options = args[1] || {};
            
            console.log('📡 Network request:', url, options);
            
            const startTime = Date.now();
            const requestInfo = {
                url,
                method: options.method || 'GET',
                startTime,
                timestamp: new Date().toISOString()
            };
            
            requests.push(requestInfo);
            
            return originalFetch.apply(this, args)
                .then(response => {
                    const endTime = Date.now();
                    requestInfo.duration = endTime - startTime;
                    requestInfo.status = response.status;
                    requestInfo.success = response.ok;
                    
                    console.log('📡 Request completed:', requestInfo);
                    return response;
                })
                .catch(error => {
                    const endTime = Date.now();
                    requestInfo.duration = endTime - startTime;
                    requestInfo.error = error.message;
                    requestInfo.success = false;
                    
                    console.error('📡 Request failed:', requestInfo);
                    throw error;
                });
        };
        
        return requests;
    },
    
    // Full diagnostic report
    async runFullDiagnostics() {
        console.log('🚀 Running full inventory diagnostics...');
        
        const report = {
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            currentURL: window.location.href,
            results: {}
        };
        
        // Check DOM elements
        report.results.domElements = this.checkDOMElements();
        
        // Monitor network requests
        const networkRequests = this.monitorNetworkRequests();
        
        // Test API endpoint
        report.results.apiTest = await this.testInventoryAPI();
        
        // Test load functions
        report.results.loadFunctionTest = await this.testLoadProductsFunction();
        
        // Get recent network requests
        setTimeout(() => {
            report.results.networkRequests = networkRequests.slice(-10); // Last 10 requests
        }, 2000);
        
        console.log('📊 Full Diagnostic Report:', report);
        
        return report;
    },
    
    // Fix common issues
    async attemptAutoFix() {
        console.log('🔧 Attempting automatic fixes...');
        
        const fixes = [];
        
        // Fix 1: Reset loading state
        const loadingElement = document.getElementById('loadingState');
        if (loadingElement && !loadingElement.classList.contains('hidden')) {
            loadingElement.classList.add('hidden');
            fixes.push('Reset loading state');
            console.log('✅ Fixed: Reset loading state');
        }
        
        // Fix 2: Show products container
        const productsContainer = document.getElementById('productsContainer');
        if (productsContainer && productsContainer.classList.contains('hidden')) {
            productsContainer.classList.remove('hidden');
            fixes.push('Show products container');
            console.log('✅ Fixed: Show products container');
        }
        
        // Fix 3: Retry API call
        try {
            const apiResult = await this.testInventoryAPI();
            if (apiResult.success && apiResult.data && apiResult.data.products) {
                // Try to populate products directly
                const gridView = document.getElementById('gridView');
                if (gridView) {
                    gridView.innerHTML = '';
                    
                    apiResult.data.products.forEach(product => {
                        const card = document.createElement('div');
                        card.className = 'product-card bg-white rounded-lg shadow-lg p-6';
                        card.innerHTML = `
                            <h3 class="font-bold text-lg">${product.name}</h3>
                            <p class="text-gray-600 text-sm">${product.category || 'No Category'}</p>
                            <div class="flex justify-between items-center mt-2">
                                <span class="font-semibold">${window.formatCurrency ? window.formatCurrency(product.sale_price || 0) : ((product.sale_price || 0) + ' ' + (window.AppConfig?.currentCurrency || 'MRU'))}</span>
                                <span>Stock: ${product.current_stock || 0}</span>
                            </div>
                        `;
                        gridView.appendChild(card);
                    });
                    
                    fixes.push('Populated products directly');
                    console.log('✅ Fixed: Populated products directly');
                }
                
                // Update stats if available
                if (apiResult.data.stats) {
                    const stats = apiResult.data.stats;
                    const totalEl = document.getElementById('totalProducts');
                    const inStockEl = document.getElementById('inStockProducts');
                    const lowStockEl = document.getElementById('lowStockProducts');
                    const stockValueEl = document.getElementById('stockValue');
                    
                    if (totalEl) totalEl.textContent = stats.total || '0';
                    if (inStockEl) inStockEl.textContent = (stats.total || 0) - (stats.out_of_stock || 0);
                    if (lowStockEl) lowStockEl.textContent = stats.low_stock || '0';
                    if (stockValueEl) stockValueEl.textContent = window.formatCurrency ? window.formatCurrency(stats.inventory_value || 0) : ((stats.inventory_value || 0) + ' ' + (window.AppConfig?.currentCurrency || 'MRU'));
                    
                    fixes.push('Updated statistics');
                    console.log('✅ Fixed: Updated statistics');
                }
            }
        } catch (error) {
            console.error('❌ Auto-fix failed:', error);
        }
        
        console.log('🔧 Auto-fix completed. Applied fixes:', fixes);
        return fixes;
    }
};

// Add diagnostic panel to page if on inventory page
if (window.location.pathname.includes('/inventory')) {
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🔧 Adding diagnostic panel to inventory page...');
        
        // Create diagnostic panel
        const panel = document.createElement('div');
        panel.id = 'inventoryDiagnosticsPanel';
        panel.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            background: white;
            border: 2px solid #3b82f6;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 9999;
            max-width: 300px;
            font-family: monospace;
            font-size: 12px;
        `;
        
        panel.innerHTML = `
            <h3 style="margin: 0 0 10px 0; color: #3b82f6;">🔧 Inventory Diagnostics</h3>
            <div id="diagnosticResults" style="margin-bottom: 10px; max-height: 200px; overflow-y: auto;"></div>
            <button onclick="inventoryDiagnostics.runFullDiagnostics()" 
                    style="background: #3b82f6; color: white; border: none; padding: 5px 10px; border-radius: 4px; margin-right: 5px; cursor: pointer;">
                Run Diagnostics
            </button>
            <button onclick="inventoryDiagnostics.attemptAutoFix()" 
                    style="background: #059669; color: white; border: none; padding: 5px 10px; border-radius: 4px; margin-right: 5px; cursor: pointer;">
                Auto Fix
            </button>
            <button onclick="this.parentElement.style.display='none'" 
                    style="background: #dc2626; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">
                Hide
            </button>
        `;
        
        document.body.appendChild(panel);
        
        // Auto-run diagnostics after 3 seconds
        setTimeout(() => {
            console.log('🔧 Auto-running diagnostics...');
            inventoryDiagnostics.runFullDiagnostics().then(report => {
                const results = document.getElementById('diagnosticResults');
                if (results) {
                    results.innerHTML = `
                        <div style="color: ${report.results.apiTest.success ? 'green' : 'red'};">
                            API Test: ${report.results.apiTest.success ? 'PASS' : 'FAIL'}
                        </div>
                        <div style="color: ${report.results.loadFunctionTest.success ? 'green' : 'red'};">
                            Load Function: ${report.results.loadFunctionTest.success ? 'PASS' : 'FAIL'}
                        </div>
                        <div>DOM Elements: ${Object.values(report.results.domElements).filter(e => e.exists).length}/${Object.keys(report.results.domElements).length}</div>
                    `;
                }
            });
        }, 3000);
    });
}

console.log('✅ Inventory Diagnostics Script ready');
