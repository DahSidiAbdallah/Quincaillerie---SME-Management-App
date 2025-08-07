/**
 * API Error Debugger
 * This file provides tools for debugging API communication issues
 */

console.log('📋 API Error Debugger loading...');

// Create a global API error tracking object
window.apiErrorTracker = {
  errors: [],
  lastRequests: [],
  maxItems: 20,
  
  // Add an error to the tracker
  addError: function(endpoint, error, requestData) {
    const timestamp = new Date();
    this.errors.unshift({
      timestamp,
      endpoint,
      error: {
        message: error.message,
        stack: error.stack,
        status: error.status || 'unknown'
      },
      requestData
    });
    
    // Keep only the last maxItems errors
    if (this.errors.length > this.maxItems) {
      this.errors.pop();
    }
    
    console.error(`API Error [${timestamp.toLocaleTimeString()}] ${endpoint}:`, error);
  },
  
  // Track successful API requests
  trackRequest: function(endpoint, method, response) {
    const timestamp = new Date();
    this.lastRequests.unshift({
      timestamp,
      endpoint,
      method,
      status: response.status,
      success: response.ok
    });
    
    // Keep only the last maxItems requests
    if (this.lastRequests.length > this.maxItems) {
      this.lastRequests.pop();
    }
  },
  
  // Get error statistics
  getStats: function() {
    return {
      totalErrors: this.errors.length,
      endpointStats: this.errors.reduce((stats, error) => {
        stats[error.endpoint] = (stats[error.endpoint] || 0) + 1;
        return stats;
      }, {}),
      mostCommonEndpoint: this.errors.length > 0 ? 
        Object.entries(this.errors.reduce((stats, error) => {
          stats[error.endpoint] = (stats[error.endpoint] || 0) + 1;
          return stats;
        }, {})).sort((a, b) => b[1] - a[1])[0][0] : null
    };
  },
  
  // Clear all tracked errors
  clear: function() {
    this.errors = [];
    this.lastRequests = [];
  },
  
  // Show error details in console
  showDetails: function() {
    console.group('API Error Details');
    this.errors.forEach((error, index) => {
      console.group(`Error #${index + 1} - ${error.timestamp.toLocaleTimeString()} - ${error.endpoint}`);
      console.log('Error:', error.error);
      console.log('Request Data:', error.requestData);
      console.groupEnd();
    });
    console.groupEnd();
  }
};

// Patch fetch to monitor API calls
const originalFetch = window.fetch;
window.fetch = function(url, options) {
  const isApiCall = typeof url === 'string' && (
    url.startsWith('/api/') || 
    (options && options.headers && 
     options.headers['Content-Type'] === 'application/json')
  );
  
  if (isApiCall) {
    console.log(`API Call: ${options?.method || 'GET'} ${url}`, options);
    
    return originalFetch.apply(this, arguments)
      .then(response => {
        // Track the request
        window.apiErrorTracker.trackRequest(url, options?.method || 'GET', response);
        return response;
      })
      .catch(error => {
        // Track the error
        window.apiErrorTracker.addError(url, error, options);
        throw error;
      });
  }
  
  // For non-API calls, use the original fetch
  return originalFetch.apply(this, arguments);
};

// Create debug UI if we're in the admin section
function createDebugUI() {
  if (!window.location.pathname.includes('/admin')) return;
  
  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDebugUI);
  } else {
    initDebugUI();
  }
  
  function initDebugUI() {
    // Add a button to the page
    const button = document.createElement('button');
    button.textContent = 'API Debug';
    button.className = 'bg-gray-800 text-white text-xs px-2 py-1 rounded fixed bottom-3 right-3 z-50 opacity-50 hover:opacity-100';
    button.onclick = showDebugPanel;
    document.body.appendChild(button);
  }
  
  function showDebugPanel() {
    // Create panel
    const panel = document.createElement('div');
    panel.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50';
    panel.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-3/4 max-h-3/4 overflow-auto p-6">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-medium text-gray-900">API Debug Panel</h3>
          <button id="close-debug-panel" class="text-gray-400 hover:text-gray-500">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        
        <div class="space-y-6">
          <div>
            <h4 class="font-medium text-gray-900">Recent API Errors (${window.apiErrorTracker.errors.length})</h4>
            <div class="mt-2 max-h-48 overflow-y-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Endpoint</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Error</th>
                  </tr>
                </thead>
                <tbody id="error-list" class="bg-white divide-y divide-gray-200 text-xs">
                  ${window.apiErrorTracker.errors.map(error => `
                    <tr>
                      <td class="px-3 py-2 whitespace-nowrap">${error.timestamp.toLocaleTimeString()}</td>
                      <td class="px-3 py-2 whitespace-nowrap">${error.endpoint}</td>
                      <td class="px-3 py-2">${error.error.message || 'Unknown error'}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
              ${window.apiErrorTracker.errors.length === 0 ? '<p class="text-sm text-gray-500 p-3">No errors recorded</p>' : ''}
            </div>
          </div>
          
          <div>
            <h4 class="font-medium text-gray-900">Recent API Requests</h4>
            <div class="mt-2 max-h-48 overflow-y-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Method</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Endpoint</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody id="request-list" class="bg-white divide-y divide-gray-200 text-xs">
                  ${window.apiErrorTracker.lastRequests.map(req => `
                    <tr>
                      <td class="px-3 py-2 whitespace-nowrap">${req.timestamp.toLocaleTimeString()}</td>
                      <td class="px-3 py-2 whitespace-nowrap">${req.method}</td>
                      <td class="px-3 py-2 whitespace-nowrap">${req.endpoint}</td>
                      <td class="px-3 py-2 whitespace-nowrap">
                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                          ${req.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                          ${req.status}
                        </span>
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
              ${window.apiErrorTracker.lastRequests.length === 0 ? '<p class="text-sm text-gray-500 p-3">No requests recorded</p>' : ''}
            </div>
          </div>
          
          <div class="flex justify-end space-x-3 pt-3 border-t">
            <button id="clear-errors" class="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
              Clear Data
            </button>
            <button id="view-console" class="bg-blue-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
              View Details in Console
            </button>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(panel);
    
    // Add event listeners
    document.getElementById('close-debug-panel').addEventListener('click', () => panel.remove());
    document.getElementById('clear-errors').addEventListener('click', () => {
      window.apiErrorTracker.clear();
      panel.remove();
      showDebugPanel();
    });
    document.getElementById('view-console').addEventListener('click', () => {
      window.apiErrorTracker.showDetails();
    });
  }
}

// Initialize debug UI
createDebugUI();

// Export debugging utilities to global scope for console use
window.apiDebug = {
  showErrors: () => window.apiErrorTracker.showDetails(),
  clearErrors: () => window.apiErrorTracker.clear(),
  getStats: () => window.apiErrorTracker.getStats()
};

console.log('📋 API Error Debugger loaded and monitoring API calls');
