# Generated manually for QR code field length increase

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0002_alter_inventoryscan_scanned_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventoryscan',
            name='qr_code',
            field=models.CharField(db_index=True, help_text='Scanned QR code', max_length=500),
        ),
    ]
