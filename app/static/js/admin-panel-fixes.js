/**
 * Admin Panel Fix - Improved Error Handling
 * This script patches the admin panel functions with better error handling
 */
console.log('📌 Admin Panel Fixes loading...');

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Applying admin panel fixes...');
    
    // Helper function to show toast notifications
    function showToast(message, isError = false) {
        const toast = document.createElement('div');
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed; 
            bottom: 20px; 
            left: 20px; 
            background: ${isError ? '#ef4444' : '#10b981'}; 
            color: white; 
            padding: 12px 16px; 
            border-radius: 6px; 
            z-index: 9999;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            max-width: 80%;
            font-size: 14px;
        `;
        document.body.appendChild(toast);
        
        // Remove after 4 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.5s ease';
            setTimeout(() => toast.remove(), 500);
        }, 4000);
        
        return toast;
    }
    
    // Helper function to handle API errors consistently
    function handleApiError(error, action, entityName) {
        console.error(`Error ${action} ${entityName}:`, error);
        
        let errorMessage = `Erreur lors de ${action} ${entityName}`;
        
        // Extract error message if available
        if (error.message) {
            errorMessage += `: ${error.message}`;
        }
        
        // If it's a network error (which would result in undefined status)
        if (error.isNetworkError) {
            errorMessage = `Erreur de connexion: Impossible de contacter le serveur`;
        }
        
        showToast(errorMessage, true);
        return null;
    }

    // Enhanced API fetch with better response handling
    function enhancedApiFetch(url, options = {}) {
        return window.apiFetch(url, options)
            .then(response => {
                if (!response.ok) {
                    // Create a more detailed error
                    const error = new Error(`Request failed with status ${response.status}`);
                    error.response = response;
                    error.status = response.status;
                    
                    // For common status codes, add helpful messages
                    if (response.status === 403) {
                        error.message = "Accès non autorisé. Permissions insuffisantes.";
                    } else if (response.status === 404) {
                        error.message = "Ressource introuvable.";
                    } else if (response.status === 500) {
                        error.message = "Erreur serveur interne. Veuillez réessayer plus tard.";
                    }
                    
                    throw error;
                }
                return response.json().catch(err => {
                    // Handle JSON parsing errors
                    const parseError = new Error("Erreur de format dans la réponse du serveur");
                    parseError.originalError = err;
                    throw parseError;
                });
            })
            .then(data => {
                if (!data.success && data.message) {
                    throw new Error(data.message);
                }
                return data;
            });
    }
    
    // Wait for Alpine.js to be loaded and initialize
    function waitForAlpine(callback) {
        if (typeof Alpine !== 'undefined' && document.querySelector('main[x-data]')) {
            setTimeout(callback, 100); // Small delay to ensure Alpine has initialized components
        } else {
            setTimeout(() => waitForAlpine(callback), 50);
        }
    }
    
    // Apply fixes to admin panel functions
    waitForAlpine(() => {
        try {
            const mainElement = document.querySelector('main[x-data]');
            if (!mainElement) {
                console.error('❌ Admin panel main element not found');
                return;
            }
            
            const adminManager = Alpine.$data(mainElement);
            if (!adminManager) {
                console.error('❌ Admin manager component not found');
                return;
            }
            
            // Store original functions
            const originalToggleUserStatus = adminManager.toggleUserStatus;
            const originalDeleteUser = adminManager.deleteUser;
            const originalSaveSettings = adminManager.saveSettings;
            const originalCreateBackup = adminManager.createBackup;
            const originalDeleteBackup = adminManager.deleteBackup;
            
            // Enhance toggleUserStatus with better error handling
            adminManager.toggleUserStatus = function(user) {
                console.log('Enhanced toggleUserStatus for:', user.username);
                
                // Save the current status to revert in case of error
                const originalStatus = user.is_active;
                
                // Optimistic UI update
                user.is_active = !user.is_active;
                
                // Show status toast
                const statusToast = showToast(`Mise à jour du statut de ${user.username}...`);
                
                return enhancedApiFetch(`/api/auth/users/${user.id}`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({is_active: user.is_active})
                })
                    .then(data => {
                        statusToast.textContent = `Statut de ${user.username} mis à jour avec succès`;
                        statusToast.style.background = '#10b981';
                        
                        // Dispatch event for diagnostics tool
                        document.dispatchEvent(new CustomEvent('admin-users-updated', { detail: adminManager.users }));
                        
                        // Store updated users in global context for backup access
                        if (window.__adminData) {
                            window.__adminData.users = adminManager.users;
                        }
                        
                        return data;
                    })
                    .catch(error => {
                        // Revert the optimistic update if there was an error
                        user.is_active = originalStatus;
                        
                        // Store reverted users in global context
                        if (window.__adminData) {
                            window.__adminData.users = adminManager.users;
                        }
                        
                        return handleApiError(error, "de la mise à jour du statut de", user.username);
                    });
            };
            
            // Enhance deleteUser with better error handling
            adminManager.deleteUser = function(user) {
                if (!confirm(`Êtes-vous sûr de vouloir supprimer l'utilisateur ${user.username}?`)) {
                    return;
                }
                
                // Store user for potential restoration
                const deletedUser = {...user};
                const userIndex = adminManager.users.findIndex(u => u.id === user.id);
                
                // Optimistic UI update - remove from list immediately
                adminManager.users = adminManager.users.filter(u => u.id !== user.id);
                
                // Store updated users in global context for backup access
                if (window.__adminData) {
                    window.__adminData.users = adminManager.users;
                }
                
                // Show status toast
                const statusToast = showToast(`Suppression de ${user.username}...`);
                
                return enhancedApiFetch(`/api/auth/users/${user.id}`, { method: 'DELETE' })
                    .then(data => {
                        statusToast.textContent = `${user.username} supprimé avec succès`;
                        statusToast.style.background = '#10b981';
                        
                        // Dispatch event for diagnostics tool
                        document.dispatchEvent(new CustomEvent('admin-users-updated', { detail: adminManager.users }));
                        
                        return data;
                    })
                    .catch(error => {
                        // Restore user to the list if deletion failed
                        if (userIndex >= 0) {
                            adminManager.users.splice(userIndex, 0, deletedUser);
                        } else {
                            adminManager.users.push(deletedUser);
                        }
                        
                        // Store restored users in global context
                        if (window.__adminData) {
                            window.__adminData.users = adminManager.users;
                        }
                        
                        return handleApiError(error, "de la suppression de", user.username);
                    });
            };
            
            // Enhance saveSettings with better error handling
            adminManager.saveSettings = function() {
                // Save a copy of the settings before saving
                const originalSettings = JSON.parse(JSON.stringify(adminManager.settings));
                
                // Show saving status toast
                const statusToast = showToast('Sauvegarde des paramètres en cours...');
                
                // Store settings in global context for backup access
                if (window.__adminData) {
                    window.__adminData.settings = adminManager.settings;
                }
                
                return enhancedApiFetch('/api/admin/settings', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(adminManager.settings)
                })
                    .then(data => { 
                        statusToast.textContent = 'Paramètres sauvegardés avec succès';
                        statusToast.style.background = '#10b981';
                        
                        // Trigger an update event that other tools can listen for
                        document.dispatchEvent(new CustomEvent('admin-settings-updated', { detail: adminManager.settings }));
                        
                        return data;
                    })
                    .catch(error => {
                        // Restore original settings on error
                        adminManager.settings = originalSettings;
                        
                        // Store restored settings in global context
                        if (window.__adminData) {
                            window.__adminData.settings = originalSettings;
                        }
                        
                        return handleApiError(error, "de la sauvegarde", "des paramètres");
                    });
            };
            
            // Enhance createBackup with better error handling
            adminManager.createBackup = function() {
                // Show creating status toast
                const statusToast = showToast('Création de la sauvegarde en cours...');
                
                return enhancedApiFetch('/api/admin/backups', {method: 'POST'})
                    .then(data => {
                        statusToast.textContent = 'Sauvegarde créée avec succès!';
                        statusToast.style.background = '#10b981';
                        
                        // Refresh backups list
                        return enhancedApiFetch('/api/admin/backups')
                            .then(backupData => {
                                adminManager.backups = backupData.backups || [];
                                
                                // Store in global backup
                                if (window.__adminData) {
                                    window.__adminData.backups = adminManager.backups;
                                }
                                
                                // Dispatch event for diagnostics tool
                                document.dispatchEvent(new CustomEvent('admin-backups-updated', { detail: adminManager.backups }));
                                
                                return data;
                            })
                            .catch(error => {
                                console.error('Error refreshing backups list:', error);
                                return data; // Still return successful backup creation
                            });
                    })
                    .catch(error => {
                        return handleApiError(error, "de la création", "de la sauvegarde");
                    });
            };
            
            // Enhance deleteBackup with better error handling
            adminManager.deleteBackup = function(backup) {
                if (!confirm('Êtes-vous sûr de vouloir supprimer cette sauvegarde?')) {
                    return;
                }
                
                // Store backup for potential restoration
                const deletedBackup = {...backup};
                const backupIndex = adminManager.backups.findIndex(b => b.id === backup.id);
                
                // Optimistic UI update - remove from list immediately
                adminManager.backups = adminManager.backups.filter(b => b.id !== backup.id);
                
                // Store in global backup
                if (window.__adminData) {
                    window.__adminData.backups = adminManager.backups;
                }
                
                // Show status toast
                const statusToast = showToast('Suppression de la sauvegarde en cours...');
                
                return enhancedApiFetch(`/api/admin/backups/${backup.id}`, {method: 'DELETE'})
                    .then(data => { 
                        statusToast.textContent = 'Sauvegarde supprimée avec succès';
                        statusToast.style.background = '#10b981';
                        
                        // Dispatch event for diagnostics tool
                        document.dispatchEvent(new CustomEvent('admin-backups-updated', { detail: adminManager.backups }));
                        
                        return data;
                    })
                    .catch(error => {
                        // Restore backup to the list if deletion failed
                        if (backupIndex >= 0) {
                            adminManager.backups.splice(backupIndex, 0, deletedBackup);
                        } else {
                            adminManager.backups.push(deletedBackup);
                        }
                        
                        // Store restored backups in global context
                        if (window.__adminData) {
                            window.__adminData.backups = adminManager.backups;
                        }
                        
                        return handleApiError(error, "de la suppression", "de la sauvegarde");
                    });
            };
            
            console.log('✅ Admin panel fixes applied successfully');
        } catch (error) {
            console.error('❌ Error applying admin panel fixes:', error);
        }
    });
});
