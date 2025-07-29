/**
 * Inventory API Diagnostic Tool
 * This script adds a visible debug panel to the page and directly tests API connectivity
 */

(function() {
    console.log('📊 Inventory API Diagnostic Tool loaded');
    
    // Create diagnostic panel
    function createDiagnosticPanel() {
        // Create panel container
        const panel = document.createElement('div');
        panel.id = 'api-diagnostic-panel';
        panel.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            width: 300px;
            background: #f8d7da;
            border: 2px solid #dc3545;
            border-radius: 5px;
            padding: 15px;
            z-index: 9999;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
            font-family: Arial, sans-serif;
            font-size: 14px;
            color: #333;
            max-height: 80vh;
            overflow-y: auto;
        `;
        
        // Add title
        const title = document.createElement('h3');
        title.textContent = '🔍 API Diagnostics';
        title.style.cssText = 'margin-top: 0; color: #721c24; font-size: 16px; margin-bottom: 10px;';
        panel.appendChild(title);
        
        // Add status section
        const statusDiv = document.createElement('div');
        statusDiv.id = 'api-diagnostic-status';
        statusDiv.textContent = 'Ready to test';
        statusDiv.style.cssText = 'margin-bottom: 10px; padding: 5px; background: #f5f5f5; border-radius: 3px;';
        panel.appendChild(statusDiv);
        
        // Add buttons
        const buttonDiv = document.createElement('div');
        buttonDiv.style.cssText = 'display: flex; gap: 5px; margin-bottom: 10px;';
        
        // Login button
        const loginBtn = document.createElement('button');
        loginBtn.textContent = '1. Login';
        loginBtn.id = 'api-diagnostic-login';
        loginBtn.style.cssText = 'flex: 1; padding: 8px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer;';
        buttonDiv.appendChild(loginBtn);
        
        // Test API button
        const testBtn = document.createElement('button');
        testBtn.textContent = '2. Test API';
        testBtn.id = 'api-diagnostic-test';
        testBtn.style.cssText = 'flex: 1; padding: 8px; background: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer;';
        buttonDiv.appendChild(testBtn);
        
        // Clear button
        const clearBtn = document.createElement('button');
        clearBtn.textContent = 'Clear';
        clearBtn.id = 'api-diagnostic-clear';
        clearBtn.style.cssText = 'padding: 8px; background: #6c757d; color: white; border: none; border-radius: 3px; cursor: pointer;';
        buttonDiv.appendChild(clearBtn);
        
        panel.appendChild(buttonDiv);
        
        // Add results area
        const resultsDiv = document.createElement('div');
        resultsDiv.id = 'api-diagnostic-results';
        resultsDiv.style.cssText = 'background: white; border: 1px solid #ddd; border-radius: 3px; padding: 10px; max-height: 200px; overflow-y: auto;';
        panel.appendChild(resultsDiv);
        
        // Add minimize button
        const minimizeBtn = document.createElement('button');
        minimizeBtn.textContent = '−';
        minimizeBtn.style.cssText = 'position: absolute; top: 10px; right: 10px; background: none; border: none; font-size: 16px; cursor: pointer; padding: 0; width: 20px; height: 20px; line-height: 1;';
        minimizeBtn.title = 'Minimize';
        
        let minimized = false;
        minimizeBtn.addEventListener('click', () => {
            if (minimized) {
                statusDiv.style.display = 'block';
                buttonDiv.style.display = 'flex';
                resultsDiv.style.display = 'block';
                minimizeBtn.textContent = '−';
                minimized = false;
            } else {
                statusDiv.style.display = 'none';
                buttonDiv.style.display = 'none';
                resultsDiv.style.display = 'none';
                minimizeBtn.textContent = '+';
                minimized = true;
            }
        });
        panel.appendChild(minimizeBtn);
        
        return panel;
    }
    
    // Log message to results
    function logResult(message, type = 'info') {
        const resultsDiv = document.getElementById('api-diagnostic-results');
        if (!resultsDiv) return;
        
        const entry = document.createElement('div');
        
        let bgColor = '#f8f9fa';
        if (type === 'error') bgColor = '#f8d7da';
        if (type === 'success') bgColor = '#d4edda';
        if (type === 'warning') bgColor = '#fff3cd';
        
        entry.style.cssText = `padding: 5px; margin-bottom: 5px; background: ${bgColor}; border-radius: 3px; font-size: 12px;`;
        
        const timestamp = new Date().toLocaleTimeString();
        entry.textContent = `[${timestamp}] ${message}`;
        
        resultsDiv.appendChild(entry);
        resultsDiv.scrollTop = resultsDiv.scrollHeight;
    }
    
    // Update status
    function updateStatus(message, type = 'info') {
        const statusDiv = document.getElementById('api-diagnostic-status');
        if (!statusDiv) return;
        
        let bgColor = '#f8f9fa';
        if (type === 'error') bgColor = '#f8d7da';
        if (type === 'success') bgColor = '#d4edda';
        if (type === 'warning') bgColor = '#fff3cd';
        
        statusDiv.textContent = message;
        statusDiv.style.background = bgColor;
    }
    
    // Login function
    async function testLogin() {
        try {
            updateStatus('Logging in...', 'info');
            logResult('Attempting login with admin/1234');
            
            const loginData = {
                username: 'admin',
                pin: '1234'
            };
            
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                },
                credentials: 'same-origin',
                body: JSON.stringify(loginData)
            });
            
            logResult(`Login response status: ${response.status}`);
            
            if (!response.ok) {
                updateStatus(`Login failed (${response.status})`, 'error');
                logResult(`Login failed with status ${response.status}`, 'error');
                return false;
            }
            
            const data = await response.json();
            
            if (data.success) {
                updateStatus('Login successful', 'success');
                logResult(`Login successful: ${data.message || 'Authenticated'}`, 'success');
                return true;
            } else {
                updateStatus(`Login failed: ${data.message}`, 'error');
                logResult(`Login failed: ${data.message}`, 'error');
                return false;
            }
        } catch (error) {
            updateStatus('Login error', 'error');
            logResult(`Login error: ${error.message}`, 'error');
            console.error('Login error:', error);
            return false;
        }
    }
    
    // Test API function
    async function testApi() {
        try {
            updateStatus('Testing API...', 'info');
            logResult('Fetching products from inventory API');
            
            const response = await fetch('/api/inventory/products', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                },
                credentials: 'same-origin',
                cache: 'no-store'
            });
            
            logResult(`API response status: ${response.status}`);
            
            if (!response.ok) {
                updateStatus(`API failed (${response.status})`, 'error');
                logResult(`API request failed with status ${response.status}`, 'error');
                
                // Check if it's a login issue
                if (response.status === 401) {
                    logResult('Authentication required - trying login', 'warning');
                    const loginSuccess = await testLogin();
                    if (loginSuccess) {
                        logResult('Retrying API request after login', 'info');
                        testApi(); // Try again
                    }
                }
                
                return;
            }
            
            const data = await response.json();
            
            if (data.success) {
                updateStatus(`API successful (${data.products.length} products)`, 'success');
                logResult(`API call successful - found ${data.products.length} products`, 'success');
                
                // Display first product as example
                if (data.products && data.products.length > 0) {
                    const product = data.products[0];
                    logResult(`Example product: ${product.name}, Price: ${product.sale_price}, Stock: ${product.current_stock}`);
                }
                
                // Manually update the page if we can find the container
                try {
                    const container = document.getElementById('gridView');
                    if (container) {
                        logResult('Attempting to manually update UI with products', 'info');
                        container.innerHTML = '';
                        
                        // Simple display of products
                        data.products.forEach(product => {
                            const card = document.createElement('div');
                            card.className = 'product-card bg-white rounded-lg shadow-lg p-6';
                            card.innerHTML = `
                                <h3 class="font-bold text-lg">${product.name}</h3>
                                <p class="text-gray-600 text-sm">${product.category}</p>
                                <div class="flex justify-between items-center mt-2">
                                    <span class="font-semibold">${product.sale_price}</span>
                                    <span>Stock: ${product.current_stock}</span>
                                </div>
                            `;
                            container.appendChild(card);
                        });
                        
                        // Hide loading state
                        const loadingElement = document.getElementById('loadingState');
                        if (loadingElement) loadingElement.classList.add('hidden');
                        
                        // Show products container
                        const productsContainer = document.getElementById('productsContainer');
                        if (productsContainer) productsContainer.classList.remove('hidden');
                        
                        logResult('Successfully updated UI with products', 'success');
                    } else {
                        logResult('Could not find gridView container to update UI', 'warning');
                    }
                } catch (displayError) {
                    logResult(`Error updating UI: ${displayError.message}`, 'error');
                }
            } else {
                updateStatus(`API error: ${data.message}`, 'error');
                logResult(`API returned error: ${data.message}`, 'error');
            }
        } catch (error) {
            updateStatus('API error', 'error');
            logResult(`API error: ${error.message}`, 'error');
            console.error('API error:', error);
        }
    }
    
    // Initialize diagnostic panel
    function initDiagnostics() {
        try {
            // Check if we're on the inventory page
            if (!window.location.pathname.includes('inventory')) {
                console.log('Not on inventory page, diagnostics not needed');
                return;
            }
            
            console.log('Initializing inventory API diagnostics');
            
            // Create and add panel to document
            const panel = createDiagnosticPanel();
            document.body.appendChild(panel);
            
            // Add event listeners to buttons
            document.getElementById('api-diagnostic-login').addEventListener('click', testLogin);
            document.getElementById('api-diagnostic-test').addEventListener('click', testApi);
            document.getElementById('api-diagnostic-clear').addEventListener('click', () => {
                document.getElementById('api-diagnostic-results').innerHTML = '';
            });
            
            // Log initialization
            logResult('Diagnostics panel initialized');
            logResult('Click "Login" first, then "Test API"');
            updateStatus('Ready to test', 'info');
            
            console.log('Diagnostics panel initialized successfully');
        } catch (error) {
            console.error('Error initializing diagnostics panel:', error);
        }
    }
    
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDiagnostics);
    } else {
        initDiagnostics();
    }
})();
