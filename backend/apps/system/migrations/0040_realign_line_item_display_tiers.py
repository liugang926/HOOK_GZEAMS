from django.db import migrations


LINE_ITEM_RELATION_CODES = [
    'pickup_items',
    'transfer_items',
    'return_items',
    'loan_items',
]


def realign_line_item_display_tiers(apps, schema_editor):
    ObjectRelationDefinition = apps.get_model('system', 'ObjectRelationDefinition')

    # through_line_item is a peer/derived relation and should remain in Related,
    # not render as an L1 master-detail table.
    ObjectRelationDefinition.objects.filter(
        relation_kind='through_line_item',
    ).update(display_tier='L2')

    # True line-item master/detail relations are direct_fk relations from the
    # operation document to its *Item rows.
    ObjectRelationDefinition.objects.filter(
        relation_kind='direct_fk',
        relation_code__in=LINE_ITEM_RELATION_CODES,
    ).update(
        display_tier='L1',
        display_mode='inline_editable',
    )


def reverse_realign_line_item_display_tiers(apps, schema_editor):
    ObjectRelationDefinition = apps.get_model('system', 'ObjectRelationDefinition')

    ObjectRelationDefinition.objects.filter(
        relation_kind='through_line_item',
    ).update(display_tier='L1')

    ObjectRelationDefinition.objects.filter(
        relation_kind='direct_fk',
        relation_code__in=LINE_ITEM_RELATION_CODES,
    ).update(display_tier='L1')


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0039_seed_line_item_objects'),
    ]

    operations = [
        migrations.RunPython(realign_line_item_display_tiers, reverse_realign_line_item_display_tiers),
    ]
