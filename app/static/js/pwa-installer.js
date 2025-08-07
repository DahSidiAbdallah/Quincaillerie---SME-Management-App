/**
 * PWA Installer and Offline Handler
 * Manages service worker registration, app installation, and offline mode detection.
 */

// Variables for app installation
let deferredPrompt;
let installButton;

// Get install button when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    installButton = document.getElementById('pwaInstallButton');
    checkInstallationSupport();
});

// Service worker registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('Service Worker registered with scope:', registration.scope);
                
                // Register for background sync if available
                if ('SyncManager' in window) {
                    navigator.serviceWorker.ready.then(registration => {
                        // Register sync when user goes online
                        window.addEventListener('online', () => {
                            registration.sync.register('sync-queued-requests')
                                .catch(error => {
                                    console.error('Background sync registration error:', error);
                                });
                        });
                        
                        // Try to register periodic sync if supported
                        if ('periodicSync' in registration) {
                            navigator.permissions.query({
                                name: 'periodic-background-sync',
                            }).then(status => {
                                if (status.state === 'granted') {
                                    registration.periodicSync.register('daily-sync', {
                                        minInterval: 24 * 60 * 60 * 1000, // One day
                                    }).then(() => {
                                        console.log('Periodic background sync registered');
                                    }).catch(error => {
                                        console.error('Periodic background sync registration error:', error);
                                    });
                                }
                            });
                        }
                    });
                }
                
                // Check for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    console.log('Service Worker update found!');
                    
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            // New version available
                            showUpdateNotification();
                        }
                    });
                });
            })
            .catch(error => {
                console.error('Service Worker registration failed:', error);
            });
            
        // Listen for controller change
        navigator.serviceWorker.addEventListener('controllerchange', () => {
            console.log('Service Worker controller changed - page will reload');
            window.location.reload();
        });
        
        // Listen for messages from service worker
        navigator.serviceWorker.addEventListener('message', event => {
            const data = event.data;
            
            switch (data.type) {
                case 'SYNC_COMPLETED':
                    showSyncNotification(data.syncedCount, data.failedCount);
                    // Refresh data in the UI if applicable
                    if (typeof refreshAppData === 'function') {
                        refreshAppData();
                    }
                    break;
                    
                case 'PROCESS_PENDING_OPERATIONS':
                    // Call the offline handler to process pending operations
                    if (window.offlineData && window.offlineData.processPendingOperations) {
                        window.offlineData.processPendingOperations()
                            .then(result => {
                                if (result.processed > 0) {
                                    showSyncNotification(result.processed, result.failed);
                                    // Refresh data in the UI if applicable
                                    if (typeof refreshAppData === 'function') {
                                        refreshAppData();
                                    }
                                }
                            })
                            .catch(err => console.error('Error processing pending operations:', err));
                    }
                    break;
                
                case 'AUTH_REQUIRED':
                    // Redirect to login page if authentication is required
                    showToast('Veuillez vous connecter pour synchroniser les données', 'warning', 5000);
                    // Wait a moment before redirecting to allow the user to see the message
                    setTimeout(() => {
                        window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
                    }, 2000);
                    break;
                    
                case 'CACHE_UPDATED':
                    console.log('Cache updated:', data);
                    break;
                    
                case 'OFFLINE_STATUS':
                    updateOfflineStatus(data.isOffline);
                    break;
                    
                case 'UPDATE_AVAILABLE':
                    showUpdateNotification();
                    break;
                    
                default:
                    console.log('Unknown message from Service Worker:', data.type, data);
            }
        });
    });
}

// App installation
window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent Chrome 67+ from automatically showing the prompt
    e.preventDefault();
    
    // Stash the event so it can be triggered later
    deferredPrompt = e;
    
    // Update UI to show the install button
    if (!installButton) {
        installButton = document.getElementById('pwaInstallButton');
    }
    
    if (installButton) {
        // Show the install button
        installButton.classList.remove('hidden');
        
        // Clear previous event listeners to avoid duplicates
        const newButton = installButton.cloneNode(true);
        installButton.parentNode.replaceChild(newButton, installButton);
        installButton = newButton;
        
        // Add new click event listener
        installButton.addEventListener('click', () => {
            // Hide the button
            installButton.classList.add('hidden');
            
            // Show the prompt
            deferredPrompt.prompt();
            
            // Wait for the user to respond to the prompt
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('User accepted the install prompt');
                    showToast('Application installée avec succès!');
                    // Send analytics event
                    if (typeof sendAnalytics === 'function') {
                        sendAnalytics('app_install', 'accepted');
                    }
                } else {
                    console.log('User dismissed the install prompt');
                }
                
                deferredPrompt = null;
            });
        });
    }
});

