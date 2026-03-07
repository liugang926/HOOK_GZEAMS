"""
Demo Data Generator for GZEAMS

Creates comprehensive demo data for all business objects.
Run with: python manage.py shell < create_demo_data.py
"""
import os
import sys
import django
import random
from datetime import datetime, timedelta, date
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.organizations.models import Organization, Department
from apps.assets.models import (
    Asset, AssetCategory, Supplier, Location, AssetStatusLog,
    AssetPickup, PickupItem, AssetTransfer, TransferItem,
    AssetReturn, ReturnItem, AssetLoan, LoanItem
)
from apps.consumables.models import Consumable, ConsumableCategory, ConsumableStock, ConsumableIssue
from apps.it_assets.models import ITAsset, ITSoftware, ITSoftwareLicense, ITLicenseAllocation, ITMaintenanceRecord, ConfigurationChange
from apps.maintenance.models import Maintenance, MaintenancePlan, MaintenanceTask
from apps.licenses.models import SoftwareLicense, LicenseAllocation, Software
from apps.inventory.models import InventoryTask, InventorySnapshot, InventoryItem
from apps.procurement.models import PurchaseRequest, AssetReceipt
from apps.finance.models import FinanceVoucher, VoucherTemplate
from apps.insurance.models import InsurancePolicy, ClaimRecord, InsuranceCompany, InsuredAsset, PremiumPayment, PolicyRenewal
from apps.leasing.models import LeasingContract, LeaseItem, LeaseReturn, LeaseExtension, RentPayment
from apps.workflows.models import WorkflowDefinition, WorkflowInstance, WorkflowTask, WorkflowTemplate, WorkflowApproval, WorkflowOperationLog
from apps.accounts.models import User
from apps.system.models import BusinessObject

User = get_user_model()

# ============================================================
# CONFIGURATION
# ============================================================

# Get or create organization and user
org, _ = Organization.objects.get_or_create(
    code='DEMO',
    defaults={
        'name': 'Demo Company',
        'org_type': 'company',
        'is_active': True,
        'contact_person': 'Admin',
        'contact_phone': '400-123-4567',
        'email': 'admin@demo.com',
        'address': '北京市朝阳区建国路88号'
    }
)

# Get admin user
admin_user = User.objects.filter(username='admin').first()

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def random_date(start_date, end_date):
    """Generate random date between start and end."""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

def random_decimal(min_val, max_val):
    """Generate random decimal."""
    return Decimal(str(round(random.uniform(min_val, max_val), 2)))

# ============================================================
# SYSTEM MANAGEMENT - Departments
# ============================================================

print("Creating Departments...")

departments_data = [
    {'code': 'HQ', 'name': '总部', 'level': 0},
    {'code': 'TECH', 'name': '技术部', 'level': 1, 'parent': 'HQ'},
    {'code': 'SALES', 'name': '销售部', 'level': 1, 'parent': 'HQ'},
    {'code': 'HR', 'name': '人力资源部', 'level': 1, 'parent': 'HQ'},
    {'code': 'FINANCE', 'name': '财务部', 'level': 1, 'parent': 'HQ'},
    {'code': 'BACKEND', 'name': '后端组', 'level': 2, 'parent': 'TECH'},
    {'code': 'FRONTEND', 'name': '前端组', 'level': 2, 'parent': 'TECH'},
    {'code': 'SALES_NORTH', 'name': '华北区', 'level': 2, 'parent': 'SALES'},
    {'code': 'SALES_SOUTH', 'name': '华南区', 'level': 2, 'parent': 'SALES'},
]

dept_map = {}
for dept_data in departments_data:
    parent_code = dept_data.pop('parent', None)
    parent = dept_map.get(parent_code) if parent_code else None

    dept, created = Department.objects.get_or_create(
        organization=org,
        code=dept_data['code'],
        defaults={
            **dept_data,
            'created_by': admin_user
        }
    )
    if created:
        if parent:
            dept.parent = parent
            dept.save()
    dept_map[dept_data['code']] = dept
    print(f"  - {dept.code}: {dept.name}")

# Create demo users
print("\nCreating Demo Users...")
users_data = [
    {'username': 'zhang_san', 'first_name': '张', 'last_name': '三', 'dept': 'TECH'},
    {'username': 'li_si', 'first_name': '李', 'last_name': '四', 'dept': 'SALES'},
    {'username': 'wang_wu', 'first_name': '王', 'last_name': '五', 'dept': 'FINANCE'},
    {'username': 'zhao_liu', 'first_name': '赵', 'last_name': '六', 'dept': 'HR'},
    {'username': 'chen_qi', 'first_name': '陈', 'last_name': '七', 'dept': 'BACKEND'},
    {'username': 'zhou_ba', 'first_name': '周', 'last_name': '八', 'dept': 'FRONTEND'},
    {'username': 'wu_jiu', 'first_name': '吴', 'last_name': '九', 'dept': 'SALES_NORTH'},
    {'username': 'zheng_shi', 'first_name': '郑', 'last_name': '十', 'dept': 'SALES_SOUTH'},
]

