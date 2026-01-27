from django.db import migrations

def update_sequence_rules(apps, schema_editor):
    SequenceRule = apps.get_model('system', 'SequenceRule')
    
    # 1. Update/Clean existing rules to English prefixes
    # TRANSFER_NO: DB -> TF
    SequenceRule.objects.filter(code='TRANSFER_NO').update(
        name='Transfer Order No',
        prefix='TF',
        description='Asset Transfer Order Numbering'
    )
    
    # PICKUP_NO: LY -> PK
    SequenceRule.objects.filter(code='PICKUP_NO').update(
        name='Pickup Order No',
        prefix='PK',
        description='Asset Pickup Order Numbering'
    )
    
    # 2. Seed missing rules
    # RETURN_NO: RT
    SequenceRule.objects.get_or_create(
        code='RETURN_NO',
        defaults={
            'name': 'Return Order No',
            'prefix': 'RT',
            'pattern': '{PREFIX}{YYYY}{MM}{SEQ}',
            'seq_length': 4,
            'reset_period': 'monthly',
            'description': 'Asset Return Order Numbering',
            'current_value': 0,
            'is_active': True,
        }
    )
    
    # LOAN_NO: LN
    SequenceRule.objects.get_or_create(
        code='LOAN_NO',
        defaults={
            'name': 'Loan Order No',
            'prefix': 'LN',
            'pattern': '{PREFIX}{YYYY}{MM}{SEQ}',
            'seq_length': 4,
            'reset_period': 'monthly',
            'description': 'Asset Loan Order Numbering',
            'current_value': 0,
            'is_active': True,
        }
    )
    
    # Update names for existing ASSET_CODE, SCRAP_NO, INVENTORY_NO to English
    SequenceRule.objects.filter(code='ASSET_CODE').update(name='Asset Code', description='Asset Card Code Rule')
    SequenceRule.objects.filter(code='SCRAP_NO').update(name='Scrap Order No', prefix='SC', description='Asset Scrap Order Numbering')
    SequenceRule.objects.filter(code='INVENTORY_NO').update(name='Inventory Task No', prefix='IV', description='Inventory Task Numbering')


def reverse_update(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('system', '0006_seed_operation_status'),
    ]

    operations = [
        migrations.RunPython(update_sequence_rules, reverse_update),
    ]
