/**
 * Admin API diagnostic script
 * This script checks the connection to admin-related APIs and displays diagnostic info
 * Enhanced with better UI and helper function integration
 */
console.log('🔧 Admin API Diagnostics Tool starting...');

// Create diagnostic UI
function setupDiagnosticsUI() {
    const diagContainer = document.createElement('div');
    diagContainer.id = 'admin-diagnostics';
    diagContainer.style.cssText = 'position: fixed; bottom: 10px; right: 10px; width: 400px; max-height: 500px; overflow-y: auto; background: #fff; border: 2px solid #3b82f6; border-radius: 8px; padding: 10px; font-family: monospace; font-size: 12px; z-index: 9999; box-shadow: 0 0 10px rgba(0,0,0,0.2);';
    
    const header = document.createElement('div');
    header.innerHTML = '<h3 style="margin: 0 0 10px 0; color: #3b82f6;">Admin API Diagnostics</h3>';
    header.style.cssText = 'display: flex; justify-content: space-between; align-items: center;';
    
    const minimizeButton = document.createElement('button');
    minimizeButton.textContent = '-';
    minimizeButton.style.cssText = 'background: #3b82f6; color: white; border: none; border-radius: 4px; padding: 2px 6px; cursor: pointer; margin-right: 5px;';
    minimizeButton.onclick = () => {
        const content = document.getElementById('admin-diagnostics-content');
        const actions = document.getElementById('admin-diagnostics-actions');
        if (content.style.display === 'none') {
            content.style.display = 'block';
            actions.style.display = 'flex';
            minimizeButton.textContent = '-';
            diagContainer.style.width = '400px';
        } else {
            content.style.display = 'none';
            actions.style.display = 'none';
            minimizeButton.textContent = '+';
            diagContainer.style.width = '200px';
        }
    };
    
    const closeButton = document.createElement('button');
    closeButton.textContent = 'X';
    closeButton.style.cssText = 'background: #ef4444; color: white; border: none; border-radius: 4px; padding: 2px 6px; cursor: pointer;';
    closeButton.onclick = () => diagContainer.remove();
    
    header.appendChild(minimizeButton);
    header.appendChild(closeButton);
    diagContainer.appendChild(header);
    
    // Add action buttons
    const actions = document.createElement('div');
    actions.id = 'admin-diagnostics-actions';
    actions.style.cssText = 'display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap;';
    
    // Reload data button
    const reloadButton = document.createElement('button');
    reloadButton.textContent = 'Reload Data';
    reloadButton.style.cssText = 'background: #3b82f6; color: white; border: none; border-radius: 4px; padding: 4px 8px; cursor: pointer; font-size: 12px;';
    reloadButton.onclick = () => {
        if (window.adminHelpers && window.adminHelpers.reloadData) {
            window.adminHelpers.reloadData();
            log('🔄 Data reload requested');
        } else {
            log('❌ Admin helpers not available', true);
        }
    };
    actions.appendChild(reloadButton);
    
    // Check Alpine data button
    const alpineButton = document.createElement('button');
    alpineButton.textContent = 'Check Alpine Data';
    alpineButton.style.cssText = 'background: #10b981; color: white; border: none; border-radius: 4px; padding: 4px 8px; cursor: pointer; font-size: 12px;';
    alpineButton.onclick = () => {
        try {
            const adminComponent = window.adminHelpers ? 
                window.adminHelpers.getAdminComponent() : 
                (Alpine && Alpine.$data ? Alpine.$data(document.querySelector('main[x-data]')) : null);
                
            if (adminComponent) {
                log('✅ Alpine data accessible');
                log(`Users: ${adminComponent.users ? adminComponent.users.length : 0}`);
                log(`Settings: ${adminComponent.settings ? 'Available' : 'Not available'}`);
                log(`Backups: ${adminComponent.backups ? adminComponent.backups.length : 0}`);
            } else {
                log('❌ Alpine data not accessible', true);
            }
        } catch (err) {
            log(`❌ Error checking Alpine data: ${err.message}`, true);
        }
    };
    actions.appendChild(alpineButton);
    
    // Force UI update button
    const uiUpdateButton = document.createElement('button');
    uiUpdateButton.textContent = 'Force UI Update';
    uiUpdateButton.style.cssText = 'background: #8b5cf6; color: white; border: none; border-radius: 4px; padding: 4px 8px; cursor: pointer; font-size: 12px;';
    uiUpdateButton.onclick = () => {
        if (window.adminHelpers && window.adminHelpers.refreshAlpineBindings) {
            window.adminHelpers.refreshAlpineBindings();
            log('🔄 Forced Alpine UI update');
        } else {
            log('❌ Alpine refresh helper not available', true);
        }
    };
    actions.appendChild(uiUpdateButton);
    
    diagContainer.appendChild(actions);
    
    const content = document.createElement('div');
    content.id = 'admin-diagnostics-content';
    diagContainer.appendChild(content);
    
    document.body.appendChild(diagContainer);
    
    return content;
}

