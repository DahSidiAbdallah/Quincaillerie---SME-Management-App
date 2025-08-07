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
                    // Show optimistic UI update
                    window.adminHelpers.showToast(`Suppression de l'utilisateur ${user.username}...`);
                    window.adminHelpers.removeUserFromUI(user.id);
                }
            });
            
            // Patch toggleUserStatus method
            patchMethod('toggleUserStatus', function(user) {
                console.log('🔄 Real-time UI update for toggleUserStatus');
                if (window.adminHelpers && window.adminHelpers.updateUserInUI) {
                    const newStatus = !user.is_active;
                    // Toggle is_active in the UI immediately for better UX
                    window.adminHelpers.updateUserInUI(user.id, { is_active: newStatus });
                    // Show status update toast
                    window.adminHelpers.showToast(
                        `Utilisateur ${user.username} ${newStatus ? 'activé' : 'désactivé'}`,
                        false,
                        2000
                    );
                }
            });
            
            // Patch createBackup method
            patchMethod('createBackup', function() {
                console.log('🔄 Real-time UI update for createBackup - will refresh data');
                // Show optimistic toast
                const toast = window.adminHelpers && window.adminHelpers.showToast 
                    ? window.adminHelpers.showToast('Création de la sauvegarde en cours...', false, 0)
                    : null;
                    
                setTimeout(() => {
                    if (this.loadData) {
                        this.loadData();
                        
                        // Update toast once complete
                        if (toast) {
                            toast.textContent = 'Sauvegarde créée avec succès';
                            toast.style.background = '#10b981';
                            setTimeout(() => {
                                toast.style.opacity = '0';
                                setTimeout(() => toast.remove(), 300);
                            }, 2000);
                        }
                    }
                }, 500);
            });
            
            // Patch saveSettings method
            patchMethod('saveSettings', function() {
                console.log('🔄 Real-time UI update for saveSettings');
                // Show optimistic toast
                if (window.adminHelpers && window.adminHelpers.showToast) {
                    window.adminHelpers.showToast('Paramètres enregistrés avec succès', false, 2000);
                }
                // If we have updateSettingsInUI helper, use it to ensure UI stays in sync with saved data
                if (window.adminHelpers && window.adminHelpers.updateSettingsInUI && this.settings) {
                    window.adminHelpers.updateSettingsInUI(this.settings);
                }
            });
            
            // Patch deleteBackup method
            patchMethod('deleteBackup', function(backup) {
                console.log('🔄 Real-time UI update for deleteBackup');
                // Show optimistic toast
                if (window.adminHelpers && window.adminHelpers.showToast) {
                    window.adminHelpers.showToast('Suppression de la sauvegarde...', false, 0);
                }
                
                if (window.adminHelpers && window.adminHelpers.refreshBackupList) {
                    setTimeout(() => {
                        if (this.loadData) {
                            this.loadData();
                            
                            // Show completion toast
                            if (window.adminHelpers && window.adminHelpers.showToast) {
                                window.adminHelpers.showToast('Sauvegarde supprimée avec succès', false, 2000);
                            }
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
