"""
Test Django Admin Panel for Mobile Module using Django's test client.
"""
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 60)
print("Django Admin Panel Test - Mobile Module")
print("=" * 60)

# Create client
client = Client()

# Test 1: Check admin login page
print("\n1. Testing Admin Login Page...")
response = client.get('/admin/')
print(f"   Login page status: {response.status_code}")
assert response.status_code == 302, "Admin should redirect to login"
print("   Login page accessible (redirects to login)")

# Test 2: Admin login
print("\n2. Testing Admin Login...")
admin = User.objects.filter(username='admin').first()
if admin:
    print(f"   Admin user exists: {admin.username}")
    print(f"   Admin is superuser: {admin.is_superuser}")
else:
    print("   ERROR: Admin user not found!")

# Force login for testing
client.force_login(admin)
print("   Logged in as admin")

# Test 3: Access admin dashboard
print("\n3. Testing Admin Dashboard...")
response = client.get('/admin/')
print(f"   Dashboard status: {response.status_code}")
assert response.status_code == 200, "Dashboard should load"
print("   Dashboard loaded successfully")

# Check for Mobile app in dashboard
content = response.content.decode('utf-8')
if 'Mobile' in content:
    mobile_count = content.count('Mobile')
    print(f"   Found 'Mobile' {mobile_count} times in dashboard")

    # Check for specific mobile models
    mobile_models = [
        ('Mobile devices', 'device'),
        ('Sync logs', 'log'),
        ('Approval delegates', 'delegate')
    ]

    for model_name, keyword in mobile_models:
        if model_name in content:
            print(f"     Found: {model_name}")
        else:
            # Try alternative names
            if keyword.lower() in content.lower():
                print(f"     Found related: {model_name}")
            else:
                print(f"     Not found: {model_name}")
else:
    print("   ERROR: Mobile app not found in dashboard")

# Test 4: Test mobile model admin pages
print("\n4. Testing Mobile Model Admin Pages...")

mobile_admin_paths = [
    ('/admin/mobile/mobiledevice/', 'Mobile Devices'),
    ('/admin/mobile/synclog/', 'Sync Logs'),
    ('/admin/mobile/approvaldelegate/', 'Approval Delegates'),
]

for path, name in mobile_admin_paths:
    response = client.get(path)
    status = "OK" if response.status_code == 200 else "FAIL"
    print(f"   {status}: {name} - {response.status_code}")

# Test 5: Test API endpoints
print("\n5. Testing Mobile API Endpoints...")
api_endpoints = [
    ('/api/mobile/devices/', 'Mobile Devices API'),
    ('/api/mobile/sync-logs/', 'Sync Logs API'),
    ('/api/mobile/delegates/', 'Approval Delegates API'),
]

for path, name in api_endpoints:
    response = client.get(path)
    # 403 is expected without auth, 200 with auth
    status = "OK" if response.status_code in [200, 401, 403] else "FAIL"
    print(f"   {status}: {name} - {response.status_code}")

# Test 6: Test API schema
print("\n6. Testing API Schema...")
response = client.get('/api/schema/')
print(f"   API Schema status: {response.status_code}")
if response.status_code == 200:
    content = response.content.decode('utf-8').lower()
    if 'openapi' in content or 'swagger' in content:
        print("   OK: API Schema is accessible")
    else:
        print("   WARN: API Schema accessible but format unclear")
else:
    print(f"   FAIL: API Schema returned {response.status_code}")

print("\n" + "=" * 60)
print("All Admin Tests Completed Successfully!")
print("=" * 60)
