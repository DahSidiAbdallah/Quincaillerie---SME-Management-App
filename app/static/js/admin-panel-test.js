/**
 * Test utility for admin panel real-time updates
 * Run this file in the browser console to test and debug real-time updates
 */

// Define test utilities
const adminTests = {
    /**
     * Simulate toggling a user's active status
     * @param {number} userId - The ID of the user to toggle
     * @returns {Promise<Object>} The response from the toggle operation
     */
    async testToggleUser(userId) {
        console.log(`Testing toggle for user ${userId}`);
        const adminComponent = window.adminHelpers?.getAdminComponent();
        
        if (!adminComponent) {
            console.error('❌ Admin component not found');
            return null;
        }
        
        const user = adminComponent.users.find(u => u.id == userId);
        if (!user) {
            console.error(`❌ User with ID ${userId} not found`);
            return null;
        }
        
        console.log(`Found user: ${user.username}, status: ${user.is_active}`);
        
        try {
            // Call the enhanced toggle function
            const result = await adminComponent.toggleUserStatus(user);
            console.log('✅ Toggle user operation completed', result);
            return result;
        } catch (error) {
            console.error('❌ Toggle user operation failed', error);
            return null;
        }
    },
    
    /**
     * Simulate creating a backup
     * @returns {Promise<Object>} The response from the backup creation operation
     */
    async testCreateBackup() {
        console.log('Testing backup creation');
        const adminComponent = window.adminHelpers?.getAdminComponent();
        
        if (!adminComponent) {
            console.error('❌ Admin component not found');
            return null;
        }
        
        try {
            // Call the enhanced createBackup function
            const result = await adminComponent.createBackup();
            console.log('✅ Create backup operation completed', result);
            return result;
        } catch (error) {
            console.error('❌ Create backup operation failed', error);
            return null;
        }
    },
    
    /**
     * Test saving settings
     * @param {Object} settings - The settings to save
     * @returns {Promise<Object>} The response from the save operation
     */
    async testSaveSettings(settings = null) {
        console.log('Testing save settings');
        const adminComponent = window.adminHelpers?.getAdminComponent();
        
        if (!adminComponent) {
            console.error('❌ Admin component not found');
            return null;
        }
        
        // If no settings provided, use the current settings
        if (!settings) {
            settings = adminComponent.settings || {};
            
            // Add a test value to verify the save
            settings.testValue = new Date().toISOString();
            console.log('Using test settings', settings);
        }
        
        try {
            // Update settings in the component
            Object.assign(adminComponent.settings, settings);
            
            // Call the save function
            const result = await adminComponent.saveSettings();
            console.log('✅ Save settings operation completed', result);
            return result;
        } catch (error) {
            console.error('❌ Save settings operation failed', error);
            return null;
        }
    },
    
    /**
     * Simulate user actions by clicking UI elements
     * @param {string} action - The action to simulate ('toggle', 'edit', 'delete')
     * @param {number} index - The index of the user in the table (0-based)
     */
    simulateUserAction(action, index = 0) {
        const actions = {
            'toggle': () => document.querySelectorAll('button .fa-power-off')[index].closest('button').click(),
            'edit': () => document.querySelectorAll('button .fa-edit')[index].closest('button').click(),
            'delete': () => document.querySelectorAll('button .fa-trash-alt')[index].closest('button').click()
        };
        
        if (actions[action]) {
            console.log(`Simulating ${action} for user at index ${index}`);
            actions[action]();
        } else {
            console.error(`❌ Unknown action: ${action}`);
        }
    },
    
    /**
     * Run a comprehensive test of all real-time update features
     */
    async testAll() {
        console.log('Running comprehensive admin panel tests...');
        
        // Check if adminHelpers is available
        if (!window.adminHelpers) {
            console.error('❌ Admin helpers not available. Tests may fail.');
        }
        
        // Test Alpine.js data accessibility
        const adminComponent = window.adminHelpers?.getAdminComponent();
        if (adminComponent) {
            console.log('✅ Admin component found', {
                users: adminComponent.users?.length || 0,
                backups: adminComponent.backups?.length || 0,
                settings: !!adminComponent.settings
            });
            
            // Test user toggle
            if (adminComponent.users && adminComponent.users.length > 0) {
                await this.testToggleUser(adminComponent.users[0].id);
            }
            
            // Test backup creation
            await this.testCreateBackup();
            
            // Test settings save
            await this.testSaveSettings();
            
            console.log('✅ All tests completed');
        } else {
            console.error('❌ Admin component not found. Tests cannot run.');
        }
    }
};

// Expose test utilities globally
window.adminTests = adminTests;
console.log('✅ Admin tests utility loaded. Use window.adminTests to access test functions.');
console.log('Example: window.adminTests.testAll() to run all tests');