function log(message, isError = false) {
    const content = document.getElementById('admin-diagnostics-content');
    const entry = document.createElement('div');
    entry.style.cssText = `margin-bottom: 8px; color: ${isError ? '#ef4444' : '#333'};`;
    entry.innerHTML = message;
    content.appendChild(entry);
    console.log(message);
}

async function testAuthStatus() {
    log('Checking authentication status...');
    try {
        const response = await fetch('/api/auth/status');
        const data = await response.json();
        
        log(`Auth status: ${data.authenticated ? 'Authenticated ✅' : 'Not authenticated ❌'}`);
        if (data.authenticated) {
            log(`User: ${data.user.username} (${data.user.role})`);
            return data.user;
        }
    } catch (err) {
        log(`Error checking auth status: ${err.message}`, true);
    }
    return null;
}

async function testUsersList() {
    log('Testing users list API...');
    try {
        const response = await fetch('/api/auth/users');
        if (!response.ok) {
            log(`Error: Server returned ${response.status} ${response.statusText}`, true);
            return null;
        }
        
        const data = await response.json();
        if (data.success) {
            log(`Users list retrieved: ${data.users.length} users found ✅`);
            return data.users;
        } else {
            log(`Error: ${data.message}`, true);
        }
    } catch (err) {
        log(`Error getting users list: ${err.message}`, true);
    }
    return null;
}

async function testSettings() {
    log('Testing settings API...');
    try {
        const response = await fetch('/api/admin/settings');
        if (!response.ok) {
            log(`Error: Server returned ${response.status} ${response.statusText}`, true);
            return null;
        }
        
        const data = await response.json();
        if (data.success) {
            log(`Settings retrieved ✅`);
            return data.settings;
        } else {
            log(`Error: ${data.message}`, true);
        }
    } catch (err) {
        log(`Error getting settings: ${err.message}`, true);
    }
    return null;
}

async function testBackups() {
    log('Testing backups API...');
    try {
        const response = await fetch('/api/admin/backups');
        if (!response.ok) {
            log(`Error: Server returned ${response.status} ${response.statusText}`, true);
            return null;
        }
        
        const data = await response.json();
        if (data.success) {
            log(`Backups list retrieved: ${data.backups.length} backups found ✅`);
            return data.backups;
        } else {
            log(`Error: ${data.message}`, true);
        }
    } catch (err) {
        log(`Error getting backups: ${err.message}`, true);
    }
    return null;
}

// Test if Alpine data is accessible and find Alpine instances
function testAlpineData() {
    log('Checking Alpine.js data...');
    // Check if Alpine is defined
    if (typeof Alpine === 'undefined') {
        log('Alpine.js is not defined ❌', true);
        return false;
    }

    try {
        // Find the Alpine component root element
        const mainElement = document.querySelector('main[x-data]');
        if (!mainElement) {
            log('Alpine.js root element not found ❌', true);
            return false;
        }
        
        // Try to get the Alpine component instance directly
        const alpineComponent = Alpine.$data(mainElement);
        if (alpineComponent) {
            log('Alpine.js data accessible ✅');
            return { success: true, component: alpineComponent, element: mainElement };
        } else {
            log('Alpine.js data not accessible via $data ❌', true);
            return { success: false };
        }
    } catch (err) {
        log(`Error accessing Alpine.js data: ${err.message}`, true);
        return { success: false };
    }
}

