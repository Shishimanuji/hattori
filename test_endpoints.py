#!/usr/bin/env python3
"""
Comprehensive endpoint testing script for the PRMS API
"""

import requests
import json
import sys
from typing import Dict, List, Tuple

API_BASE = "http://127.0.0.1:8001/api"

class EndpointTester:
    def __init__(self):
        self.token = None
        self.headers = {}
        
    def login(self, username: str = "admin", password: str = "admin123") -> bool:
        """Login and get JWT token"""
        try:
            print(f"🔐 Logging in as '{username}'...")
            response = requests.post(
                f"{API_BASE}/auth/login",
                json={"username": username, "password": password},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
                print(f"✓ Login successful. Token: {self.token[:50]}...")
                return True
            else:
                print(f"✗ Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Login error: {e}")
            return False
    
    def test_endpoint(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> Tuple[bool, dict]:
        """Test a single endpoint"""
        url = f"{API_BASE}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data, timeout=10)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=10)
            else:
                return False, {"error": f"Unsupported method: {method}"}
            
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "url": url,
                "method": method.upper()
            }
            
            # Try to parse JSON response
            try:
                result["data"] = response.json()
            except:
                result["text"] = response.text[:500]  # Truncate long responses
            
            success = response.status_code < 400
            return success, result
            
        except requests.exceptions.Timeout:
            return False, {"error": "Timeout"}
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection failed"}
        except Exception as e:
            return False, {"error": str(e)}
    
    def run_tests(self):
        """Run comprehensive endpoint tests"""
        if not self.login():
            print("❌ Cannot proceed without valid login")
            return
        
        print("\n" + "="*80)
        print("🧪 BACKEND ENDPOINT TESTING")
        print("="*80)
        
        # Define test cases
        test_cases = [
            # Health endpoint (no auth needed)
            ("GET", "/health", "Health Check", False),  # No /api prefix
            
            # Dashboard endpoints (auth required)
            ("GET", "/dashboard/metrics", "Dashboard Metrics"),
            ("GET", "/dashboard/projects", "Project Overview"),
            ("GET", "/dashboard/resources", "Resource Distribution"),
            ("GET", "/dashboard/trends", "Utilization Trends"),
            ("GET", "/dashboard/budget-status", "Budget Status"),
            ("GET", "/dashboard/infrastructure/kpis", "Infrastructure KPIs"),
            
            # 8-Tab Dashboard endpoints
            ("GET", "/dashboard/tab/dashboard", "Dashboard Tab"),
            ("GET", "/dashboard/tab/projects", "Projects Tab"),
            ("GET", "/dashboard/tab/assets", "Assets Tab"),
            ("GET", "/dashboard/tab/resources", "Resources Tab"),
            ("GET", "/dashboard/tab/documents", "Documents Tab"),
            ("GET", "/dashboard/tab/reports", "Reports Tab"),
            ("GET", "/dashboard/tab/alerts", "Alerts Tab"),
            ("GET", "/dashboard/tab/administration", "Administration Tab"),
            
            # Auth endpoints (with token)
            ("POST", "/auth/logout", "Logout"),
            
            # Other endpoints (we'll add more as we discover them)
        ]
        
        results = []
        for test_case in test_cases:
            if len(test_case) == 4:  # Has auth flag
                method, endpoint, description, needs_auth = test_case
            else:  # Default to needs auth
                method, endpoint, description = test_case
                needs_auth = True
            
            print(f"\n📍 Testing: {description}")
            print(f"   {method} {endpoint}")
            
            # Handle health endpoint differently (no /api prefix)
            if endpoint == "/health":
                url = f"http://127.0.0.1:8001{endpoint}"
                try:
                    response = requests.get(url, timeout=10)
                    result = {
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "url": url,
                        "method": method.upper()
                    }
                    
                    try:
                        result["data"] = response.json()
                    except:
                        result["text"] = response.text[:500]
                    
                    success = response.status_code < 400
                except Exception as e:
                    success = False
                    result = {"error": str(e)}
            else:
                success, result = self.test_endpoint(method, endpoint)
            
            results.append((description, success, result))
            
            if success:
                status = result.get("status_code", "Unknown")
                print(f"   ✅ SUCCESS ({status})")
                
                # Show sample response data
                if "data" in result and isinstance(result["data"], dict):
                    data = result["data"]
                    if isinstance(data, dict):
                        keys = list(data.keys())[:5]  # Show first 5 keys
                        print(f"   📊 Response keys: {keys}")
                        
                        # Show counts if available
                        for key in ["total", "count", "projects", "assets"]:
                            if key in data:
                                value = data[key]
                                if isinstance(value, (int, float)):
                                    print(f"   📈 {key}: {value}")
                                elif isinstance(value, list):
                                    print(f"   📈 {key}: {len(value)} items")
                
            else:
                status = result.get("status_code", "ERROR")
                error = result.get("error", "Unknown error")
                
                if "data" in result and "detail" in result["data"]:
                    error = result["data"]["detail"]
                elif "text" in result:
                    error = result["text"][:100]
                
                print(f"   ❌ FAILED ({status}): {error}")
        
        # Summary
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        
        passed = sum(1 for _, success, _ in results if success)
        failed = len(results) - passed
        
        print(f"Total Tests: {len(results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {passed/len(results)*100:.1f}%")
        
        if failed > 0:
            print(f"\n🔍 FAILED TESTS:")
            for desc, success, result in results:
                if not success:
                    status = result.get("status_code", "ERROR")
                    error = result.get("error", "Unknown")
                    if "data" in result and "detail" in result["data"]:
                        error = result["data"]["detail"]
                    print(f"   • {desc}: {status} - {error}")
        
        return results

if __name__ == "__main__":
    tester = EndpointTester()
    results = tester.run_tests()