demo_users = {}
for user_data in users_data:
    dept_code = user_data.pop('dept', None)
    username = user_data['username']

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            **user_data,
            'email': f'{username}@demo.com',
            'is_active': True,
        }
    )
    if created:
        user.set_password('demo123')
        user.save()

    # Link to department
    if dept_code and dept_map.get(dept_code):
        from apps.organizations.models import UserDepartment
        UserDepartment.objects.get_or_create(
            user=user,
            organization=org,
            department=dept_map[dept_code],
            defaults={'is_primary': True, 'position': user_data.get('last_name', '')}
        )

    demo_users[username] = user
    print(f"  - {user.username}: {user.get_full_name()}")

# ============================================================
# ASSET MANAGEMENT
# ============================================================

print("\n=== ASSET MANAGEMENT ===")

# Asset Categories
print("Creating Asset Categories...")
categories_data = [
    {'code': '2001', 'name': '电子设备', 'depreciation_method': 'straight_line', 'useful_life': 60},
    {'code': '2001.01', 'name': '计算机设备', 'parent': '2001', 'useful_life': 60},
    {'code': '2001.02', 'name': '网络设备', 'parent': '2001', 'useful_life': 60},
    {'code': '2002', 'name': '办公家具', 'depreciation_method': 'straight_line', 'useful_life': 120},
    {'code': '2003', 'name': '车辆', 'depreciation_method': 'straight_line', 'useful_life': 48},
    {'code': '2004', 'name': '其他设备', 'depreciation_method': 'straight_line', 'useful_life': 36},
]

category_map = {}
for cat_data in categories_data:
    parent_code = cat_data.pop('parent', None)
    parent = category_map.get(parent_code) if parent_code else None

    defaults = {
        'name': cat_data['name'],
        'organization': org,
        'created_by': admin_user,
    }
    if 'depreciation_method' in cat_data:
        defaults['depreciation_method'] = cat_data['depreciation_method']
    if 'useful_life' in cat_data:
        defaults['default_useful_life'] = cat_data['useful_life']

    category, created = AssetCategory.objects.get_or_create(
        organization=org,
        code=cat_data['code'],
        defaults=defaults
    )
    if created and parent:
        category.parent = parent
        category.save()
    category_map[cat_data['code']] = category
    print(f"  - {category.code}: {category.full_name}")

# Locations
print("Creating Locations...")
locations_data = [
    {'name': '总部大楼', 'type': 'building'},
    {'name': 'A座', 'type': 'building', 'parent': '总部大楼'},
    {'name': 'B座', 'type': 'building', 'parent': '总部大楼'},
    {'name': '3楼', 'type': 'floor', 'parent': 'A座'},
    {'name': '5楼', 'type': 'floor', 'parent': 'A座'},
    {'name': '会议室301', 'type': 'room', 'parent': '3楼'},
    {'name': '会议室302', 'type': 'room', 'parent': '3楼'},
    {'name': '开放办公区', 'type': 'area', 'parent': '5楼'},
    {'name': '仓库', 'type': 'warehouse', 'parent': 'B座'},
]

location_map = {}
for loc_data in locations_data:
    parent_name = loc_data.pop('parent', None)
    parent = location_map.get(parent_name) if parent_name else None

    location, created = Location.objects.get_or_create(
        organization=org,
        name=loc_data['name'],
        defaults={
            **loc_data,
            'created_by': admin_user,
        }
    )
    if created and parent:
        location.parent = parent
        location.save()
    location_map[loc_data['name']] = location
    print(f"  - {location.path}")

# Suppliers
print("Creating Suppliers...")
suppliers_data = [
    {'code': 'SUP001', 'name': '北京科技设备有限公司', 'contact': '张经理', 'phone': '010-12345678', 'email': 'zhang@tech.com'},
    {'code': 'SUP002', 'name': '上海办公家具有限公司', 'contact': '李经理', 'phone': '021-87654321', 'email': 'li@furniture.com'},
    {'code': 'SUP003', 'name': '深圳网络设备供应商', 'contact': '王经理', 'phone': '0755-11112222', 'email': 'wang@network.com'},
    {'code': 'SUP004', 'name': '广州汽车贸易公司', 'contact': '赵经理', 'phone': '020-33334444', 'email': 'zhao@auto.com'},
]

supplier_map = {}
for sup_data in suppliers_data:
    code = sup_data.pop('code')
    supplier, created = Supplier.objects.get_or_create(
        organization=org,
        code=code,
        defaults={
            **sup_data,
            'created_by': admin_user,
        }
    )
    supplier_map[code] = supplier
    print(f"  - {supplier.code}: {supplier.name}")

# Assets
print("Creating Assets (20)...")
asset_brands = ['联想', '戴尔', '惠普', '苹果', '华为', '小米']
asset_models = ['ThinkPad X1', 'OptiPlex 7090', 'ProBook 450', 'MacBook Pro', 'MateBook X', 'RedmiBook']
asset_specs = ['i5-1135G7/16GB/512GB', 'i7-11800H/32GB/1TB', 'M1/16GB/512GB', 'R7-5800H/16GB/512GB']

