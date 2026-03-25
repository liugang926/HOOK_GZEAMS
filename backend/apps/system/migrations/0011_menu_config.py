# Generated manually for dynamic menu system

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0010_tabconfig_usercolumnpreference'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessobject',
            name='menu_config',
            field=models.JSONField(default=dict, blank=True, db_comment='Menu configuration (icon, group, order, show_in_menu)'),
        ),
    ]
