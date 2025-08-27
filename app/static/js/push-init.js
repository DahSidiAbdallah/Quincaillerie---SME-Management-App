// Push Notification Registration and Handler
// This script registers the service worker and subscribes the user to push notifications

if ('serviceWorker' in navigator && 'PushManager' in window) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('Service Worker registered:', registration);
                // Subscribe to push notifications
                return registration.pushManager.getSubscription()
                    .then(function(subscription) {
                        if (subscription) {
                            return subscription;
                        }
                        // Replace with your VAPID public key (Base64 URL-encoded)
                        const vapidPublicKey = window.PushVAPIDPublicKey || '';
                        if (!vapidPublicKey) {
                            console.warn('No VAPID public key set for push notifications.');
                            return null;
                        }
                        const convertedVapidKey = urlBase64ToUint8Array(vapidPublicKey);
                        return registration.pushManager.subscribe({
                            userVisibleOnly: true,
                            applicationServerKey: convertedVapidKey
                        });
                    });
            })
            .then(function(subscription) {
                if (subscription) {
                    // Send subscription to server (implement endpoint on backend)
                    fetch('/api/push/subscribe', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'same-origin',
                        body: JSON.stringify(subscription)
                    });
                }
            })
            .catch(function(error) {
                console.error('Service Worker registration or push subscription failed:', error);
            });
    });
}

// Helper to convert VAPID key
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/-/g, '+')
        .replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}