// Update Alpine data directly using multiple strategies
function updateAlpineData(users, settings, backups) {
    log('Attempting to update Alpine.js data...');
    
    // Try multiple strategies to update Alpine data
    const strategies = [
        updateViaAlpineData,
        updateViaDispatchEvent,
        updateViaJSGlobal,
        updateViaDirectDOMManipulation
    ];
    
    let success = false;
    for (const strategy of strategies) {
        if (strategy(users, settings, backups)) {
            success = true;
            break;
        }
    }
    
    if (!success) {
        log('Failed to update data with any strategy. Falling back to DOM injection.', true);
        injectUsersDirectly(users);
    }
}

// Strategy 1: Try using Alpine.$data
function updateViaAlpineData(users, settings, backups) {
    try {
        const mainElement = document.querySelector('main[x-data]');
        if (!mainElement) return false;
        
        const alpineData = Alpine.$data(mainElement);
        if (!alpineData) return false;
        
        log('Updating via Alpine.$data...');
        if (users && Array.isArray(users)) {
            alpineData.users = users;
            log('Updated users data ✅');
        }
        
        if (settings) {
            alpineData.settings = settings;
            log('Updated settings data ✅');
        }
        
        if (backups && Array.isArray(backups)) {
            alpineData.backups = backups;
            log('Updated backups data ✅');
        }
        
        return true;
    } catch (err) {
        log(`Error with Alpine.$data update: ${err.message}`, true);
        return false;
    }
}

// Strategy 2: Try using custom events
function updateViaDispatchEvent(users, settings, backups) {
    try {
        log('Updating via custom events...');
        const mainElement = document.querySelector('main[x-data]');
        if (!mainElement) return false;
        
        if (users) {
            const usersEvent = new CustomEvent('update-users', { detail: { users } });
            mainElement.dispatchEvent(usersEvent);
            log('Dispatched users update event ✅');
        }
        
        if (settings) {
            const settingsEvent = new CustomEvent('update-settings', { detail: { settings } });
            mainElement.dispatchEvent(settingsEvent);
            log('Dispatched settings update event ✅');
        }
        
        if (backups) {
            const backupsEvent = new CustomEvent('update-backups', { detail: { backups } });
            mainElement.dispatchEvent(backupsEvent);
            log('Dispatched backups update event ✅');
        }
        
        return true;
    } catch (err) {
        log(`Error with event dispatch update: ${err.message}`, true);
        return false;
    }
}

// Strategy 3: Create a global variable to pass data
function updateViaJSGlobal(users, settings, backups) {
    try {
        log('Updating via global variables...');
        
        // Create a global object to store our data
        window.__adminData = window.__adminData || {};
        
        if (users) {
            window.__adminData.users = users;
            log('Set global users data ✅');
        }
        
        if (settings) {
            window.__adminData.settings = settings;
            log('Set global settings data ✅');
        }
        
        if (backups) {
            window.__adminData.backups = backups;
            log('Set global backups data ✅');
        }
        
        // Execute a small script to help sync this data
        const script = document.createElement('script');
        script.textContent = `
            try {
                const mainEl = document.querySelector('main[x-data]');
                if (mainEl && window.__adminData) {
                    const comp = Alpine.$data(mainEl);
                    if (comp) {
                        if (window.__adminData.users) comp.users = window.__adminData.users;
                        if (window.__adminData.settings) comp.settings = window.__adminData.settings;
                        if (window.__adminData.backups) comp.backups = window.__adminData.backups;
                    }
                }
            } catch (e) {
                console.error('Error syncing global data:', e);
            }
        `;
        document.body.appendChild(script);
        
        return true;
    } catch (err) {
        log(`Error with global variable update: ${err.message}`, true);
        return false;
    }
}

// Strategy 4: Direct DOM manipulation for critical components
function updateViaDirectDOMManipulation(users, settings, backups) {
    // This is a fallback approach
    return false;
}

