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
        options.credentials = 'same-origin';
    }
    
    // Set content type if not provided and method is not GET
    if (options.method && options.method !== 'GET' && !options.headers['Content-Type']) {
        options.headers['Content-Type'] = 'application/json';
    }
    
    // Return the fetch promise
    return fetch(url, options)
        .then(response => {
            if (response.status === 401) {
                window.location.href = '/login';
                throw new Error('Not authenticated');
            }
            if (!response.ok) {
                throw new Error('API error: ' + response.status);
            }
            // Always parse JSON
            return response.json();
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

// Format currency values consistently (uses AppConfig.currentCurrency when available)
function formatCurrency(amount) {
    try {
        if (window.formatCurrency) {
            return window.formatCurrency(amount);
        }
        const cur = (window.AppConfig && window.AppConfig.currentCurrency) ? window.AppConfig.currentCurrency : 'MRU';
        const num = Number(amount || 0);
        const parts = num.toFixed(2).split('.');
        const intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
        const fracPart = parts[1];
        return `${intPart},${fracPart} ${cur}`;
    } catch (e) {
        const cur = (window.AppConfig && window.AppConfig.currentCurrency) ? window.AppConfig.currentCurrency : 'MRU';
        return `0,00 ${cur}`;
    }
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
