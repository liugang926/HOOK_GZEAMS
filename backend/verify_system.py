import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.system.models import DictionaryItem, SequenceRule
from apps.assets.models import Asset
from apps.consumables.models import Consumable
from apps.system.services import DictionaryService, SequenceService
from django.utils.translation import gettext as _

def verify_system():
    print("=== Verifying System Data ===")
    
    # 1. Verify Dictionary Items (English)
    print("\n[1] Checking Dictionary Items...")
    statuses = DictionaryService.get_items('ASSET_STATUS')
    print(f"ASSET_STATUS count: {len(statuses)}")
    names = [s['name'] for s in statuses]
    print(f"Names: {names}")
    
    expected_names = ['Pending Entry', 'In Use', 'Idle', 'Under Maintenance', 'Lent Out', 'Lost', 'Scrapped']
    missing = [n for n in expected_names if n not in names]
    if missing:
        print(f"FAILED: Missing ASSET_STATUS items: {missing}")
    else:
        print("PASSED: ASSET_STATUS items correct.")

    consumable_statuses = DictionaryService.get_items('CONSUMABLE_STATUS')
    print(f"\nCONSUMABLE_STATUS count: {len(consumable_statuses)}")
    c_names = [s['name'] for s in consumable_statuses]
    print(f"Names: {c_names}")
    
    c_expected = ['Normal', 'Low Stock', 'Out of Stock', 'Discontinued']
    c_missing = [n for n in c_expected if n not in c_names]
    if c_missing:
        print(f"FAILED: Missing CONSUMABLE_STATUS items: {c_missing}")
    else:
        print("PASSED: CONSUMABLE_STATUS items correct.")

    # 2. Verify Sequence Rules
    print("\n[2] Checking Sequence Rules...")
    try:
        rule = SequenceRule.objects.get(code='ASSET_CODE')
        print(f"PASSED: ASSET_CODE rule found (Current: {rule.current_value})")
    except SequenceRule.DoesNotExist:
        print("FAILED: ASSET_CODE rule missing!")

    try:
        rule = SequenceRule.objects.get(code='CONSUMABLE_PURCHASE_NO')
        print(f"PASSED: CONSUMABLE_PURCHASE_NO rule found (Pattern: {rule.pattern})")
    except SequenceRule.DoesNotExist:
        print("FAILED: CONSUMABLE_PURCHASE_NO rule missing!")

    # 3. Verify Services
    print("\n[3] Checking Services...")
    label = DictionaryService.get_label('ASSET_STATUS', 'in_use')
    print(f"Label for 'in_use': {label}")
    if label == 'In Use': # Assuming English default
         print("PASSED: get_label returned English.")
    else:
         print(f"WARNING: get_label returned '{label}' (Expected 'In Use')")

if __name__ == '__main__':
    verify_system()