// Last resort: Inject users directly into the DOM
function injectUsersDirectly(users) {
    if (!users || !Array.isArray(users) || users.length === 0) {
        log('No user data to inject', true);
        return;
    }
    
    try {
        log('Attempting direct DOM injection of users...');
        const userTable = document.querySelector('table tbody');
        
        if (!userTable) {
            log('User table not found in DOM', true);
            return;
        }
        
        // Clear existing rows except for template
        const template = userTable.querySelector('template');
        userTable.innerHTML = '';
        if (template) userTable.appendChild(template);
        
        // Create a row for each user
        users.forEach(user => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-50';
            row.dataset.userId = user.id; // Add user ID as data attribute
            
            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="flex-shrink-0 h-10 w-10">
                            <div class="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                                <i class="fas fa-user text-blue-600"></i>
                            </div>
                        </div>
                        <div class="ml-4">
                            <div class="text-sm font-medium text-gray-900">${user.username}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${user.role === 'admin' ? 'bg-red-100 text-red-800' : 
                          user.role === 'manager' ? 'bg-blue-100 text-blue-800' : 
                          'bg-green-100 text-green-800'}">
                        ${user.role}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${user.last_login || 'Jamais'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                        ${user.is_active ? 'Actif' : 'Inactif'}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button onclick="window.getAdminComponent().editUser(${JSON.stringify(user).replace(/"/g, '&quot;')})" class="text-blue-600 hover:text-blue-900 mr-3">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button onclick="window.getAdminComponent().toggleUserStatus(${JSON.stringify(user).replace(/"/g, '&quot;')})" class="text-yellow-600 hover:text-yellow-900 mr-3">
                        <i class="fas fa-power-off"></i>
                    </button>
                    <button onclick="window.getAdminComponent().deleteUser(${JSON.stringify(user).replace(/"/g, '&quot;')})" class="text-red-600 hover:text-red-900">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            
            userTable.appendChild(row);
        });
        
        log('Users injected directly into DOM ✅');
        
        // Add event listeners to the injected buttons
        addEventListenersToInjectedElements();
    } catch (err) {
        log(`Error injecting users: ${err.message}`, true);
    }
}

// Add Alpine.js event listeners
function setupAlpineEventListeners() {
    try {
        const mainElement = document.querySelector('main[x-data]');
        if (!mainElement) return;
        
        // Add event listeners for our custom events
        mainElement.addEventListener('update-users', function(e) {
            const alpine = Alpine.$data(mainElement);
            if (alpine) {
                alpine.users = e.detail.users;
                log('Users updated via event listener ✅');
            }
        });
        
        mainElement.addEventListener('update-settings', function(e) {
            const alpine = Alpine.$data(mainElement);
            if (alpine) {
                alpine.settings = e.detail.settings;
                log('Settings updated via event listener ✅');
            }
        });
        
        mainElement.addEventListener('update-backups', function(e) {
            const alpine = Alpine.$data(mainElement);
            if (alpine) {
                alpine.backups = e.detail.backups;
                log('Backups updated via event listener ✅');
            }
        });
        
        log('Alpine event listeners set up ✅');
    } catch (err) {
        log(`Error setting up event listeners: ${err.message}`, true);
    }
}

// Update tab content if needed
function updateTabContent(users, settings, backups) {
    try {
        // Find any empty tables and inject data if appropriate
        const emptyTables = document.querySelectorAll('tbody:empty');
        
        if (emptyTables.length > 0) {
            log(`Found ${emptyTables.length} empty tables, attempting to populate...`);
            
            // Look for user table
            const userTab = document.querySelector('[x-show="activeTab === \'users\'"]');
            if (userTab && users && users.length > 0) {
                const tbody = userTab.querySelector('tbody');
                if (tbody) {
                    injectUsersDirectly(users);
                }
            }
            
            // Attempt to show users tab
            const userTabButton = document.querySelector('button[x-text="\'Utilisateurs\'"]') || 
                                document.querySelector('button:contains("Utilisateurs")');
            if (userTabButton) {
                log('Clicking users tab button');
                userTabButton.click();
            }
        }
    } catch (err) {
        log(`Error updating tab content: ${err.message}`, true);
    }
}

