#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Remaining demo data generation script for GZEAMS.
Creates remaining business objects: Consumables, Maintenance, Inventory, Procurement.

Run with: docker-compose exec -T backend python manage.py shell < create_remaining_demo.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.assets.models import Asset, Supplier, Location
from apps.consumables.models import Consumable, ConsumableCategory
from apps.lifecycle.models import (
    Maintenance, MaintenancePlan, MaintenanceTask,
    PurchaseRequest, AssetReceipt
)
from apps.inventory.models import InventoryTask
from apps.organizations.models import Organization, Department
from datetime import date, timedelta
from decimal import Decimal
import random

User = get_user_model()

# Get existing data
org = Organization.objects.get(code='DEMO')
admin_user = User.objects.filter(username='admin').first()
demo_users = list(User.objects.filter(username__in=['zhang_san', 'li_si', 'wang_wu', 'zhao_liu', 'chen_qi']))
departments = list(Department.objects.filter(organization=org))
assets = list(Asset.objects.filter(organization=org))

print(f"Found {len(assets)} assets, {len(departments)} departments, {len(demo_users)} demo users")

# Get warehouse location
warehouse = Location.objects.filter(organization=org, name='仓库').first()
if not warehouse:
    warehouse, _ = Location.objects.get_or_create(
        organization=org, name='仓库',
        defaults={
            'code': 'WH01',
            'address': '总部大楼1楼',
            'created_by': admin_user
        }
    )

print("\n=== CONSUMABLES (10) ===")
cons_category, _ = ConsumableCategory.objects.get_or_create(
    organization=org, code='C01',
    defaults={'name': '办公耗材', 'created_by': admin_user}
)

consumable_names = ['打印纸', '签字笔', '文件夹', '订书机', '计算器', '鼠标', '键盘', 'U盘', '硬盘', '电池']
for i, name in enumerate(consumable_names, 1):
    consumable, created = Consumable.objects.get_or_create(
        organization=org, code=f'CON{i:04d}',
        defaults={
            'name': name,
            'category': cons_category,
            'unit': random.choice(['个', '包', '盒', '只', '条']),
            'specification': f'规格-{random.randint(1, 5)}',
            'min_stock': random.randint(10, 50),
            'max_stock': random.randint(100, 500),
            'reorder_point': random.randint(20, 100),
            'current_stock': random.randint(50, 500),
            'available_stock': random.randint(50, 500),
            'warehouse': warehouse,
            'purchase_price': Decimal(random.randint(1, 100)),
            'created_by': admin_user,
        }
    )
    if created:
        print(f"Consumable: {consumable.code} - {consumable.name}")

print("\n=== MAINTENANCE (10) ===")
maintenance_types = ['routine', 'corrective', 'preventive']
for i in range(1, 11):
    maintenance_date = date(2024, random.randint(1, 12), random.randint(1, 28))

    maintenance, created = Maintenance.objects.get_or_create(
        organization=org, maintenance_no=f'MNT{i:04d}',
        defaults={
            'asset_code': f'ZC{random.randint(202401, 202412)}{random.randint(1, 99):03d}',
            'maintenance_type': random.choice(maintenance_types),
            'maintenance_date': maintenance_date,
            'technician': random.choice(demo_users).get_full_name(),
            'cost': Decimal(random.randint(100, 5000)),
            'description': f'定期维护保养 #{i}',
            'status': random.choice(['pending', 'in_progress', 'completed']),
            'created_by': admin_user,
        }
    )
    if created:
        print(f"Maintenance: {maintenance.maintenance_no} - {maintenance.maintenance_type}")

print("\n=== MAINTENANCE PLANS (3) ===")
for i in range(1, 4):
    plan, created = MaintenancePlan.objects.get_or_create(
        organization=org, plan_no=f'PLAN{i:03d}',
        defaults={
            'name': f'季度维护计划-{i}',
            'plan_type': 'quarterly',
            'start_date': date(2025, 1, 1),
            'end_date': date(2025, 12, 31),
            'description': f'按季度进行设备维护检查',
            'status': 'active',
            'created_by': admin_user,
        }
    )
    if created:
        print(f"Plan: {plan.plan_no} - {plan.name}")

