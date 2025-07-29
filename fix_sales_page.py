#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix script for sales page statistics and adding period filter
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the app directory to the path
app_dir = os.path.abspath(os.path.dirname(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

def fix_sales_stats():
    """Fix the stats initialization and loading in sales.html template"""
    try:
        sales_html_path = os.path.join(app_dir, 'app', 'templates', 'sales.html')
        backup_path = os.path.join(app_dir, 'app', 'templates', 'sales.html.bak2')
        
        # Read original file
        with open(sales_html_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
            
        # Create backup
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        logger.info(f"Created backup of sales.html at {backup_path}")
        
        # Fix 1: Update the statistics loading function in the Alpine.js app
        updated_content = original_content.replace(
            """                loadStats() {
                    // Fetch stats from the server
                    fetch('/api/sales/stats')
                        .then(response => response.json())
                        .then(data => {
                            console.log('Stats API response:', data);
                            if (data.success) {
                                this.stats = data.stats || this.stats;
                            }
                        })
                        .catch(error => console.error('Error loading stats:', error));
                },""",
            
            """                loadStats() {
                    // Fetch stats from the server
                    fetch('/api/sales/stats')
                        .then(response => response.json())
                        .then(data => {
                            console.log('Stats API response:', data);
                            if (data.success) {
                                this.stats = data.stats || this.stats;
                                
                                // Make sure we update client count from customers array if available
                                if (this.customers && this.customers.length > 0) {
                                    this.stats.active_customers = this.customers.length;
                                }
                                
                                // Count today's sales from sales array if needed
                                if (this.stats.today_sales === 0 && this.sales && this.sales.length > 0) {
                                    const today = new Date().toISOString().split('T')[0];
                                    const todaySales = this.sales.filter(sale => 
                                        sale.sale_date && sale.sale_date.startsWith(today)
                                    ).length;
                                    if (todaySales > 0) {
                                        this.stats.today_sales = todaySales;
                                    }
                                }
                            }
                        })
                        .catch(error => console.error('Error loading stats:', error));
                },"""
        )
        
        # Fix 2: Initialize the sales data with all records, not just today
        updated_content = updated_content.replace(
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
                    }""",
            
            """                loadData() {
                    // Fetch data from the server
                    const url = new URL('/api/sales', window.location.origin);
                    
                    // Always set a high limit to get all records initially
                    url.searchParams.append('limit', '100');
                    
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
                    }"""
        )
        
        # Fix 3: Add period filter next to status filter in the UI
        updated_content = updated_content.replace(
            """                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-bold">Transactions Récentes</h2>
                    <div class="flex space-x-4">
                        <input type="text" x-model="searchTerm" placeholder="Rechercher..." class="border border-gray-300 rounded-md px-3 py-2 text-sm" />
                        <select x-model="filterStatus" class="border border-gray-300 rounded-md px-3 py-2 text-sm">
                            <option value="">Tous les statuts</option>
                            <option value="completed">Complété</option>
                            <option value="pending">En attente</option>
                            <option value="cancelled">Annulé</option>
                        </select>
                    </div>
                </div>""",
            
            """                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-bold">Transactions Récentes</h2>
                    <div class="flex space-x-4">
                        <input type="text" x-model="searchTerm" placeholder="Rechercher..." class="border border-gray-300 rounded-md px-3 py-2 text-sm" />
                        <select x-model="filterStatus" class="border border-gray-300 rounded-md px-3 py-2 text-sm">
                            <option value="">Tous les statuts</option>
                            <option value="completed">Complété</option>
                            <option value="pending">En attente</option>
                            <option value="cancelled">Annulé</option>
                        </select>
                        <select x-model="filterDate" @change="loadData()" class="border border-gray-300 rounded-md px-3 py-2 text-sm">
                            <option value="all">Toutes les périodes</option>
                            <option value="today">Aujourd'hui</option>
                            <option value="week">7 derniers jours</option>
                            <option value="month">30 derniers jours</option>
                        </select>
                    </div>
                </div>"""
        )
        
        # Fix 4: Make sure the Alpine.js data initializes with filterDate as 'all' by default
        updated_content = updated_content.replace(
            """        <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8" x-data="salesManager()">""",
            """        <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8" x-data="salesManager()" x-init="$nextTick(() => { filterDate = 'all'; loadData(); })">"""
        )
        
        # Fix 5: Update the initialization of stats and data in the salesManager function
        updated_content = updated_content.replace(
            """            function salesManager() {
                return {
                    stats: {
                        today_sales: 0,
                        today_amount: 0,
                        pending_amount: 0,
                        active_customers: 0,
                    },
                    sales: [],
                    customers: [],
                    products: [],""",
            
            """            function salesManager() {
                return {
                    stats: {
                        today_sales: 0,
                        today_amount: 0,
                        pending_amount: 0,
                        active_customers: 0,
                        monthly_revenue: 0
                    },
                    sales: [],
                    customers: [],
                    products: [],
                    filterDate: 'all',"""
        )
        
        # Write the updated content back to the file
        with open(sales_html_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        logger.info("Updated sales.html template with fixes for statistics and period filter")
        
    except Exception as e:
        logger.error(f"Error fixing sales template: {e}")

def fix_sales_api():
    """Fix the sales API to return all sales by default"""
    try:
        sales_api_path = os.path.join(app_dir, 'app', 'api', 'sales.py')
        backup_path = os.path.join(app_dir, 'app', 'api', 'sales.py.bak')
        
        # Read original file
        with open(sales_api_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
            
        # Create backup
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        logger.info(f"Created backup of sales.py at {backup_path}")
        
        # Fix: Update the get_sales function to return all sales by default (no date filter)
        updated_content = original_content.replace(
            """        # Base query
        query = '''
            SELECT s.*, u.username as created_by_name,
                   (SELECT COUNT(*) FROM sale_items si WHERE si.sale_id = s.id) as items_count,
                   (SELECT SUM(si.profit_margin) FROM sale_items si WHERE si.sale_id = s.id) as total_profit
            FROM sales s
            LEFT JOIN users u ON s.created_by = u.id
            WHERE 1=1
        '''
        params = []
        
        # Add filters
        if start_date:
            query += ' AND DATE(s.sale_date) >= ?'
            params.append(start_date)
        elif not end_date:
            # Default: show only sales from today if no date filter specified
            today_date = datetime.now().strftime('%Y-%m-%d')
            query += ' AND DATE(s.sale_date) = ?'
            params.append(today_date)""",
            
            """        # Base query
        query = '''
            SELECT s.*, u.username as created_by_name,
                   (SELECT COUNT(*) FROM sale_items si WHERE si.sale_id = s.id) as items_count,
                   (SELECT SUM(si.profit_margin) FROM sale_items si WHERE si.sale_id = s.id) as total_profit
            FROM sales s
            LEFT JOIN users u ON s.created_by = u.id
            WHERE 1=1
        '''
        params = []
        
        # Add filters
        if start_date:
            query += ' AND DATE(s.sale_date) >= ?'
            params.append(start_date)"""
        )
        
        # Write the updated content back to the file
        with open(sales_api_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        logger.info("Updated sales.py API to return all sales by default")
        
    except Exception as e:
        logger.error(f"Error fixing sales API: {e}")

def main():
    """Main function"""
    logger.info("Starting fixes for sales page statistics and period filter")
    
    # Fix the sales.html template for statistics and add period filter
    fix_sales_stats()
    
    # Fix the sales API to return all sales by default
    fix_sales_api()
    
    logger.info("Fixes completed. Please restart the application for changes to take effect.")

if __name__ == "__main__":
    main()
