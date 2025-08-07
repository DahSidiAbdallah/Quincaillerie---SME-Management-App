/**
 * Offline Capability Tester
 * This script helps test offline capabilities and background sync functionality
 */

// Utility functions for testing offline capabilities
const offlineTester = {
    /**
     * Test if the service worker is installed and active
     * @returns {Promise<boolean>} True if service worker is active
     */
    async checkServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.getRegistration();
                return !!registration && !!registration.active;
            } catch (err) {
                console.error('Error checking service worker:', err);
                return false;
            }
        }
        return false;
    },

    /**
     * Check if background sync is supported
     * @returns {Promise<boolean>} True if background sync is supported
     */
    async checkBackgroundSync() {
        if ('serviceWorker' in navigator && 'SyncManager' in window) {
            try {
                const registration = await navigator.serviceWorker.ready;
                return 'sync' in registration;
            } catch (err) {
                console.error('Error checking background sync:', err);
                return false;
            }
        }
        return false;
    },

    /**
     * Test offline data storage by creating a test record in IndexedDB
     * @returns {Promise<object>} Result object with success/error information
     */
    async testOfflineStorage() {
        if (!window.offlineData) {
            return { 
                success: false, 
                error: "Offline data handler not available" 
            };
        }

        try {
            // Create a test object
            const testObject = {
                id: `test-${Date.now()}`,
                name: "Test Object",
                timestamp: new Date().toISOString(),
                testValue: Math.random().toString(36).substring(2)
            };

            // Try to store and retrieve it
            const stored = await window.offlineData.storeData('products', testObject);
            if (!stored) {
                throw new Error("Failed to store test object");
            }

            // Retrieve the test object
            const retrieved = await window.offlineData.getItemById('products', testObject.id);
            if (!retrieved || retrieved.id !== testObject.id) {
                throw new Error("Failed to retrieve test object");
            }

            // Clean up by deleting the test object
            await window.offlineData.deleteItem('products', testObject.id);

            return {
                success: true,
                message: "Offline storage is working correctly"
            };
        } catch (error) {
            console.error('Error testing offline storage:', error);
            return {
                success: false,
                error: error.message || "Unknown error during offline storage test"
            };
        }
    },

    /**
     * Test background sync by creating a pending operation
     * @returns {Promise<object>} Result of the test
     */
    async testBackgroundSync() {
        if (!window.offlineData) {
            return { 
                success: false, 
                error: "Offline data handler not available" 
            };
        }

        try {
            // Create a test pending operation
            const testOperation = {
                type: 'test_sync',
                data: {
                    testId: `sync-test-${Date.now()}`,
                    timestamp: new Date().toISOString()
                }
            };

            // Store the pending operation
            const stored = await window.offlineData.storePendingOperation(
                testOperation.type, 
                testOperation.data
            );

            if (!stored) {
                throw new Error("Failed to store test sync operation");
            }

            // Get all pending operations to verify it was stored
            const pendingOps = await window.offlineData.getPendingOperations();
            const found = pendingOps.some(op => 
                op.type === testOperation.type && 
                op.data.testId === testOperation.data.testId
            );

            if (!found) {
                throw new Error("Test sync operation not found in pending operations");
            }

            // Try to register background sync
            if ('serviceWorker' in navigator && 'SyncManager' in window) {
                const registration = await navigator.serviceWorker.ready;
                await registration.sync.register('sync-test');
            }

            return {
                success: true,
                message: "Background sync test operation created successfully",
                pendingCount: pendingOps.length
            };
        } catch (error) {
            console.error('Error testing background sync:', error);
            return {
                success: false,
                error: error.message || "Unknown error during background sync test"
            };
        }
    },

    /**
     * Run all offline capability tests
     * @returns {Promise<object>} Results of all tests
     */
    async runAllTests() {
        const results = {
            serviceWorker: await this.checkServiceWorker(),
            backgroundSyncSupport: await this.checkBackgroundSync(),
            offlineStorage: await this.testOfflineStorage(),
            backgroundSync: await this.testBackgroundSync(),
            navigator: {
                onLine: navigator.onLine,
                connection: navigator.connection ? {
                    effectiveType: navigator.connection.effectiveType,
                    saveData: navigator.connection.saveData,
                    type: navigator.connection.type
                } : null
            }
        };

        console.log('Offline capability test results:', results);
        return results;
    },

    /**
     * Create a simple UI to display test results
     * @param {object} results - Test results
     */
    displayTestResults(results) {
        // Create container
        const container = document.createElement('div');
        container.id = 'offline-test-results';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 350px;
            max-height: 80vh;
            overflow-y: auto;
            background: white;
            border: 2px solid #3b82f6;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 9999;
            font-family: system-ui, -apple-system, sans-serif;
        `;

        // Create header
        const header = document.createElement('div');
        header.innerHTML = '<h3 style="margin: 0 0 15px 0; color: #3b82f6;">Offline Capability Test Results</h3>';
        header.style.cssText = 'display: flex; justify-content: space-between; align-items: center;';
        
        // Add close button
        const closeButton = document.createElement('button');
        closeButton.textContent = '×';
        closeButton.style.cssText = `
            background: #ef4444;
            color: white;
            border: none;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            font-size: 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        closeButton.onclick = () => container.remove();
        
        header.appendChild(closeButton);
        container.appendChild(header);

        // Create content
        const content = document.createElement('div');
        
        // Service Worker Status
        content.innerHTML += `
            <div class="test-item" style="margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #e5e7eb;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>Service Worker</strong>
                    <span style="
                        color: white; 
                        background: ${results.serviceWorker ? '#10b981' : '#ef4444'}; 
                        padding: 2px 8px; 
                        border-radius: 9999px; 
                        font-size: 12px;"
                    >
                        ${results.serviceWorker ? 'Active' : 'Inactive'}
                    </span>
                </div>
            </div>
        `;
        
        // Background Sync Support
        content.innerHTML += `
            <div class="test-item" style="margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #e5e7eb;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>Background Sync API</strong>
                    <span style="
                        color: white; 
                        background: ${results.backgroundSyncSupport ? '#10b981' : '#ef4444'}; 
                        padding: 2px 8px; 
                        border-radius: 9999px; 
                        font-size: 12px;"
                    >
                        ${results.backgroundSyncSupport ? 'Supported' : 'Not Supported'}
                    </span>
                </div>
            </div>
        `;
        
        // Offline Storage Test
        content.innerHTML += `
            <div class="test-item" style="margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #e5e7eb;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>Offline Storage</strong>
                    <span style="
                        color: white; 
                        background: ${results.offlineStorage.success ? '#10b981' : '#ef4444'}; 
                        padding: 2px 8px; 
                        border-radius: 9999px; 
                        font-size: 12px;"
                    >
                        ${results.offlineStorage.success ? 'Working' : 'Failed'}
                    </span>
                </div>
                <div style="font-size: 12px; margin-top: 5px; color: #6b7280;">
                    ${results.offlineStorage.message || results.offlineStorage.error || ''}
                </div>
            </div>
        `;
        
        // Background Sync Test
        content.innerHTML += `
            <div class="test-item" style="margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #e5e7eb;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>Background Sync Test</strong>
                    <span style="
                        color: white; 
                        background: ${results.backgroundSync.success ? '#10b981' : '#ef4444'}; 
                        padding: 2px 8px; 
                        border-radius: 9999px; 
                        font-size: 12px;"
                    >
                        ${results.backgroundSync.success ? 'Passed' : 'Failed'}
                    </span>
                </div>
                <div style="font-size: 12px; margin-top: 5px; color: #6b7280;">
                    ${results.backgroundSync.message || results.backgroundSync.error || ''}
                </div>
            </div>
        `;
        
        // Network Status
        content.innerHTML += `
            <div class="test-item" style="margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #e5e7eb;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>Network Status</strong>
                    <span style="
                        color: white; 
                        background: ${results.navigator.onLine ? '#10b981' : '#f59e0b'}; 
                        padding: 2px 8px; 
                        border-radius: 9999px; 
                        font-size: 12px;"
                    >
                        ${results.navigator.onLine ? 'Online' : 'Offline'}
                    </span>
                </div>
                ${results.navigator.connection ? `
                <div style="font-size: 12px; margin-top: 5px; color: #6b7280;">
                    Connection Type: ${results.navigator.connection.type || 'unknown'}<br>
                    Effective Type: ${results.navigator.connection.effectiveType || 'unknown'}<br>
                    Save Data: ${results.navigator.connection.saveData ? 'Yes' : 'No'}
                </div>
                ` : ''}
            </div>
        `;
        
        // Add test buttons
        const buttonsContainer = document.createElement('div');
        buttonsContainer.style.cssText = 'display: flex; gap: 10px; margin-top: 15px;';
        
        // Force sync button
        const syncButton = document.createElement('button');
        syncButton.textContent = 'Force Sync';
        syncButton.style.cssText = `
            background: #3b82f6;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 14px;
            cursor: pointer;
            flex: 1;
        `;
        syncButton.onclick = async () => {
            if ('serviceWorker' in navigator && 'SyncManager' in window) {
                try {
                    const registration = await navigator.serviceWorker.ready;
                    await registration.sync.register('sync-all');
                    alert('Sync requested successfully');
                } catch (err) {
                    alert('Error requesting sync: ' + err.message);
                }
            } else {
                alert('Background sync not supported by your browser');
            }
        };
        buttonsContainer.appendChild(syncButton);
        
        // Re-test button
        const retestButton = document.createElement('button');
        retestButton.textContent = 'Run Tests Again';
        retestButton.style.cssText = `
            background: #10b981;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 14px;
            cursor: pointer;
            flex: 1;
        `;
        retestButton.onclick = async () => {
            container.remove();
            const newResults = await offlineTester.runAllTests();
            offlineTester.displayTestResults(newResults);
        };
        buttonsContainer.appendChild(retestButton);
        
        content.appendChild(buttonsContainer);
        container.appendChild(content);
        document.body.appendChild(container);
    },

    /**
     * Run tests and display results
     */
    async testAndDisplay() {
        const results = await this.runAllTests();
        this.displayTestResults(results);
    }
};

// Expose the tester globally for use in console
window.offlineTester = offlineTester;

console.log('Offline capability tester loaded. Run window.offlineTester.testAndDisplay() to test offline features.');
