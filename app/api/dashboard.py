#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard API for Quincaillerie & SME Management App
Provides endpoints for dashboard data
"""

from flask import Blueprint, jsonify, session, request
from datetime import datetime, timedelta
import logging
import re
import json
from db.database import DatabaseManager
import difflib

# Prefer rapidfuzz if available for better fuzzy matching, but allow fallback to difflib
try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except Exception:
    fuzz = None
    HAS_RAPIDFUZZ = False
    # provide a small token_set_ratio fallback using difflib
    def _token_set_ratio(a, b):
        try:
            if not a or not b:
                return 0.0
            # Normalize tokens
            atoks = sorted({t.lower() for t in re.split(r"\W+", str(a)) if t})
            btoks = sorted({t.lower() for t in re.split(r"\W+", str(b)) if t})
            if not atoks or not btoks:
                return 0.0
            a_join = ' '.join(atoks)
            b_join = ' '.join(btoks)
            return difflib.SequenceMatcher(None, a_join, b_join).ratio() * 100.0
        except Exception:
            return 0.0

    class _FuzzFallback:
        @staticmethod
        def token_set_ratio(a, b):
            return _token_set_ratio(a, b)

    fuzz = _FuzzFallback()

from db.database import DatabaseManager

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__)
db_manager = DatabaseManager()

@dashboard_bp.route('/stats')
def get_dashboard_stats():
    """Get all dashboard statistics in a single API call (numeric values)."""
    try:
        # Get basic stats
        total_products = db_manager.get_total_products()

        # Get low stock items
        low_stock_items = db_manager.get_low_stock_items()

        # Get today's sales
        today_sales = db_manager.get_today_sales()
        today_sales_count = today_sales.get('count', 0)
        today_sales_amount = today_sales.get('total', 0) or 0

        # Get pending debts
        pending_debts = db_manager.get_pending_debts()
        pending_debts_count = pending_debts.get('count', 0)
        pending_debts_amount = pending_debts.get('total', 0) or 0
        # Get overdue debts (explicitly overdue by due_date < today)
        try:
            overdue_debts = db_manager.get_overdue_debts()
            overdue_debts_count = int(overdue_debts.get('count', 0))
            overdue_debts_amount = float(overdue_debts.get('total', 0) or 0)
        except Exception:
            overdue_debts_count = 0
            overdue_debts_amount = 0.0

        # Get total revenue
        total_revenue = db_manager.get_total_revenue() or 0

        # Get cash balance
        cash_balance = db_manager.get_cash_balance() or 0

        # Calculate yesterday's sales for comparison
        yesterday_total = 0.0
        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute(
                '''
                SELECT SUM(total_amount) as total, COUNT(*) as count
                FROM sales
                WHERE DATE(sale_date) = DATE(?, '-1 day')
                AND is_deleted = 0
                ''',
                (today,),
            )
            row = cursor.fetchone()
            if row and row['total'] is not None:
                yesterday_total = float(row['total']) or 0.0
        except Exception as _e:
            yesterday_total = 0.0
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

        # Calculate sales change percentage
        sales_change = 0.0
        if yesterday_total and yesterday_total > 0:
            try:
                sales_change = ((float(today_sales_amount) - float(yesterday_total)) / float(yesterday_total)) * 100.0
            except Exception:
                sales_change = 0.0

        # Return numeric stats (frontend formats currency)
        return jsonify({
            'success': True,
            'stats': {
                'total_products': int(total_products or 0),
                'low_stock_count': len(low_stock_items) if isinstance(low_stock_items, list) else int(low_stock_items or 0),
                'low_stock_items': low_stock_items,
                'today_sales_count': int(today_sales_count or 0),
                'today_sales': float(today_sales_amount or 0),
                'total_revenue': float(total_revenue or 0),
                'pending_debts_count': int(pending_debts_count or 0),
                'pending_debts': float(pending_debts_amount or 0),
                'overdue_debts_count': overdue_debts_count,
                'overdue_debts': overdue_debts_amount,
                'cash_balance': float(cash_balance or 0),
                'sales_change': round(float(sales_change), 1)
            }
        })
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        return jsonify({'success': False, 'error': str(e)})

@dashboard_bp.route('/yesterday-sales')
def get_yesterday_sales():
    """Get yesterday's sales summary (total and count)."""
    conn = None
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            '''
            SELECT SUM(total_amount) as total, COUNT(*) as count
            FROM sales
            WHERE DATE(sale_date) = DATE(?, '-1 day')
            AND is_deleted = 0
            ''',
            (today,),
        )
        row = cursor.fetchone()
        result = {
            'total': float(row['total']) if row and row['total'] else 0.0,
            'count': int(row['count']) if row and row['count'] else 0,
        }
        return jsonify({'success': True, 'yesterday': result})
    except Exception as e:
        logger.error(f"Error fetching yesterday sales: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass

@dashboard_bp.route('/activities')
def get_dashboard_activities():
    """Get recent activities for dashboard"""
    try:
        limit = int(request.args.get('limit', 10))
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # If date range provided, query activity log with a date filter.
        # Some installations may have either `action_time` or `created_at` (or both).
        # Query pragmas first and build a safe SQL statement that doesn't reference missing columns.
        if start_date or end_date:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            try:
                # Inspect available columns to avoid referencing non-existent ones
                cursor.execute("PRAGMA table_info(user_activity_log)")
                cols = [c[1] for c in cursor.fetchall()]
                has_action_time = 'action_time' in cols
                has_created_at = 'created_at' in cols

                where_clauses = []
                params = []

                # Build date filters depending on which timestamp columns exist
                if start_date:
                    if has_action_time and has_created_at:
                        where_clauses.append('(DATE(a.action_time) >= ? OR DATE(a.created_at) >= ?)')
                        params.extend([start_date, start_date])
                    elif has_action_time:
                        where_clauses.append('DATE(a.action_time) >= ?')
                        params.append(start_date)
                    elif has_created_at:
                        where_clauses.append('DATE(a.created_at) >= ?')
                        params.append(start_date)
                    else:
                        # No timestamp columns - cannot apply date filter
                        pass

                if end_date:
                    if has_action_time and has_created_at:
                        where_clauses.append('(DATE(a.action_time) <= ? OR DATE(a.created_at) <= ?)')
                        params.extend([end_date, end_date])
                    elif has_action_time:
                        where_clauses.append('DATE(a.action_time) <= ?')
                        params.append(end_date)
                    elif has_created_at:
                        where_clauses.append('DATE(a.created_at) <= ?')
                        params.append(end_date)
                    else:
                        # No timestamp columns - cannot apply date filter
                        pass

                where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'

                # Choose a safe select expression and ordering depending on available columns
                if has_action_time and has_created_at:
                    select_time = 'COALESCE(a.action_time, a.created_at) as created_at'
                    order_by = 'COALESCE(a.action_time, a.created_at) DESC'
                elif has_action_time:
                    select_time = 'a.action_time as created_at'
                    order_by = 'a.action_time DESC'
                elif has_created_at:
                    select_time = 'a.created_at as created_at'
                    order_by = 'a.created_at DESC'
                else:
                    # No timestamp columns available; fall back to id ordering
                    select_time = 'a.id as created_at'
                    order_by = 'a.id DESC'

                query = (
                    f"SELECT a.id, a.action_type, a.description, {select_time}, u.username "
                    "FROM user_activity_log a JOIN users u ON a.user_id = u.id "
                    f"WHERE {where_sql} ORDER BY {order_by} LIMIT ?"
                )
                params.append(limit)
                cursor.execute(query, params)
                rows = cursor.fetchall()
                activities = [dict(r) for r in rows]
            finally:
                conn.close()
        else:
            activities = db_manager.get_recent_activities(limit=limit)
        
        # Format activities for frontend display
        formatted_activities = []
        for activity in activities:
            activity_type = determine_activity_type(activity.get('action_type', '') or '')
            time_ago = format_time_ago(activity.get('created_at', '') or activity.get('action_time', ''))

            # Include structured fields if present so the frontend can link to affected records
            formatted_activities.append({
                'type': activity_type,
                'title': activity.get('action_type', 'Action'),
                'description': activity.get('description', ''),
                'time_ago': time_ago,
                'user': activity.get('username', ''),
                'table_affected': activity.get('table_affected') or activity.get('table') or None,
                'record_id': activity.get('record_id') if activity.get('record_id') is not None else (activity.get('record') if activity.get('record') is not None else None),
                'meta': activity.get('meta') if activity.get('meta') is not None else None
            })
        
        return jsonify({'success': True, 'activities': formatted_activities})
    except Exception as e:
        logger.error(f"Error fetching activities: {e}")
        return jsonify({'success': False, 'error': str(e)})


@dashboard_bp.route('/activities/matches')
def activity_matches():
    """Suggest possible record matches for a given activity (sale matching heuristics)."""

    def parse_amount_customer(desc_text, meta_obj=None):
        """Return (amount: float|None, customer: str|None) parsed from description or meta."""
        amount = None
        customer = None

        # Try to parse amount and optional customer after 'à'
        m = re.search(r"(\d[\d\s\.,']{0,20}\d)\s*(?:([A-Za-z]{2,4}|MRU|MRO|USD|EUR)\b)?(?:\s*à\s*(.+))?", desc_text, re.IGNORECASE)
        if m:
            raw_amount = m.group(1)
            try:
                raw_amount = raw_amount.replace("'", '').replace(' ', '').replace(',', '.')
                amount = float(re.sub(r"[^0-9\.]", '', raw_amount))
            except Exception:
                amount = None
            if m.lastindex and m.lastindex >= 3 and m.group(3):
                customer = m.group(3).strip()

        # Fallback to meta fields
        if not amount and meta_obj and isinstance(meta_obj, dict):
            for k in ('amount', 'total', 'capture', 'original_amount'):
                if k in meta_obj:
                    try:
                        a = str(meta_obj[k]).replace(',', '.')
                        amount = float(re.sub(r"[^0-9\.]", '', a))
                        break
                    except Exception:
                        continue

        if not customer and meta_obj and isinstance(meta_obj, dict):
            for k in ('customer', 'customer_name', 'client'):
                if k in meta_obj:
                    customer = str(meta_obj[k]).strip()
                    break

        return amount, customer

    def find_candidate_rows(cursor, amount, customer, tol_pct=0.05):
        """Return list of DB rows potentially matching the parsed amount/customer."""
        rows = []
        try:
            if amount is not None:
                low = max(amount * (1.0 - tol_pct), 0.0)
                high = amount * (1.0 + tol_pct)
                cursor.execute('SELECT id, customer_name, total_amount, sale_date FROM sales WHERE total_amount BETWEEN ? AND ? ORDER BY sale_date DESC LIMIT 200', (low, high))
                rows = cursor.fetchall()
            elif customer:
                cursor.execute('SELECT id, customer_name, total_amount, sale_date FROM sales WHERE customer_name LIKE ? ORDER BY sale_date DESC LIMIT 200', (f'%{customer}%',))
                rows = cursor.fetchall()
            else:
                rows = []
        except Exception:
            rows = []

        # Broader token search if nothing found but we have a customer
        if not rows and customer:
            tokens = [t for t in re.split(r"\s+", customer) if len(t) > 2]
            if tokens:
                like_clause = ' OR '.join(['customer_name LIKE ?' for _ in tokens])
                params = [f'%{t}%' for t in tokens]
                try:
                    cursor.execute(f'SELECT id, customer_name, total_amount, sale_date FROM sales WHERE ({like_clause}) ORDER BY sale_date DESC LIMIT 200', params)
                    rows = cursor.fetchall()
                except Exception:
                    rows = []

        return rows

    def score_candidates(rows, amount, customer):
        """Return list of candidate dicts with a normalized score (0..100)."""
        candidates = []
        for r in rows:
            cid = r['id']
            cname = r['customer_name'] or ''
            camount = r['total_amount'] if r['total_amount'] is not None else 0.0

            score_amount = 0.0
            score_name = 0.0

            if amount is not None and camount is not None:
                # amount closeness: 1.0 exact, decays linearly; clamp to [0,1]
                score_amount = 1.0 - (abs(camount - amount) / max(abs(amount), 1.0))
                score_amount = max(0.0, min(1.0, score_amount))

            if customer:
                try:
                    # token_set_ratio yields 0..100; normalize to 0..1
                    score_name = fuzz.token_set_ratio(customer, cname) / 100.0
                except Exception:
                    score_name = 0.0

            # token overlap bonus up to 0.2
            token_bonus = 0.0
            try:
                c_tokens = {t.lower() for t in re.split(r"\W+", cname) if t}
                q_tokens = {t.lower() for t in re.split(r"\W+", customer) if t} if customer else set()
                if q_tokens and c_tokens:
                    overlap = len(q_tokens & c_tokens) / max(len(q_tokens), 1)
                    token_bonus = overlap * 0.2
            except Exception:
                token_bonus = 0.0

            if amount is not None:
                combined = (0.7 * score_amount) + (0.3 * score_name) + token_bonus
            else:
                combined = score_name + token_bonus

            # Cap combined to 1.0 and convert to 0..100 scale
            combined = max(0.0, min(1.0, combined))
            candidates.append({
                'id': cid,
                'customer_name': cname,
                'total_amount': camount,
                'sale_date': r['sale_date'],
                'score': round(combined * 100, 1)
            })

        # sort and return
        candidates.sort(key=lambda x: x.get('score', 0), reverse=True)
        return candidates

    try:
        aid = request.args.get('id')
        if not aid:
            return jsonify({'success': False, 'error': 'id is required'}), 400

        conn = db_manager.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, description, meta FROM user_activity_log WHERE id = ?', (aid,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'success': False, 'error': 'activity not found'}), 404

        desc = row['description'] if 'description' in row.keys() and row['description'] else ''
        meta = None
        try:
            meta = json.loads(row['meta']) if row.get('meta') else None
        except Exception:
            meta = None

        amount, customer = parse_amount_customer(desc, meta)

        tol_pct = 0.05
        if amount is not None and amount < 50:
            tol_pct = 0.20

        rows = find_candidate_rows(cursor, amount, customer, tol_pct=tol_pct)
        candidates = score_candidates(rows, amount, customer)[:20]

        conn.close()
        return jsonify({'success': True, 'candidates': candidates, 'parsed': {'amount': amount, 'customer': customer}})
    except Exception as e:
        logger.error(f"Error finding activity matches: {e}")
        return jsonify({'success': False, 'error': str(e)})


@dashboard_bp.route('/activities/bulk-match', methods=['POST'])
def activity_bulk_match():
    """Run matching heuristics across recent unstructured activities and return candidate suggestions.
    This endpoint does NOT alter the database; it's a read-only suggestion tool.
    """
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        # Fetch recent unstructured activities (limit to avoid long runs)
        cursor.execute("SELECT id, description, meta FROM user_activity_log ORDER BY id DESC LIMIT 500")
        rows = cursor.fetchall()
        results = []
        for row in rows:
            try:
                aid = row['id']
                desc = row['description'] or ''
                meta = None
                try:
                    meta = json.loads(row['meta']) if row.get('meta') else None
                except Exception:
                    meta = None

                amount, customer = None, None
                try:
                    amount, customer = globals()['parse_amount_customer'](desc, meta)
                except Exception:
                    # fallback to inline helper if not available
                    from flask import current_app
                    amount, customer = None, None

                tol = 0.05
                if amount is not None and amount < 50:
                    tol = 0.2

                candidate_rows = globals().get('find_candidate_rows')(cursor, amount, customer, tol_pct=tol)
                candidates = globals().get('score_candidates')(candidate_rows, amount, customer)[:10]

                results.append({'activity_id': aid, 'candidates': candidates})
            except Exception:
                continue

        conn.close()
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        logger.error(f"Error in bulk matching: {e}")
        try:
            conn.close()
        except Exception:
            pass
        return jsonify({'success': False, 'error': str(e)})


@dashboard_bp.route('/activities/confirm-match', methods=['POST'])
def activity_confirm_match():
    """Associate an activity with a specific table and record id (manual confirmation)."""
    try:
        data = request.get_json() or {}
        aid = data.get('activity_id')
        table = data.get('table_affected')
        rid = data.get('record_id')
        if not aid or not table or not rid:
            return jsonify({'success': False, 'error': 'activity_id, table_affected and record_id are required'}), 400

        conn = db_manager.get_connection()
        cursor = conn.cursor()
        # Update the activity row
        meta = json.dumps({'confirmed_by': session.get('user_id'), 'confirmed_at': datetime.now().isoformat()}, ensure_ascii=False)
        cursor.execute('UPDATE user_activity_log SET table_affected = ?, record_id = ?, meta = COALESCE(meta, ?) WHERE id = ?', (table, rid, meta, aid))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error confirming activity match: {e}")
        return jsonify({'success': False, 'error': str(e)})

@dashboard_bp.route('/top-products')
def get_top_products():
    """Get top selling products"""
    try:
        # Get top selling products 
        products = db_manager.get_top_selling_products(days=30, limit=5)
        # Fallback: if no recent sales, broaden the window to all-time to avoid empty UI
        if not products:
            products = db_manager.get_top_selling_products(days=3650, limit=5)
        # Ensure numeric monetary values are returned (frontend applies formatting)
        for product in products:
            try:
                if 'total_sales' in product and product['total_sales'] is not None:
                    product['total_sales'] = float(product['total_sales'])
                if 'quantity_sold' in product and product['quantity_sold'] is not None:
                    product['quantity_sold'] = int(product['quantity_sold'])
            except Exception:
                # If casting fails, leave as-is
                pass
        
        return jsonify({'success': True, 'products': products})
    except Exception as e:
        logger.error(f"Error fetching top products: {e}")
        return jsonify({'success': False, 'error': str(e)})

@dashboard_bp.route('/sales-chart')
def get_sales_chart_data():
    """Get data for sales chart"""
    try:
        # Get sales chart data
        chart_data = db_manager.get_sales_chart_data(days=7)
        
        return jsonify({
            'success': True, 
            'daily': chart_data['daily'],
            'weekly': chart_data['weekly']
        })
    except Exception as e:
        logger.error(f"Error fetching sales chart data: {e}")
        return jsonify({'success': False, 'error': str(e)})

def determine_activity_type(action_type):
    """Determine activity type based on action_type"""
    action_type = action_type.lower()
    
    if 'vente' in action_type or 'sale' in action_type:
        return 'sale'
    elif 'stock' in action_type or 'inventory' in action_type:
        return 'stock'
    elif 'login' in action_type or 'connexion' in action_type:
        return 'login'
    elif 'paiement' in action_type or 'payment' in action_type:
        return 'payment'
    else:
        return 'other'

def format_time_ago(timestamp_str):
    """Format timestamp as 'time ago'"""
    if not timestamp_str:
        return "Récemment"
    
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"Il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"Il y a {hours} heure{'s' if hours > 1 else ''}"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"Il y a {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return "À l'instant"
    except Exception:
        return "Récemment"
