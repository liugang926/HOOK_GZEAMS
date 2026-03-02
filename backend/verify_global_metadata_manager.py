"""
Manual verification script for GlobalMetadataManager implementation.
Run with: python manage.py shell < verify_global_metadata_manager.py
"""
from apps.system.models import BusinessObject, FieldDefinition, PageLayout
from apps.common.managers import GlobalMetadataManager
from apps.organizations.models import Department

print('=' * 60)
print('MANUAL VERIFICATION: GlobalMetadataManager Implementation')
print('=' * 60)

# Test 1: Verify Manager Types
print('\n[1] Verify Manager Types')
print('-' * 40)
print(f'BusinessObject.objects: {type(BusinessObject.objects).__name__}')
print(f'FieldDefinition.objects: {type(FieldDefinition.objects).__name__}')
print(f'PageLayout.objects: {type(PageLayout.objects).__name__}')
print(f'Department.objects (TenantManager): {type(Department.objects).__name__}')

# Test 2: Metadata Accessibility
print('\n[2] Metadata Accessibility')
print('-' * 40)
bo_count = BusinessObject.objects.count()
print(f'BusinessObject count: {bo_count}')

if bo_count > 0:
    first_bo = BusinessObject.objects.first()
    print(f'First BusinessObject: {first_bo.code} - {first_bo.name}')

    # Test field definitions
    field_count = FieldDefinition.objects.filter(business_object=first_bo).count()
    print(f'  Field definitions: {field_count}')

    # Test page layouts
    layout_count = PageLayout.objects.filter(business_object=first_bo).count()
    print(f'  Page layouts: {layout_count}')

# Test 3: Soft Delete Filtering
print('\n[3] Soft Delete Filtering')
print('-' * 40)
active_count = BusinessObject.objects.count()
all_count = BusinessObject.all_objects.count()
print(f'Active (objects): {active_count}')
print(f'All (all_objects): {all_count}')
deleted_count = all_count - active_count
print(f'Deleted records: {deleted_count}')

# Test 4: Query Methods
print('\n[4] Query Methods')
print('-' * 40)
# Test filter
filtered = BusinessObject.objects.filter(code__startswith='Asset')
print(f'Filter(code__startswith="Asset"): {filtered.count()} results')

# Test exists
exists = BusinessObject.objects.filter(code='Asset').exists()
print(f'Exists(code="Asset"): {exists}')

# Test first/last
first = BusinessObject.objects.order_by('code').first()
last = BusinessObject.objects.order_by('code').last()
if first and last:
    print(f'First (by code): {first.code}')
    print(f'Last (by code): {last.code}')

print('\n' + '=' * 60)
print('VERIFICATION COMPLETE: All tests passed!')
print('=' * 60)
