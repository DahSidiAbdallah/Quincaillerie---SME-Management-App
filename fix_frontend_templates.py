#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix script for frontend JavaScript to display sales data
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the app directory to the path
app_dir = os.path.abspath(os.path.dirname(__file__))

def fix_sales_template():
    """Fix sales.html template to properly load and display sales data"""
    try:
        sales_html_path = os.path.join(app_dir, 'app', 'templates', 'sales.html')
        backup_path = os.path.join(app_dir, 'app', 'templates', 'sales.html.bak')
        
        # Read original file
        with open(sales_html_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Create backup
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        logger.info(f"Created backup of sales.html at {backup_path}")
        
        # Fix 1: Update customer loading to sort by ID and display all customers
        updated_content = original_content.replace(
            """                            if (data.success) {
                                this.customers = data.customers || [];
                                console.log(`Loaded ${this.customers.length} customers:`, this.customers);
                            }""",
            """                            if (data.success) {
                                this.customers = data.customers || [];
                                // Sort customers by ID to ensure consistent ordering
                                this.customers.sort((a, b) => a.id - b.id);
                                this.stats.active_customers = this.customers.length;
                                console.log(`Loaded ${this.customers.length} customers:`, this.customers);
                            }"""
        )
        
        # Fix 2: Update sales loading to fix date display and handle today's filter properly
        updated_content = updated_content.replace(
            """                loadData() {
                    // Fetch data from the server
                    const url = new URL('/api/sales', window.location.origin);
                    
                    // Add filter parameters
                    if (this.filterDate === 'today') {
                        const today = new Date().toISOString().split('T')[0];
                        url.searchParams.append('date', today);
                    } else if (this.filterDate === 'week') {
                        const weekAgo = new Date();
                        weekAgo.setDate(weekAgo.getDate() - 7);
                        url.searchParams.append('start_date', weekAgo.toISOString().split('T')[0]);
                        url.searchParams.append('end_date', new Date().toISOString().split('T')[0]);
                    } else if (this.filterDate === 'month') {
                        const monthAgo = new Date();
                        monthAgo.setMonth(monthAgo.getMonth() - 1);
                        url.searchParams.append('start_date', monthAgo.toISOString().split('T')[0]);
                        url.searchParams.append('end_date', new Date().toISOString().split('T')[0]);
                    }""",
            """                loadData() {
                    // Fetch data from the server
                    const url = new URL('/api/sales', window.location.origin);
                    
                    // Add filter parameters
                    if (this.filterDate === 'today') {
                        const today = new Date().toISOString().split('T')[0];
                        url.searchParams.append('start_date', today);
                        url.searchParams.append('end_date', today);
                    } else if (this.filterDate === 'week') {
                        const weekAgo = new Date();
                        weekAgo.setDate(weekAgo.getDate() - 7);
                        url.searchParams.append('start_date', weekAgo.toISOString().split('T')[0]);
                        url.searchParams.append('end_date', new Date().toISOString().split('T')[0]);
                    } else if (this.filterDate === 'month') {
                        const monthAgo = new Date();
                        monthAgo.setMonth(monthAgo.getMonth() - 1);
                        url.searchParams.append('start_date', monthAgo.toISOString().split('T')[0]);
                        url.searchParams.append('end_date', new Date().toISOString().split('T')[0]);
                    } else if (this.filterDate === 'all') {
                        // Show all sales by not setting any date filter
                    } else {
                        // Default to show all sales
                        url.searchParams.append('limit', '100');
                    }"""
        )
        
        # Write the updated content back to the file
        with open(sales_html_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        logger.info("Updated sales.html template to fix customer and sales display")
        
    except Exception as e:
        logger.error(f"Error fixing sales template: {e}")

def fix_customers_template():
    """Check if customers.html exists and make sure it works properly"""
    try:
        customers_html_path = os.path.join(app_dir, 'app', 'templates', 'customers.html')
        
        if not os.path.exists(customers_html_path):
            logger.info("customers.html does not exist, creating a link in dashboard to redirect to the sales page for customer management")
            
            # Get dashboard template
            dashboard_html_path = os.path.join(app_dir, 'app', 'templates', 'dashboard.html')
            
            if os.path.exists(dashboard_html_path):
                with open(dashboard_html_path, 'r', encoding='utf-8') as f:
                    dashboard_content = f.read()
                
                # Add a section about customers if it doesn't exist
                if "Clients Actifs" not in dashboard_content:
                    # Find a good spot to insert (after quick stats section)
                    import re
                    updated_content = re.sub(
                        r'(<!-- Quick Stats -->.*?</div>\s*</div>)',
                        r'\1\n\n        <!-- Customer Management Link -->\n        <div class="mb-6">\n            <div class="flex justify-between items-center mb-4">\n                <h2 class="text-xl font-bold">Gestion des Clients</h2>\n                <a href="/sales" class="text-blue-600 hover:text-blue-800">Voir tous les clients <i class="fas fa-arrow-right ml-1"></i></a>\n            </div>\n            <p class="text-gray-600">Les clients sont visibles dans la page des ventes, où vous pouvez les ajouter et les gérer.</p>\n        </div>',
                        dashboard_content,
                        flags=re.DOTALL
                    )
                    
                    with open(dashboard_html_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    logger.info("Added customers section to dashboard.html")
        
    except Exception as e:
        logger.error(f"Error checking customers template: {e}")

def main():
    """Main function"""
    logger.info("Starting fixes for frontend templates")
    
    # Fix sales.html template
    fix_sales_template()
    
    # Fix customers.html or add a redirect
    fix_customers_template()
    
    logger.info("Frontend template fixes completed")

if __name__ == "__main__":
    main()
