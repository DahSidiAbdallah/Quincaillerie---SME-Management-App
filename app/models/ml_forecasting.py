#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Machine Learning Forecasting Models
Handles stock predictions, sales forecasting, and AI recommendations
"""

import sqlite3
import pandas as pd
import numpy as np
import os
from datetime import datetime, date, timedelta
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class StockPredictor:
    """Predicts stock levels and generates stock alerts"""

    def __init__(self, db_path=None):
        env_path = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_PATH')
        if env_path and env_path.startswith('sqlite:///'):
            env_path = env_path.replace('sqlite:///', '', 1)
        default_path = os.path.join(os.path.dirname(__file__), '../db/quincaillerie.db')
        self.db_path = os.path.abspath(env_path or db_path or default_path)
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def predict_stock_alerts(self) -> List[Dict[str, Any]]:
        """Predict which products will run out of stock soon"""
        try:
            conn = self.get_connection()
            
            # Get products with their sales history
            query = '''
                SELECT p.id, p.name, p.current_stock, p.min_stock_alert,
                       COUNT(DISTINCT DATE(s.sale_date)) as sales_days,
                       SUM(si.quantity) as total_sold,
                       AVG(si.quantity) as avg_quantity_per_sale,
                       MAX(DATE(s.sale_date)) as last_sale_date
                FROM products p
                LEFT JOIN sale_items si ON p.id = si.product_id
                LEFT JOIN sales s ON si.sale_id = s.id
                WHERE p.is_active = 1 
                AND (s.sale_date IS NULL OR DATE(s.sale_date) >= DATE('now', '-60 days'))
                GROUP BY p.id
                HAVING p.current_stock > 0
            '''
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            predictions = []
            
            for _, row in df.iterrows():
                prediction = self._analyze_product_stock(row)
                if prediction:
                    predictions.append(prediction)
            
            # Sort by urgency (days until stockout)
            predictions.sort(key=lambda x: x.get('days_until_stockout', float('inf')))
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting stock alerts: {e}")
            return []
    
    def _analyze_product_stock(self, product_data) -> Optional[Dict[str, Any]]:
        """Analyze individual product stock situation"""
        try:
            current_stock = product_data['current_stock']
            total_sold = product_data['total_sold'] or 0
            sales_days = product_data['sales_days'] or 0
            last_sale_date = product_data['last_sale_date']
            
            # Calculate daily average consumption
            if sales_days > 0 and total_sold > 0:
                daily_consumption = total_sold / sales_days
            else:
                # No sales history, use default low consumption
                daily_consumption = 0.1
            
            # Adjust for recent activity
            if last_sale_date:
                last_sale = datetime.strptime(last_sale_date, '%Y-%m-%d').date()
                days_since_last_sale = (date.today() - last_sale).days
                
                # Reduce consumption rate if no recent sales
                if days_since_last_sale > 14:
                    daily_consumption *= 0.5
                elif days_since_last_sale > 7:
                    daily_consumption *= 0.7
            
            # Predict days until stockout
            days_until_stockout = current_stock / daily_consumption if daily_consumption > 0 else float('inf')
            
            # Determine alert level
            alert_level = 'info'
            if days_until_stockout <= 3:
                alert_level = 'critical'
            elif days_until_stockout <= 7:
                alert_level = 'warning'
            elif days_until_stockout <= 14:
                alert_level = 'info'
            else:
                return None  # No alert needed
            
            # Calculate confidence based on data quality
            confidence = min(0.9, 0.3 + (sales_days / 30) * 0.6)  # More sales days = higher confidence
            
            return {
                'product_id': product_data['id'],
                'product_name': product_data['name'],
                'current_stock': current_stock,
                'daily_consumption': round(daily_consumption, 2),
                'days_until_stockout': round(days_until_stockout, 1),
                'alert_level': alert_level,
                'confidence': confidence,
                'recommendation': self._generate_stock_recommendation(days_until_stockout, current_stock, daily_consumption)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing product stock: {e}")
            return None
    
    def _generate_stock_recommendation(self, days_until_stockout, current_stock, daily_consumption) -> str:
        """Generate stock recommendation message"""
        if days_until_stockout <= 3:
            return f"Réapprovisionnement urgent requis (rupture dans {days_until_stockout:.1f} jours)"
        elif days_until_stockout <= 7:
            return f"Planifiez le réapprovisionnement (rupture dans {days_until_stockout:.1f} jours)"
        else:
            return f"Surveillez le stock (rupture dans {days_until_stockout:.1f} jours)"
    
    def generate_restock_suggestions(self) -> List[Dict[str, Any]]:
        """Generate intelligent restocking suggestions"""
        try:
            conn = self.get_connection()
            
            # Get comprehensive product data
            query = '''
                SELECT p.id, p.name, p.current_stock, p.min_stock_alert,
                       p.purchase_price, p.sale_price,
                       COUNT(DISTINCT DATE(s.sale_date)) as sales_days,
                       SUM(si.quantity) as total_sold,
                       SUM(si.profit_margin) as total_profit,
                       MAX(DATE(s.sale_date)) as last_sale_date,
                       AVG(si.quantity) as avg_quantity_per_sale
                FROM products p
                LEFT JOIN sale_items si ON p.id = si.product_id
                LEFT JOIN sales s ON si.sale_id = s.id
                WHERE p.is_active = 1 
                AND (s.sale_date IS NULL OR DATE(s.sale_date) >= DATE('now', '-90 days'))
                GROUP BY p.id
            '''
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            suggestions = []
            
            for _, row in df.iterrows():
                suggestion = self._generate_restock_suggestion(row)
                if suggestion:
                    suggestions.append(suggestion)
            
            # Sort by priority score
            suggestions.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
            
            return suggestions[:20]  # Top 20 suggestions
            
        except Exception as e:
            logger.error(f"Error generating restock suggestions: {e}")
            return []
    
    def _generate_restock_suggestion(self, product_data) -> Optional[Dict[str, Any]]:
        """Generate restock suggestion for individual product"""
        try:
            # Sanitize numeric fields (sqlite NULL -> pandas NaN)
            def _num(val, default=0):
                try:
                    if val is None:
                        return default
                    # pandas/np NaN handling
                    if isinstance(val, float) and np.isnan(val):
                        return default
                    if isinstance(val, (np.floating,)) and np.isnan(float(val)):
                        return default
                    return val
                except Exception:
                    return default

            current_stock = int(_num(product_data.get('current_stock'), 0))
            total_sold = _num(product_data.get('total_sold'), 0)
            sales_days = int(_num(product_data.get('sales_days'), 0))
            total_profit = _num(product_data.get('total_profit'), 0)
            min_stock_alert = int(_num(product_data.get('min_stock_alert'), 5))
            purchase_price = float(_num(product_data.get('purchase_price'), 0))
            
            # Skip if no sales history
            if total_sold == 0:
                return None
            
            # Calculate velocity metrics
            daily_sales = total_sold / max(sales_days, 1)
            profit_per_unit = (float(total_profit) / float(total_sold)) if total_sold > 0 else 0
            
            # Calculate suggested restock quantity
            # Base on 30 days of sales + safety stock
            base_qty = (daily_sales * 30) + min_stock_alert
            if isinstance(base_qty, float) and np.isnan(base_qty):
                base_qty = float(min_stock_alert)
            suggested_quantity = int(max(0, round(base_qty)))
            
            # Adjust based on profitability
            if profit_per_unit > 100:  # High profit items
                suggested_quantity = int(max(0, round(suggested_quantity * 1.2)))
            elif profit_per_unit < 20:  # Low profit items
                suggested_quantity = int(max(0, round(suggested_quantity * 0.8)))
            
            # Ensure minimum order
            suggested_quantity = max(suggested_quantity, int(min_stock_alert) * 2)
            
            # Calculate investment required
            investment_required = float(suggested_quantity) * purchase_price
            
            # Calculate priority score
            velocity_score = min(max(0.0, float(daily_sales) * 10.0), 50.0)  # Max 50 points
            profit_score = min(max(0.0, float(profit_per_unit) / 10.0), 30.0)  # Max 30 points
            stock_urgency = max(0, 20 - current_stock)  # Max 20 points
            
            priority_score = float(velocity_score) + float(profit_score) + float(stock_urgency)
            
            # Determine priority level
            if priority_score >= 70:
                priority = 'high'
            elif priority_score >= 40:
                priority = 'medium'
            else:
                priority = 'low'
            
            return {
                'product_id': product_data['id'],
                'product_name': product_data['name'],
                'current_stock': current_stock,
                'suggested_quantity': suggested_quantity,
                'investment_required': round(float(investment_required), 0),
                'daily_sales_rate': round(float(daily_sales), 2),
                'profit_per_unit': round(float(profit_per_unit), 0),
                'priority': priority,
                'priority_score': round(priority_score, 1),
                'confidence': min(0.9, (sales_days / 30) if sales_days else 0.0),  # Higher confidence with more data
                'reasoning': self._generate_restock_reasoning(priority, daily_sales, profit_per_unit, current_stock)
            }
            
        except Exception as e:
            logger.error(f"Error generating restock suggestion: {e}")
            return None
    
    def _generate_restock_reasoning(self, priority, daily_sales, profit_per_unit, current_stock) -> str:
        """Generate human-readable reasoning for restock suggestion"""
        reasons = []
        
        if daily_sales > 1:
            reasons.append(f"Ventes élevées ({daily_sales:.1f}/jour)")
        
        if profit_per_unit > 50:
            reasons.append(f"Rentabilité élevée ({profit_per_unit:.0f} MRU/unité)")
        
        if current_stock < 5:
            reasons.append(f"Stock très bas ({current_stock} unités)")
        
        if priority == 'high':
            reasons.append("Priorité élevée")
        
        return ", ".join(reasons) if reasons else "Réapprovisionnement recommandé"

class SalesForecaster:
    """Forecasts sales trends and patterns"""

    def __init__(self, db_path=None):
        env_path = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_PATH')
        if env_path and env_path.startswith('sqlite:///'):
            env_path = env_path.replace('sqlite:///', '', 1)
        default_path = os.path.join(os.path.dirname(__file__), '../db/quincaillerie.db')
        self.db_path = os.path.abspath(env_path or db_path or default_path)
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def predict_overall_sales(self, days_ahead: int = 7) -> Dict[str, Any]:
        """Predict overall sales for next N days"""
        try:
            conn = self.get_connection()
            
            # Get historical sales data
            query = '''
                SELECT DATE(sale_date) as date,
                       COUNT(*) as transaction_count,
                       SUM(total_amount) as daily_revenue,
                       AVG(total_amount) as avg_transaction
                FROM sales
                WHERE DATE(sale_date) >= DATE('now', '-60 days')
                GROUP BY DATE(sale_date)
                ORDER BY date
            '''
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if df.empty:
                return {
                    'forecast': [],
                    'confidence': 0.0,
                    'trend': 'insufficient_data',
                    'total_predicted_revenue': 0
                }
            
            # Convert date column to datetime
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            
            # Calculate moving averages
            df['revenue_ma7'] = df['daily_revenue'].rolling(window=7, min_periods=1).mean()
            df['transactions_ma7'] = df['transaction_count'].rolling(window=7, min_periods=1).mean()
            
            # Simple trend analysis
            recent_avg = df['daily_revenue'].tail(7).mean()
            older_avg = df['daily_revenue'].head(7).mean()
            
            if recent_avg > older_avg * 1.1:
                trend = 'increasing'
                trend_factor = 1.05
            elif recent_avg < older_avg * 0.9:
                trend = 'decreasing'
                trend_factor = 0.95
            else:
                trend = 'stable'
                trend_factor = 1.0
            
            # Generate forecast
            base_revenue = df['revenue_ma7'].iloc[-1] if not df['revenue_ma7'].empty else recent_avg
            base_transactions = df['transactions_ma7'].iloc[-1] if not df['transactions_ma7'].empty else df['transaction_count'].tail(7).mean()
            
            forecast = []
            total_predicted_revenue = 0
            
            for i in range(days_ahead):
                # Add some random variation
                daily_variation = np.random.normal(1.0, 0.1)
                
                predicted_revenue = base_revenue * trend_factor * daily_variation
                predicted_transactions = max(1, int(base_transactions * trend_factor * daily_variation))
                
                forecast_date = (datetime.now() + timedelta(days=i+1)).date()
                
                forecast.append({
                    'date': forecast_date.isoformat(),
                    'predicted_revenue': round(predicted_revenue, 0),
                    'predicted_transactions': predicted_transactions,
                    'confidence': max(0.4, min(0.8, len(df) / 30))  # More data = higher confidence
                })
                
                total_predicted_revenue += predicted_revenue
            
            return {
                'forecast': forecast,
                'trend': trend,
                'total_predicted_revenue': round(total_predicted_revenue, 0),
                'avg_daily_revenue': round(base_revenue, 0),
                'confidence': max(0.4, min(0.8, len(df) / 30)),
                'data_points': len(df)
            }
            
        except Exception as e:
            logger.error(f"Error predicting overall sales: {e}")
            return {
                'forecast': [],
                'confidence': 0.0,
                'trend': 'error',
                'total_predicted_revenue': 0
            }
    
    def predict_product_sales(self, product_id: int, days_ahead: int = 7) -> Dict[str, Any]:
        """Predict sales for a specific product"""
        try:
            conn = self.get_connection()
            
            # Get product sales history
            query = '''
                SELECT DATE(s.sale_date) as date,
                       SUM(si.quantity) as quantity_sold,
                       COUNT(DISTINCT s.id) as transactions
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                WHERE si.product_id = ? AND DATE(s.sale_date) >= DATE('now', '-60 days')
                GROUP BY DATE(s.sale_date)
                ORDER BY date
            '''
            
            df = pd.read_sql_query(query, conn, params=(product_id,))
            
            # Get product info
            conn.execute('SELECT name FROM products WHERE id = ?', (product_id,))
            product_result = conn.fetchone()
            product_name = product_result[0] if product_result else f'Product {product_id}'
            
            conn.close()
            
            if df.empty:
                return {
                    'product_id': product_id,
                    'product_name': product_name,
                    'forecast': [],
                    'confidence': 0.0,
                    'trend': 'no_data'
                }
            
            # Calculate average daily sales
            avg_daily_sales = df['quantity_sold'].mean()
            
            # Simple trend analysis
            recent_avg = df['quantity_sold'].tail(7).mean()
            older_avg = df['quantity_sold'].head(7).mean()
            
            if recent_avg > older_avg * 1.2:
                trend = 'increasing'
                trend_factor = 1.1
            elif recent_avg < older_avg * 0.8:
                trend = 'decreasing'
                trend_factor = 0.9
            else:
                trend = 'stable'
                trend_factor = 1.0
            
            # Generate forecast
            forecast = []
            for i in range(days_ahead):
                # Add randomness
                daily_variation = max(0.1, np.random.normal(1.0, 0.2))
                predicted_quantity = max(0, avg_daily_sales * trend_factor * daily_variation)
                
                forecast_date = (datetime.now() + timedelta(days=i+1)).date()
                
                forecast.append({
                    'date': forecast_date.isoformat(),
                    'predicted_quantity': round(predicted_quantity, 1),
                    'confidence': max(0.3, min(0.7, len(df) / 20))
                })
            
            return {
                'product_id': product_id,
                'product_name': product_name,
                'forecast': forecast,
                'trend': trend,
                'avg_daily_sales': round(avg_daily_sales, 1),
                'confidence': max(0.3, min(0.7, len(df) / 20)),
                'data_points': len(df)
            }
            
        except Exception as e:
            logger.error(f"Error predicting product sales: {e}")
            return {
                'product_id': product_id,
                'forecast': [],
                'confidence': 0.0,
                'trend': 'error'
            }
    
    def get_weekly_trends(self) -> Dict[str, Any]:
        """Get weekly sales trends and patterns"""
        try:
            conn = self.get_connection()
            
            # Get sales by day of week
            query = '''
                SELECT 
                    CASE strftime('%w', sale_date)
                        WHEN '0' THEN 'Dimanche'
                        WHEN '1' THEN 'Lundi'
                        WHEN '2' THEN 'Mardi'
                        WHEN '3' THEN 'Mercredi'
                        WHEN '4' THEN 'Jeudi'
                        WHEN '5' THEN 'Vendredi'
                        WHEN '6' THEN 'Samedi'
                    END as day_name,
                    strftime('%w', sale_date) as day_number,
                    COUNT(*) as transaction_count,
                    SUM(total_amount) as revenue,
                    AVG(total_amount) as avg_transaction
                FROM sales
                WHERE DATE(sale_date) >= DATE('now', '-30 days')
                GROUP BY strftime('%w', sale_date)
                ORDER BY day_number
            '''
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if df.empty:
                return {
                    'weekly_pattern': [],
                    'best_day': None,
                    'worst_day': None,
                    'confidence': 0.0
                }
            
            # Find best and worst days
            best_day = df.loc[df['revenue'].idxmax()]
            worst_day = df.loc[df['revenue'].idxmin()]
            
            weekly_pattern = []
            for _, row in df.iterrows():
                weekly_pattern.append({
                    'day': row['day_name'],
                    'avg_revenue': round(row['revenue'] / 4, 0),  # Assuming 4 weeks of data
                    'avg_transactions': round(row['transaction_count'] / 4, 1),
                    'avg_transaction_value': round(row['avg_transaction'], 0)
                })
            
            return {
                'weekly_pattern': weekly_pattern,
                'best_day': {
                    'day': best_day['day_name'],
                    'avg_revenue': round(best_day['revenue'] / 4, 0)
                },
                'worst_day': {
                    'day': worst_day['day_name'],
                    'avg_revenue': round(worst_day['revenue'] / 4, 0)
                },
                'confidence': 0.7 if len(df) >= 5 else 0.4
            }
            
        except Exception as e:
            logger.error(f"Error getting weekly trends: {e}")
            return {
                'weekly_pattern': [],
                'best_day': None,
                'worst_day': None,
                'confidence': 0.0
            }
    
    def get_stock_alerts(self) -> List[Dict[str, Any]]:
        """Get current stock alerts (wrapper for StockPredictor)"""
        stock_predictor = StockPredictor(self.db_path)
        return stock_predictor.predict_stock_alerts()