for i in range(1, 21):
    category = random.choice(list(category_map.values()))
    supplier = random.choice(list(supplier_map.values()))
    custodian = random.choice(list(demo_users.values()))
    department = random.choice(list(dept_map.values()))
    location = random.choice(list(location_map.values()))

    purchase_date = random_date(date(2023, 1, 1), date(2025, 12, 31))
    purchase_price = random_decimal(3000, 25000)

    asset, created = Asset.objects.get_or_create(
        asset_code=f'ZC{purchase_date.strftime("%Y%m")}{i:04d}',
        defaults={
            'asset_name': f'{random.choice(asset_brands)} {random.choice(asset_models)}',
            'organization': org,
            'asset_category': category,
            'specification': random.choice(asset_specs),
            'brand': random.choice(asset_brands),
            'model': random.choice(asset_models),
            'serial_number': f'SN{random.randint(100000, 999999)}',
            'purchase_price': purchase_price,
            'current_value': purchase_price * Decimal('0.8'),
            'purchase_date': purchase_date,
            'depreciation_start_date': purchase_date,
            'useful_life': category.default_useful_life,
            'residual_rate': Decimal('5.00'),
            'supplier': supplier,
            'department': department,
            'location': location,
            'custodian': custodian,
            'asset_status': random.choice(['pending', 'in_use', 'idle', 'maintenance', 'lent']),
            'created_by': admin_user,
        }
    )
    if created:
        print(f"  - {asset.asset_code}: {asset.asset_name}")

# Asset Pickup Orders
print("Creating Asset Pickup Orders (15)...")
pickup_statuses = ['draft', 'pending', 'approved', 'completed', 'cancelled']
for i in range(1, 16):
    pickup_no = f'LY202501{i:04d}'
    applicant = random.choice(list(demo_users.values()))
    department = random.choice(list(dept_map.values()))

    pickup_date = random_date(date(2025, 1, 1), date(2025, 12, 31))
    status = random.choice(pickup_statuses)

    pickup, created = AssetPickup.objects.get_or_create(
        organization=org,
        pickup_no=pickup_no,
        defaults={
            'applicant': applicant,
            'department': department,
            'pickup_date': pickup_date,
            'pickup_reason': f'部门办公需要领用设备 #{i}',
            'status': status,
            'approved_by': admin_user if status in ['approved', 'completed'] else None,
            'approved_at': pickup_date if status in ['approved', 'completed'] else None,
            'completed_at': pickup_date + timedelta(days=1) if status == 'completed' else None,
            'created_by': admin_user,
        }
    )

    if created:
        # Add pickup items
        assets = Asset.objects.filter(organization=org, asset_status='idle')[:random.randint(1, 3)]
        for asset in assets:
            PickupItem.objects.get_or_create(
                pickup=pickup,
                asset=asset,
                defaults={
                    'organization': org,
                    'quantity': 1,
                    'snapshot_original_location': asset.location,
                    'snapshot_original_custodian': asset.custodian,
                    'created_by': admin_user,
                }
            )
        print(f"  - {pickup.pickup_no}: {pickup.applicant.get_full_name()} ({status})")

# Asset Transfer Orders
print("Creating Asset Transfer Orders (12)...")
transfer_statuses = ['draft', 'pending', 'approved', 'completed']
for i in range(1, 13):
    transfer_no = f'TF202501{i:04d}'
    from_dept = random.choice(list(dept_map.values()))
    to_dept = random.choice([d for d in dept_map.values() if d != from_dept])

    transfer_date = random_date(date(2025, 1, 1), date(2025, 12, 31))
    status = random.choice(transfer_statuses)

    transfer, created = AssetTransfer.objects.get_or_create(
        organization=org,
        transfer_no=transfer_no,
        defaults={
            'from_department': from_dept,
            'to_department': to_dept,
            'transfer_date': transfer_date,
            'transfer_reason': f'部门间资产调拨 #{i}',
            'status': status,
            'from_approved_by': admin_user if status in ['approved', 'completed'] else None,
            'from_approved_at': transfer_date if status in ['approved', 'completed'] else None,
            'to_approved_by': admin_user if status in ['approved', 'completed'] else None,
            'to_approved_at': transfer_date if status in ['approved', 'completed'] else None,
            'completed_at': transfer_date + timedelta(days=1) if status == 'completed' else None,
            'created_by': admin_user,
        }
    )

    if created:
        assets = Asset.objects.filter(organization=org, department=from_dept)[:random.randint(1, 2)]
        for asset in assets:
            TransferItem.objects.get_or_create(
                transfer=transfer,
                asset=asset,
                defaults={
                    'organization': org,
                    'from_location': asset.location,
                    'from_custodian': asset.custodian,
                    'to_location': random.choice(list(location_map.values())),
                    'created_by': admin_user,
                }
            )
        print(f"  - {transfer.transfer_no}: {transfer.from_department.name} -> {transfer.to_department.name}")

