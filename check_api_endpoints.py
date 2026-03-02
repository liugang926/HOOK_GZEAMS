"""
Check Backend API Endpoints Availability

This script tests all business object API endpoints to verify they are working.
"""

import requests
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

def test_endpoints():
    """Test all API endpoints"""

    # Step 1: Login to get token
    print("=" * 80)
    print("Step 1: Authenticating...")
    print("=" * 80)

    login_url = f"{BASE_URL}/auth/login/"
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }

    try:
        response = requests.post(login_url, json=login_data)
        print(f"Login URL: {login_url}")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get('data', {}).get('token') or token_data.get('token')
            print(f"✅ Login successful! Token: {token[:50]}...")
        else:
            print(f"❌ Login failed!")
            print(f"Response: {response.text[:200]}")
            return

    except Exception as e:
        print(f"❌ Login error: {str(e)}")
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
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url, headers=headers)
            status_code = response.status_code
            response_body = response.text[:200]

            print(f"URL: {url}")
            print(f"Status Code: {status_code}")
            print(f"Response: {response_body}")

            # Determine status
            if status_code == 200:
                status = "✅ Working (200)"
            elif status_code == 401:
                status = "⚠️  Exists but Unauthorized (401)"
            elif status_code == 400:
                status = "⚠️  Exists but Bad Request (400)"
            elif status_code == 404:
                status = "❌ Not Found (404)"
            elif status_code == 405:
                status = "⚠️  Exists but Method Not Allowed (405)"
            else:
                status = f"⚠️  Unexpected ({status_code})"

            results.append({
                "name": name,
                "endpoint": endpoint,
                "status_code": status_code,
                "status": status,
                "response": response_body
            })

        except requests.exceptions.ConnectionError:
            print(f"❌ Connection Error - Server may not be running")
            results.append({
                "name": name,
                "endpoint": endpoint,
                "status_code": None,
                "status": "❌ Connection Error",
                "response": "Server not accessible"
            })
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                "name": name,
                "endpoint": endpoint,
                "status_code": None,
                "status": f"❌ Error: {str(e)}",
                "response": str(e)
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

    print(f"\n✅ Working Endpoints ({len(working_endpoints)}):")
    for r in working_endpoints:
        print(f"  ✓ {r['name']:20s} {r['endpoint']:30s} {r['status']}")

    if missing_endpoints:
        print(f"\n❌ Missing Endpoints ({len(missing_endpoints)}):")
        for r in missing_endpoints:
            print(f"  ✗ {r['name']:20s} {r['endpoint']:30s} {r['status']}")

    if error_endpoints:
        print(f"\n⚠️  Error Endpoints ({len(error_endpoints)}):")
        for r in error_endpoints:
            print(f"  ! {r['name']:20s} {r['endpoint']:30s} {r['status']}")

    print("\n" + "=" * 80)
    print(f"Total: {len(results)} endpoints tested")
    print(f"Working: {len(working_endpoints)}")
    print(f"Missing: {len(missing_endpoints)}")
    print(f"Errors: {len(error_endpoints)}")
    print("=" * 80)

if __name__ == "__main__":
    test_endpoints()
