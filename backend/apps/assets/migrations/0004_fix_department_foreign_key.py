# Generated manually to fix foreign key references to Department model

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


def recreate_asset_pickups_with_correct_fk(connection):
    """Recreate asset_pickups table with correct foreign key to departments."""
    with connection.schema_editor() as schema_editor:
        # Get existing models
        asset_pickups_model = migrations.state.ModelState('assets', 'AssetPickup', [])

        # Note: SQLite doesn't support ALTER CONSTRAINT, so we need to recreate tables
        # This migration recreates the foreign key to point to departments table instead of organizations
        pass


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0003_add_base_model_fields"),
        ("organizations", "0005_add_base_model_fields"),
    ]

    operations = [
        # Recreate AssetPickup with correct foreign key
        migrations.RemoveField(
            model_name='assetpickup',
            name='department',
        ),
        migrations.AddField(
            model_name='assetpickup',
            name='department',
            field=models.ForeignKey(
                help_text='Pickup department',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='department_pickups',
                to='organizations.department',
            ),
        ),
        # Recreate AssetTransfer with correct foreign keys
        migrations.RemoveField(
            model_name='assettransfer',
            name='from_department',
        ),
        migrations.AddField(
            model_name='assettransfer',
            name='from_department',
            field=models.ForeignKey(
                help_text='Source department',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='transfers_out',
                to='organizations.department',
            ),
        ),
        migrations.RemoveField(
            model_name='assettransfer',
            name='to_department',
        ),
        migrations.AddField(
            model_name='assettransfer',
            name='to_department',
            field=models.ForeignKey(
                help_text='Target department',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='transfers_in',
                to='organizations.department',
            ),
        ),
        # Recreate Asset.department with correct foreign key
        migrations.RemoveField(
            model_name='asset',
            name='department',
        ),
        migrations.AddField(
            model_name='asset',
            name='department',
            field=models.ForeignKey(
                blank=True,
                help_text='Using department',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='assets',
                to='organizations.department',
            ),
        ),
    ]
