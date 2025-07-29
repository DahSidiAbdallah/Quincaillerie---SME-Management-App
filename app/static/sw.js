// Service Worker for Quincaillerie Management App
const CACHE_NAME = 'quincaillerie-v1.0.0';
const OFFLINE_URL = '/offline.html';

// Resources to cache for offline functionality
const STATIC_CACHE_URLS = [
    '/',
    '/static/manifest.json',
    '/offline.html',
    // Tailwind CSS (CDN)
    'https://cdn.tailwindcss.com',
    // Alpine.js (CDN)
    'https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js',
    // Chart.js (CDN)
    'https://cdn.jsdelivr.net/npm/chart.js',
    // Core application routes
    '/dashboard',
    '/inventory',
    '/sales',
    '/finance',
    '/reports',
    // API endpoints for offline data
    '/api/dashboard/stats',
    '/api/inventory/products',
    '/api/sales/recent'
];

// API endpoints that should be cached for offline access
const API_CACHE_PATTERNS = [
    /^\/api\/inventory\/products/,
    /^\/api\/dashboard\/stats/,
    /^\/api\/sales\/recent/,
    /^\/api\/finance\/summary/
];

// Install event - cache static resources
self.addEventListener('install', event => {
    console.log('Service Worker: Installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Service Worker: Caching static files');
                return cache.addAll(STATIC_CACHE_URLS);
            })
            .then(() => {
                console.log('Service Worker: Static files cached successfully');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('Service Worker: Error caching static files:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker: Activating...');
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== CACHE_NAME) {
                            console.log('Service Worker: Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Service Worker: Activated successfully');
                return self.clients.claim();
            })
    );
});

// Fetch event - implement offline-first strategy
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests and chrome-extension requests
    if (request.method !== 'GET' || url.protocol === 'chrome-extension:') {
        return;
    }
    
    // Handle different types of requests
    if (request.destination === 'document') {
        // HTML pages - Network first, then cache
        event.respondWith(networkFirstStrategy(request));
    } else if (isAPIRequest(request)) {
        // API requests - Cache first for GET, network only for others
        event.respondWith(apiRequestStrategy(request));
    } else if (isStaticResource(request)) {
        // Static resources - Cache first
        event.respondWith(cacheFirstStrategy(request));
    } else {
        // Default strategy - Network first
        event.respondWith(networkFirstStrategy(request));
    }
});

// Network first strategy (for HTML pages)
async function networkFirstStrategy(request) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
            return networkResponse;
        }
        
        throw new Error('Network response not ok');
    } catch (error) {
        console.log('Service Worker: Network failed, trying cache:', request.url);
        
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // If it's a page request and we have no cache, return offline page
        if (request.destination === 'document') {
            const offlineResponse = await caches.match(OFFLINE_URL);
            if (offlineResponse) {
                return offlineResponse;
            }
        }
        
        throw error;
    }
}

// Cache first strategy (for static resources)
async function cacheFirstStrategy(request) {
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
        // Update cache in background
        updateCacheInBackground(request);
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('Service Worker: Failed to fetch resource:', request.url, error);
        throw error;
    }
}