# Asset Return Orders
print("Creating Asset Return Orders (10)...")
return_statuses = ['draft', 'pending', 'confirmed', 'completed']
for i in range(1, 11):
    return_no = f'RT202501{i:04d}'
    returner = random.choice(list(demo_users.values()))

    return_date = random_date(date(2025, 1, 1), date(2025, 12, 31))
    status = random.choice(return_statuses)

    asset_return, created = AssetReturn.objects.get_or_create(
        organization=org,
        return_no=return_no,
        defaults={
            'returner': returner,
            'return_date': return_date,
            'return_reason': f'归还闲置设备 #{i}',
            'status': status,
            'return_location': random.choice(list(location_map.values())),
            'confirmed_by': admin_user if status in ['confirmed', 'completed'] else None,
            'confirmed_at': return_date if status in ['confirmed', 'completed'] else None,
            'completed_at': return_date + timedelta(days=1) if status == 'completed' else None,
            'created_by': admin_user,
        }
    )

    if created:
        assets = Asset.objects.filter(organization=org, custodian=returner)[:random.randint(1, 2)]
        for asset in assets:
            ReturnItem.objects.get_or_create(
                asset_return=asset_return,
                asset=asset,
                defaults={
                    'organization': org,
                    'asset_status': random.choice(['idle', 'maintenance', 'scrapped']),
                    'condition_description': '设备完好',
                    'created_by': admin_user,
                }
            )
        print(f"  - {asset_return.return_no}: {asset_return.returner.get_full_name()} ({status})")

# Asset Loan Orders
print("Creating Asset Loan Orders (12)...")
loan_statuses = ['draft', 'pending', 'approved', 'borrowed', 'returned', 'overdue']
for i in range(1, 13):
    loan_no = f'JY202501{i:04d}'
    borrower = random.choice(list(demo_users.values()))

    borrow_date = random_date(date(2025, 1, 1), date(2025, 12, 31))
    expected_return = borrow_date + timedelta(days=random.randint(7, 30))
    status = random.choice(loan_statuses)

    actual_return = None
    if status == 'returned':
        actual_return = expected_return - timedelta(days=random.randint(1, 5))
    elif status == 'overdue':
        actual_return = None

    asset_loan, created = AssetLoan.objects.get_or_create(
        organization=org,
        loan_no=loan_no,
        defaults={
            'borrower': borrower,
            'borrow_date': borrow_date,
            'expected_return_date': expected_return,
            'actual_return_date': actual_return,
            'loan_reason': f'临时借用设备 #{i}',
            'status': status,
            'approved_by': admin_user if status in ['approved', 'borrowed', 'returned', 'overdue'] else None,
            'approved_at': borrow_date if status in ['approved', 'borrowed', 'returned', 'overdue'] else None,
            'lent_by': admin_user if status in ['borrowed', 'returned', 'overdue'] else None,
            'lent_at': borrow_date + timedelta(hours=1) if status in ['borrowed', 'returned', 'overdue'] else None,
            'returned_at': actual_return,
            'return_confirmed_by': admin_user if status == 'returned' else None,
            'asset_condition': 'good' if status == 'returned' else '',
            'created_by': admin_user,
        }
    )

    if created:
        assets = Asset.objects.filter(organization=org, asset_status='idle')[:random.randint(1, 2)]
        for asset in assets:
            LoanItem.objects.get_or_create(
                loan=asset_loan,
                asset=asset,
                defaults={
                    'organization': org,
                    'remark': '借用期间注意保管',
                    'created_by': admin_user,
                }
            )
        print(f"  - {asset_loan.loan_no}: {asset_loan.borrower.get_full_name()} ({status})")

# ============================================================
# IT ASSET MANAGEMENT
# ============================================================

print("\n=== IT ASSET MANAGEMENT ===")

print("Creating IT Assets (15)...")
for i in range(1, 16):
    custodian = random.choice(list(demo_users.values()))
    department = random.choice(list(dept_map.values()))
    location = random.choice(list(location_map.values()))

    purchase_date = random_date(date(2023, 1, 1), date(2025, 12, 31))

    it_asset, created = ITAsset.objects.get_or_create(
        organization=org,
        asset_code=f'IT{purchase_date.strftime("%Y%m")}{i:04d}',
        defaults={
            'asset_name': f'{random.choice(["服务器", "交换机", "路由器", "防火墙"])}-{i:03d}',
            'asset_type': random.choice(['server', 'network', 'storage', 'security']),
            'brand': random.choice(['戴尔', '惠普', '华为', '思科', '华三']),
            'model': f'{random.choice(["PowerEdge", "ProLiant", "Fabric", "Catalyst"])}-{random.randint(100, 999)}',
            'serial_number': f'IT-SN{random.randint(100000, 999999)}',
            'ip_address': f'192.168.1.{random.randint(10, 250)}',
            'mac_address': ':'.join(f'{random.randint(0, 255):02X}' for _ in range(6)),
            'purchase_price': random_decimal(5000, 50000),
            'purchase_date': purchase_date,
            'warranty_expire': purchase_date + timedelta(days=1095),  # 3 years
            'department': department,
            'location': location,
            'custodian': custodian,
            'status': random.choice(['active', 'inactive', 'maintenance', 'retired']),
            'created_by': admin_user,
        }
    )
    if created:
        print(f"  - {it_asset.asset_code}: {it_asset.asset_name}")

