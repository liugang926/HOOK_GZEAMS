from django.db import migrations

def seed_data(apps, schema_editor):
    DictionaryType = apps.get_model('system', 'DictionaryType')
    DictionaryItem = apps.get_model('system', 'DictionaryItem')
    SequenceRule = apps.get_model('system', 'SequenceRule')
    
    # 1. Dictionary Types
    dicts = [
        {
            'code': 'CONSUMABLE_STATUS',
            'name': 'Consumable Status',
            'name_en': 'Consumable Status',
            'items': [
                {'code': 'normal', 'label': 'Normal', 'label_en': 'Normal', 'sort_order': 10},
                {'code': 'low_stock', 'label': 'Low Stock', 'label_en': 'Low Stock', 'sort_order': 20, 'color': 'warning'},
                {'code': 'out_of_stock', 'label': 'Out of Stock', 'label_en': 'Out of Stock', 'sort_order': 30, 'color': 'danger'},
                {'code': 'discontinued', 'label': 'Discontinued', 'label_en': 'Discontinued', 'sort_order': 40, 'color': 'secondary'},
            ]
        },
        {
            'code': 'CONSUMABLE_PURCHASE_STATUS',
            'name': 'Purchase Status',
            'name_en': 'Purchase Status',
            'items': [
                {'code': 'draft', 'label': 'Draft', 'label_en': 'Draft', 'sort_order': 10},
                {'code': 'pending', 'label': 'Pending Approval', 'label_en': 'Pending Approval', 'sort_order': 20, 'color': 'warning'},
                {'code': 'approved', 'label': 'Approved', 'label_en': 'Approved', 'sort_order': 30, 'color': 'success'},
                {'code': 'received', 'label': 'Received', 'label_en': 'Received', 'sort_order': 40, 'color': 'info'},
                {'code': 'completed', 'label': 'Completed', 'label_en': 'Completed', 'sort_order': 50, 'color': 'success'},
                {'code': 'cancelled', 'label': 'Cancelled', 'label_en': 'Cancelled', 'sort_order': 60, 'color': 'secondary'},
            ]
        },
        {
            'code': 'CONSUMABLE_ISSUE_STATUS',
            'name': 'Issue Status',
            'name_en': 'Issue Status',
            'items': [
                {'code': 'draft', 'label': 'Draft', 'label_en': 'Draft', 'sort_order': 10},
                {'code': 'pending', 'label': 'Pending Approval', 'label_en': 'Pending Approval', 'sort_order': 20, 'color': 'warning'},
                {'code': 'approved', 'label': 'Approved', 'label_en': 'Approved', 'sort_order': 30, 'color': 'success'},
                {'code': 'issued', 'label': 'Issued', 'label_en': 'Issued', 'sort_order': 40, 'color': 'info'},
                {'code': 'completed', 'label': 'Completed', 'label_en': 'Completed', 'sort_order': 50, 'color': 'success'},
                {'code': 'rejected', 'label': 'Rejected', 'label_en': 'Rejected', 'sort_order': 60, 'color': 'danger'},
            ]
        }
    ]

    for d in dicts:
        dtype, _ = DictionaryType.objects.get_or_create(
            code=d['code'],
            defaults={
                'name': d['name'],
                'name_en': d.get('name_en', ''),
                'is_system': True
            }
        )
        if dtype.name != d['name']:
             dtype.name = d['name']
             dtype.name_en = d.get('name_en', '')
             dtype.save()
             
        for item in d['items']:
            obj, created = DictionaryItem.objects.get_or_create(
                dictionary_type=dtype,
                code=item['code'],
                defaults={
                    'name': item['label'],
                    'name_en': item.get('label_en', ''),
                    'sort_order': item['sort_order'],
                    'color': item.get('color', 'default'),
                    'is_active': True
                }
            )
            # Update name if it matches old Chinese or just enforce English
            if not created and obj.name != item['label']:
                obj.name = item['label']
                obj.name_en = item.get('label_en', '')
                obj.save()

    # 2. Sequence Rules
    sequences = [
        {
            'code': 'CONSUMABLE_PURCHASE_NO',
            'name': 'Consumable Purchase No',
            'prefix': 'CP',
            'pattern': '{PREFIX}{YYYY}{MM}{SEQ}',
            'seq_length': 4,
            'current_value': 0,
            'reset_period': 'month'
        },
        {
            'code': 'CONSUMABLE_ISSUE_NO',
            'name': 'Consumable Issue No',
            'prefix': 'CI',
            'pattern': '{PREFIX}{YYYY}{MM}{SEQ}',
            'seq_length': 4,
            'current_value': 0,
            'reset_period': 'month'
        }
    ]

    for seq in sequences:
        SequenceRule.objects.get_or_create(
            code=seq['code'],
            defaults={
                'name': seq['name'],
                'prefix': seq['prefix'],
                'pattern': seq['pattern'],
                'seq_length': seq['seq_length'],
                'current_value': seq['current_value'],
                'reset_period': seq['reset_period']
            }
        )

def reverse_seed_data(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('consumables', '0002_add_base_model_fields'),
        ('system', '0004_public_models'),
    ]

    operations = [
        migrations.RunPython(seed_data, reverse_seed_data),
    ]
