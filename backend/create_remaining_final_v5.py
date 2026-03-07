#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Final demo data generation script for GZEAMS.
Creates remaining business objects with correct model fields.

Run with: docker-compose exec -T backend python manage.py shell < create_remaining_final_v5.py
"""
import os
import django
from datetime import date, timedelta
from decimal import Decimal
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.assets.models import Asset, Supplier
from apps.lifecycle.models import PurchaseRequest, AssetReceipt
from apps.organizations.models import Organization

User = get_user_model()

# Get existing data
org = Organization.objects.get(code='DEMO')
admin_user = User.objects.filter(username='admin').first()
demo_users = list(User.objects.filter(username__in=['zhang_san', 'li_si', 'wang_wu', 'zhao_liu', 'chen_qi']))

print(f"Found {len(demo_users)} demo users")

print("\n=== PURCHASE REQUESTS (8) ===")
request_statuses = ['draft', 'submitted', 'approved', 'processing', 'completed', 'rejected']
for i in range(1, 9):
    request_no = f'PR2025{i:04d}'
    request_date = date(2025, random.randint(1, 6), random.randint(1, 28))

    request, created = PurchaseRequest.objects.get_or_create(
        organization=org, request_no=request_no,
        defaults={
            'status': random.choice(request_statuses),
            'applicant': random.choice(demo_users),
            'department': org,  # Use the main organization as department
            'request_date': request_date,
            'expected_date': request_date + timedelta(days=30),
            'reason': f'部门业务需要采购相关设备: {random.choice(["电脑", "办公椅", "打印机"])} #{i}',
            'budget_amount': Decimal(random.randint(10000, 100000)),
            'approved_by': admin_user if random.random() > 0.3 else None,
            'approved_at': request_date + timedelta(days=random.randint(1, 5)) if random.random() > 0.3 else None,
            'created_by': admin_user,
        }
    )
    if created:
        print(f"Request: {request.request_no} - {request.status}")

print("\n=== ASSET RECEIPTS (6) ===")
suppliers = list(Supplier.objects.filter(organization=org))
receipt_statuses = ['pending', 'partial', 'completed']
for i in range(1, 7):
    receipt_no = f'AR2025{i:04d}'
    receipt_date = date(2025, random.randint(1, 6), random.randint(1, 28))

    receipt, created = AssetReceipt.objects.get_or_create(
        organization=org, receipt_no=receipt_no,
        defaults={
            'supplier': random.choice(suppliers) if suppliers else None,
            'receipt_date': receipt_date,
            'total_amount': Decimal(random.randint(20000, 100000)),
            'quantity': random.randint(5, 20),
            'status': random.choice(receipt_statuses),
            'received_by': random.choice(demo_users),
            'inspected_by': admin_user if random.random() > 0.3 else None,
            'warehouse_location': '仓库',
            'remarks': f'货物验收合格，入库',
            'created_by': admin_user,
        }
    )
    if created and receipt.supplier:
        print(f"Receipt: {receipt.receipt_no} - {receipt.supplier.name}")

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

print("\n=== Demo data creation completed! ===")
