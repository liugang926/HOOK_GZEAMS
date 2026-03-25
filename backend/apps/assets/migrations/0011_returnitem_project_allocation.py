from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
        ('assets', '0010_asset_source_traceability'),
    ]

    operations = [
        migrations.AddField(
            model_name='returnitem',
            name='project_allocation',
            field=models.ForeignKey(
                blank=True,
                help_text='Linked project allocation being returned',
                null=True,
                on_delete=models.SET_NULL,
                related_name='return_items',
                to='projects.projectasset',
            ),
        ),
        migrations.AddIndex(
            model_name='returnitem',
            index=models.Index(fields=['organization', 'project_allocation'], name='return_item_organiz_ebd0f4_idx'),
        ),
    ]
