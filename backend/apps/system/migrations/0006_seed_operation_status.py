"""
Data migration to seed operation status dictionaries.

This migration adds dictionary types for:
- PICKUP_STATUS: Asset pickup order statuses
- TRANSFER_STATUS: Asset transfer order statuses
- RETURN_STATUS: Asset return order statuses
- LOAN_STATUS: Asset loan order statuses
"""
from django.db import migrations


def seed_operation_status_dictionaries(apps, schema_editor):
    """Seed operation status dictionaries."""
    DictionaryType = apps.get_model('system', 'DictionaryType')
    DictionaryItem = apps.get_model('system', 'DictionaryItem')

    def create_dict_type(code, name, name_en, description, sort_order):
        dict_type, _ = DictionaryType.objects.get_or_create(
            code=code,
            organization_id=None,
            defaults={
                'name': name,
                'name_en': name_en,
                'description': description,
                'is_system': True,
                'is_active': True,
                'sort_order': sort_order,
            }
        )
        # Ensure name is English
        if dict_type.name != name:
            dict_type.name = name
            dict_type.save()
        return dict_type

    def create_items(dict_type, items):
        for item_data in items:
            obj, created = DictionaryItem.objects.get_or_create(
                dictionary_type=dict_type,
                code=item_data['code'],
                organization_id=None,
                defaults={
                    'name': item_data['name'],
                    'name_en': item_data['name_en'],
                    'color': item_data.get('color', ''),
                    'is_default': item_data.get('is_default', False),
                    'is_active': True,
                    'sort_order': item_data['sort_order'],
                }
            )
            # Update name if it matches old or just enforce English
            if not created and obj.name != item_data['name']:
                obj.name = item_data['name']
                obj.save()

    # =========================================================================
    # PICKUP_STATUS - Pickup Order Status
    # =========================================================================
    pickup_status_type = create_dict_type(
        'PICKUP_STATUS', 'Pickup Order Status', 'Pickup Order Status',
        'Status of asset pickup orders', 10
    )
    create_items(pickup_status_type, [
        {'code': 'draft', 'name': 'Draft', 'name_en': 'Draft', 'color': '#909399', 'is_default': True, 'sort_order': 1},
        {'code': 'pending', 'name': 'Pending Approval', 'name_en': 'Pending Approval', 'color': '#E6A23C', 'sort_order': 2},
        {'code': 'approved', 'name': 'Approved', 'name_en': 'Approved', 'color': '#67C23A', 'sort_order': 3},
        {'code': 'rejected', 'name': 'Rejected', 'name_en': 'Rejected', 'color': '#F56C6C', 'sort_order': 4},
        {'code': 'completed', 'name': 'Completed', 'name_en': 'Completed', 'color': '#409EFF', 'sort_order': 5},
        {'code': 'cancelled', 'name': 'Cancelled', 'name_en': 'Cancelled', 'color': '#909399', 'sort_order': 6},
    ])

    # =========================================================================
    # TRANSFER_STATUS - Transfer Order Status
    # =========================================================================
    transfer_status_type = create_dict_type(
        'TRANSFER_STATUS', 'Transfer Order Status', 'Transfer Order Status',
        'Status of asset transfer orders', 11
    )
    create_items(transfer_status_type, [
        {'code': 'draft', 'name': 'Draft', 'name_en': 'Draft', 'color': '#909399', 'is_default': True, 'sort_order': 1},
        {'code': 'pending', 'name': 'Pending Approval', 'name_en': 'Pending Approval', 'color': '#E6A23C', 'sort_order': 2},
        {'code': 'out_approved', 'name': 'Out Department Approved', 'name_en': 'Out Department Approved', 'color': '#67C23A', 'sort_order': 3},
        {'code': 'approved', 'name': 'Both Approved', 'name_en': 'Both Approved', 'color': '#67C23A', 'sort_order': 4},
        {'code': 'rejected', 'name': 'Rejected', 'name_en': 'Rejected', 'color': '#F56C6C', 'sort_order': 5},
        {'code': 'completed', 'name': 'Completed', 'name_en': 'Completed', 'color': '#409EFF', 'sort_order': 6},
        {'code': 'cancelled', 'name': 'Cancelled', 'name_en': 'Cancelled', 'color': '#909399', 'sort_order': 7},
    ])

    # =========================================================================
    # RETURN_STATUS - Return Order Status
    # =========================================================================
    return_status_type = create_dict_type(
        'RETURN_STATUS', 'Return Order Status', 'Return Order Status',
        'Status of asset return orders', 12
    )
    create_items(return_status_type, [
        {'code': 'draft', 'name': 'Draft', 'name_en': 'Draft', 'color': '#909399', 'is_default': True, 'sort_order': 1},
        {'code': 'pending', 'name': 'Pending Confirmation', 'name_en': 'Pending Confirmation', 'color': '#E6A23C', 'sort_order': 2},
        {'code': 'confirmed', 'name': 'Confirmed', 'name_en': 'Confirmed', 'color': '#67C23A', 'sort_order': 3},
        {'code': 'completed', 'name': 'Completed', 'name_en': 'Completed', 'color': '#409EFF', 'sort_order': 4},
        {'code': 'cancelled', 'name': 'Cancelled', 'name_en': 'Cancelled', 'color': '#909399', 'sort_order': 5},
    ])

    # =========================================================================
    # LOAN_STATUS - Loan Order Status
    # =========================================================================
    loan_status_type = create_dict_type(
        'LOAN_STATUS', 'Loan Order Status', 'Loan Order Status',
        'Status of asset loan orders', 13
    )
    create_items(loan_status_type, [
        {'code': 'draft', 'name': 'Draft', 'name_en': 'Draft', 'color': '#909399', 'is_default': True, 'sort_order': 1},
        {'code': 'pending', 'name': 'Pending Approval', 'name_en': 'Pending Approval', 'color': '#E6A23C', 'sort_order': 2},
        {'code': 'approved', 'name': 'Approved', 'name_en': 'Approved', 'color': '#67C23A', 'sort_order': 3},
        {'code': 'rejected', 'name': 'Rejected', 'name_en': 'Rejected', 'color': '#F56C6C', 'sort_order': 4},
        {'code': 'borrowed', 'name': 'Borrowed', 'name_en': 'Borrowed', 'color': '#409EFF', 'sort_order': 5},
        {'code': 'overdue', 'name': 'Overdue', 'name_en': 'Overdue', 'color': '#F56C6C', 'sort_order': 6},
        {'code': 'returned', 'name': 'Returned', 'name_en': 'Returned', 'color': '#67C23A', 'sort_order': 7},
        {'code': 'cancelled', 'name': 'Cancelled', 'name_en': 'Cancelled', 'color': '#909399', 'sort_order': 8},
    ])


def reverse_seed(apps, schema_editor):
    """Reverse the seeding (optional, for rollback)."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0005_seed_initial_data'),
    ]

    operations = [
        migrations.RunPython(seed_operation_status_dictionaries, reverse_seed),
    ]
