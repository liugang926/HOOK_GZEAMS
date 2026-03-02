"""
Check Backend API Endpoints Availability

This script tests all business object API endpoints to verify they are working.
Using built-in urllib to avoid dependency issues.
"""

import urllib.request
import urllib.error
import urllib.parse
import json

# Configuration
BASE_URL = "http://localhost:8000/api"
USERNAME = "admin"
PASSWORD = "admin123"

# API Endpoints to test
ENDPOINTS = [
    ("/assets/", "资产卡片"),
    ("/asset-categories/", "资产分类"),
    ("/suppliers/", "供应商"),
    ("/locations/", "存放地点"),
    ("/departments/", "部门"),
    ("/consumables/", "低值易耗品"),
    ("/inventory-tasks/", "盘点任务"),
    ("/maintenance/", "维修记录"),
]

def make_request(url, method="GET", body=None, token=None):
    """Make HTTP request"""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, method=method)

    for key, value in headers.items():
        req.add_header(key, value)

    if body:
        req.data = body.encode('utf-8')

    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            response_body = response.read().decode('utf-8')[:200]
            return status_code, response_body, None
    except urllib.error.HTTPError as e:
        status_code = e.code
        try:
            response_body = e.read().decode('utf-8')[:200]
        except:
            response_body = "No response body"
        return status_code, response_body, None
    except urllib.error.URLError as e:
        return None, None, f"Connection Error: {str(e)}"
    except Exception as e:
        return None, None, f"Error: {str(e)}"

def test_endpoints():
    """Test all API endpoints"""

    # Step 1: Login to get token
    print("=" * 80)
    print("Step 1: Authenticating...")
    print("=" * 80)

    login_url = f"{BASE_URL}/auth/login/"
    login_data = json.dumps({
        "username": USERNAME,
        "password": PASSWORD
    })

    status_code, response_body, error = make_request(login_url, "POST", login_data)

    print(f"Login URL: {login_url}")
    print(f"Status Code: {status_code}")
    print(f"Response: {response_body}")

    if error:
        print(f"[ERROR] Login error: {error}")
        print("Make sure the backend server is running!")
        return

    if status_code != 200:
        print(f"[ERROR] Login failed with status {status_code}")
        return

    # Extract token
    try:
        response_data = json.loads(response_body)
        token = None

        # Try different token locations
        if 'data' in response_data and isinstance(response_data['data'], dict):
            token = response_data['data'].get('token')
        if not token:
            token = response_data.get('token')
        if not token:
            token = response_data.get('access')

        if not token:
            print(f"[ERROR] Could not extract token from response")
            print(f"Full response: {response_body}")
            return

        print(f"[OK] Login successful! Token: {token[:50]}...")
    except Exception as e:
        print(f"[ERROR] Error parsing login response: {str(e)}")
        return

    # Step 2: Test each endpoint
    print("\n" + "=" * 80)
    print("Step 2: Testing API Endpoints")
    print("=" * 80)

    results = []

    for endpoint, name in ENDPOINTS:
        print(f"\n{'─' * 80}")
        print(f"Testing: {name} - {endpoint}")
        print(f"{'─' * 80}")

        url = f"{BASE_URL}{endpoint}"

        status_code, response_body, error = make_request(url, "GET", token=token)

        print(f"URL: {url}")
        print(f"Status Code: {status_code}")
        print(f"Response: {response_body}")

        # Determine status
        if error:
            status = f"[ERROR] {error}"
        elif status_code == 200:
            status = "[OK] Working (200)"
        elif status_code == 401:
            status = "[WARN] Exists but Unauthorized (401)"
        elif status_code == 400:
            status = "[WARN] Exists but Bad Request (400)"
        elif status_code == 404:
            status = "[MISSING] Not Found (404)"
        elif status_code == 405:
            status = "[WARN] Exists but Method Not Allowed (405)"
        else:
            status = f"[WARN] Unexpected ({status_code})"

        results.append({
            "name": name,
            "endpoint": endpoint,
            "status_code": status_code,
            "status": status,
            "response": response_body
        })

    # Step 3: Summary
    print("\n" + "=" * 80)
    print("Step 3: Summary")
    print("=" * 80)

    working_endpoints = []
    missing_endpoints = []
    error_endpoints = []

    for result in results:
        if result["status_code"] in [200, 400, 401, 405]:
            working_endpoints.append(result)
        elif result["status_code"] == 404:
            missing_endpoints.append(result)
        else:
            error_endpoints.append(result)

    print(f"\n[OK] Working Endpoints ({len(working_endpoints)}):")
    for r in working_endpoints:
        print(f"  [+] {r['name']:20s} {r['endpoint']:30s} {r['status']}")

    if missing_endpoints:
        print(f"\n[MISSING] Missing Endpoints ({len(missing_endpoints)}):")
        for r in missing_endpoints:
            print(f"  [-] {r['name']:20s} {r['endpoint']:30s} {r['status']}")

    if error_endpoints:
        print(f"\n[ERROR] Error Endpoints ({len(error_endpoints)}):")
        for r in error_endpoints:
            print(f"  [!] {r['name']:20s} {r['endpoint']:30s} {r['status']}")

    print("\n" + "=" * 80)
    print(f"Total: {len(results)} endpoints tested")
    print(f"Working: {len(working_endpoints)}")
    print(f"Missing: {len(missing_endpoints)}")
    print(f"Errors: {len(error_endpoints)}")
    print("=" * 80)

    # Step 4: Find URL configurations
    print("\n" + "=" * 80)
    print("Step 4: URL Configuration Analysis")
    print("=" * 80)
    print("\nSearching for URL configuration files...")

    import os
    backend_path = os.path.join(os.path.dirname(__file__), 'backend')

    for r in missing_endpoints + error_endpoints:
        endpoint_path = r['endpoint'].strip('/').split('/')[0]
        print(f"\n[SEARCH] Searching for: {endpoint_path}")

        # Search in urls.py files
        for root, dirs, files in os.walk(backend_path):
            if 'urls.py' in files:
                urls_file = os.path.join(root, 'urls.py')
                try:
                    with open(urls_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if endpoint_path.replace('-', '_') in content or endpoint_path in content:
                            print(f"  Found in: {urls_file}")
                            # Find relevant lines
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if endpoint_path.replace('-', '_') in line or endpoint_path in line:
                                    start = max(0, i-2)
                                    end = min(len(lines), i+3)
                                    print(f"  Lines {start+1}-{end}:")
                                    for j in range(start, end):
                                        print(f"    {j+1}: {lines[j]}")
                                    break
                except Exception as e:
                    pass

if __name__ == "__main__":
    test_endpoints()
