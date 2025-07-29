/**
 * Network Request Interceptor - FIXED VERSION
 * This script will monitor fetch and XHR requests to help debug API issues.
 * XHR interception is implemented safely to avoid recursion issues.
 */
(function() {
    console.log('🔧 Installing Network Request Interceptor');
    
    // Store original fetch
    const originalFetch = window.fetch;
    
    // Override fetch to log all requests
    window.fetch = async function(resource, init) {
        const url = typeof resource === 'string' ? resource : resource.url;
        
        console.log(`🔵 Fetch request to: ${url}`, {
            method: init?.method || 'GET',
            headers: init?.headers,
            credentials: init?.credentials,
            body: init?.body ? (typeof init.body === 'string' ? init.body.substring(0, 100) : 'Binary data') : null
        });
        
        try {
            const response = await originalFetch.apply(this, arguments);
            
            // Clone the response to log it without consuming it
            const clonedResponse = response.clone();
            
            // Log response info
            console.log(`✅ Fetch response from: ${url}`, {
                status: response.status,
                statusText: response.statusText,
                headers: Object.fromEntries([...response.headers.entries()]),
                type: response.type,
                url: response.url
            });
            
            // Try to log response body if it's JSON
            clonedResponse.text().then(text => {
                try {
                    if (text) {
                        const data = JSON.parse(text);
                        console.log(`📄 Response data from: ${url}`, data);
                    }
                } catch (e) {
                    console.log(`📄 Response from: ${url} (not JSON)`, text.substring(0, 150) + '...');
                }
            }).catch(() => {});
            
            return response;
        } catch (error) {
            console.error(`❌ Fetch error for: ${url}`, error);
            throw error;
        }
    };
    
    // Safe XHR monitoring implementation
    const originalXHROpen = XMLHttpRequest.prototype.open;
    const originalXHRSend = XMLHttpRequest.prototype.send;
    
    // Flag to prevent recursion
    const markerSymbol = Symbol('monitored');
    
    // Override open to track URL and method
    XMLHttpRequest.prototype.open = function(method, url, async = true, user, password) {
        // Store request details for logging
        this._requestDetails = {
            method,
            url,
            async
        };
        
        // Call original open
        return originalXHROpen.apply(this, arguments);
    };
    
    // Override send to log requests
    XMLHttpRequest.prototype.send = function(body) {
        // Check if already monitored to prevent recursion
        if (this[markerSymbol]) {
            return originalXHRSend.apply(this, arguments);
        }
        
        // Mark as monitored
        this[markerSymbol] = true;
        
        // Prepare request info for logging
        const requestInfo = this._requestDetails || { method: 'unknown', url: 'unknown' };
        console.log(`� XHR request to: ${requestInfo.url}`, {
            method: requestInfo.method,
            body: body ? (typeof body === 'string' ? body.substring(0, 100) : 'Binary data') : null
        });
        
        // Setup response handlers
        const originalOnload = this.onload;
        const originalOnerror = this.onerror;
        
        this.onload = function(e) {
            console.log(`✅ XHR response from: ${requestInfo.url}`, {
                status: this.status,
                statusText: this.statusText,
                responseType: this.responseType,
                responseLength: this.responseText ? this.responseText.length : 0
            });
            
            // Call original handler if exists
            if (originalOnload) originalOnload.apply(this, arguments);
        };
        
        this.onerror = function(e) {
            console.error(`❌ XHR error for: ${requestInfo.url}`);
            
            // Call original handler if exists
            if (originalOnerror) originalOnerror.apply(this, arguments);
        };
        
        // Call original send
        return originalXHRSend.apply(this, arguments);
    };
    
    console.log('🔍 Network request interceptor active - monitoring fetch and XHR requests safely');
})();
