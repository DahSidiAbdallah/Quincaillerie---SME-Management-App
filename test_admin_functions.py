#!/usr/bin/env python3
"""
Test script for admin and settings functionality
Tests all database methods and API endpoints for admin panel
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.data.database import DatabaseManager

class AdminFunctionalityTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.db = DatabaseManager()
        self.test_results = []
        
    def log_test(self, test_name, success, message=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}: {message}"
        print(result)
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
    def test_database_methods(self):
        """Test all database methods used by admin/settings"""
        print("\n🔧 Testing Database Methods...")
        
        # Test get_users
        try:
            users = self.db.get_users()
            self.log_test("get_users()", True, f"Found {len(users)} users")
        except Exception as e:
            self.log_test("get_users()", False, f"Error: {e}")
        
        # Test app settings
        try:
            settings = self.db.get_app_settings()
            self.log_test("get_app_settings()", True, f"Found {len(settings)} settings")
        except Exception as e:
            self.log_test("get_app_settings()", False, f"Error: {e}")
        
        # Test update app settings
        try:
            test_settings = {
                'currency': 'EUR',
                'tax_rate': '20.0',
                'backup_frequency': 'daily'
            }
            result = self.db.set_app_settings(test_settings)
            success = result.get('success', False) if isinstance(result, dict) else False
            message = str(result.get('error', 'Settings updated')) if isinstance(result, dict) else 'Unknown result'
            self.log_test("set_app_settings()", success, message)
        except Exception as e:
            self.log_test("update_app_settings()", False, f"Error: {e}")
        
        # Test create user (without actually creating to avoid conflicts)
        try:
            test_user = {
                'username': 'test_user_temp',
                'pin': '1234',
                'role': 'employee',
                'language': 'fr'
            }
            # Just check if method exists and handles validation
            result = self.db.create_user({})  # Empty data should fail gracefully
            self.log_test("create_user() validation", 
                         not result.get('success', True), 
                         "Correctly rejects empty data")
        except Exception as e:
            self.log_test("create_user()", False, f"Error: {e}")
    
    def test_api_endpoints(self):
        """Test admin and settings API endpoints"""
        print("\n🌐 Testing API Endpoints...")
        
        # Test admin endpoints
        admin_endpoints = [
            '/api/admin/settings',
            '/api/admin/users',
            '/api/admin/backups',
            '/api/admin/logs',
            '/api/admin/system-info'
        ]
        
        for endpoint in admin_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                success = response.status_code in [200, 401]  # 401 is OK (auth required)
                self.log_test(f"GET {endpoint}", success, 
                             f"Status: {response.status_code}")
            except requests.exceptions.ConnectionError:
                self.log_test(f"GET {endpoint}", False, "Connection refused - server not running")
            except Exception as e:
                self.log_test(f"GET {endpoint}", False, f"Error: {e}")
        
        # Test settings endpoints  
        settings_endpoints = [
            '/api/settings/user-info',
            '/api/settings/preferences',
            '/api/settings/notifications'
        ]
        
        for endpoint in settings_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                success = response.status_code in [200, 401]  # 401 is OK (auth required)
                self.log_test(f"GET {endpoint}", success, 
                             f"Status: {response.status_code}")
            except requests.exceptions.ConnectionError:
                self.log_test(f"GET {endpoint}", False, "Connection refused - server not running")
            except Exception as e:
                self.log_test(f"GET {endpoint}", False, f"Error: {e}")
    
    def test_file_integrity(self):
        """Test that all required files exist and are accessible"""
        print("\n📁 Testing File Integrity...")
        
        required_files = [
            'app/templates/admin.html',
            'app/templates/settings.html',
            'app/api/admin.py',
            'app/api/settings.py',
            'app/data/database.py',
            'app/static/js/admin-diagnostics.js'
        ]
        
        for file_path in required_files:
            full_path = os.path.join(os.path.dirname(__file__), file_path)
            exists = os.path.exists(full_path)
            self.log_test(f"File exists: {file_path}", exists, 
                         f"Path: {full_path}")
    
    def test_template_syntax(self):
        """Check template files for basic syntax issues"""
        print("\n📝 Testing Template Syntax...")
        
        templates = {
            'app/templates/admin.html': ['adminManager', 'alpinejs', 'x-data'],
            'app/templates/settings.html': ['settingsManager', 'alpinejs', 'x-data']
        }
        
        for template_path, required_items in templates.items():
            full_path = os.path.join(os.path.dirname(__file__), template_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    missing_items = []
                    for item in required_items:
                        if item not in content:
                            missing_items.append(item)
                    
                    if not missing_items:
                        self.log_test(f"Template syntax: {template_path}", True, 
                                     "All required elements found")
                    else:
                        self.log_test(f"Template syntax: {template_path}", False, 
                                     f"Missing: {', '.join(missing_items)}")
                        
                except Exception as e:
                    self.log_test(f"Template syntax: {template_path}", False, f"Error: {e}")
            else:
                self.log_test(f"Template syntax: {template_path}", False, "File not found")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📊 ADMIN/SETTINGS FUNCTIONALITY TEST REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")
        
        print(f"\nReport generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save detailed report
        report_file = f"admin_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'success_rate': (passed_tests/total_tests)*100
                },
                'tests': self.test_results,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"Detailed report saved to: {report_file}")
    
    def run_all_tests(self):
        """Run all tests and generate report"""
        print("🚀 Starting Admin/Settings Functionality Tests...")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.test_file_integrity()
        self.test_template_syntax()
        self.test_database_methods()
        self.test_api_endpoints()
        
        self.generate_report()

if __name__ == "__main__":
    tester = AdminFunctionalityTester()
    tester.run_all_tests()
