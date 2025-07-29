// This fix will be applied to the inventory.html page
// It adds proper session cookie handling and improves authentication flow

// 1. First, create a utility function to check if we're authenticated
async function checkAuthentication() {
    try {
        const response = await fetch('/api/auth/status', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin' // Important: include cookies
        });
        
        if (!response.ok) {
            console.error('Auth check failed with status:', response.status);
            return false;
        }
        
        const data = await response.json();
        return data.authenticated === true;
    } catch (error) {
        console.error('Error checking authentication:', error);
        return false;
    }
}

// 2. Create a function to handle login
async function performLogin(username, pin) {
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ username, pin }),
            credentials: 'same-origin' // Important: include cookies
        });
        
        if (!response.ok) {
            console.error('Login failed with status:', response.status);
            return false;
        }
        
        const data = await response.json();
        return data.success === true;
    } catch (error) {
        console.error('Error during login:', error);
        return false;
    }
}

// 3. Create a function to load products with proper credentials
async function loadProductsWithAuth() {
    // First check if we're authenticated
    const isAuthenticated = await checkAuthentication();
    
    if (!isAuthenticated) {
        // Try to login
        console.log('Not authenticated, attempting login...');
        const loginSuccess = await performLogin('admin', '1234');
        
        if (!loginSuccess) {
            console.error('Login failed, cannot load products');
            showNotification('Veuillez vous connecter pour accéder à l\'inventaire', 'error');
            setTimeout(() => {
                window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
            }, 2000);
            return;
        }
    }
    
    // Now load products with proper credentials
    try {
        console.log('Loading products with authentication...');
        const response = await fetch('/api/inventory/products', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin' // Important: include cookies
        });
        
        if (!response.ok) {
            console.error('Failed to load products:', response.status);
            if (response.status === 401) {
                showNotification('Session expirée. Reconnexion en cours...', 'warning');
                // Try login again
                const retryLogin = await performLogin('admin', '1234');
                if (retryLogin) {
                    // Try loading products one more time
                    return loadProductsWithAuth();
                } else {
                    showNotification('Échec de reconnexion. Veuillez vous connecter manuellement.', 'error');
                    setTimeout(() => {
                        window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
                    }, 2000);
                }
                return;
            }
            throw new Error(`API responded with status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Products loaded successfully:', data);
        
        // Update global products array
        if (data.success) {
            currentProducts = data.products || [];
            console.log(`Loaded ${currentProducts.length} products`);
            
            // Update UI
            displayProducts();
            if (data.stats) {
                updateStats(data.stats);
            }
        } else {
            console.error('API error:', data.message);
            currentProducts = [];
            displayProducts();
        }
    } catch (error) {
        console.error('Error loading products:', error);
        showNotification('Erreur lors du chargement des produits', 'error');
    } finally {
        isLoading = false;
        hideLoading();
    }
}

// 4. Add this to the main script - these functions will replace the existing ones
// or be used alongside existing functions
