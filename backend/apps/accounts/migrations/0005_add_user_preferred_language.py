"""
Add preferred_language field to User model for i18n support.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_add_base_model_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='preferred_language',
            field=models.CharField(
                db_comment='User preferred language code (e.g., zh-CN, en-US)',
                default='zh-CN',
                max_length=10,
            ),
        ),
    ]
