"""
Django management command to create demo data for all business objects.

Generates 20-50 realistic demo records for testing and demonstration purposes.
Handles all major business objects: Assets, Consumables, Lifecycle, Inventory, Organizations.

Usage:
    python manage.py create_demo_data [--count N] [--organization ORG_ID]
"""
import random
from decimal import Decimal
from datetime import datetime, timedelta, date

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.organizations.models import Organization, Department
from apps.accounts.models import User
from apps.assets.models import (
    Asset, AssetCategory, Supplier, Location,
    AssetPickup, PickupItem, AssetTransfer, TransferItem,
    AssetReturn, ReturnItem, AssetLoan, LoanItem
)
from apps.consumables.models import (
    Consumable, ConsumableCategory, ConsumableStock,
    ConsumablePurchase, PurchaseItem, ConsumableIssue, IssueItem
)
from apps.lifecycle.models import (
    PurchaseRequest, PurchaseRequestItem,
    AssetReceipt, AssetReceiptItem,
    Maintenance, MaintenancePlan, MaintenanceTask,
    DisposalRequest, DisposalItem
)
from apps.inventory.models import (
    InventoryTask, InventorySnapshot, InventoryScan
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Create demo data for all business objects in the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=30,
            help='Number of records to create for each model (default: 30)'
        )
        parser.add_argument(
            '--organization',
            type=str,
            default=None,
            help='Organization ID to use (uses first organization if not specified)'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip models that already have data'
        )

    def handle(self, *args, **options):
        count = options['count']
        org_id = options.get('organization')
        skip_existing = options['skip_existing']

        self.stdout.write(self.style.SUCCESS('Starting demo data creation...'))

        # Get or create organization
        organization = self._get_organization(org_id)
        if not organization:
            self.stdout.write(self.style.ERROR('No organization found. Please create one first.'))
            return

        # Get or create users
        users = self._get_or_create_users(organization, count=5)
        departments = self._get_or_create_departments(organization, users, count=5)

        # Statistics tracking
        stats = {}

        # 1. Create Asset Categories
        if not skip_existing or not AssetCategory.objects.filter(organization=organization).exists():
            asset_categories = self._create_asset_categories(organization)
            stats['asset_categories'] = len(asset_categories)
            self.stdout.write(f'  Created {len(asset_categories)} asset categories')
        else:
            asset_categories = list(AssetCategory.objects.filter(organization=organization, is_deleted=False))
            stats['asset_categories'] = len(asset_categories)
            self.stdout.write(f'  Using existing {len(asset_categories)} asset categories')

        # 2. Create Locations
        if not skip_existing or not Location.objects.filter(organization=organization).exists():
            locations = self._create_locations(organization)
            stats['locations'] = len(locations)
            self.stdout.write(f'  Created {len(locations)} locations')
        else:
            locations = list(Location.objects.filter(organization=organization, is_deleted=False))
            stats['locations'] = len(locations)
            self.stdout.write(f'  Using existing {len(locations)} locations')

        # 3. Create Suppliers
        if not skip_existing or not Supplier.objects.filter(organization=organization).exists():
            suppliers = self._create_suppliers(organization, count=10)
            stats['suppliers'] = len(suppliers)
            self.stdout.write(f'  Created {len(suppliers)} suppliers')
        else:
            suppliers = list(Supplier.objects.filter(organization=organization, is_deleted=False))
            stats['suppliers'] = len(suppliers)
            self.stdout.write(f'  Using existing {len(suppliers)} suppliers')

        # 4. Create Assets
        if not skip_existing or not Asset.objects.filter(organization=organization).exists():
            assets = self._create_assets(organization, asset_categories, locations, suppliers, departments, users, count)
            stats['assets'] = len(assets)
            self.stdout.write(f'  Created {len(assets)} assets')
        else:
            assets = list(Asset.objects.filter(organization=organization, is_deleted=False))
            stats['assets'] = len(assets)
            self.stdout.write(f'  Using existing {len(assets)} assets')

        # 5. Create Consumable Categories
        if not skip_existing or not ConsumableCategory.objects.filter(organization=organization).exists():
            consumable_categories = self._create_consumable_categories(organization)
            stats['consumable_categories'] = len(consumable_categories)
            self.stdout.write(f'  Created {len(consumable_categories)} consumable categories')
        else:
            consumable_categories = list(ConsumableCategory.objects.filter(organization=organization, is_deleted=False))
            stats['consumable_categories'] = len(consumable_categories)
            self.stdout.write(f'  Using existing {len(consumable_categories)} consumable categories')

        # 6. Create Consumables
        if not skip_existing or not Consumable.objects.filter(organization=organization).exists():
            consumables = self._create_consumables(organization, consumable_categories, locations, suppliers, count=20)
            stats['consumables'] = len(consumables)
            self.stdout.write(f'  Created {len(consumables)} consumables')
        else:
            consumables = list(Consumable.objects.filter(organization=organization, is_deleted=False))
            stats['consumables'] = len(consumables)
            self.stdout.write(f'  Using existing {len(consumables)} consumables')

        # 7. Create Consumable Stock Transactions
        if not skip_existing or not ConsumableStock.objects.filter(organization=organization).exists():
            stock_transactions = self._create_consumable_stocks(consumables, users, count=min(count, 50))
            stats['consumable_stocks'] = len(stock_transactions)
            self.stdout.write(f'  Created {len(stock_transactions)} stock transactions')
        else:
            stock_transactions = list(ConsumableStock.objects.filter(organization=organization, is_deleted=False))
            stats['consumable_stocks'] = len(stock_transactions)
            self.stdout.write(f'  Using existing {len(stock_transactions)} stock transactions')

        # 8. Create Consumable Purchases
        if not skip_existing or not ConsumablePurchase.objects.filter(organization=organization).exists():
            consumable_purchases = self._create_consumable_purchases(organization, suppliers, consumables, users, count=min(count, 20))
            stats['consumable_purchases'] = len(consumable_purchases)
            self.stdout.write(f'  Created {len(consumable_purchases)} consumable purchases')
        else:
            consumable_purchases = list(ConsumablePurchase.objects.filter(organization=organization, is_deleted=False))
            stats['consumable_purchases'] = len(consumable_purchases)
            self.stdout.write(f'  Using existing {len(consumable_purchases)} consumable purchases')

        # 9. Create Consumable Issues
        if not skip_existing or not ConsumableIssue.objects.filter(organization=organization).exists():
            consumable_issues = self._create_consumable_issues(organization, departments, users, consumables, count=min(count, 20))
            stats['consumable_issues'] = len(consumable_issues)
            self.stdout.write(f'  Created {len(consumable_issues)} consumable issues')
        else:
            consumable_issues = list(ConsumableIssue.objects.filter(organization=organization, is_deleted=False))
            stats['consumable_issues'] = len(consumable_issues)
            self.stdout.write(f'  Using existing {len(consumable_issues)} consumable issues')

        # 10. Create Purchase Requests
        if not skip_existing or not PurchaseRequest.objects.filter(organization=organization).exists():
            purchase_requests = self._create_purchase_requests(organization, departments, users, asset_categories, count=min(count, 20))
            stats['purchase_requests'] = len(purchase_requests)
            self.stdout.write(f'  Created {len(purchase_requests)} purchase requests')
        else:
            purchase_requests = list(PurchaseRequest.objects.filter(organization=organization, is_deleted=False))
            stats['purchase_requests'] = len(purchase_requests)
            self.stdout.write(f'  Using existing {len(purchase_requests)} purchase requests')

        # 11. Create Asset Receipts
        if not skip_existing or not AssetReceipt.objects.filter(organization=organization).exists():
            asset_receipts = self._create_asset_receipts(organization, users, suppliers, asset_categories, count=min(count, 15))
            stats['asset_receipts'] = len(asset_receipts)
            self.stdout.write(f'  Created {len(asset_receipts)} asset receipts')
        else:
            asset_receipts = list(AssetReceipt.objects.filter(organization=organization, is_deleted=False))
            stats['asset_receipts'] = len(asset_receipts)
            self.stdout.write(f'  Using existing {len(asset_receipts)} asset receipts')

        # 12. Create Maintenance Records
        if not skip_existing or not Maintenance.objects.filter(organization=organization).exists():
            maintenance_records = self._create_maintenance_records(organization, assets, users, count=min(count, 20))
            stats['maintenance'] = len(maintenance_records)
            self.stdout.write(f'  Created {len(maintenance_records)} maintenance records')
        else:
            maintenance_records = list(Maintenance.objects.filter(organization=organization, is_deleted=False))
            stats['maintenance'] = len(maintenance_records)
            self.stdout.write(f'  Using existing {len(maintenance_records)} maintenance records')

        # 13. Create Maintenance Plans
        if not skip_existing or not MaintenancePlan.objects.filter(organization=organization).exists():
            maintenance_plans = self._create_maintenance_plans(organization, asset_categories, assets, users, count=10)
            stats['maintenance_plans'] = len(maintenance_plans)
            self.stdout.write(f'  Created {len(maintenance_plans)} maintenance plans')
        else:
            maintenance_plans = list(MaintenancePlan.objects.filter(organization=organization, is_deleted=False))
            stats['maintenance_plans'] = len(maintenance_plans)
            self.stdout.write(f'  Using existing {len(maintenance_plans)} maintenance plans')

        # 14. Create Disposal Requests
        if not skip_existing or not DisposalRequest.objects.filter(organization=organization).exists():
            disposal_requests = self._create_disposal_requests(organization, departments, users, assets, count=min(count, 10))
            stats['disposal_requests'] = len(disposal_requests)
            self.stdout.write(f'  Created {len(disposal_requests)} disposal requests')
        else:
            disposal_requests = list(DisposalRequest.objects.filter(organization=organization, is_deleted=False))
            stats['disposal_requests'] = len(disposal_requests)
            self.stdout.write(f'  Using existing {len(disposal_requests)} disposal requests')

        # 15. Create Asset Pickups
        if not skip_existing or not AssetPickup.objects.filter(organization=organization).exists():
            asset_pickups = self._create_asset_pickups(organization, departments, users, assets, count=min(count, 15))
            stats['asset_pickups'] = len(asset_pickups)
            self.stdout.write(f'  Created {len(asset_pickups)} asset pickups')
        else:
            asset_pickups = list(AssetPickup.objects.filter(organization=organization, is_deleted=False))
            stats['asset_pickups'] = len(asset_pickups)
            self.stdout.write(f'  Using existing {len(asset_pickups)} asset pickups')

        # 16. Create Asset Transfers
        if not skip_existing or not AssetTransfer.objects.filter(organization=organization).exists():
            asset_transfers = self._create_asset_transfers(organization, departments, users, assets, locations, count=min(count, 15))
            stats['asset_transfers'] = len(asset_transfers)
            self.stdout.write(f'  Created {len(asset_transfers)} asset transfers')
        else:
            asset_transfers = list(AssetTransfer.objects.filter(organization=organization, is_deleted=False))
            stats['asset_transfers'] = len(asset_transfers)
            self.stdout.write(f'  Using existing {len(asset_transfers)} asset transfers')

        # 17. Create Asset Returns
        if not skip_existing or not AssetReturn.objects.filter(organization=organization).exists():
            asset_returns = self._create_asset_returns(organization, users, assets, locations, count=min(count, 10))
            stats['asset_returns'] = len(asset_returns)
            self.stdout.write(f'  Created {len(asset_returns)} asset returns')
        else:
            asset_returns = list(AssetReturn.objects.filter(organization=organization, is_deleted=False))
            stats['asset_returns'] = len(asset_returns)
            self.stdout.write(f'  Using existing {len(asset_returns)} asset returns')

        # 18. Create Asset Loans
        if not skip_existing or not AssetLoan.objects.filter(organization=organization).exists():
            asset_loans = self._create_asset_loans(organization, users, assets, count=min(count, 15))
            stats['asset_loans'] = len(asset_loans)
            self.stdout.write(f'  Created {len(asset_loans)} asset loans')
        else:
            asset_loans = list(AssetLoan.objects.filter(organization=organization, is_deleted=False))
            stats['asset_loans'] = len(asset_loans)
            self.stdout.write(f'  Using existing {len(asset_loans)} asset loans')

        # 19. Create Inventory Tasks
        if not skip_existing or not InventoryTask.objects.filter(organization=organization).exists():
            inventory_tasks = self._create_inventory_tasks(organization, departments, asset_categories, users, count=min(count, 10))
            stats['inventory_tasks'] = len(inventory_tasks)
            self.stdout.write(f'  Created {len(inventory_tasks)} inventory tasks')
        else:
            inventory_tasks = list(InventoryTask.objects.filter(organization=organization, is_deleted=False))
            stats['inventory_tasks'] = len(inventory_tasks)
            self.stdout.write(f'  Using existing {len(inventory_tasks)} inventory tasks')

        # 20. Create Inventory Snapshots and Scans
        if inventory_tasks and assets:
            if not skip_existing or not InventorySnapshot.objects.filter(task__organization=organization).exists():
                snapshots = self._create_inventory_snapshots(inventory_tasks, assets, users)
                stats['inventory_snapshots'] = len(snapshots)
                self.stdout.write(f'  Created {len(snapshots)} inventory snapshots')
            else:
                snapshots = list(InventorySnapshot.objects.filter(task__organization=organization, is_deleted=False))
                stats['inventory_snapshots'] = len(snapshots)
                self.stdout.write(f'  Using existing {len(snapshots)} inventory snapshots')

            if not skip_existing or not InventoryScan.objects.filter(task__organization=organization).exists():
                scans = self._create_inventory_scans(inventory_tasks, assets, users, count=min(count, 50))
                stats['inventory_scans'] = len(scans)
                self.stdout.write(f'  Created {len(scans)} inventory scans')
            else:
                scans = list(InventoryScan.objects.filter(task__organization=organization, is_deleted=False))
                stats['inventory_scans'] = len(scans)
                self.stdout.write(f'  Using existing {len(scans)} inventory scans')

        # Print summary
        self.stdout.write(self.style.SUCCESS('\n=== Demo Data Creation Summary ==='))
        self.stdout.write(f'Organization: {organization.name}')
        for model_name, count in stats.items():
            self.stdout.write(f'  {model_name}: {count}')
        total_records = sum(stats.values())
        self.stdout.write(self.style.SUCCESS(f'\nTotal records created: {total_records}'))
        self.stdout.write(self.style.SUCCESS('Demo data creation completed!'))

    def _get_organization(self, org_id):
        """Get organization by ID or return first available."""
        if org_id:
            try:
                return Organization.objects.get(id=org_id, is_deleted=False)
            except Organization.DoesNotExist:
                return None
        return Organization.objects.filter(is_deleted=False).first()

    def _get_or_create_users(self, organization, count=5):
        """Get or create demo users."""
        users = []
        user_data = [
            ('admin', 'Administrator', 'admin@demo.com'),
            ('user1', 'Zhang Wei', 'zhang.wei@demo.com'),
            ('user2', 'Li Na', 'li.na@demo.com'),
            ('user3', 'Wang Feng', 'wang.feng@demo.com'),
            ('user4', 'Liu Yang', 'liu.yang@demo.com'),
        ]

        for username, full_name, email in user_data[:count]:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': full_name.split()[0] if full_name else '',
                    'last_name': full_name.split()[1] if full_name and ' ' in full_name else full_name or '',
                    'current_organization': organization,
                    'is_active': True
                }
            )
            if created:
                user.set_password('demo123456')
                user.save()

            # Link user to organization
            from apps.accounts.models import UserOrganization
            UserOrganization.objects.get_or_create(
                user=user,
                organization=organization,
                defaults={'role': 'admin' if username == 'admin' else 'member', 'is_primary': True}
            )
            users.append(user)

        return users

    def _get_or_create_departments(self, organization, users, count=5):
        """Get or create demo departments."""
        departments = []
        dept_data = [
            ('IT', 'IT Department', users[1] if len(users) > 1 else users[0]),
            ('HR', 'Human Resources', users[2] if len(users) > 2 else users[0]),
            ('FIN', 'Finance Department', users[3] if len(users) > 3 else users[0]),
            ('OPS', 'Operations', users[4] if len(users) > 4 else users[0]),
            ('MKT', 'Marketing', users[0]),
        ]

        for code, name, leader in dept_data[:count]:
            dept, created = Department.objects.get_or_create(
                organization=organization,
                code=code,
                defaults={'name': name, 'leader': leader, 'is_active': True}
            )
            departments.append(dept)

        return departments

    def _create_asset_categories(self, organization):
        """Create asset categories."""
        categories_data = [
            ('2001', 'Computer Equipment', 'straight_line', 60, 5.00),
            ('2002', 'Office Equipment', 'straight_line', 60, 5.00),
            ('2003', 'Furniture & Fixtures', 'straight_line', 84, 5.00),
            ('2004', 'Vehicles', 'straight_line', 60, 5.00),
            ('2005', 'Machinery', 'straight_line', 120, 5.00),
        ]

        categories = []
        for code, name, depr_method, life, residual_rate in categories_data:
            category = AssetCategory.objects.create(
                organization=organization,
                code=code,
                name=name,
                depreciation_method=depr_method,
                default_useful_life=life,
                residual_rate=Decimal(str(residual_rate)),
                is_custom=False,
                is_active=True
            )
            categories.append(category)

        return categories

    def _create_locations(self, organization):
        """Create location hierarchy."""
        locations = []

        # Create buildings
        building_a = Location.objects.create(
            organization=organization,
            name='Building A',
            location_type='building',
            level=0,
            path='Building A'
        )
        locations.append(building_a)

        building_b = Location.objects.create(
            organization=organization,
            name='Building B',
            location_type='building',
            level=0,
            path='Building B'
        )
        locations.append(building_b)

        # Create floors and rooms
        for building in [building_a, building_b]:
            for floor_num in range(1, 4):
                floor = Location.objects.create(
                    organization=organization,
                    name=f'Floor {floor_num}',
                    parent=building,
                    location_type='floor',
                    level=1,
                    path=f'{building.path} / Floor {floor_num}'
                )
                locations.append(floor)

                for room_num in range(101, 106, 2):
                    room = Location.objects.create(
                        organization=organization,
                        name=f'Room {floor_num}{room_num}',
                        parent=floor,
                        location_type='room',
                        level=2,
                        path=f'{floor.path} / Room {floor_num}{room_num}'
                    )
                    locations.append(room)

        # Create warehouse
        warehouse = Location.objects.create(
            organization=organization,
            name='Main Warehouse',
            location_type='warehouse',
            level=0,
            path='Main Warehouse'
        )
        locations.append(warehouse)

        return locations

    def _create_suppliers(self, organization, count=10):
        """Create suppliers."""
        suppliers_data = [
            ('SUP001', 'Beijing Technology Co., Ltd.', 'Zhang San', '010-12345678', 'zhang@tech.com'),
            ('SUP002', 'Shanghai Electronics Corp.', 'Li Si', '021-87654321', 'li@electronics.com'),
            ('SUP003', 'Guangzhou Furniture Ltd.', 'Wang Wu', '020-11112222', 'wang@furniture.com'),
            ('SUP004', 'Shenzhen Computer Systems', 'Zhao Liu', '0755-33334444', 'zhao@computer.com'),
            ('SUP005', 'Hangzhou Office Supplies', 'Qian Qi', '0571-55556666', 'qian@office.com'),
            ('SUP006', 'Chengdu Vehicle Services', 'Sun Ba', '028-77778888', 'sun@vehicle.com'),
            ('SUP007', 'Wuhan Machinery Works', 'Zhou Jiu', '027-99990000', 'zhou@machinery.com'),
            ('SUP008', 'Nanjing Equipment Inc.', 'Wu Shi', '025-12121212', 'wu@equipment.com'),
            ('SUP009', 'Tianjin Materials Co.', 'Zheng Yi', '022-23232323', 'zheng@materials.com'),
            ('SUP010', 'Xi\'an Industrial Supplies', 'Feng Er', '029-34343434', 'feng@industrial.com'),
        ]

        suppliers = []
        for data in suppliers_data[:count]:
            supplier = Supplier.objects.create(
                organization=organization,
                code=data[0],
                name=data[1],
                contact=data[2],
                phone=data[3],
                email=data[4],
                address=f'{data[1]} Address, China'
            )
            suppliers.append(supplier)

        return suppliers

    def _create_assets(self, organization, categories, locations, suppliers, departments, users, count=30):
        """Create assets."""
        asset_templates = [
            # Computer Equipment
            {'category': '2001', 'name': 'Desktop Computer', 'brand': 'Lenovo', 'model': 'ThinkCentre', 'price': 5000},
            {'category': '2001', 'name': 'Laptop Computer', 'brand': 'Dell', 'model': 'XPS 15', 'price': 12000},
            {'category': '2001', 'name': 'Server', 'brand': 'HP', 'model': 'ProLiant', 'price': 35000},
            {'category': '2001', 'name': 'Printer', 'brand': 'Canon', 'model': 'imageRunner', 'price': 8000},
            {'category': '2001', 'name': 'Projector', 'brand': 'Epson', 'model': 'EB-X450', 'price': 6000},
            # Office Equipment
            {'category': '2002', 'name': 'Photocopier', 'brand': 'Ricoh', 'model': 'MP C4504', 'price': 25000},
            {'category': '2002', 'name': 'Scanner', 'brand': 'Fujitsu', 'model': 'fi-7160', 'price': 4500},
            {'category': '2002', 'name': 'Shredder', 'brand': 'Fellowes', 'model': 'Powershred', 'price': 1500},
            # Furniture
            {'category': '2003', 'name': 'Office Desk', 'brand': 'Steelcase', 'model': 'Gesture', 'price': 3000},
            {'category': '2003', 'name': 'Office Chair', 'brand': 'Herman Miller', 'model': 'Aeron', 'price': 8000},
            {'category': '2003', 'name': 'Filing Cabinet', 'brand': 'Kinnarps', 'model': 'Storage', 'price': 2000},
            # Vehicles
            {'category': '2004', 'name': 'Sedan Car', 'brand': 'Volkswagen', 'model': 'Passat', 'price': 180000},
            {'category': '2004', 'name': 'SUV Vehicle', 'brand': 'Toyota', 'model': 'Prado', 'price': 350000},
            {'category': '2004', 'name': 'Van', 'brand': 'Ford', 'model': 'Transit', 'price': 120000},
        ]

        assets = []
        status_choices = ['pending', 'in_use', 'idle', 'maintenance']

        for i in range(count):
            template = asset_templates[i % len(asset_templates)]
            category = next((c for c in categories if c.code == template['category']), categories[0])

            purchase_date = timezone.now().date() - timedelta(days=random.randint(30, 1095))

            asset = Asset.objects.create(
                organization=organization,
                asset_category=category,
                asset_name=f"{template['name']} {i+1:03d}",
                specification=template['model'],
                brand=template['brand'],
                unit='台',
                serial_number=f'SN{datetime.now().strftime("%Y%m")}{random.randint(10000, 99999)}',
                purchase_price=Decimal(str(template['price'] + random.randint(-500, 500))),
                current_value=Decimal(str(template['price'] * random.uniform(0.6, 0.95))),
                accumulated_depreciation=Decimal(str(template['price'] * random.uniform(0.05, 0.4))),
                purchase_date=purchase_date,
                depreciation_start_date=purchase_date,
                useful_life=60,
                residual_rate=Decimal('5.00'),
                supplier=random.choice(suppliers) if suppliers else None,
                department=random.choice(departments) if departments else None,
                location=random.choice(locations) if locations else None,
                custodian=random.choice(users) if users else None,
                asset_status=random.choice(status_choices)
            )
            assets.append(asset)

        return assets

    def _create_consumable_categories(self, organization):
        """Create consumable categories."""
        categories_data = [
            ('CAT001', 'Office Paper'),
            ('CAT002', 'Writing Instruments'),
            ('CAT003', 'Desk Supplies'),
            ('CAT004', 'Electronics Accessories'),
            ('CAT005', 'Kitchen Supplies'),
        ]

        categories = []
        for code, name in categories_data:
            category = ConsumableCategory.objects.create(
                organization=organization,
                code=code,
                name=name,
                unit='包',
                min_stock=10,
                max_stock=100,
                reorder_point=20,
                is_active=True
            )
            categories.append(category)

        return categories

    def _create_consumables(self, organization, categories, locations, suppliers, count=20):
        """Create consumables."""
        consumable_templates = [
            {'category': 'CAT001', 'name': 'A4 Copy Paper', 'brand': 'Double A', 'unit': '包', 'price': 25.00},
            {'category': 'CAT001', 'name': 'A3 Copy Paper', 'brand': 'Double A', 'unit': '包', 'price': 35.00},
            {'category': 'CAT002', 'name': 'Ballpoint Pen (Black)', 'brand': 'M&G', 'unit': '支', 'price': 1.50},
            {'category': 'CAT002', 'name': 'Ballpoint Pen (Blue)', 'brand': 'M&G', 'unit': '支', 'price': 1.50},
            {'category': 'CAT002', 'name': 'Gel Pen', 'brand': 'Pilot', 'unit': '支', 'price': 3.00},
            {'category': 'CAT002', 'name': 'Mechanical Pencil', 'brand': 'Pentel', 'unit': '支', 'price': 5.00},
            {'category': 'CAT003', 'name': 'Stapler', 'brand': 'Max', 'unit': '个', 'price': 15.00},
            {'category': 'CAT003', 'name': 'Staples (Box)', 'brand': 'Max', 'unit': '盒', 'price': 5.00},
            {'category': 'CAT003', 'name': 'Paper Clips', 'brand': 'Deli', 'unit': '盒', 'price': 3.00},
            {'category': 'CAT003', 'name': 'Binder Clips', 'brand': 'Deli', 'unit': '盒', 'price': 8.00},
            {'category': 'CAT004', 'name': 'USB Cable (Type-C)', 'brand': 'Anker', 'unit': '根', 'price': 25.00},
            {'category': 'CAT004', 'name': 'HDMI Cable', 'brand': 'Baseus', 'unit': '根', 'price': 30.00},
            {'category': 'CAT004', 'name': 'Mouse Pad', 'brand': '3M', 'unit': '个', 'price': 20.00},
            {'category': 'CAT005', 'name': 'Paper Cups (Pack)', 'brand': 'Generic', 'unit': '包', 'price': 10.00},
            {'category': 'CAT005', 'name': 'Coffee Filters', 'brand': 'Melitta', 'unit': '盒', 'price': 15.00},
        ]

        consumables = []
        for i in range(count):
            template = consumable_templates[i % len(consumable_templates)]
            category = next((c for c in categories if c.code == template['category']), categories[0])

            current_stock = random.randint(20, 150)

            consumable = Consumable.objects.create(
                organization=organization,
                code=f'CON{datetime.now().strftime("%Y%m")}{i+1:03d}',
                name=template['name'],
                category=category,
                specification='Standard',
                brand=template['brand'],
                unit=template['unit'],
                current_stock=current_stock,
                available_stock=current_stock - random.randint(0, 10),
                locked_stock=random.randint(0, 5),
                purchase_price=Decimal(str(template['price'])),
                average_price=Decimal(str(template['price'] * random.uniform(0.95, 1.05))),
                min_stock=10,
                max_stock=100,
                reorder_point=20,
                status='normal' if current_stock > 20 else 'low_stock',
                warehouse=random.choice(locations) if locations else None
            )
            consumables.append(consumable)

        return consumables

    def _create_consumable_stocks(self, consumables, users, count=50):
        """Create consumable stock transactions."""
        transaction_types = ['purchase', 'issue', 'return', 'adjustment']
        transactions = []

        for i in range(count):
            consumable = random.choice(consumables)
            transaction_type = random.choice(transaction_types)
            quantity = random.randint(-10, 50)

            transaction = ConsumableStock.objects.create(
                organization=consumable.organization,
                consumable=consumable,
                transaction_type=transaction_type,
                quantity=quantity,
                before_stock=consumable.current_stock - quantity,
                after_stock=consumable.current_stock,
                source_type='manual',
                source_no=f'MANUAL{i+1:04d}',
                handler=random.choice(users) if users else None,
                remark=f'Manual {transaction_type} adjustment'
            )
            transactions.append(transaction)

        return transactions

    def _create_consumable_purchases(self, organization, suppliers, consumables, users, count=20):
        """Create consumable purchase orders."""
        purchases = []

        for i in range(count):
            purchase_date = timezone.now().date() - timedelta(days=random.randint(1, 90))

            purchase = ConsumablePurchase.objects.create(
                organization=organization,
                purchase_no=f'CP{purchase_date.strftime("%Y%m")}{i+1:03d}',
                purchase_date=purchase_date,
                supplier=random.choice(suppliers) if suppliers else None,
                total_amount=Decimal(str(random.uniform(100, 5000))),
                status=random.choice(['draft', 'approved', 'completed']),
                approved_by=random.choice(users) if users else None,
                approved_at=purchase_date + timedelta(days=random.randint(1, 3)) if random.random() > 0.3 else None,
                received_by=random.choice(users) if users else None,
                received_at=purchase_date + timedelta(days=random.randint(5, 10)) if random.random() > 0.5 else None,
                remark=f'Purchase order {i+1}'
            )
            purchases.append(purchase)

            # Add items - ensure unique consumables per purchase
            num_items = min(random.randint(1, 5), len(consumables))
            selected_consumables = random.sample(consumables, num_items)
            for j, consumable in enumerate(selected_consumables):
                quantity = random.randint(10, 100)
                unit_price = consumable.purchase_price

                PurchaseItem.objects.create(
                    organization=organization,
                    purchase=purchase,
                    consumable=consumable,
                    quantity=quantity,
                    unit_price=unit_price,
                    amount=Decimal(str(quantity * float(unit_price))),
                    remark=f'Item {j+1}'
                )

        return purchases

    def _create_consumable_issues(self, organization, departments, users, consumables, count=20):
        """Create consumable issue orders."""
        issues = []

        for i in range(count):
            issue_date = timezone.now().date() - timedelta(days=random.randint(1, 60))

            issue = ConsumableIssue.objects.create(
                organization=organization,
                issue_no=f'CI{issue_date.strftime("%Y%m")}{i+1:03d}',
                issue_date=issue_date,
                applicant=random.choice(users) if users else None,
                department=organization,  # department field expects Organization instance
                issue_reason=f'Daily office supplies request {i+1}',
                status=random.choice(['draft', 'approved', 'completed']),
                approved_by=random.choice(users) if users else None,
                approved_at=issue_date + timedelta(days=1) if random.random() > 0.3 else None,
                issued_by=random.choice(users) if users else None,
                issued_at=issue_date + timedelta(days=random.randint(1, 3)) if random.random() > 0.5 else None,
                remark=f'Issue order {i+1}'
            )
            issues.append(issue)

            # Add items - ensure unique consumables per issue
            num_items = min(random.randint(1, 4), len(consumables))
            selected_consumables = random.sample(consumables, num_items)
            for j, consumable in enumerate(selected_consumables):
                quantity = random.randint(1, 20)

                IssueItem.objects.create(
                    organization=organization,
                    issue=issue,
                    consumable=consumable,
                    quantity=quantity,
                    snapshot_before_stock=consumable.current_stock,
                    remark=f'Item {j+1}'
                )

        return issues

    def _create_purchase_requests(self, organization, departments, users, categories, count=20):
        """Create purchase requests."""
        requests = []

        for i in range(count):
            request_date = timezone.now().date() - timedelta(days=random.randint(1, 120))

            request = PurchaseRequest.objects.create(
                organization=organization,
                request_no=f'PR{request_date.strftime("%Y%m")}{i+1:03d}',
                request_date=request_date,
                expected_date=request_date + timedelta(days=random.randint(15, 45)),
                status=random.choice(['draft', 'submitted', 'approved', 'processing', 'completed']),
                applicant=random.choice(users) if users else None,
                department=organization,  # department field expects Organization instance
                reason=f'Asset procurement request for project {i+1}',
                budget_amount=Decimal(str(random.uniform(10000, 200000))),
                approved_by=random.choice(users) if users else None,
                approved_at=request_date + timedelta(days=random.randint(2, 7)) if random.random() > 0.4 else None,
                approval_comment=f'Approved for budget year {request_date.year}',
                remark=f'Purchase request {i+1}'
            )
            requests.append(request)

            # Add items
            num_items = random.randint(1, 5)
            for j in range(num_items):
                category = random.choice(categories)

                PurchaseRequestItem.objects.create(
                    organization=organization,
                    purchase_request=request,
                    asset_category=category,
                    sequence=j+1,
                    item_name=f'{category.name} Item {j+1}',
                    specification='Standard configuration',
                    brand='Various',
                    quantity=random.randint(1, 20),
                    unit='台',
                    unit_price=Decimal(str(random.uniform(1000, 20000))),
                    total_amount=Decimal('0'),
                    suggested_supplier='Beijing Technology Co., Ltd.',
                    remark=f'Item {j+1}'
                )

        return requests

    def _create_asset_receipts(self, organization, users, suppliers, categories, count=15):
        """Create asset receipts."""
        receipts = []

        for i in range(count):
            receipt_date = timezone.now().date() - timedelta(days=random.randint(1, 365))

            receipt = AssetReceipt.objects.create(
                organization=organization,
                receipt_no=f'RC{receipt_date.strftime("%Y%m")}{i+1:03d}',
                receipt_date=receipt_date,
                receipt_type=random.choice(['purchase', 'transfer', 'return']),
                supplier=random.choice(suppliers).name if suppliers else 'Unknown Supplier',
                delivery_no=f'DN{receipt_date.strftime("%Y%m%d")}{random.randint(100, 999)}',
                receiver=random.choice(users) if users else None,
                inspector=random.choice(users) if users else None,
                status=random.choice(['draft', 'submitted', 'inspecting', 'passed', 'rejected']),
                inspection_result='All items passed quality inspection' if random.random() > 0.2 else 'Some items defective',
                passed_at=receipt_date + timedelta(days=1) if random.random() > 0.5 else None,
                remark=f'Receipt {i+1}'
            )
            receipts.append(receipt)

            # Add items
            num_items = random.randint(1, 5)
            for j in range(num_items):
                category = random.choice(categories)
                ordered_qty = random.randint(1, 20)
                received_qty = ordered_qty - random.randint(0, 2)
                qualified_qty = received_qty - random.randint(0, 1)

                AssetReceiptItem.objects.create(
                    organization=organization,
                    asset_receipt=receipt,
                    asset_category=category,
                    sequence=j+1,
                    item_name=f'{category.name} Item {j+1}',
                    specification='Standard',
                    brand='Various',
                    ordered_quantity=ordered_qty,
                    received_quantity=received_qty,
                    qualified_quantity=qualified_qty,
                    defective_quantity=received_qty - qualified_qty,
                    unit_price=Decimal(str(random.uniform(1000, 15000))),
                    total_amount=Decimal('0'),
                    asset_generated=False,
                    remark=f'Item {j+1}'
                )

        return receipts

    def _create_maintenance_records(self, organization, assets, users, count=20):
        """Create maintenance records."""
        priorities = ['low', 'normal', 'high', 'urgent']
        statuses = ['reported', 'assigned', 'processing', 'completed', 'cancelled']
        records = []

        for i in range(count):
            report_time = timezone.now() - timedelta(days=random.randint(1, 180))

            maintenance = Maintenance.objects.create(
                organization=organization,
                maintenance_no=f'MT{report_time.strftime("%Y%m")}{i+1:03d}',
                status=random.choice(statuses),
                priority=random.choice(priorities),
                asset=random.choice(assets) if assets else None,
                reporter=random.choice(users) if users else None,
                report_time=report_time,
                fault_description=f'Equipment malfunction detected: {random.choice(["Power issue", "Display problem", "Noise", "Overheating", "Software error", "Mechanical failure"])}',
                fault_photo_urls=[f'http://example.com/photos/fault_{i}.jpg'] if random.random() > 0.7 else [],
                technician=random.choice(users) if users else None,
                assigned_at=report_time + timedelta(hours=random.randint(1, 24)) if random.random() > 0.3 else None,
                start_time=report_time + timedelta(days=random.randint(0, 2)) if random.random() > 0.5 else None,
                end_time=report_time + timedelta(days=random.randint(1, 5)) if random.random() > 0.6 else None,
                work_hours=Decimal(str(random.uniform(0.5, 8.0))) if random.random() > 0.4 else None,
                fault_cause='Component wear and tear' if random.random() > 0.5 else None,
                repair_method='Replaced defective parts' if random.random() > 0.4 else None,
                replaced_parts='Power supply unit, Cooling fan' if random.random() > 0.6 else None,
                repair_result='Equipment restored to normal operation' if random.random() > 0.3 else None,
                labor_cost=Decimal(str(random.uniform(100, 500))),
                material_cost=Decimal(str(random.uniform(50, 1000))),
                other_cost=Decimal(str(random.uniform(0, 100))),
                total_cost=Decimal('0'),
                verified_by=random.choice(users) if users else None,
                verified_at=report_time + timedelta(days=random.randint(2, 7)) if random.random() > 0.5 else None,
                verification_result='Verified functional' if random.random() > 0.3 else None,
                remark=f'Maintenance record {i+1}'
            )
            maintenance.calculate_total_cost()
            records.append(maintenance)

        return records

    def _create_maintenance_plans(self, organization, categories, assets, users, count=10):
        """Create maintenance plans."""
        cycle_types = ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']
        plans = []

        for i in range(count):
            start_date = timezone.now().date() + timedelta(days=random.randint(1, 30))
            end_date = start_date + timedelta(days=random.randint(180, 730)) if random.random() > 0.3 else None

            plan = MaintenancePlan.objects.create(
                organization=organization,
                plan_name=f'{random.choice(["Routine", "Preventive", "Periodic"])} Maintenance Plan {i+1}',
                plan_code=f'MP{datetime.now().strftime("%Y%m")}{i+1:03d}',
                status=random.choice(['active', 'paused', 'archived']),
                target_type=random.choice(['category', 'asset', 'location']),
                cycle_type=random.choice(cycle_types),
                cycle_value=random.randint(1, 4),
                start_date=start_date,
                end_date=end_date,
                remind_days_before=random.randint(3, 7),
                maintenance_content=f'Perform standard {random.choice(cycle_types)} maintenance checks',
                estimated_hours=Decimal(str(random.uniform(2, 16))),
                remark=f'Maintenance plan {i+1}'
            )

            # Add targets
            if plan.target_type == 'category':
                num_categories = random.randint(1, 3)
                for j in range(num_categories):
                    plan.asset_categories.add(random.choice(categories))
            elif plan.target_type == 'asset':
                num_assets = random.randint(1, 10)
                for j in range(num_assets):
                    plan.assets.add(random.choice(assets))

            # Add remind users
            if users:
                num_users = random.randint(1, min(3, len(users)))
                for j in range(num_users):
                    plan.remind_users.add(users[j])

            plans.append(plan)

        return plans

    def _create_disposal_requests(self, organization, departments, users, assets, count=10):
        """Create disposal requests."""
        disposal_types = ['scrap', 'sale', 'donation', 'transfer', 'destroy']
        reasons = ['damage', 'obsolete', 'expired', 'excess', 'other']
        statuses = ['draft', 'submitted', 'appraising', 'approved', 'executing', 'completed', 'cancelled']
        requests = []

        for i in range(count):
            request_date = timezone.now().date() - timedelta(days=random.randint(1, 90))

            request = DisposalRequest.objects.create(
                organization=organization,
                request_no=f'DS{request_date.strftime("%Y%m")}{i+1:03d}',
                status=random.choice(statuses),
                disposal_type=random.choice(disposal_types),
                applicant=random.choice(users) if users else None,
                department=organization,  # department field expects Organization instance
                request_date=request_date,
                disposal_reason=f'Asset disposal request: {random.choice(["Beyond repair", "Technology upgrade", "No longer needed", "End of life"])}.',
                reason_type=random.choice(reasons),
                current_approver=random.choice(users) if users else None,
                remark=f'Disposal request {i+1}'
            )
            requests.append(request)

            # Add items
            num_items = random.randint(1, 5)
            for j in range(num_items):
                asset = random.choice(assets) if assets else None

                original_value = Decimal(str(random.uniform(5000, 100000)))
                accumulated = original_value * Decimal(str(random.uniform(0.3, 0.9)))

                DisposalItem.objects.create(
                    organization=organization,
                    disposal_request=request,
                    asset=asset,
                    sequence=j+1,
                    original_value=original_value,
                    accumulated_depreciation=accumulated,
                    net_value=original_value - accumulated,
                    appraisal_result=f'Asset condition: {random.choice(["Poor", "Fair", "Good"])}',
                    residual_value=Decimal(str(random.uniform(100, 5000))) if random.random() > 0.5 else None,
                    appraised_by=random.choice(users) if users and random.random() > 0.4 else None,
                    appraised_at=request_date + timedelta(days=random.randint(1, 5)) if random.random() > 0.5 else None,
                    disposal_executed=random.random() > 0.7,
                    executed_at=request_date + timedelta(days=random.randint(10, 20)) if random.random() > 0.8 else None,
                    actual_residual_value=Decimal(str(random.uniform(50, 3000))) if random.random() > 0.6 else None,
                    buyer_info='Beijing Second-hand Market' if random.random() > 0.8 else None,
                    remark=f'Disposal item {j+1}'
                )

        return requests

    def _create_asset_pickups(self, organization, departments, users, assets, count=15):
        """Create asset pickup orders."""
        statuses = ['draft', 'pending', 'approved', 'rejected', 'completed', 'cancelled']
        pickups = []

        for i in range(count):
            pickup_date = timezone.now().date() - timedelta(days=random.randint(1, 60))

            pickup = AssetPickup.objects.create(
                organization=organization,
                pickup_no=f'LY{pickup_date.strftime("%Y%m")}{i+1:03d}',
                applicant=random.choice(users) if users else None,
                department=random.choice(departments) if departments else None,
                pickup_date=pickup_date,
                pickup_reason=f'Asset pickup for {random.choice(["new project", "daily work", "business trip", "remote work"])}.',
                status=random.choice(statuses),
                approved_by=random.choice(users) if users and random.random() > 0.3 else None,
                approved_at=pickup_date + timedelta(days=1) if random.random() > 0.5 else None,
                approval_comment='Approved' if random.random() > 0.7 else '',
                completed_at=pickup_date + timedelta(days=random.randint(2, 5)) if random.random() > 0.6 else None
            )
            pickups.append(pickup)

            # Add items
            num_items = random.randint(1, 3)
            for j in range(num_items):
                asset = random.choice(assets) if assets else None

                PickupItem.objects.create(
                    organization=organization,
                    pickup=pickup,
                    asset=asset,
                    quantity=1,
                    remark=f'Pickup item {j+1}',
                    snapshot_original_location=asset.location if asset else None,
                    snapshot_original_custodian=asset.custodian if asset else None
                )

        return pickups

    def _create_asset_transfers(self, organization, departments, users, assets, locations, count=15):
        """Create asset transfer orders."""
        statuses = ['draft', 'pending', 'out_approved', 'approved', 'rejected', 'completed', 'cancelled']
        transfers = []

        for i in range(count):
            transfer_date = timezone.now().date() - timedelta(days=random.randint(1, 90))

            from_dept = random.choice(departments) if departments else None
            to_dept = random.choice([d for d in departments] if departments else [])
            while from_dept and to_dept and from_dept.id == to_dept.id:
                to_dept = random.choice(departments)

            transfer = AssetTransfer.objects.create(
                organization=organization,
                transfer_no=f'TF{transfer_date.strftime("%Y%m")}{i+1:03d}',
                from_department=from_dept,
                to_department=to_dept,
                transfer_date=transfer_date,
                transfer_reason=f'Asset transfer due to {random.choice(["department reorganization", "project requirements", "resource optimization"])}.',
                status=random.choice(statuses),
                from_approved_by=random.choice(users) if users and random.random() > 0.4 else None,
                from_approved_at=transfer_date + timedelta(days=1) if random.random() > 0.5 else None,
                from_approve_comment='Approved for transfer' if random.random() > 0.7 else '',
                to_approved_by=random.choice(users) if users and random.random() > 0.4 else None,
                to_approved_at=transfer_date + timedelta(days=random.randint(1, 3)) if random.random() > 0.5 else None,
                to_approve_comment='Accepted' if random.random() > 0.7 else '',
                completed_at=transfer_date + timedelta(days=random.randint(3, 7)) if random.random() > 0.6 else None
            )
            transfers.append(transfer)

            # Add items
            num_items = random.randint(1, 4)
            for j in range(num_items):
                asset = random.choice(assets) if assets else None

                TransferItem.objects.create(
                    organization=organization,
                    transfer=transfer,
                    asset=asset,
                    from_location=asset.location if asset else None,
                    from_custodian=asset.custodian if asset else None,
                    to_location=random.choice(locations) if locations else None,
                    remark=f'Transfer item {j+1}'
                )

        return transfers

    def _create_asset_returns(self, organization, users, assets, locations, count=10):
        """Create asset return orders."""
        statuses = ['draft', 'pending', 'confirmed', 'completed', 'cancelled']
        returns = []

        for i in range(count):
            return_date = timezone.now().date() - timedelta(days=random.randint(1, 60))

            asset_return = AssetReturn.objects.create(
                organization=organization,
                return_no=f'RT{return_date.strftime("%Y%m")}{i+1:03d}',
                returner=random.choice(users) if users else None,
                return_date=return_date,
                return_reason=f'Asset return due to {random.choice(["project completion", "resignation", "equipment upgrade", "no longer needed"])}.',
                status=random.choice(statuses),
                return_location=random.choice(locations) if locations else None,
                confirmed_by=random.choice(users) if users and random.random() > 0.4 else None,
                confirmed_at=return_date + timedelta(days=random.randint(1, 3)) if random.random() > 0.5 else None,
                reject_reason='' if random.random() > 0.2 else 'Condition not acceptable',
                completed_at=return_date + timedelta(days=random.randint(2, 5)) if random.random() > 0.6 else None
            )
            returns.append(asset_return)

            # Add items
            num_items = random.randint(1, 3)
            for j in range(num_items):
                asset = random.choice(assets) if assets else None

                ReturnItem.objects.create(
                    organization=organization,
                    asset_return=asset_return,
                    asset=asset,
                    asset_status=random.choice(['idle', 'maintenance', 'scrapped']),
                    condition_description=random.choice(['Good condition', 'Minor scratches', 'Needs cleaning', 'Requires maintenance']),
                    remark=f'Return item {j+1}'
                )

        return returns

    def _create_asset_loans(self, organization, users, assets, count=15):
        """Create asset loan orders."""
        statuses = ['draft', 'pending', 'approved', 'rejected', 'borrowed', 'overdue', 'returned', 'cancelled']
        conditions = ['good', 'minor_damage', 'major_damage', 'lost']
        loans = []

        for i in range(count):
            borrow_date = timezone.now().date() - timedelta(days=random.randint(1, 120))
            expected_return = borrow_date + timedelta(days=random.randint(7, 60))

            is_returned = random.random() > 0.5
            actual_return = borrow_date + timedelta(days=random.randint(1, 30)) if is_returned else None

            loan = AssetLoan.objects.create(
                organization=organization,
                loan_no=f'LN{borrow_date.strftime("%Y%m")}{i+1:03d}',
                borrower=random.choice(users) if users else None,
                borrow_date=borrow_date,
                expected_return_date=expected_return,
                actual_return_date=actual_return,
                loan_reason=f'Asset loan for {random.choice(["business trip", "client presentation", "remote work", "temporary project"])}.',
                status='returned' if is_returned else random.choice(['draft', 'pending', 'approved', 'borrowed', 'overdue', 'cancelled']),
                approved_by=random.choice(users) if users and random.random() > 0.3 else None,
                approved_at=borrow_date + timedelta(hours=random.randint(1, 24)) if random.random() > 0.5 else None,
                approval_comment='Approved' if random.random() > 0.8 else '',
                lent_by=random.choice(users) if users and random.random() > 0.4 else None,
                lent_at=borrow_date + timedelta(days=random.randint(0, 2)) if random.random() > 0.5 else None,
                returned_at=actual_return + timedelta(days=1) if is_returned and random.random() > 0.5 else None,
                return_confirmed_by=random.choice(users) if users and is_returned and random.random() > 0.4 else None,
                asset_condition=random.choice(conditions) if is_returned else '',
                return_comment='Returned in good condition' if is_returned and random.random() > 0.7 else ''
            )
            loans.append(loan)

            # Add items
            num_items = random.randint(1, 2)
            for j in range(num_items):
                asset = random.choice(assets) if assets else None

                LoanItem.objects.create(
                    organization=organization,
                    loan=loan,
                    asset=asset,
                    remark=f'Loan item {j+1}'
                )

        return loans

    def _create_inventory_tasks(self, organization, departments, categories, users, count=10):
        """Create inventory tasks."""
        types = ['full', 'partial', 'department', 'category']
        statuses = ['draft', 'pending', 'in_progress', 'completed', 'cancelled']
        tasks = []

        for i in range(count):
            planned_date = timezone.now().date() + timedelta(days=random.randint(-30, 90))

            task = InventoryTask.objects.create(
                organization=organization,
                task_name=f'{random.choice(["Annual", "Quarterly", "Monthly", "Special"])} Inventory {i+1}',
                description=f'Inventory task for {random.choice(["year-end audit", "asset verification", "loss prevention", "compliance check"])}.',
                inventory_type=random.choice(types),
                status=random.choice(statuses),
                department=random.choice(departments) if departments and random.random() > 0.5 else None,
                category=random.choice(categories) if categories and random.random() > 0.5 else None,
                sample_ratio=random.randint(10, 50) if random.random() > 0.7 else None,
                planned_date=planned_date,
                started_at=planned_date + timedelta(days=1) if random.random() > 0.5 else None,
                completed_at=planned_date + timedelta(days=random.randint(3, 10)) if random.random() > 0.6 else None,
                total_count=random.randint(50, 500),
                scanned_count=random.randint(0, 500),
                normal_count=random.randint(0, 450),
                surplus_count=random.randint(0, 10),
                missing_count=random.randint(0, 10),
                damaged_count=random.randint(0, 5),
                location_changed_count=random.randint(0, 15),
                notes=f'Inventory completed without issues' if random.random() > 0.7 else 'Some discrepancies found'
            )
            tasks.append(task)

            # Add executors
            if users:
                num_executors = random.randint(1, min(3, len(users)))
                for j in range(num_executors):
                    from apps.inventory.models import InventoryTaskExecutor
                    InventoryTaskExecutor.objects.create(
                        task=task,
                        executor=users[j],
                        is_primary=(j == 0),
                        completed_count=random.randint(0, 200)
                    )

        return tasks

    def _create_inventory_snapshots(self, tasks, assets, users):
        """Create inventory snapshots."""
        snapshots = []

        for task in tasks:
            # Create snapshots for some assets
            num_snapshots = random.randint(10, min(50, len(assets)))
            selected_assets = random.sample(assets, min(num_snapshots, len(assets)))

            for asset in selected_assets:
                snapshot = InventorySnapshot.objects.create(
                    organization=task.organization,
                    task=task,
                    asset=asset,
                    asset_code=asset.asset_code,
                    asset_name=asset.asset_name,
                    asset_category_id=str(asset.asset_category_id),
                    asset_category_name=asset.asset_category.name if asset.asset_category else '',
                    location_id=str(asset.location_id) if asset.location_id else None,
                    location_name=asset.location.name if asset.location else '',
                    custodian_id=str(asset.custodian_id) if asset.custodian_id else None,
                    custodian_name=asset.custodian.get_full_name() if asset.custodian else '',
                    department_id=str(asset.department_id) if asset.department_id else None,
                    department_name=asset.department.full_path_name if asset.department else '',
                    asset_status=asset.asset_status,
                    snapshot_data={'notes': 'Snapshot created'},
                    scanned=random.random() > 0.5,
                    scanned_at=timezone.now() - timedelta(days=random.randint(1, 30)) if random.random() > 0.6 else None,
                    scan_count=random.randint(0, 3)
                )
                snapshots.append(snapshot)

        return snapshots

    def _create_inventory_scans(self, tasks, assets, users, count=50):
        """Create inventory scans."""
        statuses = ['normal', 'damaged', 'missing', 'location_changed', 'custodian_changed', 'surplus']
        methods = ['qr', 'rfid', 'manual']
        scans = []

        for i in range(count):
            task = random.choice(tasks) if tasks else None
            if not task:
                continue

            asset = random.choice(assets) if assets else None
            status = random.choice(statuses)

            scan = InventoryScan.objects.create(
                organization=task.organization,
                task=task,
                asset=asset,
                qr_code=asset.qr_code if asset else f'UNKNOWN_QR_{i}',
                scanned_by=random.choice(users) if users else None,
                scanned_at=timezone.now() - timedelta(days=random.randint(1, 30)),
                scan_method=random.choice(methods),
                scan_status=status,
                original_location_id=str(asset.location_id) if asset and asset.location_id else None,
                original_location_name=asset.location.name if asset and asset.location else '',
                original_custodian_id=str(asset.custodian_id) if asset and asset.custodian_id else None,
                original_custodian_name=asset.custodian.get_full_name() if asset and asset.custodian else '',
                actual_location_id=str(asset.location_id) if asset and asset.location_id and random.random() > 0.3 else None,
                actual_location_name=asset.location.name if asset and asset.location and random.random() > 0.3 else '',
                actual_custodian_id=str(asset.custodian_id) if asset and asset.custodian_id and random.random() > 0.3 else None,
                actual_custodian_name=asset.custodian.get_full_name() if asset and asset.custodian and random.random() > 0.3 else '',
                photos=[f'http://example.com/photos/scan_{i}.jpg'] if random.random() > 0.8 else [],
                remark=f'Scan record {i+1}'
            )
            scans.append(scan)

        return scans
