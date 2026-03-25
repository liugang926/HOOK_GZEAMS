from django.db import migrations


LINE_ITEM_NAME_FIXES = {
    "PickupItem": ("领用明细", "Pickup Item"),
    "TransferItem": ("调拨明细", "Transfer Item"),
    "ReturnItem": ("归还明细", "Return Item"),
    "LoanItem": ("借用明细", "Loan Item"),
}


def apply_name_fixes(apps, schema_editor):
    BusinessObject = apps.get_model("system", "BusinessObject")

    for code, (name, name_en) in LINE_ITEM_NAME_FIXES.items():
        BusinessObject.objects.filter(code=code).update(name=name, name_en=name_en)


class Migration(migrations.Migration):

    dependencies = [
        ("system", "0040_realign_line_item_display_tiers"),
    ]

    operations = [
        migrations.RunPython(apply_name_fixes, migrations.RunPython.noop),
    ]
