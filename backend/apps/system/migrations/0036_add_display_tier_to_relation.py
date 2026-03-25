from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0035_menugroup_menuentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='objectrelationdefinition',
            name='display_tier',
            field=models.CharField(
                choices=[
                    ('L1', 'Line Item (Inline in Details)'),
                    ('L2', 'Business Related (Default)'),
                    ('L3', 'Extended Related (Collapsed)'),
                ],
                db_comment='Display tier: L1=inline detail, L2=related tab, L3=collapsed',
                default='L2',
                max_length=2,
            ),
        ),
    ]