// API request strategy
async function apiRequestStrategy(request) {
    const url = new URL(request.url);
    
    // For POST/PUT/DELETE requests, try network only and sync later if failed
    if (request.method !== 'GET') {
        return networkOnlyWithSync(request);
    }
    
    // For GET requests, try cache first for better performance
    try {
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse) {
            // Update cache in background
            updateCacheInBackground(request);
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('Service Worker: API request failed:', request.url);
        
        // Return cached response if available
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline response for API requests
        return new Response(
            JSON.stringify({
                success: false,
                error: 'Offline - data not available',
                offline: true
            }),
            {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

// Network only with sync for write operations
async function networkOnlyWithSync(request) {
    try {
        const response = await fetch(request);
        return response;
    } catch (error) {
        // Store request for later sync
        await storeRequestForSync(request);
        
        return new Response(
            JSON.stringify({
                success: false,
                error: 'Request queued for sync when online',
                queued: true
            }),
            {
                status: 202,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

// Update cache in background
function updateCacheInBackground(request) {
    fetch(request)
        .then(response => {
            if (response.ok) {
                return caches.open(CACHE_NAME)
                    .then(cache => cache.put(request, response));
            }
        })
        .catch(error => {
            console.log('Service Worker: Background cache update failed:', error);
        });
}

// Store request for later synchronization
async function storeRequestForSync(request) {
    try {
        const body = request.method !== 'GET' ? await request.text() : null;
        
        const requestData = {
            url: request.url,
            method: request.method,
            headers: Object.fromEntries(request.headers.entries()),
            body: body,
            timestamp: Date.now()
        };
        
        // Store in IndexedDB for sync later
        const db = await openSyncDB();
        const transaction = db.transaction(['sync_queue'], 'readwrite');
        const store = transaction.objectStore('sync_queue');
        
        await store.add(requestData);
        
        console.log('Service Worker: Request stored for sync:', request.url);
    } catch (error) {
        console.error('Service Worker: Error storing request for sync:', error);
    }
}

// Open IndexedDB for sync queue
function openSyncDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('QuincaillerieSyncDB', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
        
        request.onupgradeneeded = event => {
            const db = event.target.result;
            
            if (!db.objectStoreNames.contains('sync_queue')) {
                const store = db.createObjectStore('sync_queue', { 
                    keyPath: 'id', 
                    autoIncrement: true 
                });
                store.createIndex('timestamp', 'timestamp', { unique: false });
            }
        };
    });
}

// Helper functions
function isAPIRequest(request) {
    const url = new URL(request.url);
    return url.pathname.startsWith('/api/');
}

function isStaticResource(request) {
    const url = new URL(request.url);
    const staticExtensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2'];
    
    return staticExtensions.some(ext => url.pathname.endsWith(ext)) ||
           url.hostname === 'cdn.tailwindcss.com' ||
           url.hostname === 'unpkg.com' ||
           url.hostname === 'cdn.jsdelivr.net';
}

// Background sync event
self.addEventListener('sync', event => {
    console.log('Service Worker: Background sync triggered:', event.tag);
    
    if (event.tag === 'sync-queued-requests') {
        event.waitUntil(syncQueuedRequests());
    }
});

// Sync queued requests when back online
async function syncQueuedRequests() {
    try {
        const db = await openSyncDB();
        const transaction = db.transaction(['sync_queue'], 'readwrite');
        const store = transaction.objectStore('sync_queue');
        
        const requests = await store.getAll();
        
        for (const requestData of requests) {
            try {
                const response = await fetch(requestData.url, {
                    method: requestData.method,
                    headers: requestData.headers,
                    body: requestData.body
                });
                
                if (response.ok) {
                    // Remove from sync queue
                    await store.delete(requestData.id);
                    console.log('Service Worker: Synced request:', requestData.url);
                } else {
                    console.log('Service Worker: Sync failed for request:', requestData.url);
                }
            } catch (error) {
                console.error('Service Worker: Error syncing request:', requestData.url, error);
            }
        }
        
        // Notify clients about sync completion
        const clients = await self.clients.matchAll();
        clients.forEach(client => {
            client.postMessage({
                type: 'SYNC_COMPLETED',
                syncedCount: requests.length
            });
        });
        
    } catch (error) {
        console.error('Service Worker: Error during sync:', error);
    }
}

// Message handling from main thread
self.addEventListener('message', event => {
    const { type, data } = event.data;
    
    switch (type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;
            
        case 'CACHE_URLS':
            if (data && data.urls) {
                cacheUrls(data.urls);
            }
            break;
            
        case 'CLEAR_CACHE':
            clearCache().then(() => {
                event.ports[0].postMessage({ success: true });
            });
            break;
            
        case 'GET_CACHE_SIZE':
            getCacheSize().then(size => {
                event.ports[0].postMessage({ size });
            });
            break;
            
        default:
            console.log('Service Worker: Unknown message type:', type);
    }
});

// Cache specific URLs
async function cacheUrls(urls) {
    try {
        const cache = await caches.open(CACHE_NAME);
        await cache.addAll(urls);
        console.log('Service Worker: URLs cached successfully');
    } catch (error) {
        console.error('Service Worker: Error caching URLs:', error);
    }
}

// Clear all caches
async function clearCache() {
    const cacheNames = await caches.keys();
    await Promise.all(
        cacheNames.map(cacheName => caches.delete(cacheName))
    );
    console.log('Service Worker: All caches cleared');
}

// Get cache size estimate
async function getCacheSize() {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
        const estimate = await navigator.storage.estimate();
        return {
            used: estimate.usage,
            available: estimate.quota
        };
    }
    return { used: 0, available: 0 };
}

// Push notification handling
self.addEventListener('push', event => {
    if (!event.data) return;
    
    const data = event.data.json();
    const options = {
        body: data.body,
        icon: '/static/icon-192x192.png',
        badge: '/static/badge-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: data.primaryKey || 1
        },
        actions: [
            {
                action: 'explore',
                title: 'Voir Détails',
                icon: '/static/checkmark.png'
            },
            {
                action: 'close',
                title: 'Fermer',
                icon: '/static/xmark.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    if (event.action === 'explore') {
        // Open the app
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Error handling
self.addEventListener('error', event => {
    console.error('Service Worker: Error occurred:', event.error);
});

self.addEventListener('unhandledrejection', event => {
    console.error('Service Worker: Unhandled promise rejection:', event.reason);
});

console.log('Service Worker: Loaded successfully');
