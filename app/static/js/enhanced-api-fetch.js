/**
 * Enhanced API fetch utilities for robust API communication
 * This improves upon the basic apiFetch function in common.js
 */

// Global configuration
const API_CONFIG = {
  // Default timeout in milliseconds
  timeout: 10000,
  // Retry configuration
  retry: {
    maxRetries: 2,
    delayMs: 1000,
    retryableStatuses: [408, 429, 500, 502, 503, 504]
  },
  // Error messages by status code
  errorMessages: {
    401: "Votre session a expiré. Veuillez vous reconnecter.",
    403: "Accès refusé. Vous n'avez pas les permissions nécessaires.",
    404: "La ressource demandée est introuvable.",
    500: "Une erreur interne du serveur est survenue.",
    502: "Le serveur n'est pas disponible actuellement.",
    503: "Le service est temporairement indisponible.",
    504: "Délai d'attente dépassé lors de la communication avec le serveur."
  }
};

/**
 * Robust API fetch function with error handling, retries, and timeouts
 * 
 * @param {string} url - The API endpoint URL
 * @param {object} options - Fetch options object
 * @param {number} [attemptNum=0] - Current retry attempt number (used internally)
 * @returns {Promise} - Promise that resolves with the parsed JSON response
 */
window.enhancedApiFetch = function(url, options = {}, attemptNum = 0) {
  // Parse request options
  const fetchOptions = { 
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    credentials: 'same-origin'
  };
  
  // Create an AbortController for timeout functionality
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeout);
  fetchOptions.signal = controller.signal;
  
  // Log request for debugging
  console.log(`API Request (${attemptNum > 0 ? 'Retry ' + attemptNum : 'Initial'}):`, { 
    url, 
    method: fetchOptions.method || 'GET',
    headers: fetchOptions.headers
  });
  
  // Create and return the fetch promise
  return fetch(url, fetchOptions)
    .then(response => {
      // Clear the timeout since we got a response
      clearTimeout(timeoutId);
      
      // Log response for debugging
      console.log(`API Response (${url}):`, {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries([...response.headers])
      });
      
      // Check if response is OK (status 2xx)
      if (response.ok) {
        // For successful responses, try to parse JSON or return text
        const contentType = response.headers.get('Content-Type') || '';
        if (contentType.includes('application/json')) {
          return response.json();
        } else {
          return response.text().then(text => ({ text, success: true }));
        }
      }
      
      // Handle specific error status codes
      if (response.status === 401) {
        // Unauthorized - redirect to login page
        console.warn('Session expired, redirecting to login page');
        setTimeout(() => { window.location.href = '/login'; }, 1500);
        throw new Error(API_CONFIG.errorMessages[401]);
      }
      
      // Check if we should retry based on status code
      if (API_CONFIG.retry.retryableStatuses.includes(response.status) && attemptNum < API_CONFIG.retry.maxRetries) {
        console.warn(`Retrying request due to status ${response.status}, attempt ${attemptNum + 1}`);
        return new Promise(resolve => {
          setTimeout(() => {
            resolve(enhancedApiFetch(url, options, attemptNum + 1));
          }, API_CONFIG.retry.delayMs * (attemptNum + 1));
        });
      }
      
      // For all other error statuses, parse the error response
      return response.json()
        .then(errorData => {
          // Use specific error message from API if available
          const errorMessage = errorData.message || errorData.error || API_CONFIG.errorMessages[response.status] || `Error ${response.status}: ${response.statusText}`;
          const error = new Error(errorMessage);
          error.status = response.status;
          error.data = errorData;
          throw error;
        })
        .catch(e => {
          // If JSON parsing fails, create a generic error
          if (!e.status) {
            const error = new Error(API_CONFIG.errorMessages[response.status] || `Error ${response.status}: ${response.statusText}`);
            error.status = response.status;
            throw error;
          }
          throw e;
        });
    })
    .catch(error => {
      // Clear the timeout in case of error
      clearTimeout(timeoutId);
      
      // Handle abort errors (timeouts)
      if (error.name === 'AbortError') {
        console.error(`Request timeout for ${url}`);
        throw new Error('La requête a pris trop de temps. Veuillez réessayer.');
      }
      
      // Log and rethrow the error
      console.error(`API error (${url}):`, error);
      throw error;
    });
};

/**
 * Display a toast notification for API operations
 * 
 * @param {string} message - Message to display
 * @param {string} [type='success'] - Type of toast (success, error, warning, info)
 * @param {number} [duration=3000] - Duration in milliseconds
 */
window.showApiToast = function(message, type = 'success', duration = 3000) {
  // Create toast element if it doesn't exist
  let toast = document.getElementById('api-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'api-toast';
    toast.style.cssText = `
      position: fixed;
      bottom: 20px;
      left: 20px;
      padding: 12px 16px;
      border-radius: 6px;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
      font-size: 14px;
      z-index: 9999;
      transition: opacity 0.3s ease, transform 0.3s ease;
      opacity: 0;
      transform: translateY(20px);
    `;
    document.body.appendChild(toast);
  }
  
  // Set toast style based on type
  const colors = {
    success: { bg: '#10b981', text: '#ffffff' },
    error: { bg: '#ef4444', text: '#ffffff' },
    warning: { bg: '#f59e0b', text: '#ffffff' },
    info: { bg: '#3b82f6', text: '#ffffff' }
  };
  
  const style = colors[type] || colors.info;
  toast.style.backgroundColor = style.bg;
  toast.style.color = style.text;
  
  // Set message
  toast.textContent = message;
  
  // Show toast
  setTimeout(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
  }, 10);
  
  // Hide toast after duration
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(20px)';
    
    // Remove toast after animation completes
    setTimeout(() => {
      toast.remove();
    }, 300);
  }, duration);
};

// Override the global apiFetch with our enhanced version
window.apiFetch = window.enhancedApiFetch;

console.log('Enhanced API fetch utilities loaded');
