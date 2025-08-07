/**
 * Offline Data Handler
 * Manages caching and retrieval of data for offline use
 */

// IndexedDB database name and version
const DB_NAME = 'QuincaillerieOfflineDB';
const DB_VERSION = 1;

// Open the database
function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
        
        request.onupgradeneeded = event => {
            const db = event.target.result;
            
            // Create object stores for offline data
            if (!db.objectStoreNames.contains('products')) {
                db.createObjectStore('products', { keyPath: 'id' });
            }
            
            if (!db.objectStoreNames.contains('sales')) {
                db.createObjectStore('sales', { keyPath: 'id', autoIncrement: true });
            }
            
            if (!db.objectStoreNames.contains('customers')) {
                db.createObjectStore('customers', { keyPath: 'id' });
            }
            
            if (!db.objectStoreNames.contains('pendingOperations')) {
                const store = db.createObjectStore('pendingOperations', { 
                    keyPath: 'id', 
                    autoIncrement: true 
                });
                store.createIndex('timestamp', 'timestamp', { unique: false });
                store.createIndex('type', 'type', { unique: false });
            }
        };
    });
}

// Store data in IndexedDB
async function storeData(storeName, data) {
    try {
        const db = await openDB();
        const transaction = db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        
        if (Array.isArray(data)) {
            // If it's an array, store each item
            for (const item of data) {
                await store.put(item);
            }
        } else {
            // If it's a single item
            await store.put(data);
        }
        
        return true;
    } catch (error) {
        console.error(`Error storing data in ${storeName}:`, error);
        return false;
    }
}

// Get all data from a store
async function getAllData(storeName) {
    try {
        const db = await openDB();
        const transaction = db.transaction([storeName], 'readonly');
        const store = transaction.objectStore(storeName);
        
        return await store.getAll();
    } catch (error) {
        console.error(`Error getting data from ${storeName}:`, error);
        return [];
    }
}

// Get a single item by ID
async function getItemById(storeName, id) {
    try {
        const db = await openDB();
        const transaction = db.transaction([storeName], 'readonly');
        const store = transaction.objectStore(storeName);
        
        return await store.get(id);
    } catch (error) {
        console.error(`Error getting item #${id} from ${storeName}:`, error);
        return null;
    }
}

// Delete an item by ID
async function deleteItem(storeName, id) {
    try {
        const db = await openDB();
        const transaction = db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        
        await store.delete(id);
        return true;
    } catch (error) {
        console.error(`Error deleting item #${id} from ${storeName}:`, error);
        return false;
    }
}

// Store pending operation for later sync
async function storePendingOperation(type, data) {
    try {
        const pendingOp = {
            type: type,
            data: data,
            timestamp: Date.now()
        };
        
        const db = await openDB();
        const transaction = db.transaction(['pendingOperations'], 'readwrite');
        const store = transaction.objectStore('pendingOperations');
        
        await store.add(pendingOp);
        
        // Request sync if possible
        if ('serviceWorker' in navigator && 'SyncManager' in window) {
            const registration = await navigator.serviceWorker.ready;
            await registration.sync.register('sync-pending-operations');
        }
        
        return true;
    } catch (error) {
        console.error('Error storing pending operation:', error);
        return false;
    }
}

// Get all pending operations
async function getPendingOperations() {
    return await getAllData('pendingOperations');
}

