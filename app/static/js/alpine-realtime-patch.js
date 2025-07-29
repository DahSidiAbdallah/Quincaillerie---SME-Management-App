/**
 * This script patches Alpine.js methods to ensure UI updates in real-time
 * It should be included right after Alpine.js is loaded and before the admin-diagnostics.js
 */

(function() {
    // Wait for Alpine and document to be ready
    function waitForAlpine(callback) {
        if (typeof Alpine !== 'undefined') {
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', callback);
            } else {
                callback();
            }
        } else {
            setTimeout(() => waitForAlpine(callback), 100);
        }
    }
    
    waitForAlpine(() => {
        console.log('🛠️ Setting up real-time UI update patching...');
        
        // Create a wrapper for the admin component
        const patchedMethods = {
            // Original methods will be stored here when patched
        };
        
        // Function to patch a method for real-time UI updates
        function patchMethod(methodName, callback) {
            document.addEventListener('alpine:init', () => {
                try {
                    const mainEl = document.querySelector('main[x-data]');
                    if (!mainEl) return;
                    
                    const component = Alpine.$data(mainEl);
                    if (!component || typeof component[methodName] !== 'function') return;
                    
                    // Store original method
                    patchedMethods[methodName] = component[methodName];
                    
                    // Replace with patched version
                    component[methodName] = function(...args) {
                        // Call original method
                        const result = patchedMethods[methodName].apply(this, args);
                        
                        // Execute callback for UI updates
                        if (callback) {
                            callback.apply(this, args);
                        }
                        
                        return result;
                    };
                    
                    console.log(`✅ Patched ${methodName} for real-time UI updates`);
                } catch (err) {
                    console.error(`❌ Error patching ${methodName}:`, err);
                }
            });
        }
        
        // Observer to watch for Alpine component initialization
        const observer = new MutationObserver((mutations) => {
            for (let mutation of mutations) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'x-data') {
                    patchComponentMethods();
                    observer.disconnect();
                    break;
                }
            }
        });
        
        // Start observing for Alpine initialization
        observer.observe(document.body, { 
            attributes: true, 
            subtree: true, 
            attributeFilter: ['x-data']
        });
        
        // Apply patches when component is ready
        function patchComponentMethods() {
            // Patch deleteUser method
            patchMethod('deleteUser', function(user) {
                console.log('🔄 Real-time UI update for deleteUser');
                if (window.adminHelpers && window.adminHelpers.removeUserFromUI) {
                    window.adminHelpers.removeUserFromUI(user.id);
                }
            });
            
            // Patch toggleUserStatus method
            patchMethod('toggleUserStatus', function(user) {
                console.log('🔄 Real-time UI update for toggleUserStatus');
                if (window.adminHelpers && window.adminHelpers.updateUserInUI) {
                    // Toggle is_active in the UI immediately for better UX
                    window.adminHelpers.updateUserInUI(user.id, { is_active: !user.is_active });
                }
            });
            
            // Patch createBackup method
            patchMethod('createBackup', function() {
                console.log('🔄 Real-time UI update for createBackup - will refresh data');
                setTimeout(() => {
                    if (this.loadData) {
                        this.loadData();
                    }
                }, 500);
            });
            
            // Patch saveSettings method
            patchMethod('saveSettings', function() {
                console.log('🔄 Real-time UI update for saveSettings');
                // Settings save is handled by the original function
            });
            
            // Patch deleteBackup method
            patchMethod('deleteBackup', function(backup) {
                console.log('🔄 Real-time UI update for deleteBackup');
                if (window.adminHelpers && window.adminHelpers.refreshBackupList) {
                    setTimeout(() => {
                        if (this.loadData) {
                            this.loadData();
                        }
                    }, 500);
                }
            });
            
            console.log('✅ All admin methods patched for real-time UI updates');
        }
        
        // Attempt to patch immediately if Alpine is already initialized
        setTimeout(() => {
            const mainEl = document.querySelector('main[x-data]');
            if (mainEl && Alpine.$data && Alpine.$data(mainEl)) {
                patchComponentMethods();
                observer.disconnect();
            }
        }, 500);
    });
})();
