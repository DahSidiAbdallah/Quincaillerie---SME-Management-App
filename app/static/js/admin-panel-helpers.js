/**
 * Admin Panel Helper Functions
 * This script provides utilities for enhancing the admin panel functionality
 * with improved real-time updates, UI manipulation, and error handling.
 */

(function() {
    // Create global namespace for admin helpers
    window.adminHelpers = window.adminHelpers || {};
    
    /**
     * Get the Alpine.js admin component data
     * @returns {Object|null} The admin component data or null if not found
     */
    function getAdminComponent() {
        try {
            const mainElement = document.querySelector('main[x-data]');
            return mainElement && typeof Alpine !== 'undefined' ? Alpine.$data(mainElement) : null;
        } catch (err) {
            console.error('Error getting admin component:', err);
            return null;
        }
    }
    
    /**
     * Force Alpine.js to re-evaluate bindings
     */
    function refreshAlpineBindings() {
        try {
            Alpine.morph && Alpine.morph(document.body, document.body.innerHTML);
        } catch (err) {
            console.error('Error refreshing Alpine bindings:', err);
        }
    }
    
    /**
     * Show a toast notification
     * @param {string} message The message to display
     * @param {boolean} isError Whether this is an error message
     * @param {number} duration How long to show the toast (ms)
     * @returns {HTMLElement} The toast element
     */
    function showToast(message, isError = false, duration = 3000) {
        // Create toast container if it doesn't exist
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = 'position: fixed; bottom: 20px; left: 20px; z-index: 9999;';
            document.body.appendChild(container);
        }
        
        // Create toast element
        const toast = document.createElement('div');
        toast.style.cssText = `
            margin-top: 10px;
            padding: 12px 16px;
            border-radius: 4px;
            color: white;
            font-size: 14px;
            max-width: 300px;
            box-shadow: 0 3px 6px rgba(0,0,0,0.16);
            background: ${isError ? '#ef4444' : '#3b82f6'};
            transition: all 0.3s ease;
        `;
        toast.textContent = message;
        
        // Add to container
        container.appendChild(toast);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
        
        return toast;
    }
    
    /**
     * Update a user in the UI
     * @param {string|number} userId The ID of the user to update
     * @param {Object} data The new data for the user
     */
    function updateUserInUI(userId, data) {
        try {
            const component = getAdminComponent();
            
            if (component && component.users) {
                // Find and update user in the Alpine data
                const userIndex = component.users.findIndex(u => u.id == userId);
                if (userIndex !== -1) {
                    Object.assign(component.users[userIndex], data);
                    // Trigger an update event
                    document.dispatchEvent(new CustomEvent('admin-users-updated', { 
                        detail: component.users 
                    }));
                }
            } else {
                // Fallback to direct DOM manipulation if Alpine data is not available
                const userRow = document.querySelector(`tr[data-user-id="${userId}"]`);
                if (userRow) {
                    // Update status badge if status changed
                    if (data.hasOwnProperty('is_active')) {
                        const statusBadge = userRow.querySelector('.status-badge');
                        if (statusBadge) {
                            statusBadge.className = data.is_active ? 
                                'px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800 status-badge' : 
                                'px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800 status-badge';
                            statusBadge.textContent = data.is_active ? 'Actif' : 'Inactif';
                        }
                    }
                }
            }
        } catch (err) {
            console.error('Error updating user in UI:', err);
        }
    }
    
    /**
     * Remove a user from the UI
     * @param {string|number} userId The ID of the user to remove
     */
    function removeUserFromUI(userId) {
        try {
            const component = getAdminComponent();
            
            if (component && component.users) {
                // Remove user from Alpine data
                const userIndex = component.users.findIndex(u => u.id == userId);
                if (userIndex !== -1) {
                    component.users.splice(userIndex, 1);
                    // Trigger an update event
                    document.dispatchEvent(new CustomEvent('admin-users-updated', { 
                        detail: component.users 
                    }));
                }
            }
            
            // Also remove from DOM directly as a fallback
            const userRow = document.querySelector(`tr[data-user-id="${userId}"]`);
            if (userRow) {
                userRow.style.transition = 'opacity 0.3s, height 0.3s';
                userRow.style.opacity = '0';
                userRow.style.height = '0';
                setTimeout(() => userRow.remove(), 300);
            }
        } catch (err) {
            console.error('Error removing user from UI:', err);
        }
    }
    
    /**
     * Refresh the backup list in the UI
     * @param {Array} backups Optional array of backups to set
     */
    function refreshBackupList(backups) {
        try {
            const component = getAdminComponent();
            
            if (component) {
                if (backups) {
                    component.backups = backups;
                } else if (component.loadBackups) {
                    component.loadBackups();
                }
                
                // Trigger an update event
                document.dispatchEvent(new CustomEvent('admin-backups-updated', { 
                    detail: component.backups 
                }));
            }
        } catch (err) {
            console.error('Error refreshing backup list:', err);
        }
    }
    
    /**
     * Update settings in the UI
     * @param {Object} settings The new settings
     */
    function updateSettingsInUI(settings) {
        try {
            const component = getAdminComponent();
            
            if (component && component.settings) {
                // Update Alpine settings data
                Object.assign(component.settings, settings);
                
                // Trigger an update event
                document.dispatchEvent(new CustomEvent('admin-settings-updated', { 
                    detail: component.settings 
                }));
            }
        } catch (err) {
            console.error('Error updating settings in UI:', err);
        }
    }
    
    /**
     * Force reload of all admin data
     */
    function reloadData() {
        try {
            const component = getAdminComponent();
            
            if (component && component.loadData) {
                component.loadData();
                showToast('Données rechargées avec succès');
            } else {
                console.error('Cannot reload data: component or loadData method not found');
                showToast('Impossible de recharger les données', true);
            }
        } catch (err) {
            console.error('Error reloading data:', err);
            showToast('Erreur lors du rechargement des données', true);
        }
    }
    
    // Expose helper functions globally
    Object.assign(window.adminHelpers, {
        getAdminComponent,
        refreshAlpineBindings,
        showToast,
        updateUserInUI,
        removeUserFromUI,
        refreshBackupList,
        updateSettingsInUI,
        reloadData
    });
    
    // Initialize
    document.addEventListener('DOMContentLoaded', () => {
        console.log('📦 Admin Panel Helpers initialized');
        
        // Add data attributes to user rows for direct DOM manipulation
        setTimeout(() => {
            try {
                const component = getAdminComponent();
                if (component && component.users) {
                    const userRows = document.querySelectorAll('tr');
                    userRows.forEach((row, index) => {
                        if (component.users[index]) {
                            row.setAttribute('data-user-id', component.users[index].id);
                        }
                    });
                }
            } catch (err) {
                console.error('Error initializing user row IDs:', err);
            }
        }, 1000);
    });
})();