// Listen for app installed event
window.addEventListener('appinstalled', (evt) => {
    console.log('App was installed');
    
    // Hide install button if it exists
    if (!installButton) {
        installButton = document.getElementById('pwaInstallButton');
    }
    
    if (installButton) {
        installButton.classList.add('hidden');
    }
    
    // Show confirmation toast
    showToast('Application installée avec succès!');
    
    // Send analytics event
    if (typeof sendAnalytics === 'function') {
        sendAnalytics('app_install', 'installed');
    }
});

// Online/Offline status handling
window.addEventListener('online', () => {
    console.log('App is online');
    updateOfflineStatus(false);
    
    // Sync data if service worker is available
    if (navigator.serviceWorker.controller) {
        navigator.serviceWorker.controller.postMessage({
            type: 'SYNC_DATA'
        });
        
        // Register background sync if available
        if ('serviceWorker' in navigator && 'SyncManager' in window) {
            navigator.serviceWorker.ready.then(registration => {
                registration.sync.register('sync-queued-requests')
                    .catch(error => {
                        console.error('Background sync registration error:', error);
                    });
            });
        }
    }
    
    // Show toast notification
    showToast('Connexion rétablie');
});

window.addEventListener('offline', () => {
    console.log('App is offline');
    updateOfflineStatus(true);
    
    // Show toast notification
    showToast('Mode hors ligne activé');
});

// Update offline status indicator
function updateOfflineStatus(isOffline) {
    const offlineIndicator = document.getElementById('offlineIndicator');
    const offlineIndicatorSimple = document.getElementById('offline-indicator');
    const syncIndicator = document.getElementById('syncIndicator');
    const syncText = document.getElementById('syncText');
    
    // Handle complex offline indicator (in main app)
    if (offlineIndicator) {
        if (isOffline) {
            offlineIndicator.classList.add('show');
            
            // Also update sync indicator if present
            if (syncIndicator && syncText) {
                syncIndicator.classList.remove('bg-green-500');
                syncIndicator.classList.add('bg-red-500');
                syncText.innerText = 'Hors ligne';
            }
        } else {
            offlineIndicator.classList.remove('show');
            
            // Update sync indicator if present
            if (syncIndicator && syncText) {
                syncIndicator.classList.remove('bg-red-500');
                syncIndicator.classList.add('bg-green-500');
                syncText.innerText = 'Synchronisé';
            }
        }
    }
    
    // Handle simple offline indicator (for simple pages)
    if (offlineIndicatorSimple) {
        if (isOffline) {
            offlineIndicatorSimple.classList.remove('hidden');
        } else {
            offlineIndicatorSimple.classList.add('hidden');
        }
    }
}

// Show update notification
function showUpdateNotification() {
    const notification = document.createElement('div');
    notification.className = 'fixed bottom-4 right-4 bg-indigo-600 text-white px-4 py-3 rounded-lg shadow-lg z-50 flex items-center';
    notification.innerHTML = `
        <span class="mr-2">Nouvelle version disponible!</span>
        <button id="updateButton" class="bg-white text-indigo-600 px-3 py-1 rounded-md text-sm font-medium hover:bg-indigo-50 transition">
            Mettre à jour
        </button>
    `;
    
    document.body.appendChild(notification);
    
    document.getElementById('updateButton').addEventListener('click', () => {
        // Tell service worker to skipWaiting
        if (navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
        }
        
        notification.remove();
    });
}

// Show sync notification
function showSyncNotification(successCount, failCount = 0) {
    if (successCount === 0 && failCount === 0) return;
    
    if (failCount > 0) {
        showToast(
            `${successCount} action${successCount > 1 || successCount === 0 ? 's' : ''} synchronisée${successCount > 1 ? 's' : ''}, 
            ${failCount} échec${failCount > 1 ? 's' : ''}`,
            'warning',
            5000
        );
    } else {
        showToast(
            `${successCount} action${successCount > 1 ? 's' : ''} synchronisée${successCount > 1 ? 's' : ''} avec succès`,
            'success',
            3000
        );
    }
}

