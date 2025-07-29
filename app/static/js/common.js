/**
 * Language and user preference handling functions
 * For use across all templates
 */

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
