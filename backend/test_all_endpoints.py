#!/usr/bin/env python3
"""
Comprehensive backend endpoint testing script
Tests all endpoints from all route files and documents results/errors
"""

import requests
import json
from datetime import datetime

API_BASE = "http://127.0.0.1:8001"
ENDPOINTS_TESTED = []

def login():
    """Login and return auth token"""
    try:
        response = requests.post(
            f"{API_BASE}/api/auth/login",
            json={"username": "admin", "password": "admin123"},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get('access_token')
        return None
    except Exception as e:
        print(f"Login failed: {e}")
        return None

def test_endpoint(method, path, description, headers=None, data=None, params=None):
    """Test a single endpoint and record results"""
    url = f"{API_BASE}{path}"
    result = {
        "description": description,
        "method": method,
        "path": path,
        "url": url,
        "status_code": None,
        "status": "error",
        "error": None,
        "response_data": None,
    }
    
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params,
            timeout=10
        )
        
        result["status_code"] = response.status_code
        result["response_headers"] = dict(response.headers)
        
        # Try to parse JSON response
        try:
            result["response_data"] = response.json()
        except:
            result["response_data"] = {"text": response.text[:200]}
        
        # Determine status
        if response.status_code < 400:
            result["status"] = "success"
        elif response.status_code == 401:
            result["status"] = "unauthorized"
        elif response.status_code == 403:
            result["status"] = "forbidden"
        elif response.status_code == 404:
            result["status"] = "not_found"
        elif response.status_code == 405:
            result["status"] = "method_not_allowed"
        elif response.status_code >= 500:
            result["status"] = "server_error"
            result["error"] = str(response.json().get("detail", "Internal server error"))
        else:
            result["status"] = "client_error"
            result["error"] = str(response.json().get("detail", "Client error"))
            
    except requests.exceptions.Timeout:
        result["error"] = "Request timeout"
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection failed"
    except Exception as e:
        result["error"] = str(e)
    
    ENDPOINTS_TESTED.append(result)
    return result

def print_results():
    """Print test results summary"""
    total = len(ENDPOINTS_TESTED)
    success = sum(1 for r in ENDPOINTS_TESTED if r["status"] == "success")
    unauthorized = sum(1 for r in ENDPOINTS_TESTED if r["status"] == "unauthorized")
    forbidden = sum(1 for r in ENDPOINTS_TESTED if r["status"] == "forbidden")
    not_found = sum(1 for r in ENDPOINTS_TESTED if r["status"] == "not_found")
    method_not_allowed = sum(1 for r in ENDPOINTS_TESTED if r["status"] == "method_not_allowed")
    server_error = sum(1 for r in ENDPOINTS_TESTED if r["status"] == "server_error")
    client_error = sum(1 for r in ENDPOINTS_TESTED if r["status"] in ["client_error", "error"])
    
    print("\n" + "="*100)
    print("BACKEND ENDPOINT TEST SUMMARY")
    print("="*100)
    print(f"Total Endpoints: {total}")
    print(f"✅ Success: {success}")
    print(f"🔒 Unauthorized: {unauthorized}")
    print(f"🚫 Forbidden: {forbidden}")
    print(f"❌ Not Found: {not_found}")
    print(f"✖️ Method Not Allowed: {method_not_allowed}")
    print(f"💥 Server Error: {server_error}")
    print(f"⚠️  Client Error: {client_error}")
    print("\n" + "="*100)
    
    # Print errors
    errors = [r for r in ENDPOINTS_TESTED if r["status"] not in ["success", "unauthorized", "forbidden", "method_not_allowed"]]
    if errors:
        print("\nERRORS FOUND:")
        print("-"*100)
        for r in errors:
            print(f"\n❌ {r['description']}")
            print(f"   {r['method']} {r['path']}")
            print(f"   Status: {r['status']} ({r['status_code']})")
            if r.get('error'):
                print(f"   Error: {r['error'][:200]}")
            if r.get('response_data') and isinstance(r['response_data'], dict) and 'detail' in r['response_data']:
                print(f"   Detail: {r['response_data']['detail']}")