// Show toast notification
function showToast(message, type = 'success', duration = 3000) {
    // Create toast element
    const toast = document.createElement('div');
    
    // Set color based on type
    let bgColor = 'bg-blue-600'; // default/info
    
    if (type === 'success') {
        bgColor = 'bg-green-600';
    } else if (type === 'error') {
        bgColor = 'bg-red-600';
    } else if (type === 'warning') {
        bgColor = 'bg-yellow-600';
    }
    
    toast.className = `fixed bottom-4 left-4 ${bgColor} text-white px-4 py-2 rounded-md shadow-lg z-50 transform translate-y-full transition-transform duration-300 ease-in-out`;
    
    // Add icon based on type
    let icon = '';
    if (type === 'success') {
        icon = '<svg class="inline-block w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
    } else if (type === 'error') {
        icon = '<svg class="inline-block w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>';
    } else if (type === 'warning') {
        icon = '<svg class="inline-block w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>';
    } else { // info
        icon = '<svg class="inline-block w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';
    }
    
    toast.innerHTML = `<div class="flex items-center">${icon}<span>${message}</span></div>`;
    
    document.body.appendChild(toast);
    
    // Show toast
    setTimeout(() => {
        toast.style.transform = 'translateY(0)';
    }, 100);
    
    // Hide toast after duration
    setTimeout(() => {
        toast.style.transform = 'translateY(100%)';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, duration);
}

// Force a sync of offline data
function syncOfflineData() {
    if (navigator.serviceWorker && navigator.serviceWorker.controller) {
        navigator.serviceWorker.controller.postMessage({
            type: 'SYNC_DATA'
        });
        
        if ('SyncManager' in window) {
            navigator.serviceWorker.ready.then(registration => {
                registration.sync.register('sync-queued-requests')
                    .then(() => {
                        console.log('Background sync registered');
                    })
                    .catch(error => {
                        console.error('Background sync registration error:', error);
                    });
            });
        }
    }
}

// Check initial offline status
function checkInitialOfflineStatus() {
    updateOfflineStatus(!navigator.onLine);
}

// Call this when page loads
document.addEventListener('DOMContentLoaded', checkInitialOfflineStatus);

// Check if the app can be installed on the current device
function checkInstallationSupport() {
    // Get the install button
    if (!installButton) {
        installButton = document.getElementById('pwaInstallButton');
        if (!installButton) return; // Button not in DOM
    }
    
    // Hide the button by default until we know installation is available
    installButton.classList.add('hidden');
    
    // For iOS/Safari
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
    
    if (isIOS) {
        // Check if the app is not already installed as standalone
        if (!isStandalone) {
            // On iOS, we need to show a custom install prompt
            const isSafari = /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent);
            if (isSafari) {
                // Show a custom install button for iOS Safari
                installButton.classList.remove('hidden');
                
                // Change button behavior for iOS
                installButton.addEventListener('click', showIOSInstallInstructions);
            }
        }
    }
    
    // For PWA-supported browsers, beforeinstallprompt will handle the button display
}

// Show iOS installation instructions
function showIOSInstallInstructions() {
    const iosPrompt = document.createElement('div');
    iosPrompt.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    iosPrompt.innerHTML = `
        <div class="bg-white p-4 rounded-lg max-w-md w-full mx-4">
            <h3 class="text-lg font-bold mb-2">Installer l'application sur iOS</h3>
            <ol class="list-decimal pl-5 mb-4 space-y-2">
                <li>Appuyez sur <strong>Partager</strong> <svg class="inline-block h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8h1a4 4 0 010 8h-1M5 8h1a4 4 0 010 8H5m7-14v6m-4-3l4 3 4-3"></path></svg> en bas de l'écran</li>
                <li>Faites défiler et appuyez sur <strong>Sur l'écran d'accueil</strong></li>
                <li>Appuyez sur <strong>Ajouter</strong> en haut à droite</li>
            </ol>
            <button id="closeIOSPrompt" class="bg-blue-600 text-white px-4 py-2 rounded-md w-full">Compris</button>
        </div>
    `;
    
    document.body.appendChild(iosPrompt);
    
    document.getElementById('closeIOSPrompt').addEventListener('click', () => {
        iosPrompt.remove();
    });
}
