#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Insights API Blueprint
Handles AI predictions, forecasting, and smart recommendations
"""

from flask import Blueprint, request, jsonify, session
from db.database import DatabaseManager
from models.ml_forecasting import StockPredictor, SalesForecaster
import logging
from datetime import datetime, date, timedelta
import json

logger = logging.getLogger(__name__)

ai_bp = Blueprint('ai', __name__)
db_manager = DatabaseManager()

# Initialize AI models
stock_predictor = StockPredictor()
sales_forecaster = SalesForecaster()

def require_auth():
    """Check if user is authenticated"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non authentifié'}), 401
    return None

@ai_bp.route('/stock-predictions', methods=['GET'])
def get_stock_predictions():
    """Get stock predictions and alerts"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        # Get products with potential stock issues
        predictions = stock_predictor.predict_stock_alerts()
        
        # Store predictions in cache
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Clear old predictions
        cursor.execute('''
            DELETE FROM ai_predictions 
            WHERE prediction_type = 'stock_out' AND created_at < datetime('now', '-1 day')
        ''')
        
        # Store new predictions
        for prediction in predictions:
            cursor.execute('''
                INSERT OR REPLACE INTO ai_predictions 
                (prediction_type, product_id, prediction_data, confidence_score, 
                 prediction_date, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                'stock_out',
                prediction['product_id'],
                json.dumps(prediction),
                prediction.get('confidence', 0.8),
                date.today().isoformat(),
                (datetime.now() + timedelta(hours=24)).isoformat()
            ))
        
        conn.commit()
        conn.close()
        
        # Log AI prediction request
        db_manager.log_user_action(
            session['user_id'],
            'ai_stock_prediction',
            f'Prédictions stock générées: {len(predictions)} produits'
        )
        
        return jsonify({
            'success': True,
            'predictions': predictions,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating stock predictions: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la génération des prédictions'}), 500

@ai_bp.route('/sales-forecast', methods=['GET'])
def get_sales_forecast():
    """Get sales forecasting data"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        # Get parameters
        product_id = request.args.get('product_id')
        days_ahead = int(request.args.get('days_ahead', 7))
        
        if product_id:
            # Forecast for specific product
            forecast = sales_forecaster.predict_product_sales(int(product_id), days_ahead)
        else:
            # Overall sales forecast
            forecast = sales_forecaster.predict_overall_sales(days_ahead)
        
        # Store forecast in cache
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO ai_predictions 
            (prediction_type, product_id, prediction_data, confidence_score, 
             prediction_date, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            'sales_forecast',
            product_id,
            json.dumps(forecast),
            forecast.get('confidence', 0.75),
            date.today().isoformat(),
            (datetime.now() + timedelta(hours=12)).isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        # Log AI forecast request
        db_manager.log_user_action(
            session['user_id'],
            'ai_sales_forecast',
            f'Prévisions ventes générées pour {days_ahead} jours'
        )
        
        return jsonify({
            'success': True,
            'forecast': forecast,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating sales forecast: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la génération des prévisions'}), 500

@ai_bp.route('/restock-suggestions', methods=['GET'])
def get_restock_suggestions():
    """Get AI-powered restocking suggestions"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        suggestions = stock_predictor.generate_restock_suggestions()
        
        # Store suggestions in cache
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Clear old suggestions
        cursor.execute('''
            DELETE FROM ai_predictions 
            WHERE prediction_type = 'restock_suggestion' AND created_at < datetime('now', '-1 day')
        ''')
        
        # Store new suggestions
        for suggestion in suggestions:
            cursor.execute('''
                INSERT OR REPLACE INTO ai_predictions 
                (prediction_type, product_id, prediction_data, confidence_score, 
                 prediction_date, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                'restock_suggestion',
                suggestion['product_id'],
                json.dumps(suggestion),
                suggestion.get('confidence', 0.7),
                date.today().isoformat(),
                (datetime.now() + timedelta(days=3)).isoformat()
            ))
        
        conn.commit()
        conn.close()
        
        # Log restock suggestions request
        db_manager.log_user_action(
            session['user_id'],
            'ai_restock_suggestions',
            f'Suggestions réapprovisionnement: {len(suggestions)} produits'
        )
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating restock suggestions: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la génération des suggestions'}), 500

@ai_bp.route('/capital-efficiency', methods=['GET'])
def get_capital_efficiency():
    """Calculate capital efficiency score"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get financial data for efficiency calculation
        cursor.execute('''
            SELECT 
                (SELECT COALESCE(SUM(amount), 0) FROM capital_entries) as total_capital,
                (SELECT COALESCE(SUM(purchase_price * current_stock), 0) FROM products WHERE is_active = 1) as stock_value,
                (SELECT COALESCE(SUM(profit_margin), 0) FROM sale_items) as total_profit,
                (SELECT COALESCE(SUM(total_amount), 0) FROM sales) as total_revenue
        ''')
        
        financial_data = dict(cursor.fetchone())
        
        # Calculate various efficiency metrics
        total_capital = financial_data['total_capital']
        stock_value = financial_data['stock_value']
        total_profit = financial_data['total_profit']
        total_revenue = financial_data['total_revenue']
        
        efficiency_metrics = {
            'capital_turnover': (total_revenue / total_capital) if total_capital > 0 else 0,
            'profit_margin': (total_profit / total_revenue * 100) if total_revenue > 0 else 0,
            'roi': (total_profit / total_capital * 100) if total_capital > 0 else 0,
            'stock_turnover': (total_revenue / stock_value) if stock_value > 0 else 0,
            'capital_efficiency_score': 0  # Will be calculated below
        }
        
        # Calculate overall efficiency score (0-100)
        score_components = []
        
        # ROI component (0-40 points)
        roi_score = min(efficiency_metrics['roi'] / 50 * 40, 40)  # 50% ROI = full points
        score_components.append(roi_score)
        
        # Capital turnover component (0-30 points) 
        turnover_score = min(efficiency_metrics['capital_turnover'] / 3 * 30, 30)  # 3x turnover = full points
        score_components.append(turnover_score)
        
        # Profit margin component (0-20 points)
        margin_score = min(efficiency_metrics['profit_margin'] / 25 * 20, 20)  # 25% margin = full points
        score_components.append(margin_score)
        
        # Stock turnover component (0-10 points)
        stock_turnover_score = min(efficiency_metrics['stock_turnover'] / 5 * 10, 10)  # 5x stock turnover = full points
        score_components.append(stock_turnover_score)
        
        efficiency_metrics['capital_efficiency_score'] = sum(score_components)
        
        # Generate recommendations based on scores
        recommendations = []
        
        if efficiency_metrics['roi'] < 20:
            recommendations.append({
                'type': 'roi_improvement',
                'message': 'ROI faible. Considérez augmenter les marges ou réduire le capital immobilisé.',
                'priority': 'high'
            })
        
        if efficiency_metrics['stock_turnover'] < 2:
            recommendations.append({
                'type': 'stock_optimization',
                'message': 'Rotation stock lente. Réduisez le stock dormant et focalisez sur les produits rentables.',
                'priority': 'medium'
            })
        
        if efficiency_metrics['profit_margin'] < 15:
            recommendations.append({
                'type': 'margin_improvement',
                'message': 'Marge bénéficiaire faible. Révisez vos prix de vente.',
                'priority': 'medium'  
            })
        
        # Add detailed analysis
        analysis = {
            'financial_data': financial_data,
            'efficiency_metrics': efficiency_metrics,
            'recommendations': recommendations,
            'score_breakdown': {
                'roi_score': roi_score,
                'turnover_score': turnover_score,
                'margin_score': margin_score,
                'stock_turnover_score': stock_turnover_score
            }
        }
        
        conn.close()
        
        # Log efficiency analysis
        db_manager.log_user_action(
            session['user_id'],
            'ai_efficiency_analysis',
            f'Analyse efficacité capital: score {efficiency_metrics["capital_efficiency_score"]:.1f}/100'
        )
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error calculating capital efficiency: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors du calcul d\'efficacité'}), 500

@ai_bp.route('/price-suggestions', methods=['GET'])
def get_price_suggestions():
    """Get AI-powered pricing suggestions"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        product_id = request.args.get('product_id')
        target_margin = float(request.args.get('target_margin', 25))  # Default 25% margin
        
        if product_id:
            # Suggestions for specific product
            cursor.execute('''
                SELECT p.*, 
                       AVG(si.unit_price) as avg_selling_price,
                       SUM(si.quantity) as total_sold,
                       COUNT(DISTINCT s.id) as sales_count
                FROM products p
                LEFT JOIN sale_items si ON p.id = si.product_id
                LEFT JOIN sales s ON si.sale_id = s.id
                WHERE p.id = ? AND p.is_active = 1
                GROUP BY p.id
            ''', (product_id,))
            
            products = [dict(cursor.fetchone())]
        else:
            # Suggestions for all products
            cursor.execute('''
                SELECT p.*, 
                       AVG(si.unit_price) as avg_selling_price,
                       SUM(si.quantity) as total_sold,
                       COUNT(DISTINCT s.id) as sales_count
                FROM products p
                LEFT JOIN sale_items si ON p.id = si.product_id
                LEFT JOIN sales s ON si.sale_id = s.id
                WHERE p.is_active = 1
                GROUP BY p.id
                ORDER BY total_sold DESC
                LIMIT 50
            ''')
            
            products = [dict(row) for row in cursor.fetchall()]
        
        suggestions = []
        
        for product in products:
            if not product or product['purchase_price'] is None:
                continue
            
            current_price = product['sale_price']
            purchase_price = product['purchase_price']
            avg_selling_price = product['avg_selling_price'] or current_price
            total_sold = product['total_sold'] or 0
            
            # Calculate current margin
            current_margin = ((current_price - purchase_price) / current_price * 100) if current_price > 0 else 0
            
            # Calculate optimal price for target margin
            optimal_price = purchase_price / (1 - target_margin / 100)
            
            # Calculate market-based price (based on actual sales)
            market_price = avg_selling_price if avg_selling_price else current_price
            
            # Determine velocity category
            if total_sold >= 20:
                velocity = 'high'
            elif total_sold >= 5:
                velocity = 'medium'
            else:
                velocity = 'low'
            
            # Generate recommendation
            recommendation = 'maintain'  # default
            suggested_price = current_price
            
            if current_margin < target_margin * 0.8:  # Below 80% of target
                if velocity == 'high':
                    # High velocity: gradual increase
                    suggested_price = min(optimal_price, current_price * 1.1)
                    recommendation = 'increase_gradual'
                elif velocity == 'medium':
                    # Medium velocity: moderate increase
                    suggested_price = min(optimal_price, current_price * 1.15)
                    recommendation = 'increase_moderate'
                else:
                    # Low velocity: can increase more aggressively
                    suggested_price = optimal_price
                    recommendation = 'increase_aggressive'
            
            elif current_margin > target_margin * 1.2:  # Above 120% of target
                if velocity == 'low':
                    # Low velocity with high margin: consider price reduction
                    suggested_price = max(optimal_price, current_price * 0.9)
                    recommendation = 'decrease_to_boost_sales'
            
            suggestion = {
                'product_id': product['id'],
                'product_name': product['name'],
                'current_price': current_price,
                'purchase_price': purchase_price,
                'suggested_price': round(suggested_price, 0),  # Rounded to nearest unit
                'current_margin': round(current_margin, 1),
                'suggested_margin': round(((suggested_price - purchase_price) / suggested_price * 100), 1),
                'velocity': velocity,
                'total_sold': total_sold,
                'recommendation': recommendation,
                'price_change_percentage': round(((suggested_price - current_price) / current_price * 100), 1),
                'confidence': 0.8 if total_sold >= 10 else 0.6
            }
            
            suggestions.append(suggestion)
        
        conn.close()
        
        # Sort by potential impact (price change * sales volume)
        suggestions.sort(key=lambda x: abs(x['price_change_percentage']) * x['total_sold'], reverse=True)
        
        # Log pricing analysis
        db_manager.log_user_action(
            session['user_id'],
            'ai_price_suggestions',
            f'Suggestions prix générées: {len(suggestions)} produits'
        )
        
        return jsonify({
            'success': True,
            'suggestions': suggestions[:20],  # Top 20 suggestions
            'target_margin': target_margin,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating price suggestions: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la génération des suggestions de prix'}), 500

@ai_bp.route('/smart-alerts', methods=['GET'])
def get_smart_alerts():
    """Get AI-generated smart alerts and notifications"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        alerts = []
        
        # Low stock alerts with AI severity
        cursor.execute('''
            SELECT p.name, p.current_stock, p.min_stock_alert,
                   AVG(si.quantity) as avg_daily_sales
            FROM products p
            LEFT JOIN sale_items si ON p.id = si.product_id
            LEFT JOIN sales s ON si.sale_id = s.id AND DATE(s.sale_date) >= DATE('now', '-30 days')
            WHERE p.is_active = 1 AND p.current_stock <= p.min_stock_alert
            GROUP BY p.id
        ''')
        
        for row in cursor.fetchall():
            row = dict(row)
            avg_sales = row['avg_daily_sales'] or 0
            days_until_stockout = (row['current_stock'] / avg_sales) if avg_sales > 0 else float('inf')
            
            severity = 'critical' if days_until_stockout <= 3 else 'warning' if days_until_stockout <= 7 else 'info'
            
            alerts.append({
                'type': 'low_stock',
                'severity': severity,
                'title': f'Stock faible: {row["name"]}',
                'message': f'Stock actuel: {row["current_stock"]}. Rupture estimée dans {days_until_stockout:.1f} jours.',
                'product_name': row['name'],
                'priority': 3 if severity == 'critical' else 2 if severity == 'warning' else 1
            })
        
        # Overdue debts alerts
        cursor.execute('''
            SELECT client_name, remaining_amount, due_date,
                   (julianday('now') - julianday(due_date)) as days_overdue
            FROM client_debts 
            WHERE status = 'pending' AND due_date < DATE('now')
            ORDER BY days_overdue DESC
        ''')
        
        for row in cursor.fetchall():
            row = dict(row)
            days_overdue = int(row['days_overdue'])
            severity = 'critical' if days_overdue > 30 else 'warning' if days_overdue > 7 else 'info'
            
            alerts.append({
                'type': 'overdue_debt',
                'severity': severity,
                'title': f'Dette en retard: {row["client_name"]}',
                # Use current currency from settings
                'message': (lambda cur: f"Montant: {row['remaining_amount']} {cur}. En retard de {days_overdue} jours.")((db_manager.get_app_settings().get('currency') or 'MRU')),
                'client_name': row['client_name'],
                'amount': row['remaining_amount'],
                'priority': 3 if severity == 'critical' else 2
            })
        
        # Unusual expense patterns
        cursor.execute('''
            SELECT DATE(expense_date) as date, SUM(amount) as daily_total
            FROM expenses
            WHERE DATE(expense_date) >= DATE('now', '-7 days')
            GROUP BY DATE(expense_date)
            HAVING daily_total > (
                SELECT AVG(daily_amount) * 2
                FROM (
                    SELECT SUM(amount) as daily_amount
                    FROM expenses
                    WHERE DATE(expense_date) >= DATE('now', '-30 days')
                    GROUP BY DATE(expense_date)
                )
            )
        ''')
        
        for row in cursor.fetchall():
            row = dict(row)
            alerts.append({
                'type': 'unusual_expense',
                'severity': 'warning',
                'title': f'Dépenses élevées détectées',
                'message': (lambda cur: f"Dépenses du {row['date']}: {row['daily_total']} {cur} (inhabituel)")((db_manager.get_app_settings().get('currency') or 'MRU')),
                'date': row['date'],
                'amount': row['daily_total'],
                'priority': 2
            })
        
        # Missing sales entries (no sales for 2+ days)
        cursor.execute('''
            SELECT MAX(DATE(sale_date)) as last_sale_date,
                   (julianday('now') - julianday(MAX(DATE(sale_date)))) as days_since_last_sale
            FROM sales
        ''')
        
        result = cursor.fetchone()
        if result and result[1] and result[1] >= 2:
            days_since = int(result[1])
            alerts.append({
                'type': 'missing_sales',
                'severity': 'warning' if days_since >= 3 else 'info',
                'title': 'Aucune vente récente',
                'message': f'Dernière vente il y a {days_since} jours. Vérifiez les saisies.',
                'days_since': days_since,
                'priority': 2 if days_since >= 3 else 1
            })
        
        # High performing products that are low in stock
        cursor.execute('''
            SELECT p.name, p.current_stock, SUM(si.quantity) as recent_sales
            FROM products p
            JOIN sale_items si ON p.id = si.product_id
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) >= DATE('now', '-7 days') AND p.current_stock <= 10
            GROUP BY p.id
            HAVING recent_sales >= 5
            ORDER BY recent_sales DESC
        ''')
        
        for row in cursor.fetchall():
            row = dict(row)
            alerts.append({
                'type': 'high_performer_low_stock',
                'severity': 'warning',
                'title': f'Produit performant en rupture: {row["name"]}',
                'message': f'{row["recent_sales"]} ventes cette semaine, stock: {row["current_stock"]}',
                'product_name': row['name'],
                'priority': 3
            })
        
        conn.close()
        
        # Sort alerts by priority and severity
        priority_order = {'critical': 3, 'warning': 2, 'info': 1}
        alerts.sort(key=lambda x: (x['priority'], priority_order.get(x['severity'], 0)), reverse=True)
        
        # Log smart alerts generation
        db_manager.log_user_action(
            session['user_id'],
            'ai_smart_alerts',
            f'Alertes intelligentes générées: {len(alerts)} alertes'
        )
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'alert_counts': {
                'critical': len([a for a in alerts if a['severity'] == 'critical']),
                'warning': len([a for a in alerts if a['severity'] == 'warning']),
                'info': len([a for a in alerts if a['severity'] == 'info'])
            },
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating smart alerts: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la génération des alertes'}), 500

@ai_bp.route('/summary-assistant', methods=['GET'])
def get_ai_summary():
    """Generate natural language business summary (Phase 6.1)"""
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        period = request.args.get('period', 'week')  # day, week, month
        
        if period == 'day':
            date_filter = "DATE('now')"
            period_text = "aujourd'hui"
        elif period == 'week':
            date_filter = "DATE('now', '-7 days')"
            period_text = "cette semaine"
        else:  # month
            date_filter = "DATE('now', '-30 days')"
            period_text = "ce mois"
        
        # Get key metrics
        cursor.execute(f'''
            SELECT 
                COUNT(*) as sales_count,
                SUM(total_amount) as revenue,
                SUM((SELECT SUM(profit_margin) FROM sale_items WHERE sale_id = s.id)) as profit
            FROM sales s
            WHERE DATE(sale_date) >= {date_filter}
        ''')
        
        metrics = dict(cursor.fetchone())
        
        # Get best selling product
        cursor.execute(f'''
            SELECT p.name, SUM(si.quantity) as quantity
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) >= {date_filter}
            GROUP BY p.id
            ORDER BY quantity DESC
            LIMIT 1
        ''')
        
        best_product = cursor.fetchone()
        best_product = dict(best_product) if best_product else None
        
        # Get low stock count
        cursor.execute('''
            SELECT COUNT(*) FROM products 
            WHERE is_active = 1 AND current_stock <= min_stock_alert
        ''')
        low_stock_count = cursor.fetchone()[0]
        
        # Get pending debts
        cursor.execute('''
            SELECT COUNT(*) as count, SUM(remaining_amount) as total
            FROM client_debts WHERE status = 'pending'
        ''')
        debts = dict(cursor.fetchone())
        
        conn.close()
        
        # Generate natural language summary
        summary_parts = []
        
        # Sales performance
        revenue = metrics['revenue'] or 0
        profit = metrics['profit'] or 0
        sales_count = metrics['sales_count'] or 0
        
        if revenue > 0:
            _cur = (db_manager.get_app_settings().get('currency') or 'MRU')
            summary_parts.append(f"Vous avez réalisé {revenue:,.0f} {_cur} de chiffre d'affaires {period_text}")
            if profit > 0:
                margin = (profit / revenue * 100)
                summary_parts.append(f"avec {profit:,.0f} {_cur} de bénéfice (marge de {margin:.1f}%)")
            summary_parts.append(f"sur {sales_count} vente{'s' if sales_count > 1 else ''}")
        else:
            summary_parts.append(f"Aucune vente enregistrée {period_text}")
        
        # Best product
        if best_product:
            summary_parts.append(f"Votre produit le plus vendu est '{best_product['name']}' avec {best_product['quantity']} unités")
        
        # Stock alerts
        if low_stock_count > 0:
            summary_parts.append(f"Attention: {low_stock_count} produit{'s' if low_stock_count > 1 else ''} en rupture de stock")
        
        # Debt situation
        if debts['count'] and debts['count'] > 0:
            _cur = (db_manager.get_app_settings().get('currency') or 'MRU')
            summary_parts.append(f"Vous avez {debts['count']} créance{'s' if debts['count'] > 1 else ''} en attente pour {debts['total']:,.0f} {_cur}")
        
        # Generate recommendations
        recommendations = []
        
        if revenue == 0:
            recommendations.append("Vérifiez vos saisies de vente ou relancez l'activité commerciale")
        elif profit and revenue and (profit / revenue < 0.15):
            recommendations.append("Votre marge est faible, considérez réviser vos prix")
        
        if low_stock_count > 5:
            recommendations.append("Planifiez un réapprovisionnement urgent")
        
        if debts['total'] and debts['total'] > revenue * 0.5:
            recommendations.append("Relancez vos clients pour récupérer les créances")
        
        # Combine into natural summary
        summary_text = ". ".join(summary_parts) + "."
        
        if recommendations:
            summary_text += " Recommandations: " + "; ".join(recommendations) + "."
        
        # Log AI summary generation
        db_manager.log_user_action(
            session['user_id'],
            'ai_summary_assistant',
            f'Résumé IA généré pour période: {period}'
        )
        
        return jsonify({
            'success': True,
            'summary': {
                'text': summary_text,
                'period': period_text,
                'metrics': metrics,
                'best_product': best_product,
                'recommendations': recommendations,
                'low_stock_count': low_stock_count,
                'pending_debts': debts
            },
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating AI summary: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors de la génération du résumé'}), 500
