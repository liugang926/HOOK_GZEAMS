"""
Field Types API Verification Script
Verifies that the API returns correct field types for Asset model
"""
import requests
import json

API_BASE = 'http://localhost:8000/api'

def main():
    print("=" * 60)
    print("FIELD TYPES API VERIFICATION")
    print("=" * 60)

    # Step 1: Login
    print("\n1. Logging in as admin...")
    login_resp = requests.post(
        f'{API_BASE}/auth/login/',
        json={'username': 'admin', 'password': 'admin123'}
    )
    print(f"   Login status: {login_resp.status_code}")

    if login_resp.status_code != 200:
        print(f"   Login failed: {login_resp.text}")
        return

    token = login_resp.json().get('data', {}).get('access_token')
    if not token:
        token = login_resp.json().get('access_token')
    print(f"   Token: {token[:30]}..." if token else "   No token")

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Step 2: Get field definitions
    print("\n2. Fetching field definitions for Asset...")
    fields_resp = requests.get(
        f'{API_BASE}/system/business-objects/fields/?object_code=Asset',
        headers=headers
    )
    print(f"   Fields API status: {fields_resp.status_code}")

    if fields_resp.status_code != 200:
        print(f"   Error: {fields_resp.text}")
        return

    data = fields_resp.json().get('data', {})
    fields = data.get('fields', fields_resp.json().get('fields', []))
    print(f"   Total fields: {len(fields)}")

    # Step 3: Check special fields
    print("\n3. Special Fields Check:")
    print("   " + "=" * 50)

    found = {'images': None, 'attachments': None, 'qr_fields': []}

    for field in fields:
        name = field.get('field_name') or field.get('fieldName') or field.get('code', '')
        ftype = field.get('field_type') or field.get('fieldType', '?')
        name_lower = name.lower()

        # Check images
        if 'image' in name_lower and 'thumbnail' not in name_lower:
            found['images'] = (name, ftype)
            status = "✓ CORRECT" if ftype == 'image' else "✗ WRONG"
            print(f"   {status} - {name}: {ftype}")

        # Check attachments
        if 'attachment' in name_lower:
            found['attachments'] = (name, ftype)
            status = "✓ CORRECT" if ftype == 'file' else "✗ WRONG"
            print(f"   {status} - {name}: {ftype}")

        # Check QR code
        if 'qr' in name_lower and 'code' in name_lower:
            found['qr_fields'].append((name, ftype))
            status = "✓ CORRECT" if ftype == 'qr_code' else "⚠ CHECK"
            print(f"   {status} - {name}: {ftype}")

    # Step 4: Summary
    print("\n   " + "=" * 50)
    print("4. Summary:")

    if found['images']:
        if found['images'][1] == 'image':
            print("   ✓ images field: CORRECT")
        else:
            print(f"   ✗ images field: WRONG ({found['images'][1]})")
    else:
        print("   ✗ images field: NOT FOUND")

    if found['attachments']:
        if found['attachments'][1] == 'file':
            print("   ✓ attachments field: CORRECT")
        else:
            print(f"   ✗ attachments field: WRONG ({found['attachments'][1]})")
    else:
        print("   ✗ attachments field: NOT FOUND")

    if found['qr_fields']:
        all_correct = all(f[1] == 'qr_code' for f in found['qr_fields'])
        print(f"   {'✓' if all_correct else '⚠'} qr code fields: {len(found['qr_fields'])} found")
    else:
        print("   - No QR code fields found")

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    main()