print("\n=== MAINTENANCE TASKS (6) ===")
for i in range(1, 7):
    task_date = date(2025, random.randint(1, 6), random.randint(1, 28))

    task, created = MaintenanceTask.objects.get_or_create(
        organization=org, task_no=f'TASK{i:04d}',
        defaults={
            'title': f'设备检查任务-{i}',
            'description': f'对指定设备进行全面检查',
            'scheduled_date': task_date,
            'assigned_to': random.choice(demo_users),
            'priority': random.choice(['low', 'medium', 'high']),
            'status': random.choice(['pending', 'in_progress', 'completed']),
            'completed_at': task_date + timedelta(hours=random.randint(1, 8)) if random.random() > 0.5 else None,
            'created_by': admin_user,
        }
    )
    if created:
        print(f"Task: {task.task_no} - {task.title}")

print("\n=== INVENTORY TASKS (6) ===")
for i in range(1, 7):
    task_date = date(2025, random.randint(1, 12), random.randint(1, 28))

    task, created = InventoryTask.objects.get_or_create(
        organization=org, task_code=f'PD2025{i:03d}',
        defaults={
            'task_name': f'季度资产盘点-{i}期',
            'description': f'季度盘点任务',
            'inventory_type': random.choice(['full', 'partial', 'spot']),
            'department': random.choice(departments),
            'planned_date': task_date,
            'status': random.choice(['draft', 'pending', 'in_progress', 'completed']),
            'total_count': random.randint(50, 200),
            'scanned_count': random.randint(0, 200),
            'created_by': admin_user,
        }
    )
    if created:
        print(f"Inventory: {task.task_code} - {task.task_name}")

print("\n=== PURCHASE REQUESTS (8) ===")
request_statuses = ['draft', 'submitted', 'approved', 'processing', 'completed']
for i in range(1, 9):
    request_date = date(2025, random.randint(1, 6), random.randint(1, 28))

    request, created = PurchaseRequest.objects.get_or_create(
        organization=org, request_no=f'CG2025{i:04d}',
        defaults={
            'title': f'采购申请-{random.choice(["电脑", "办公椅", "打印机"])}',
            'applicant': random.choice(demo_users),
            'department': random.choice(departments),
            'request_date': request_date,
            'expected_date': request_date + timedelta(days=30),
            'total_amount': Decimal(random.randint(10000, 100000)),
            'status': random.choice(request_statuses),
            'approved_by': admin_user if random.random() > 0.3 else None,
            'approved_at': request_date + timedelta(days=random.randint(1, 5)) if random.random() > 0.3 else None,
            'reason': f'部门业务需要采购相关设备',
            'created_by': admin_user,
        }
    )
    if created:
        print(f"Request: {request.request_no} - {request.title}")

print("\n=== ASSET RECEIPTS (6) ===")
suppliers = list(Supplier.objects.filter(organization=org))
receipt_statuses = ['pending', 'partial', 'completed']
for i in range(1, 7):
    receipt_date = date(2025, random.randint(1, 6), random.randint(1, 28))

    receipt, created = AssetReceipt.objects.get_or_create(
        organization=org, receipt_no=f'RK2025{i:04d}',
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
print(f"Consumables: {Consumable.objects.filter(organization=org).count()}")
print(f"Maintenances: {Maintenance.objects.filter(organization=org).count()}")
print(f"Maintenance Plans: {MaintenancePlan.objects.filter(organization=org).count()}")
print(f"Maintenance Tasks: {MaintenanceTask.objects.filter(organization=org).count()}")
print(f"Inventory Tasks: {InventoryTask.objects.filter(organization=org).count()}")
print(f"Purchase Requests: {PurchaseRequest.objects.filter(organization=org).count()}")
print(f"Asset Receipts: {AssetReceipt.objects.filter(organization=org).count()}")

print("\n=== Demo data creation completed! ===")
