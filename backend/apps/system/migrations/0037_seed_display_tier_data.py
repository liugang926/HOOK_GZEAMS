"""
Seed migration: set display_tier='L1' for all through_line_item relations.

These are master-detail line items that should appear inline in the Details tab,
not mixed with peer relations in the Related tab.
"""
from django.db import migrations


def seed_display_tier(apps, schema_editor):
    ObjectRelationDefinition = apps.get_model('system', 'ObjectRelationDefinition')
    ObjectRelationDefinition.objects.filter(
        relation_kind='through_line_item',
    ).update(display_tier='L1')


def reverse_seed(apps, schema_editor):
    ObjectRelationDefinition = apps.get_model('system', 'ObjectRelationDefinition')
    ObjectRelationDefinition.objects.filter(
        relation_kind='through_line_item',
    ).update(display_tier='L2')


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0036_add_display_tier_to_relation'),
    ]

    operations = [
        migrations.RunPython(seed_display_tier, reverse_seed),
    ]
