#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Final demo data generation script for GZEAMS.
Creates remaining AssetReceipts with correct model fields.

Run with: docker-compose exec -T backend python manage.py shell < create_remaining_final_v6.py
"""
import os
import django
from datetime import date, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.assets.models import Supplier
from apps.lifecycle.models import PurchaseRequest, AssetReceipt
from apps.organizations.models import Organization

User = get_user_model()

# Get existing data
org = Organization.objects.get(code='DEMO')
admin_user = User.objects.filter(username='admin').first()
demo_users = list(User.objects.filter(username__in=['zhang_san', 'li_si', 'wang_wu', 'zhao_liu', 'chen_qi']))
suppliers = list(Supplier.objects.filter(organization=org))
purchase_requests = list(PurchaseRequest.objects.filter(organization=org))

print(f"Found {len(demo_users)} demo users, {len(suppliers)} suppliers, {len(purchase_requests)} PRs")

print("\n=== ASSET RECEIPTS (6) ===")
receipt_statuses = ['draft', 'partial', 'completed', 'rejected']
for i in range(1, 7):
    receipt_date = date(2025, random.randint(1, 6), random.randint(1, 28))

    # Get supplier name or use default
    supplier_name = random.choice(suppliers).name if suppliers else f'供应商{i}'

    receipt, created = AssetReceipt.objects.get_or_create(
        organization=org, receipt_date=receipt_date, supplier=supplier_name,
        defaults={
            'status': random.choice(receipt_statuses),
            'receipt_type': 'purchase',
            'receiver': random.choice(demo_users),
            'inspector': admin_user if random.random() > 0.3 else None,
            'inspection_result': f'货物验收合格，数量正确，质量符合要求' if random.random() > 0.2 else f'部分货物需要退换',
            'passed_at': receipt_date if random.random() > 0.3 else None,
            'delivery_no': f'DEL{2025}{i:04d}',
            'purchase_request': random.choice(purchase_requests) if purchase_requests else None,
            'remark': f'入库单据 #{i}',
            'created_by': admin_user,
        }
    )
    if created:
        print(f"Receipt: {receipt.receipt_no} - {receipt.supplier} ({receipt.status})")

print("\n=== FINAL SUMMARY ===")
from apps.assets.models import AssetReturn, AssetLoan, AssetPickup, AssetTransfer, Asset
from apps.consumables.models import Consumable
from apps.lifecycle.models import Maintenance, MaintenancePlan, MaintenanceTask
from apps.inventory.models import InventoryTask

print(f"Assets: {Asset.objects.filter(organization=org).count()}")
print(f"Pickups: {AssetPickup.objects.filter(organization=org).count()}")
print(f"Transfers: {AssetTransfer.objects.filter(organization=org).count()}")
print(f"Returns: {AssetReturn.objects.filter(organization=org).count()}")
print(f"Loans: {AssetLoan.objects.filter(organization=org).count()}")
print(f"Consumables: {Consumable.objects.filter(organization=org).count()}")
print(f"Maintenances: {Maintenance.objects.filter(organization=org).count()}")
print(f"Maintenance Plans: {MaintenancePlan.objects.filter(organization=org).count()}")
print(f"Maintenance Tasks: {MaintenanceTask.objects.filter(organization=org).count()}")
print(f"Inventory Tasks: {InventoryTask.objects.filter(organization=org).count()}")
print(f"Purchase Requests: {PurchaseRequest.objects.filter(organization=org).count()}")
print(f"Asset Receipts: {AssetReceipt.objects.filter(organization=org).count()}")

print("\n=== All demo data creation completed! ===")
