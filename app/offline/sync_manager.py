#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Offline Synchronization Manager
Handles offline data storage and cloud synchronization when available
"""

import json
import sqlite3
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import hashlib

logger = logging.getLogger(__name__)

class SyncManager:
    """Manages offline-first data synchronization"""

    def __init__(self, db_path=None):
        env_path = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_PATH')
        if env_path and env_path.startswith('sqlite:///'):
            env_path = env_path.replace('sqlite:///', '', 1)
        default_path = os.path.join(os.path.dirname(__file__), '../db/quincaillerie.db')
        self.db_path = os.path.abspath(env_path or db_path or default_path)
        self.cloud_enabled = False  # Will be True when Firebase is configured
        
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Count pending sync operations
            cursor.execute('SELECT COUNT(*) FROM sync_queue WHERE sync_status = "pending"')
            pending_count = cursor.fetchone()[0]
            
            # Count failed sync operations
            cursor.execute('SELECT COUNT(*) FROM sync_queue WHERE sync_status = "failed"')
            failed_count = cursor.fetchone()[0]
            
            # Get last successful sync
            cursor.execute('''
                SELECT MAX(synced_at) FROM sync_queue 
                WHERE sync_status = "synced"
            ''')
            last_sync = cursor.fetchone()[0]
            
            # Check connectivity status (simplified - in real app would check internet)
            connectivity_status = 'online' if self.cloud_enabled else 'offline'
            
            conn.close()
            
            return {
                'connectivity': connectivity_status,
                'pending_operations': pending_count,
                'failed_operations': failed_count,
                'last_sync': last_sync,
                'cloud_enabled': self.cloud_enabled,
                'sync_health': 'good' if failed_count == 0 else 'issues' if failed_count < 10 else 'poor'
            }
            
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {
                'connectivity': 'error',
                'pending_operations': 0,
                'failed_operations': 0,
                'last_sync': None,
                'cloud_enabled': False,
                'sync_health': 'error'
            }
    
    def queue_sync_operation(self, table_name: str, record_id: int, operation: str, data: Optional[Dict] = None) -> bool:
        """Queue an operation for synchronization"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Generate unique sync ID
            sync_id = str(uuid.uuid4())
            
            # Create data hash for deduplication
            data_str = json.dumps(data, sort_keys=True) if data else ''
            data_hash = hashlib.md5(f"{table_name}:{record_id}:{operation}:{data_str}".encode()).hexdigest()
            
            # Check if similar operation already exists
            cursor.execute('''
                SELECT COUNT(*) FROM sync_queue 
                WHERE table_name = ? AND record_id = ? AND operation = ? 
                AND sync_status = "pending"
            ''', (table_name, record_id, operation))
            
            if cursor.fetchone()[0] > 0:
                logger.info(f"Similar sync operation already queued for {table_name}:{record_id}")
                conn.close()
                return True
            
            # Insert sync operation
            cursor.execute('''
                INSERT INTO sync_queue 
                (table_name, record_id, operation, data, sync_status)
                VALUES (?, ?, ?, ?, ?)
            ''', (table_name, record_id, operation, json.dumps(data) if data else None, 'pending'))
            
            conn.commit()
            conn.close()
            
            # Attempt immediate sync if online
            if self.cloud_enabled:
                self._attempt_sync()
            
            return True
            
        except Exception as e:
            logger.error(f"Error queuing sync operation: {e}")
            return False
    
    def push_changes(self, force_sync: bool = False) -> Dict[str, Any]:
        """Push local changes to cloud"""
        if not self.cloud_enabled and not force_sync:
            return {
                'success': False,
                'message': 'Cloud synchronization not enabled',
                'operations_pushed': 0
            }
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get pending operations
            cursor.execute('''
                SELECT * FROM sync_queue 
                WHERE sync_status = "pending"
                ORDER BY created_at ASC
                LIMIT 100
            ''')
            
            operations = [dict(row) for row in cursor.fetchall()]
            
            if not operations:
                conn.close()
                return {
                    'success': True,
                    'message': 'No pending operations to sync',
                    'operations_pushed': 0
                }
            
            successful_syncs = 0
            failed_syncs = 0
            
            for operation in operations:
                try:
                    # In real implementation, this would push to Firebase/cloud
                    success = self._simulate_cloud_push(operation)
                    
                    if success:
                        # Mark as synced
                        cursor.execute('''
                            UPDATE sync_queue 
                            SET sync_status = "synced", synced_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (operation['id'],))
                        successful_syncs += 1
                    else:
                        # Mark as failed
                        cursor.execute('''
                            UPDATE sync_queue 
                            SET sync_status = "failed"
                            WHERE id = ?
                        ''', (operation['id'],))
                        failed_syncs += 1
                        
                except Exception as e:
                    logger.error(f"Error syncing operation {operation['id']}: {e}")
                    failed_syncs += 1
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f'Sync completed: {successful_syncs} successful, {failed_syncs} failed',
                'operations_pushed': successful_syncs,
                'operations_failed': failed_syncs
            }
            
        except Exception as e:
            logger.error(f"Error pushing changes: {e}")
            return {
                'success': False,
                'message': f'Error during sync: {str(e)}',
                'operations_pushed': 0
            }
    
    def pull_changes(self) -> Dict[str, Any]:
        """Pull changes from cloud to local database"""
        if not self.cloud_enabled:
            return {
                'success': False,
                'message': 'Cloud synchronization not enabled',
                'operations_pulled': 0
            }
        
        try:
            # In real implementation, this would fetch from Firebase/cloud
            cloud_changes = self._simulate_cloud_pull()
            
            if not cloud_changes:
                return {
                    'success': True,
                    'message': 'No changes to pull from cloud',
                    'operations_pulled': 0
                }
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            operations_applied = 0
            
            for change in cloud_changes:
                try:
                    # Apply change to local database
                    success = self._apply_cloud_change(cursor, change)
                    if success:
                        operations_applied += 1
                except Exception as e:
                    logger.error(f"Error applying cloud change: {e}")
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f'Successfully pulled {operations_applied} changes from cloud',
                'operations_pulled': operations_applied
            }
            
        except Exception as e:
            logger.error(f"Error pulling changes: {e}")
            return {
                'success': False,
                'message': f'Error during pull: {str(e)}',
                'operations_pulled': 0
            }
    
    def _simulate_cloud_push(self, operation: Dict) -> bool:
        """Simulate pushing operation to cloud (replace with real Firebase implementation)"""
        # In real implementation, this would:
        # 1. Authenticate with Firebase
        # 2. Push the operation data to Firestore
        # 3. Handle conflicts and merging
        # 4. Return success/failure
        
        # For now, simulate 90% success rate
        import random
        return random.random() > 0.1
    
    def _simulate_cloud_pull(self) -> List[Dict]:
        """Simulate pulling changes from cloud (replace with real Firebase implementation)"""
        # In real implementation, this would:
        # 1. Authenticate with Firebase
        # 2. Query Firestore for changes since last sync
        # 3. Return list of changes to apply locally
        
        # For now, return empty list (no changes)
        return []
    
    def _apply_cloud_change(self, cursor, change: Dict) -> bool:
        """Apply a cloud change to local database"""
        try:
            table_name = change.get('table_name')
            operation = change.get('operation')
            data = change.get('data', {})
            record_id = change.get('record_id')
            
            if operation == 'insert':
                # Handle insert operation
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['?' for _ in data.keys()])
                query = f'INSERT OR IGNORE INTO {table_name} ({columns}) VALUES ({placeholders})'
                cursor.execute(query, list(data.values()))
                
            elif operation == 'update':
                # Handle update operation
                set_clause = ', '.join([f'{k} = ?' for k in data.keys()])
                query = f'UPDATE {table_name} SET {set_clause} WHERE id = ?'
                cursor.execute(query, list(data.values()) + [record_id])
                
            elif operation == 'delete':
                # Handle delete operation
                cursor.execute(f'UPDATE {table_name} SET is_active = 0 WHERE id = ?', (record_id,))
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying cloud change: {e}")
            return False
    
    def _attempt_sync(self):
        """Attempt automatic synchronization"""
        try:
            # Push any pending changes
            self.push_changes()
            
            # Pull any new changes
            self.pull_changes()
            
        except Exception as e:
            logger.error(f"Error during automatic sync: {e}")
    
    def get_offline_data_summary(self) -> Dict[str, Any]:
        """Get summary of offline data storage"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get table sizes
            table_stats = {}
            
            tables = ['products', 'sales', 'sale_items', 'expenses', 'capital_entries', 
                     'client_debts', 'supplier_debts', 'stock_movements', 'users']
            
            for table in tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                table_stats[table] = count
            
            # Get database file size
            cursor.execute('PRAGMA page_count')
            page_count = cursor.fetchone()[0]
            cursor.execute('PRAGMA page_size')
            page_size = cursor.fetchone()[0]
            db_size_bytes = page_count * page_size
            db_size_mb = round(db_size_bytes / (1024 * 1024), 2)
            
            # Get sync queue summary
            cursor.execute('''
                SELECT sync_status, COUNT(*) as count 
                FROM sync_queue 
                GROUP BY sync_status
            ''')
            sync_summary = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                'database_size_mb': db_size_mb,
                'table_counts': table_stats,
                'sync_queue_summary': sync_summary,
                'total_records': sum(table_stats.values()),
                'storage_health': 'good' if db_size_mb < 100 else 'warning' if db_size_mb < 500 else 'critical'
            }
            
        except Exception as e:
            logger.error(f"Error getting offline data summary: {e}")
            return {
                'database_size_mb': 0,
                'table_counts': {},
                'sync_queue_summary': {},
                'total_records': 0,
                'storage_health': 'error'
            }
    
    def cleanup_old_sync_records(self, days_old: int = 30) -> int:
        """Clean up old sync records to save space"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Delete old successful sync records
            cursor.execute('''
                DELETE FROM sync_queue 
                WHERE sync_status = "synced" 
                AND synced_at < datetime('now', '-{} days')
            '''.format(days_old))
            
            deleted_count = cursor.rowcount
            
            # Also clean up old failed records (but keep recent ones for debugging)
            cursor.execute('''
                DELETE FROM sync_queue 
                WHERE sync_status = "failed" 
                AND created_at < datetime('now', '-{} days')
            '''.format(days_old * 2))  # Keep failed records longer
            
            deleted_count += cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {deleted_count} old sync records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up sync records: {e}")
            return 0
    
    def enable_cloud_sync(self, firebase_config: Optional[Dict] = None):
        """Enable cloud synchronization with Firebase"""
        try:
            # In real implementation, this would:
            # 1. Validate Firebase configuration
            # 2. Initialize Firebase SDK
            # 3. Test connectivity
            # 4. Set up real-time listeners
            
            if firebase_config:
                # Validate configuration
                required_keys = ['apiKey', 'authDomain', 'projectId']
                if all(key in firebase_config for key in required_keys):
                    self.cloud_enabled = True
                    logger.info("Cloud synchronization enabled")
                    return True
            
            logger.warning("Invalid Firebase configuration")
            return False
            
        except Exception as e:
            logger.error(f"Error enabling cloud sync: {e}")
            return False
    
    def disable_cloud_sync(self):
        """Disable cloud synchronization"""
        self.cloud_enabled = False
        logger.info("Cloud synchronization disabled")
    
    def export_offline_data(self) -> Dict[str, Any]:
        """Export all offline data for backup or migration"""
        try:
            conn = self.get_connection()
            
            export_data = {}
            
            # Export key tables
            tables_to_export = ['products', 'sales', 'sale_items', 'expenses', 
                              'capital_entries', 'client_debts', 'supplier_debts', 
                              'stock_movements', 'cash_register']
            
            for table in tables_to_export:
                cursor = conn.cursor()
                cursor.execute(f'SELECT * FROM {table}')
                
                # Get column names
                columns = [description[0] for description in cursor.description]
                
                # Get all rows
                rows = cursor.fetchall()
                
                export_data[table] = {
                    'columns': columns,
                    'data': [dict(zip(columns, row)) for row in rows]
                }
            
            conn.close()
            
            # Add metadata
            export_data['_metadata'] = {
                'export_date': datetime.now().isoformat(),
                'app_version': '1.0.0',
                'total_tables': len(tables_to_export),
                'total_records': sum(len(table_data['data']) for table_data in export_data.values() if isinstance(table_data, dict) and 'data' in table_data)
            }
            
            return {
                'success': True,
                'data': export_data,
                'size_estimate': len(json.dumps(export_data))
            }
            
        except Exception as e:
            logger.error(f"Error exporting offline data: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