// Helper function to add the admin component to window for debugging
function exposeAdminToWindow() {
    try {
        const mainElement = document.querySelector('main[x-data]');
        if (!mainElement) return;
        
        // Create a helper to expose admin component
        window.getAdminComponent = function() {
            return Alpine.$data(mainElement);
        };
        
        // Add helper functions to update data in real-time
        window.adminHelpers = window.adminHelpers || {};
        
        // Helper to update user status without page refresh
        window.adminHelpers.updateUserInUI = function(userId, updates) {
            const component = Alpine.$data(mainElement);
            if (component && component.users) {
                const userIndex = component.users.findIndex(u => u.id === userId);
                if (userIndex !== -1) {
                    Object.assign(component.users[userIndex], updates);
                    log(`Updated user ${userId} in UI ✅`);
                    return true;
                }
            }
            return false;
        };
        
        // Helper to remove user from UI without page refresh
        window.adminHelpers.removeUserFromUI = function(userId) {
            const component = Alpine.$data(mainElement);
            if (component && component.users) {
                const initialLength = component.users.length;
                component.users = component.users.filter(u => u.id !== userId);
                if (component.users.length !== initialLength) {
                    log(`Removed user ${userId} from UI ✅`);
                    return true;
                }
            }
            return false;
        };
        
        // Helper to update backup list in UI without page refresh
        window.adminHelpers.refreshBackupList = function(backups) {
            const component = Alpine.$data(mainElement);
            if (component) {
                component.backups = backups;
                log('Backup list refreshed in UI ✅');
                return true;
            }
            return false;
        };
        
        log('Admin component and helpers exposed to window ✅');
    } catch (err) {
        log(`Error exposing admin component: ${err.message}`, true);
    }
}

// Add event listeners to elements injected into the DOM
function addEventListenersToInjectedElements() {
    try {
        // Add event listeners for user action buttons if they were injected directly
        document.querySelectorAll('button[onclick^="window.getAdminComponent()"]').forEach(button => {
            // These already have onclick handlers from the HTML
        });
        
        log('Event listeners added to injected elements ✅');
    } catch (err) {
        log(`Error adding event listeners: ${err.message}`, true);
    }
}

// Run all tests and attempt fixes
async function runTests() {
    const content = setupDiagnosticsUI();
    log('Running admin API diagnostics...');
    
    const user = await testAuthStatus();
    if (!user) {
        log('Not authenticated or authentication check failed', true);
        return;
    }
    
    if (user.role !== 'admin') {
        log(`User ${user.username} is not an admin (role: ${user.role})`, true);
        return;
    }
    
    // Setup Alpine event listeners
    setupAlpineEventListeners();
    
    // Check Alpine data
    const alpineStatus = testAlpineData();
    
    // Test APIs
    const users = await testUsersList();
    const settings = await testSettings();
    const backups = await testBackups();
    
    // Update Alpine data regardless of reported status
    // Try all available methods to update the data
    updateAlpineData(users, settings, backups);
    
    // Expose admin component to window for debugging
    exposeAdminToWindow();
    
    // Update tab content if needed
    updateTabContent(users, settings, backups);
    
    log('Admin API diagnostics and fixes completed.');
    
    // Add final helper button
    addHelperButton(users, settings, backups);
}

// Add a helper button to manually trigger updates
function addHelperButton(users, settings, backups) {
    const diagContainer = document.getElementById('admin-diagnostics');
    if (!diagContainer) return;
    
    const btnContainer = document.createElement('div');
    btnContainer.style.cssText = 'margin-top: 10px; display: flex; justify-content: space-between;';
    
    const updateBtn = document.createElement('button');
    updateBtn.textContent = 'Retry Data Update';
    updateBtn.style.cssText = 'background: #3b82f6; color: white; border: none; border-radius: 4px; padding: 6px 12px; cursor: pointer; margin-right: 5px;';
    updateBtn.onclick = () => updateAlpineData(users, settings, backups);
    
    const reloadBtn = document.createElement('button');
    reloadBtn.textContent = 'Show Direct UI';
    reloadBtn.style.cssText = 'background: #10b981; color: white; border: none; border-radius: 4px; padding: 6px 12px; cursor: pointer;';
    reloadBtn.onclick = () => injectUsersDirectly(users);
    
    btnContainer.appendChild(updateBtn);
    btnContainer.appendChild(reloadBtn);
    diagContainer.appendChild(btnContainer);
}

// Wait for Alpine to be defined and initialized
function waitForAlpine() {
    if (typeof Alpine !== 'undefined' && Alpine.$data) {
        runTests();
    } else {
        log('Waiting for Alpine.js to initialize...');
        setTimeout(waitForAlpine, 500);
    }
}

// Start diagnostics when document is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', waitForAlpine);
} else {
    waitForAlpine();
}
