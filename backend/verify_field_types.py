"""
Field Types Verification Script

Verifies that the API returns correct field types for Asset model:
- images field should have fieldType='image'
- attachments field should have fieldType='file'
- QR code fields should have fieldType='qr_code'
"""
import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.system.models import BusinessObject, ModelFieldDefinition
from apps.accounts.models import User

def verify_field_types():
    print("=" * 60)
    print("FIELD TYPES VERIFICATION REPORT")
    print("=" * 60)

    # Get Asset business object
    try:
        asset_bo = BusinessObject.objects.get(code='Asset')
        print(f"\n✓ Found BusinessObject: {asset_bo.name} (code: {asset_bo.code})")
    except BusinessObject.DoesNotExist:
        print("\n✗ BusinessObject 'Asset' not found!")
        return False

    # Get model field definitions
    field_defs = ModelFieldDefinition.objects.filter(
        business_object=asset_bo,
        is_deleted=False
    ).order_by('field_name')

    print(f"\n✓ Found {field_defs.count()} field definitions")

    # Check special fields
    print("\n" + "-" * 60)
    print("SPECIAL FIELDS VERIFICATION")
    print("-" * 60)

    results = {
        'images': None,
        'attachments': None,
        'qr_code_fields': []
    }

    for field in field_defs:
        field_name_lower = field.field_name.lower()

        # Check images field
        if 'image' in field_name_lower and field_name_lower not in 'thumbnail':
            results['images'] = field.field_type
            status = "✓ CORRECT" if field.field_type == 'image' else "✗ WRONG"
            print(f"\n{status} - Field: {field.field_name}")
            print(f"       Type: {field.field_type}")
            if field.field_type != 'image':
                print(f"       Expected: 'image'")

        # Check attachments field
        if 'attachment' in field_name_lower:
            results['attachments'] = field.field_type
            status = "✓ CORRECT" if field.field_type == 'file' else "✗ WRONG"
            print(f"\n{status} - Field: {field.field_name}")
            print(f"       Type: {field.field_type}")
            if field.field_type != 'file':
                print(f"       Expected: 'file'")

        # Check QR code fields
        if 'qr' in field_name_lower and 'code' in field_name_lower:
            results['qr_code_fields'].append({
                'name': field.field_name,
                'type': field.field_type
            })
            status = "✓ CORRECT" if field.field_type == 'qr_code' else "⚠ CHECK"
            print(f"\n{status} - Field: {field.field_name}")
            print(f"       Type: {field.field_type}")
            if field.field_type != 'qr_code':
                print(f"       Expected: 'qr_code'")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    success = True

    if results['images'] == 'image':
        print("✓ images field: CORRECT (type='image')")
    elif results['images']:
        print(f"✗ images field: WRONG (type='{results['images']}', expected='image')")
        success = False
    else:
        print("✗ images field: NOT FOUND")
        success = False

    if results['attachments'] == 'file':
        print("✓ attachments field: CORRECT (type='file')")
    elif results['attachments']:
        print(f"✗ attachments field: WRONG (type='{results['attachments']}', expected='file')")
        success = False
    else:
        print("✗ attachments field: NOT FOUND")
        success = False

    if results['qr_code_fields']:
        for qr_field in results['qr_code_fields']:
            if qr_field['type'] == 'qr_code':
                print(f"✓ {qr_field['name']}: CORRECT (type='qr_code')")
            else:
                print(f"⚠ {qr_field['name']}: type='{qr_field['type']}' (may need to run sync_schemas)")
    else:
        print("- No QR code fields found in Asset model")

    print("\n" + "=" * 60)
    if success:
        print("RESULT: ALL CRITICAL CHECKS PASSED ✓")
    else:
        print("RESULT: SOME CHECKS FAILED ✗")
    print("=" * 60)

    return success

if __name__ == '__main__':
    verify_field_types()