def main():
    print("="*100)
    print("BACKEND ENDPOINT TESTING")
    print("="*100)
    
    # Get auth token
    print("\n🔐 Logging in...")
    token = login()
    if not token:
        print("❌ Login failed. Cannot proceed.")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"✅ Login successful. Token: {token[:50]}...")
    
    # Test all endpoints from all route files
    print("\n🧪 Testing endpoints...\n")
    
    # ==================== HEALTH ====================
    test_endpoint("GET", "/health", "Health Check")
    test_endpoint("GET", "/api/", "Root API")
    
    # ==================== AUTH ====================
    test_endpoint("POST", "/api/auth/login", "Login", data={"username": "admin", "password": "admin123"})
    test_endpoint("POST", "/api/auth/logout", "Logout", headers=headers)
    test_endpoint("POST", "/api/auth/password-reset/request", "Request Password Reset", data={"username_or_email": "admin"})
    test_endpoint("POST", "/api/auth/password-reset/complete", "Complete Password Reset", data={"token": "test-token", "new_password": "NewPass123!"})
    test_endpoint("POST", "/api/auth/password/change", "Change Password", headers=headers, data={"old_password": "admin123", "new_password": "NewPass123!"})
    
    # ==================== DASHBOARD ====================
    test_endpoint("GET", "/api/dashboard/metrics", "Dashboard Metrics", headers=headers)
    test_endpoint("GET", "/api/dashboard/projects", "Project Overview", headers=headers)
    test_endpoint("GET", "/api/dashboard/resources", "Resource Distribution", headers=headers)
    test_endpoint("GET", "/api/dashboard/trends", "Utilization Trends", headers=headers)
    test_endpoint("GET", "/api/dashboard/budget-status", "Budget Status", headers=headers)
    test_endpoint("GET", "/api/dashboard/infrastructure/kpis", "Infrastructure KPIs", headers=headers)
    test_endpoint("POST", "/api/dashboard/cache/clear", "Clear Cache", headers=headers)
    
    # ==================== DASHBOARD TABS ====================
    test_endpoint("GET", "/api/dashboard/tab/dashboard", "Dashboard Tab", headers=headers)
    test_endpoint("GET", "/api/dashboard/tab/projects", "Projects Tab", headers=headers)
    test_endpoint("GET", "/api/dashboard/tab/projects?limit=10&offset=0", "Projects Tab with Pagination", headers=headers)
    test_endpoint("GET", "/api/dashboard/tab/projects?status=Active", "Projects Tab with Status Filter", headers=headers)
    test_endpoint("GET", "/api/dashboard/tab/projects?search=web", "Projects Tab with Search", headers=headers)
    
    test_endpoint("GET", "/api/dashboard/tab/assets", "Assets Tab", headers=headers)
    test_endpoint("GET", "/api/dashboard/tab/assets?limit=10&offset=0", "Assets Tab with Pagination", headers=headers)
    test_endpoint("GET", "/api/dashboard/tab/assets?status=Active", "Assets Tab with Status Filter", headers=headers)
    
    test_endpoint("GET", "/api/dashboard/tab/resources", "Resources Tab", headers=headers)
    test_endpoint("GET", "/api/dashboard/tab/resources?limit=10&offset=0", "Resources Tab with Pagination", headers=headers)
    test_endpoint("GET", "/api/dashboard/tab/resources?status=Active", "Resources Tab with Status Filter", headers=headers)
    
    test_endpoint("GET", "/api/dashboard/tab/documents", "Documents Tab", headers=headers)
    test_endpoint("GET", "/api/dashboard/tab/documents?limit=10&offset=0", "Documents Tab with Pagination", headers=headers)
    
    test_endpoint("GET", "/api/dashboard/tab/reports", "Reports Tab", headers=headers)
    test_endpoint("GET", "/api/dashboard/tab/reports?limit=10&offset=0", "Reports Tab with Pagination", headers=headers)
    
    test_endpoint("GET", "/api/dashboard/tab/alerts", "Alerts Tab", headers=headers)
    test_endpoint("GET", "/api/dashboard/tab/alerts?limit=10&offset=0", "Alerts Tab with Pagination", headers=headers)
    test_endpoint("GET", "/api/dashboard/tab/alerts?severity=High", "Alerts Tab with Severity Filter", headers=headers)
    
    test_endpoint("GET", "/api/dashboard/tab/administration", "Administration Tab", headers=headers)
    
    # ==================== PROJECTS ====================
    test_endpoint("GET", "/api/projects", "List Projects", headers=headers)
    test_endpoint("GET", "/api/projects?limit=10&offset=0", "List Projects with Pagination", headers=headers)
    test_endpoint("GET", "/api/projects/search", "Search Projects (ERROR EXPECTED)", headers=headers)  # Will likely fail
    
    # Get first project ID for detail tests
    try:
        response = requests.get(f"{API_BASE}/api/projects", headers=headers, timeout=5)
        if response.status_code == 200:
            projects = response.json().get("projects", [])
            if projects:
                project_id = projects[0]["id"]
                test_endpoint("GET", f"/api/projects/{project_id}", "Get Project Detail", headers=headers)
                test_endpoint("PUT", f"/api/projects/{project_id}", "Update Project", headers=headers, data={"name": "Test Project"})
                test_endpoint("DELETE", f"/api/projects/{project_id}", "Delete Project", headers=headers)
    except Exception as e:
        print(f"Could not get project ID: {e}")
    
    test_endpoint("POST", "/api/projects", "Create Project", headers=headers, data={
        "name": "Test Project",
        "project_code": "TST-001",
        "status": "Active",
        "budget": 100000
    })
    
    # ==================== USERS ====================
    test_endpoint("GET", "/api/users", "List Users", headers=headers)
    test_endpoint("GET", "/api/users?limit=10&offset=0", "List Users with Pagination", headers=headers)
    test_endpoint("GET", "/api/users/me", "Current User Info", headers=headers)
    
    # Get first user ID for detail tests
    try:
        response = requests.get(f"{API_BASE}/api/users", headers=headers, timeout=5)
        if response.status_code == 200:
            users = response.json().get("users", [])
            if users:
                user_id = users[0]["id"]
                test_endpoint("GET", f"/api/users/{user_id}", "Get User Detail", headers=headers)
                test_endpoint("PUT", f"/api/users/{user_id}", "Update User", headers=headers, data={"full_name": "Test User"})
                test_endpoint("DELETE", f"/api/users/{user_id}", "Delete User", headers=headers)
    except Exception as e:
        print(f"Could not get user ID: {e}")
    
    test_endpoint("POST", "/api/users", "Create User", headers=headers, data={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
        "role_id": 2
    })
    
    # ==================== ASSET TYPES ====================
    test_endpoint("GET", "/api/asset-types", "List Asset Types", headers=headers)
    test_endpoint("GET", "/api/asset-types?limit=10&offset=0", "List Asset Types with Pagination", headers=headers)
    
    # Get first asset type ID for detail tests
    try:
        response = requests.get(f"{API_BASE}/api/asset-types", headers=headers, timeout=5)
        if response.status_code == 200:
            asset_types = response.json().get("asset_types", [])
            if asset_types:
                asset_type_id = asset_types[0]["id"]
                test_endpoint("GET", f"/api/asset-types/{asset_type_id}", "Get Asset Type Detail", headers=headers)
                test_endpoint("PUT", f"/api/asset-types/{asset_type_id}", "Update Asset Type", headers=headers, data={"name": "Test Type"})
                test_endpoint("DELETE", f"/api/asset-types/{asset_type_id}", "Delete Asset Type", headers=headers)
    except Exception as e:
        print(f"Could not get asset type ID: {e}")
    
    test_endpoint("POST", "/api/asset-types", "Create Asset Type", headers=headers, data={
        "name": "Test Type",
        "description": "Test Description",
        "icon": "💻",
        "display_order": 99
    })
    
    # ==================== RESOURCE TYPES ====================
    test_endpoint("GET", "/api/resource-types", "List Resource Types", headers=headers)
    test_endpoint("GET", "/api/resource-types?limit=10&offset=0", "List Resource Types with Pagination", headers=headers)
    
    # Get first resource type ID for detail tests
    try:
        response = requests.get(f"{API_BASE}/api/resource-types", headers=headers, timeout=5)
        if response.status_code == 200:
            resource_types = response.json().get("resource_types", [])
            if resource_types:
                resource_type_id = resource_types[0]["id"]
                test_endpoint("GET", f"/api/resource-types/{resource_type_id}", "Get Resource Type Detail", headers=headers)
                test_endpoint("PUT", f"/api/resource-types/{resource_type_id}", "Update Resource Type", headers=headers, data={"name": "Test Type"})
                test_endpoint("DELETE", f"/api/resource-types/{resource_type_id}", "Delete Resource Type", headers=headers)
    except Exception as e:
        print(f"Could not get resource type ID: {e}")
    
    test_endpoint("POST", "/api/resource-types", "Create Resource Type", headers=headers, data={
        "name": "test_type",
        "display_name": "Test Type",
        "icon": "💻",
        "display_order": 99
    })
    
    # ==================== RESOURCES ====================
    test_endpoint("GET", "/api/resources", "List Resources", headers=headers)
    test_endpoint("GET", "/api/resources?limit=10&offset=0", "List Resources with Pagination", headers=headers)
    test_endpoint("GET", "/api/resources?status=Active", "List Resources with Status Filter", headers=headers)
    
    # Get first resource ID for detail tests
    try:
        response = requests.get(f"{API_BASE}/api/resources", headers=headers, timeout=5)
        if response.status_code == 200:
            resources = response.json().get("resources", [])
            if resources:
                resource_id = resources[0]["id"]
                test_endpoint("GET", f"/api/resources/{resource_id}", "Get Resource Detail", headers=headers)
                test_endpoint("PUT", f"/api/resources/{resource_id}", "Update Resource", headers=headers, data={"name": "Test Resource"})
                test_endpoint("DELETE", f"/api/resources/{resource_id}", "Delete Resource", headers=headers)
    except Exception as e:
        print(f"Could not get resource ID: {e}")
    
    test_endpoint("POST", "/api/resources", "Create Resource", headers=headers, data={
        "name": "Test Resource",
        "cost": 1000.00,
        "status": "Active",
        "project_id": "591dbcd5-eb83-41ba-8350-7d4ad00ce868",
        "asset_type_id": "664e43a4-f681-4eae-9971-ddf30b2b7f9d"
    })
    
    # ==================== ASSETS ====================
    test_endpoint("GET", "/api/assets", "List Assets", headers=headers)
    test_endpoint("GET", "/api/assets?limit=10&offset=0", "List Assets with Pagination", headers=headers)
    test_endpoint("GET", "/api/assets?status=Active", "List Assets with Status Filter", headers=headers)
    
    # Get first asset ID for detail tests
    try:
        response = requests.get(f"{API_BASE}/api/assets", headers=headers, timeout=5)
        if response.status_code == 200:
            assets = response.json().get("assets", [])
            if assets:
                asset_id = assets[0]["id"]
                test_endpoint("GET", f"/api/assets/{asset_id}", "Get Asset Detail", headers=headers)
                test_endpoint("PUT", f"/api/assets/{asset_id}", "Update Asset", headers=headers, data={"asset_name": "Test Asset"})
                test_endpoint("DELETE", f"/api/assets/{asset_id}", "Delete Asset", headers=headers)
    except Exception as e:
        print(f"Could not get asset ID: {e}")
    
    test_endpoint("POST", "/api/assets", "Create Asset", headers=headers, data={
        "project_id": "591dbcd5-eb83-41ba-8350-7d4ad00ce868",
        "resource_type_id": "664e43a4-f681-4eae-9971-ddf30b2b7f9d",
        "asset_name": "Test Asset",
        "manufacturer": "Test Manufacturer",
        "model": "Test Model",
        "serial_number": "TEST-123",
        "cost": "1000.00",
        "status": "Active"
    })
    
    # ==================== TEMPLATES ====================
    test_endpoint("GET", "/api/templates", "List Templates", headers=headers)
    test_endpoint("GET", "/api/templates?limit=10&offset=0", "List Templates with Pagination", headers=headers)
    
    # Get first template ID for detail tests
    try:
        response = requests.get(f"{API_BASE}/api/templates", headers=headers, timeout=5)
        if response.status_code == 200:
            templates = response.json().get("templates", [])
            if templates:
                template_id = templates[0]["id"]
                test_endpoint("GET", f"/api/templates/{template_id}", "Get Template Detail", headers=headers)
                test_endpoint("PUT", f"/api/templates/{template_id}", "Update Template", headers=headers, data={"report_name": "Test Template"})
                test_endpoint("DELETE", f"/api/templates/{template_id}", "Delete Template", headers=headers)
    except Exception as e:
        print(f"Could not get template ID: {e}")
    
    test_endpoint("POST", "/api/templates", "Create Template", headers=headers, data={
        "report_name": "Test Template",
        "description": "Test Description",
        "filters_json": {},
        "columns_config": {},
        "is_public": True
    })
    
    # ==================== DOCUMENTS ====================
    test_endpoint("GET", "/api/documents", "List Documents", headers=headers)
    test_endpoint("GET", "/api/documents?limit=10&offset=0", "List Documents with Pagination", headers=headers)
    test_endpoint("GET", "/api/documents?doc_type=Invoice", "List Documents with Type Filter", headers=headers)
    
    # Get first document ID for detail tests
    try:
        response = requests.get(f"{API_BASE}/api/documents", headers=headers, timeout=5)
        if response.status_code == 200:
            documents = response.json().get("documents", [])
            if documents:
                document_id = documents[0]["id"]
                test_endpoint("GET", f"/api/documents/{document_id}", "Get Document Detail", headers=headers)
                test_endpoint("PUT", f"/api/documents/{document_id}", "Update Document", headers=headers, data={"file_name": "Test Doc"})
                test_endpoint("DELETE", f"/api/documents/{document_id}", "Delete Document", headers=headers)
    except Exception as e:
        print(f"Could not get document ID: {e}")
    
    test_endpoint("POST", "/api/documents", "Create Document", headers=headers, data={
        "file_name": "test.pdf",
        "document_type": "Other",
        "description": "Test document",
        "project_id": "591dbcd5-eb83-41ba-8350-7d4ad00ce868"
    })
    
    # ==================== ALERTS ====================
    test_endpoint("GET", "/api/alerts", "List Alerts", headers=headers)
    test_endpoint("GET", "/api/alerts?limit=10&offset=0", "List Alerts with Pagination", headers=headers)
    test_endpoint("GET", "/api/alerts?severity=High", "List Alerts with Severity Filter", headers=headers)
    
    # Get first alert ID for detail tests
    try:
        response = requests.get(f"{API_BASE}/api/alerts", headers=headers, timeout=5)
        if response.status_code == 200:
            alerts = response.json().get("alerts", [])
            if alerts:
                alert_id = alerts[0]["id"]
                test_endpoint("GET", f"/api/alerts/{alert_id}", "Get Alert Detail", headers=headers)
                test_endpoint("PUT", f"/api/alerts/{alert_id}", "Update Alert", headers=headers, data={"title": "Test Alert"})
                test_endpoint("DELETE", f"/api/alerts/{alert_id}", "Delete Alert", headers=headers)
    except Exception as e:
        print(f"Could not get alert ID: {e}")
    
    test_endpoint("POST", "/api/alerts", "Create Alert", headers=headers, data={
        "title": "Test Alert",
        "message": "Test alert message",
        "severity": "Low",
        "status": "Active",
        "due_date": "2025-12-31"
    })
    
    # ==================== REPORT TEMPLATES ====================
    test_endpoint("GET", "/api/report-templates", "List Report Templates", headers=headers)
    test_endpoint("GET", "/api/report-templates?limit=10&offset=0", "List Report Templates with Pagination", headers=headers)
    
    # Print results
    print_results()

if __name__ == "__main__":
    main()