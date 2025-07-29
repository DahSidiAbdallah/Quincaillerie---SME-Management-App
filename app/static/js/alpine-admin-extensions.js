/**
 * Alpine.js extensions for the admin page
 * This script adds global helpers and fixes for Alpine.js functionality
 */

// Immediately-invoked function expression to avoid polluting global scope
(function() {
    console.log('📌 Alpine.js Admin Extensions loading...');
    
    // Wait for Alpine.js to be defined
    function waitForAlpine(callback) {
        if (typeof Alpine !== 'undefined') {
            callback();
        } else {
            setTimeout(() => waitForAlpine(callback), 50);
        }
    }
    
    // Initialize Alpine extensions
    waitForAlpine(() => {
        console.log('🔄 Extending Alpine.js functionality...');
        
        // Add custom directives
        Alpine.directive('admin-fix', (el, { expression }, { evaluate }) => {
            // This directive helps fix issues with the admin page
            console.log('🛠️ Applied admin-fix to element:', el);
        });
        
        // Add custom magic properties for accessing data
        Alpine.magic('adminUsers', (el) => {
            return window.__adminData?.users || [];
        });
        
        Alpine.magic('adminSettings', (el) => {
            return window.__adminData?.settings || {};
        });
        
        Alpine.magic('adminBackups', (el) => {
            return window.__adminData?.backups || [];
        });
        
        // Add global helpers
        window.adminHelpers = {
            // Function to update users data
            updateUsers: function(users) {
                if (!users) return;
                
                try {
                    const mainElement = document.querySelector('main[x-data]');
                    if (mainElement) {
                        const component = Alpine.$data(mainElement);
                        if (component) {
                            component.users = users;
                            console.log('✅ Users data updated via helper');
                        }
                    }
                } catch (err) {
                    console.error('❌ Error updating users data:', err);
                }
            },
            
            // Function to update settings data
            updateSettings: function(settings) {
                if (!settings) return;
                
                try {
                    const mainElement = document.querySelector('main[x-data]');
                    if (mainElement) {
                        const component = Alpine.$data(mainElement);
                        if (component) {
                            component.settings = settings;
                            console.log('✅ Settings data updated via helper');
                        }
                    }
                } catch (err) {
                    console.error('❌ Error updating settings data:', err);
                }
            },
            
            // Function to update backups data
            updateBackups: function(backups) {
                if (!backups) return;
                
                try {
                    const mainElement = document.querySelector('main[x-data]');
                    if (mainElement) {
                        const component = Alpine.$data(mainElement);
                        if (component) {
                            component.backups = backups;
                            console.log('✅ Backups data updated via helper');
                        }
                    }
                } catch (err) {
                    console.error('❌ Error updating backups data:', err);
                }
            },
            
            // Function to reload all data
            reloadData: async function() {
                try {
                    const mainElement = document.querySelector('main[x-data]');
                    if (mainElement) {
                        const component = Alpine.$data(mainElement);
                        if (component && typeof component.loadData === 'function') {
                            await component.loadData();
                            console.log('✅ Admin data reloaded via helper');
                            return true;
                        }
                    }
                    return false;
                } catch (err) {
                    console.error('❌ Error reloading data:', err);
                    return false;
                }
            }
        };
        
        console.log('✅ Alpine.js Admin Extensions loaded successfully');
    });
})();
