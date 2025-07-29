/**
 * Language and user preference handling functions
 * For use across all templates
 */

// Safe apiFetch function for authenticated API calls
function apiFetch(url, options = {}) {
    // Add auth token to headers if needed
    // Set defaults if options not provided
    if (!options.headers) {
        options.headers = {};
    }

    // Always send cookies for authentication
    if (!options.credentials) {
        options.credentials = 'include';
    }

    // Mark request as AJAX for Flask handlers
    if (!options.headers['X-Requested-With']) {
        options.headers['X-Requested-With'] = 'XMLHttpRequest';
    }
    
    // Set content type if not provided and method is not GET
    if (options.method && options.method !== 'GET' && !options.headers['Content-Type']) {
        options.headers['Content-Type'] = 'application/json';
    }
    
    // Return the fetch promise
    return fetch(url, options)
        .then(async response => {
            if (response.status === 401) {
                // Redirect to login on auth failure
                window.location.href = '/login';
                throw new Error('Not authenticated');
            }
            const data = await response.json().catch(() => null);
            if (!response.ok) {
                const err = new Error((data && data.message) || 'Request failed');
                err.response = response;
                err.data = data;
                throw err;
            }
            return data;
        })
        .catch(error => {
            console.error('API fetch error:', error);
            throw error;
        });
}

// Change language function - redirects to language change endpoint
function changeLanguage(lang) {
    // Save current path for redirect back
    const currentPath = window.location.pathname;
    fetch(`/set-language/${lang}?redirect=${encodeURIComponent(currentPath)}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (response.ok) {
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error changing language:', error);
    });
}

// Function to handle logout with confirmation
function handleLogout() {
    if (confirm('Êtes-vous sûr de vouloir vous déconnecter?')) {
        window.location.href = '/logout';
    }
}

/**
 * Data Consistency & Formatting Utilities
 */

// Format currency values consistently
function formatCurrency(amount) {
    return parseFloat(amount || 0).toFixed(2) + ' MRU';
}

// Format dates consistently
function formatDate(dateString) {
    if (!dateString) return '';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR');
    } catch (e) {
        console.error('Date formatting error:', e);
        return dateString;
    }
}

// Get today's date in YYYY-MM-DD format
function getTodayDate() {
    const now = new Date();
    return now.getFullYear() + '-' + 
           String(now.getMonth() + 1).padStart(2, '0') + '-' + 
           String(now.getDate()).padStart(2, '0');
}

// Calculate date range for reports
function getDateRange(period) {
    const now = new Date();
    let startDate = new Date();
    
    switch(period) {
        case 'today':
            break;
        case 'yesterday':
            startDate.setDate(startDate.getDate() - 1);
            break;
        case 'last7days':
            startDate.setDate(startDate.getDate() - 7);
            break;
        case 'thisMonth':
            startDate = new Date(now.getFullYear(), now.getMonth(), 1);
            break;
        case 'lastMonth':
            startDate = new Date(now.getFullYear(), now.getMonth() - 1, 1);
            const endOfLastMonth = new Date(now.getFullYear(), now.getMonth(), 0);
            now.setDate(endOfLastMonth.getDate());
            break;
        default:
            // Default to today
    }
    
    return {
        startDate: startDate.toISOString().split('T')[0],
        endDate: now.toISOString().split('T')[0]
    };
}