print("Creating IT Software (10)...")
software_names = ['Windows Server', 'Linux', 'Database', 'Office Suite', 'Antivirus', 'VMware', 'Docker', 'Kubernetes', 'Backup Software', 'Monitoring Tool']
for i in range(1, 11):
    it_software, created = ITSoftware.objects.get_or_create(
        organization=org,
        code=f'SFT{i:03d}',
        defaults={
            'name': software_names[i-1],
            'version': f'{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 99)}',
            'vendor': random.choice(['Microsoft', 'Oracle', 'VMware', 'Symantec', 'Cisco']),
            'license_type': random.choice(['commercial', 'opensource', 'custom']),
            'total_licenses': random.randint(10, 100),
            'used_licenses': random.randint(0, 50),
            'purchase_date': random_date(date(2023, 1, 1), date(2025, 12, 31)),
            'expire_date': random_date(date(2025, 1, 1), date(2027, 12, 31)),
            'status': random.choice(['active', 'inactive', 'expired']),
            'created_by': admin_user,
        }
    )
    if created:
        print(f"  - {it_software.code}: {it_software.name}")

# ============================================================
# CONSUMABLE MANAGEMENT
# ============================================================

print("\n=== CONSUMABLE MANAGEMENT ===")

print("Creating Consumable Categories...")
consumable_categories = [
    {'code': 'C01', 'name': '办公耗材'},
    {'code': 'C02', 'name': '电子配件'},
    {'code': 'C03', 'name': '清洁用品'},
]

consumable_category_map = {}
for cat_data in consumable_categories:
    category, created = ConsumableCategory.objects.get_or_create(
        organization=org,
        code=cat_data['code'],
        defaults={
            'name': cat_data['name'],
            'created_by': admin_user,
        }
    )
    consumable_category_map[cat_data['code']] = category
    print(f"  - {category.code}: {category.name}")

print("Creating Consumables (15)...")
consumable_names = ['打印纸', '签字笔', '文件夹', '订书机', '计算器', '鼠标', '键盘', '网线', '电源线', 'U盘', '硬盘', '内存条', '电池', '胶水', '剪刀']
for i in range(1, 16):
    category = random.choice(list(consumable_category_map.values()))
    consumable, created = Consumable.objects.get_or_create(
        organization=org,
        code=f'CON{i:04d}',
        defaults={
            'name': consumable_names[i-1],
            'category': category,
            'unit': random.choice(['个', '包', '盒', '箱', '只', '条']),
            'specification': f'规格-{random.randint(1, 5)}',
            'safe_stock': random.randint(10, 50),
            'created_by': admin_user,
        }
    )
    if created:
        print(f"  - {consumable.code}: {consumable.name}")

print("Creating Consumable Stock (15)...")
for consumable in Consumable.objects.filter(organization=org):
    stock, created = ConsumableStock.objects.get_or_create(
        organization=org,
        consumable=consumable,
        defaults={
            'quantity': random.randint(50, 500),
            'unit_price': random_decimal(1, 100),
            'location': random.choice(list(location_map.values())),
            'created_by': admin_user,
        }
    )
    if created:
        print(f"  - {consumable.name}: {stock.quantity} {consumable.unit}")

# ============================================================
# MAINTENANCE MANAGEMENT
# ============================================================

print("\n=== MAINTENANCE MANAGEMENT ===")

print("Creating Maintenance Records (12)...")
maintenance_types = ['routine', 'corrective', 'preventive']
for i in range(1, 13):
    maintenance_date = random_date(date(2024, 1, 1), date(2025, 12, 31))

    maintenance, created = Maintenance.objects.get_or_create(
        organization=org,
        code=f'MNT{i:04d}',
        defaults={
            'asset_code': f'ZC2024{random.randint(1, 999):03d}',
            'maintenance_type': random.choice(maintenance_types),
            'maintenance_date': maintenance_date,
            'technician': random.choice(list(demo_users.values())).get_full_name(),
            'cost': random_decimal(100, 5000),
            'description': f'定期维护保养 #{i}',
            'status': random.choice(['pending', 'in_progress', 'completed']),
            'created_by': admin_user,
        }
    )
    if created:
        print(f"  - {maintenance.code}: {maintenance.maintenance_type}")