// Process pending operations
async function processPendingOperations() {
    try {
        const pendingOps = await getPendingOperations();
        
        if (pendingOps.length === 0) {
            console.log('No pending operations to process');
            return { success: true, processed: 0 };
        }
        
        console.log(`Processing ${pendingOps.length} pending operations`);
        let processed = 0;
        let failed = 0;
        
        for (const op of pendingOps) {
            try {
                // Construct API endpoint based on operation type
                let endpoint = '';
                let method = 'POST';
                
                switch (op.type) {
                    case 'create_sale':
                        endpoint = '/api/sales/create';
                        method = 'POST';
                        break;
                    case 'update_product':
                        endpoint = `/api/inventory/products/${op.data.id}`;
                        method = 'PUT';
                        break;
                    case 'create_customer':
                        endpoint = '/api/customers/create';
                        method = 'POST';
                        break;
                    case 'update_inventory':
                        endpoint = '/api/inventory/update-stock';
                        method = 'PUT';
                        break;
                    case 'add_finance_record':
                        endpoint = '/api/finance/records';
                        method = 'POST';
                        break;
                    // Add other operation types as needed
                    default:
                        console.warn('Unknown operation type:', op.type);
                        continue;
                }
                
                console.log(`Processing operation: ${op.type}, ID: ${op.id}`);
                
                // Send the request to the server
                const response = await fetch(endpoint, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(op.data),
                    credentials: 'same-origin'
                });
                
                if (response.ok) {
                    // If successful, remove from pending operations
                    await deleteItem('pendingOperations', op.id);
                    processed++;
                    
                    // Update local data if needed
                    if (op.type === 'update_product') {
                        const products = await getAllData('products');
                        const index = products.findIndex(p => p.id === op.data.id);
                        if (index !== -1) {
                            products[index] = { ...products[index], ...op.data };
                            await storeData('products', products);
                        }
                    } else if (op.type === 'create_sale') {
                        // Get response data to update local record with server ID
                        try {
                            const responseData = await response.json();
                            if (responseData.success && responseData.sale_id) {
                                const sales = await getAllData('sales');
                                const localSale = sales.find(s => 
                                    s.reference === op.data.reference || 
                                    (s.created_at === op.data.created_at && !s.synced)
                                );
                                if (localSale) {
                                    localSale.id = responseData.sale_id;
                                    localSale.synced = true;
                                    await storeData('sales', sales);
                                }
                            }
                        } catch (parseError) {
                            console.error('Error parsing response:', parseError);
                        }
                    }
                    
                    console.log(`Operation ${op.id} processed successfully`);
                } else {
                    console.error(`Failed to process operation: ${op.id}, Status: ${response.status}`);
                    failed++;
                }
            } catch (error) {
                console.error('Error processing operation:', op, error);
                failed++;
            }
        }
        
        return { 
            success: true, 
            processed: processed,
            failed: failed,
            total: pendingOps.length
        };
    } catch (error) {
        console.error('Error processing pending operations:', error);
        return { success: false, error: error.message };
    }
}

// Fetch and cache API data
async function fetchAndCacheData(endpoint, storeName) {
    try {
        const response = await fetch(endpoint);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch data from ${endpoint}`);
        }
        
        const data = await response.json();
        
        if (data.success && data[storeName]) {
            // Store in IndexedDB for offline access
            await storeData(storeName, data[storeName]);
            return data[storeName];
        }
        
        return null;
    } catch (error) {
        console.error(`Error fetching and caching ${storeName}:`, error);
        
        // If fetch fails, try to get from IndexedDB
        return await getAllData(storeName);
    }
}

// Fetch products with fallback to cached data
async function getProducts() {
    return await fetchAndCacheData('/api/inventory/products', 'products');
}

// Fetch customers with fallback to cached data
async function getCustomers() {
    return await fetchAndCacheData('/api/customers/list', 'customers');
}

// Create a sale (works online or offline)
async function createSale(saleData) {
    try {
        if (navigator.onLine) {
            // Try to create sale online
            const response = await fetch('/api/sales/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(saleData)
            });
            
            if (response.ok) {
                const result = await response.json();
                
                if (result.success) {
                    // Store in local DB too
                    await storeData('sales', {
                        ...saleData,
                        id: result.sale_id,
                        synced: true
                    });
                    
                    return { 
                        success: true, 
                        sale_id: result.sale_id,
                        online: true
                    };
                }
            }
            
            throw new Error('Failed to create sale online');
        } else {
            // Offline mode - store locally and mark for sync
            const offlineSale = {
                ...saleData,
                created_at: new Date().toISOString(),
                synced: false
            };
            
            // Store in sales store
            await storeData('sales', offlineSale);
            
            // Add to pending operations
            await storePendingOperation('create_sale', saleData);
            
            return { 
                success: true,
                offline: true,
                message: 'Vente enregistrée hors ligne. Sera synchronisée quand la connexion sera rétablie.'
            };
        }
    } catch (error) {
        console.error('Error creating sale:', error);
        
        // Last resort - try to save offline even if online attempt failed
        try {
            const offlineSale = {
                ...saleData,
                created_at: new Date().toISOString(),
                synced: false
            };
            
            await storeData('sales', offlineSale);
            await storePendingOperation('create_sale', saleData);
            
            return { 
                success: true,
                offline: true,
                fallback: true,
                message: 'Vente enregistrée hors ligne suite à une erreur. Sera synchronisée plus tard.'
            };
        } catch (offlineError) {
            return { 
                success: false,
                error: 'Impossible de créer la vente: ' + error.message
            };
        }
    }
}

// Export all functions
window.offlineData = {
    storeData,
    getAllData,
    getItemById,
    deleteItem,
    storePendingOperation,
    getPendingOperations,
    processPendingOperations,
    getProducts,
    getCustomers,
    createSale
};
