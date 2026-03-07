#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Final demo data generation script for GZEAMS.
Creates remaining business objects with correct model fields.

Run with: docker-compose exec -T backend python manage.py shell < create_final_demo_v2.py
"""
import os
import django
from datetime import date, timedelta
from decimal import Decimal
import random

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
    warehouse = Location.objects.create(
        organization=org, name='仓库', code='WH01',
        address='总部大楼1楼', created_by=admin_user
    )

print("\n=== MAINTENANCE RECORDS (10) ===")
maintenance_statuses = ['reported', 'assigned', 'in_progress', 'completed', 'verified']
maintenance_priorities = ['low', 'normal', 'high', 'urgent']
for i in range(1, 11):
    maintenance_no = f'MT202501{i:04d}'
    report_time = date(2024, random.randint(1, 12), random.randint(1, 28))

    maintenance, created = Maintenance.objects.get_or_create(
        organization=org, maintenance_no=maintenance_no,
        defaults={
            'asset': random.choice(assets) if assets else None,
            'status': random.choice(maintenance_statuses),
            'priority': random.choice(maintenance_priorities),
            'reporter': random.choice(demo_users),
            'report_time': report_time,
            'fault_description': f'设备故障 #{i}，需要维修处理',
            'technician': random.choice(demo_users),
            'fault_cause': f'故障原因分析 #{i}',
            'repair_method': f'更换零件并调试',
            'repair_result': f'修复完成，设备正常运行',
            'labor_cost': Decimal(random.randint(100, 500)),
            'material_cost': Decimal(random.randint(50, 2000)),
            'total_cost': Decimal(random.randint(200, 3000)),
            'created_by': admin_user,
        }
    )
    if created:
        print(f"Maintenance: {maintenance.maintenance_no} - {maintenance.status}")

print("\n=== MAINTENANCE PLANS (3) ===")
for i in range(1, 4):
    plan_no = f'MP2025{i:03d}'
    plan, created = MaintenancePlan.objects.get_or_create(
        organization=org, plan_no=plan_no,
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
task_statuses = ['pending', 'assigned', 'in_progress', 'completed']
task_priorities = ['low', 'medium', 'high']
for i in range(1, 7):
    task_no = f'MTSK2025{i:04d}'
    scheduled_date = date(2025, random.randint(1, 6), random.randint(1, 28))

    task, created = MaintenanceTask.objects.get_or_create(
        organization=org, task_no=task_no,
        defaults={
            'title': f'设备检查任务-{i}',
            'description': f'对指定设备进行全面检查和维护',
            'scheduled_date': scheduled_date,
            'assigned_to': random.choice(demo_users),
            'priority': random.choice(task_priorities),
            'status': random.choice(task_statuses),
            'completed_at': scheduled_date + timedelta(hours=random.randint(1, 8)) if random.random() > 0.5 else None,
            'created_by': admin_user,
        }
    )
    if created:
        print(f"Task: {task.task_no} - {task.title}")

print("\n=== INVENTORY TASKS (6) ===")
inventory_statuses = ['draft', 'pending', 'in_progress', 'completed', 'cancelled']
inventory_types = ['full', 'partial', 'spot']
for i in range(1, 7):
    task_code = f'PD2025{i:03d}'
    planned_date = date(2025, random.randint(1, 12), random.randint(1, 28))

    task, created = InventoryTask.objects.get_or_create(
        organization=org, task_code=task_code,
        defaults={
            'task_name': f'季度资产盘点-{i}期',
            'description': f'季度盘点任务',
            'inventory_type': random.choice(inventory_types),
            'department': random.choice(departments) if departments else None,
            'planned_date': planned_date,
            'status': random.choice(inventory_statuses),
            'total_count': random.randint(50, 200),
            'scanned_count': random.randint(0, 200),
            'created_by': admin_user,
        }
    )
    if created:
        print(f"Inventory: {task.task_code} - {task.task_name}")

print("\n=== PURCHASE REQUESTS (8) ===")
request_statuses = ['draft', 'submitted', 'approved', 'processing', 'completed', 'rejected']
for i in range(1, 9):
    request_no = f'PR2025{i:04d}'
    request_date = date(2025, random.randint(1, 6), random.randint(1, 28))

    request, created = PurchaseRequest.objects.get_or_create(
        organization=org, request_no=request_no,
        defaults={
            'title': f'采购申请-{random.choice(["电脑", "办公椅", "打印机"])}',
            'status': random.choice(request_statuses),
            'applicant': random.choice(demo_users),
            'department': random.choice(departments) if departments else org,
            'request_date': request_date,
            'expected_date': request_date + timedelta(days=30),
            'reason': f'部门业务需要采购相关设备 #{i}',
            'budget_amount': Decimal(random.randint(10000, 100000)),
            'approved_by': admin_user if random.random() > 0.3 else None,
            'approved_at': request_date + timedelta(days=random.randint(1, 5)) if random.random() > 0.3 else None,
            'created_by': admin_user,
        }
    )
    if created:
        print(f"Request: {request.request_no} - {request.title}")

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
from apps.assets.models import AssetReturn, AssetLoan, AssetPickup, AssetTransfer
from apps.consumables.models import Consumable

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