print("Creating Maintenance Plans (5)...")
for i in range(1, 6):
    plan, created = MaintenancePlan.objects.get_or_create(
        organization=org,
        code=f'PLAN{i:03d}',
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
        print(f"  - {plan.code}: {plan.name}")

print("Creating Maintenance Tasks (8)...")
for i in range(1, 9):
    task_date = random_date(date(2025, 1, 1), date(2025, 12, 31))

    task, created = MaintenanceTask.objects.get_or_create(
        organization=org,
        code=f'TASK{i:04d}',
        defaults={
            'title': f'设备检查任务-{i}',
            'description': f'对指定设备进行全面检查',
            'scheduled_date': task_date,
            'assigned_to': random.choice(list(demo_users.values())),
            'priority': random.choice(['low', 'medium', 'high', 'urgent']),
            'status': random.choice(['pending', 'in_progress', 'completed', 'cancelled']),
            'completed_at': task_date + timedelta(hours=random.randint(1, 8)) if random.random() > 0.5 else None,
            'created_by': admin_user,
        }
    )
    if created:
        print(f"  - {task.code}: {task.title}")

# ============================================================
# SOFTWARE LICENSES
# ============================================================

print("\n=== SOFTWARE LICENSES ===")

print("Creating Software Licenses (10)...")
license_types = ['perpetual', 'subscription', 'trial']
for i in range(1, 11):
    license_start = random_date(date(2024, 1, 1), date(2025, 6, 1))
    license_expire = license_start + timedelta(days=random.randint(180, 1095))

    software_license, created = SoftwareLicense.objects.get_or_create(
        organization=org,
        license_key=f'KEY-{i:06d}-{random.randint(1000, 9999)}',
        defaults={
            'software_name': random.choice(['Windows Server', 'SQL Server', 'Oracle DB', 'VMware', 'Office 365', 'Adobe CC']),
            'vendor': random.choice(['Microsoft', 'Oracle', 'VMware', 'Adobe']),
            'license_type': random.choice(license_types),
            'quantity': random.randint(10, 100),
            'used_quantity': random.randint(0, 50),
            'purchase_date': license_start,
            'expire_date': license_expire,
            'cost': random_decimal(1000, 50000),
            'status': 'active' if license_expire > date.today() else 'expired',
            'created_by': admin_user,
        }
    )
    if created:
        print(f"  - {software_license.license_key}: {software_license.software_name}")

# ============================================================
# INVENTORY MANAGEMENT
# ============================================================

print("\n=== INVENTORY MANAGEMENT ===")

print("Creating Inventory Tasks (8)...")
task_statuses = ['draft', 'pending', 'in_progress', 'completed', 'cancelled']
for i in range(1, 9):
    task_date = random_date(date(2025, 1, 1), date(2025, 12, 31))

    task, created = InventoryTask.objects.get_or_create(
        organization=org,
        task_no=f'PD2025{i:03d}',
        defaults={
            'title': f'季度资产盘点-{i}期',
            'task_type': random.choice(['full', 'partial', 'spot']),
            'planned_date': task_date,
            'department': random.choice(list(dept_map.values())),
            'executor': random.choice(list(demo_users.values())),
            'status': random.choice(task_statuses),
            'actual_date': task_date + timedelta(days=random.randint(0, 7)) if random.random() > 0.3 else None,
            'completed_at': task_date + timedelta(days=random.randint(1, 10)) if random.random() > 0.5 else None,
            'total_assets': random.randint(50, 200),
            'scanned_assets': random.randint(40, 200),
            'exception_count': random.randint(0, 10),
            'created_by': admin_user,
        }
    )
    if created:
        print(f"  - {task.task_no}: {task.title} ({task.status})")

# ============================================================
# PROCUREMENT MANAGEMENT
# ============================================================

print("\n=== PROCUREMENT MANAGEMENT ===")

print("Creating Purchase Requests (10)...")
request_statuses = ['draft', 'pending', 'approved', 'rejected', 'ordered', 'completed']
for i in range(1, 11):
    request_date = random_date(date(2025, 1, 1), date(2025, 12, 31))

    request, created = PurchaseRequest.objects.get_or_create(
        organization=org,
        request_no=f'CG2025{i:04d}',
        defaults={
            'title': f'采购申请-{random.choice(["电脑", "办公椅", "打印机", "投影仪"])}',
            'request_type': 'asset',
            'department': random.choice(list(dept_map.values())),
            'applicant': random.choice(list(demo_users.values())),
            'request_date': request_date,
            'expected_date': request_date + timedelta(days=random.randint(7, 30)),
            'total_amount': random_decimal(10000, 100000),
            'status': random.choice(request_statuses),
            'approved_by': admin_user if random.random() > 0.3 else None,
            'approved_at': request_date + timedelta(days=random.randint(1, 5)) if random.random() > 0.3 else None,
            'reason': f'部门业务需要采购相关设备',
            'created_by': admin_user,
        }
    )
    if created:
        print(f"  - {request.request_no}: {request.title} ({request.status})")

print("Creating Asset Receipts (8)...")
receipt_statuses = ['pending', 'partial', 'completed']
for i in range(1, 9):
    receipt_date = random_date(date(2025, 1, 1), date(2025, 12, 31))

    receipt, created = AssetReceipt.objects.get_or_create(
        organization=org,
        receipt_no=f'RK2025{i:04d}',
        defaults={
            'supplier': random.choice(list(supplier_map.values())),
            'receipt_date': receipt_date,
            'total_amount': random_decimal(20000, 200000),
            'quantity': random.randint(5, 50),
            'status': random.choice(receipt_statuses),
            'received_by': random.choice(list(demo_users.values())),
            'checked_by': admin_user if random.random() > 0.3 else None,
            'warehouse': random.choice(list(location_map.values())),
            'remarks': f'货物验收合格，入库',
            'created_by': admin_user,
        }
    )
    if created:
        print(f"  - {receipt.receipt_no}: {receipt.supplier.name} ({receipt.status})")

# ============================================================
# INSURANCE MANAGEMENT
# ============================================================

print("\n=== INSURANCE MANAGEMENT ===")

print("Creating Insurance Companies (5)...")
insurance_companies = [
    {'code': 'PICC', 'name': '中国人民保险', 'contact': '刘经理', 'phone': '400-123-4567'},
    {'code': 'CPIC', 'name': '中国太平洋保险', 'contact': '陈经理', 'phone': '400-234-5678'},
    {'code': 'PING', 'name': '中国平安保险', 'contact': '杨经理', 'phone': '400-345-6789'},
    {'code': 'CCIC', 'name': '中国出口信用保险', 'contact': '黄经理', 'phone': '400-456-7890'},
    {'code': 'SINOSIG', 'name': '中国人寿保险', 'contact': '赵经理', 'phone': '400-567-8901'},
]

insurance_company_map = {}
for company_data in insurance_companies:
    company, created = InsuranceCompany.objects.get_or_create(
        organization=org,
        code=company_data['code'],
        defaults={
            **company_data,
            'created_by': admin_user,
        }
    )
    insurance_company_map[company_data['code']] = company
    if created:
        print(f"  - {company.code}: {company.name}")

print("Creating Insurance Policies (10)...")
policy_statuses = ['active', 'expired', 'cancelled', 'pending']
for i in range(1, 11):
    start_date = random_date(date(2024, 1, 1), date(2025, 6, 1))
    end_date = start_date + timedelta(days=365)

    policy, created = InsurancePolicy.objects.get_or_create(
        organization=org,
        policy_no=f'BX{i:06d}',
        defaults={
            'insurance_company': random.choice(list(insurance_company_map.values())),
            'policy_type': random.choice(['property', 'equipment', 'vehicle', 'liability']),
            'insured_amount': random_decimal(100000, 10000000),
            'premium': random_decimal(5000, 100000),
            'start_date': start_date,
            'end_date': end_date,
            'status': random.choice(policy_statuses),
            'beneficiary': org.name,
            'created_by': admin_user,
        }
    )
    if created:
        print(f"  - {policy.policy_no}: {policy.insurance_company.name}")

print("Creating Claim Records (6)...")
claim_statuses = ['pending', 'approved', 'rejected', 'paid']
for i in range(1, 7):
    claim_date = random_date(date(2024, 1, 1), date(2025, 12, 31))

    claim, created = ClaimRecord.objects.get_or_create(
        organization=org,
        claim_no=f'LP{i:06d}',
        defaults={
            'policy': random.choice(InsurancePolicy.objects.filter(organization=org)),
            'claim_date': claim_date,
            'claim_amount': random_decimal(5000, 200000),
            'claim_reason': random.choice(['设备损坏', '意外事故', '自然灾害', '盗窃']),
            'status': random.choice(claim_statuses),
            'approved_amount': random_decimal(0, 150000) if random.random() > 0.3 else None,
            'approved_date': claim_date + timedelta(days=random.randint(5, 30)) if random.random() > 0.5 else None,
            'paid_date': claim_date + timedelta(days=random.randint(30, 60)) if random.random() > 0.7 else None,
            'description': f'保险理赔申请详情',
            'created_by': admin_user,
        }
    )
    if created:
        print(f"  - {claim.claim_no}: {claim.status}")

# ============================================================
# LEASING MANAGEMENT
# ============================================================

print("\n=== LEASING MANAGEMENT ===")

print("Creating Leasing Contracts (6)...")
contract_statuses = ['active', 'expired', 'terminated', 'pending']
for i in range(1, 7):
    start_date = random_date(date(2024, 1, 1), date(2025, 1, 1))
    end_date = start_date + timedelta(days=random.randint(365, 1095))

    contract, created = LeasingContract.objects.get_or_create(
        organization=org,
        contract_no=f'ZL{i:06d}',
        defaults={
            'lessee': random.choice(list(dept_map.values())).name,
            'lessor': random.choice(['华融租赁', '国银租赁', '远东租赁', '平安租赁']),
            'asset_name': random.choice(['办公设备', '车辆', '机械设备']),
            'start_date': start_date,
            'end_date': end_date,
            'monthly_rent': random_decimal(5000, 50000),
            'deposit': random_decimal(10000, 100000),
            'total_amount': random_decimal(100000, 1000000),
            'payment_method': random.choice(['monthly', 'quarterly', 'semi_annual']),
            'status': random.choice(contract_statuses),
            'created_by': admin_user,
        }
    )
    if created:
        print(f"  - {contract.contract_no}: {contract.asset_name}")

# ============================================================
# WORKFLOW MANAGEMENT
# ============================================================

print("\n=== WORKFLOW MANAGEMENT ===")

print("Creating Workflow Definitions (5)...")
workflow_types = ['asset_pickup', 'asset_transfer', 'purchase_request', 'expense_approval', 'leave_request']
for i, wf_type in enumerate(workflow_types, 1):
    definition, created = WorkflowDefinition.objects.get_or_create(
        organization=org,
        code=f'WF{i:03d}',
        defaults={
            'name': f'{wf_type.replace("_", " ").title()} Workflow',
            'description': f'Approval workflow for {wf_type}',
            'version': 1,
            'is_active': True,
            'definition': {
                'nodes': [
                    {'id': 'start', 'type': 'start', 'name': 'Start'},
                    {'id': 'approve', 'type': 'approve', 'name': 'Manager Approval'},
                    {'id': 'end', 'type': 'end', 'name': 'End'},
                ],
                'edges': [
                    {'from': 'start', 'to': 'approve'},
                    {'from': 'approve', 'to': 'end'},
                ]
            },
            'created_by': admin_user,
        }
    )
    if created:
        print(f"  - {definition.code}: {definition.name}")

print("Creating Workflow Instances (12)...")
instance_statuses = ['pending', 'running', 'completed', 'rejected', 'cancelled']
for i in range(1, 13):
    start_date = random_date(date(2025, 1, 1), date(2025, 12, 31))
    definition = random.choice(WorkflowDefinition.objects.filter(organization=org, is_active=True))

    instance, created = WorkflowInstance.objects.get_or_create(
        organization=org,
        instance_no=f'WI{i:06d}',
        defaults={
            'definition': definition,
            'business_type': definition.code,
            'business_id': f'BUS{i:05d}',
            'initiator': random.choice(list(demo_users.values())),
            'status': random.choice(instance_statuses),
            'current_node': random.choice(['start', 'approve', 'end']),
            'started_at': start_date,
            'completed_at': start_date + timedelta(days=random.randint(1, 7)) if random.random() > 0.4 else None,
            'variables': {'amount': random_decimal(1000, 50000), 'reason': f'业务流程{i}'},
            'created_by': admin_user,
        }
    )
    if created:
        print(f"  - {instance.instance_no}: {instance.status}")

print("Creating Workflow Tasks (15)...")
task_statuses = ['pending', 'in_progress', 'completed', 'rejected', 'cancelled']
for i in range(1, 16):
    task, created = WorkflowTask.objects.get_or_create(
        organization=org,
        task_no=f'WT{i:06d}',
        defaults={
            'instance': random.choice(WorkflowInstance.objects.filter(organization=org)),
            'node_id': random.choice(['approve', 'review', 'notify']),
            'node_name': random.choice(['Manager Approval', 'Finance Review', 'HR Notification']),
            'assignee': random.choice(list(demo_users.values())),
            'status': random.choice(task_statuses),
            'due_date': random_date(date(2025, 1, 1), date(2025, 12, 31)),
            'completed_at': random_date(date(2025, 1, 1), date(2025, 12, 31)) if random.random() > 0.5 else None,
            'comment': f'任务审批意见',
            'created_by': admin_user,
        }
    )
    if created:
        print(f"  - {task.task_no}: {task.node_name} ({task.status})")

# ============================================================
# FINANCE VOUCHERS
# ============================================================

print("\n=== FINANCE VOUCHERS ===")

print("Creating Finance Vouchers (10)...")
voucher_types = ['payment', 'receipt', 'transfer']
voucher_statuses = ['draft', 'pending', 'approved', 'rejected', 'posted']
for i in range(1, 11):
    voucher_date = random_date(date(2025, 1, 1), date(2025, 12, 31))

    voucher, created = FinanceVoucher.objects.get_or_create(
        organization=org,
        voucher_no=f'PZ{i:06d}',
        defaults={
            'voucher_type': random.choice(voucher_types),
            'voucher_date': voucher_date,
            'amount': random_decimal(1000, 100000),
            'currency': 'CNY',
            'status': random.choice(voucher_statuses),
            'prepared_by': random.choice(list(demo_users.values())),
            'approved_by': admin_user if random.random() > 0.4 else None,
            'approved_at': voucher_date + timedelta(days=random.randint(1, 5)) if random.random() > 0.4 else None,
            'description': f'财务凭证-{random.choice(["采购付款", "费用报销", "工资发放", "租金支付"])}',
            'created_by': admin_user,
        }
    )
    if created:
        print(f"  - {voucher.voucher_no}: {voucher.description} ({voucher.status})")

# ============================================================
# SUMMARY
# ============================================================

print("\n" + "="*60)
print("DEMO DATA GENERATION COMPLETED!")
print("="*60)
print(f"\nOrganization: {org.name} ({org.code})")
print(f"Total Departments: {Department.objects.filter(organization=org).count()}")
print(f"Total Assets: {Asset.objects.filter(organization=org).count()}")
print(f"Total IT Assets: {ITAsset.objects.filter(organization=org).count()}")
print(f"Total Consumables: {Consumable.objects.filter(organization=org).count()}")
print(f"Total Pickups: {AssetPickup.objects.filter(organization=org).count()}")
print(f"Total Transfers: {AssetTransfer.objects.filter(organization=org).count()}")
print(f"Total Returns: {AssetReturn.objects.filter(organization=org).count()}")
print(f"Total Loans: {AssetLoan.objects.filter(organization=org).count()}")
print(f"Total Maintenances: {Maintenance.objects.filter(organization=org).count()}")
print(f"Total Inventory Tasks: {InventoryTask.objects.filter(organization=org).count()}")
print(f"Total Purchase Requests: {PurchaseRequest.objects.filter(organization=org).count()}")
print(f"Total Insurance Policies: {InsurancePolicy.objects.filter(organization=org).count()}")
print(f"Total Leasing Contracts: {LeasingContract.objects.filter(organization=org).count()}")
print(f"Total Workflow Instances: {WorkflowInstance.objects.filter(organization=org).count()}")
print(f"Total Finance Vouchers: {FinanceVoucher.objects.filter(organization=org).count()}")
print("\nDefault Login: admin / admin123")
print("="*60)
