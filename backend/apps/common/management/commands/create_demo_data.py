"""
Django management command to create demo data for all business objects.

Generates 20-50 realistic demo records for testing and demonstration purposes.
Handles all major business objects: Assets, Consumables, Lifecycle, Inventory, Organizations.

Usage:
    python manage.py create_demo_data [--count N] [--organization ORG_ID]
"""
import random
from decimal import Decimal
from datetime import datetime, timedelta, date, time as dt_time

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
from apps.finance.models import FinanceVoucher, VoucherEntry, VoucherTemplate
from apps.integration.models import IntegrationConfig, IntegrationLog, IntegrationSyncTask
from apps.integration.constants import (
    IntegrationSystemType,
    IntegrationModuleType,
    SyncDirection,
    SyncStatus,
    HealthStatus,
)
from apps.projects.models import AssetProject, ProjectAsset, ProjectMember

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
        parser.add_argument(
            '--top-up-existing',
            action='store_true',
            help='Top up existing models to the requested minimum count instead of skipping them'
        )

    def handle(self, *args, **options):
        count = options['count']
        org_id = options.get('organization')
        skip_existing = options['skip_existing']
        top_up_existing = options['top_up_existing']

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

        asset_project_target = self._resolve_target_count(count, minimum=20, maximum=30)
        finance_voucher_target = self._resolve_target_count(count, minimum=20, maximum=30)
        finance_integration_target = finance_voucher_target
        receipt_target = self._resolve_target_count(count, minimum=20, maximum=30)
        maintenance_plan_target = self._resolve_target_count(count, minimum=20, maximum=30)
        disposal_target = self._resolve_target_count(count, minimum=20, maximum=30)
        pickup_target = self._resolve_target_count(count, minimum=20, maximum=30)
        transfer_target = self._resolve_target_count(count, minimum=20, maximum=30)
        return_target = self._resolve_target_count(count, minimum=20, maximum=30)
        loan_target = self._resolve_target_count(count, minimum=20, maximum=30)
        inventory_task_target = self._resolve_target_count(count, minimum=20, maximum=30)
        inventory_scan_target = self._resolve_target_count(count, minimum=20, maximum=50)

        # 5. Create Asset Projects
        if top_up_existing:
            asset_projects, _ = self._seed_or_top_up_records(
                queryset=AssetProject.objects.filter(organization=organization, is_deleted=False),
                create_callback=lambda missing: self._create_asset_projects(
                    organization,
                    departments,
                    users,
                    count=missing,
                ),
                stats=stats,
                stats_key='asset_projects',
                label='asset projects',
                skip_existing=skip_existing,
                top_up_existing=top_up_existing,
                target_count=asset_project_target,
            )
        elif not skip_existing or not AssetProject.objects.filter(organization=organization).exists():
            asset_projects = self._create_asset_projects(organization, departments, users, count=max(20, min(count, 30)))
            stats['asset_projects'] = len(asset_projects)
            self.stdout.write(f'  Created {len(asset_projects)} asset projects')
        else:
            asset_projects = list(AssetProject.objects.filter(organization=organization, is_deleted=False))
            stats['asset_projects'] = len(asset_projects)
            self.stdout.write(f'  Using existing {len(asset_projects)} asset projects')

        # 6. Create Project Members
        if asset_projects and (not skip_existing or not ProjectMember.objects.filter(organization=organization).exists()):
            project_members = self._create_project_members(organization, asset_projects, users)
            stats['project_members'] = len(project_members)
            self.stdout.write(f'  Created {len(project_members)} project members')
        else:
            project_members = list(ProjectMember.objects.filter(organization=organization, is_deleted=False))
            stats['project_members'] = len(project_members)
            self.stdout.write(f'  Using existing {len(project_members)} project members')

        # 7. Create Project Asset Allocations
        if asset_projects and assets and (not skip_existing or not ProjectAsset.objects.filter(organization=organization).exists()):
            project_assets = self._create_project_assets(
                organization,
                asset_projects,
                assets,
                users,
                locations,
                count=max(20, min(count, len(assets))),
            )
            stats['project_assets'] = len(project_assets)
            self.stdout.write(f'  Created {len(project_assets)} project asset allocations')
        else:
            project_assets = list(ProjectAsset.objects.filter(organization=organization, is_deleted=False))
            stats['project_assets'] = len(project_assets)
            self.stdout.write(f'  Using existing {len(project_assets)} project asset allocations')

        # 8. Create Voucher Templates
        if top_up_existing:
            voucher_templates, _ = self._seed_or_top_up_records(
                queryset=VoucherTemplate.objects.filter(organization=organization, is_deleted=False),
                create_callback=lambda missing: self._create_voucher_templates(
                    organization,
                    users[0] if users else None,
                    count=missing,
                ),
                stats=stats,
                stats_key='voucher_templates',
                label='voucher templates',
                skip_existing=skip_existing,
                top_up_existing=top_up_existing,
                target_count=5,
            )
        elif not skip_existing or not VoucherTemplate.objects.filter(organization=organization).exists():
            voucher_templates = self._create_voucher_templates(organization, users[0] if users else None)
            stats['voucher_templates'] = len(voucher_templates)
            self.stdout.write(f'  Created {len(voucher_templates)} voucher templates')
        else:
            voucher_templates = list(VoucherTemplate.objects.filter(organization=organization, is_deleted=False))
            stats['voucher_templates'] = len(voucher_templates)
            self.stdout.write(f'  Using existing {len(voucher_templates)} voucher templates')

        # 9. Create Finance Vouchers and Entries
        if top_up_existing:
            existing_finance_vouchers = list(FinanceVoucher.objects.filter(organization=organization, is_deleted=False))
            existing_voucher_count = len(existing_finance_vouchers)
            existing_entry_count = VoucherEntry.objects.filter(organization=organization, is_deleted=False).count()
            missing_voucher_count = max(0, finance_voucher_target - existing_voucher_count)

            if missing_voucher_count > 0:
                created_finance_vouchers, created_voucher_entries = self._create_finance_vouchers(
                    organization,
                    users,
                    count=missing_voucher_count,
                )
                finance_vouchers = existing_finance_vouchers + created_finance_vouchers
                voucher_entries = list(VoucherEntry.objects.filter(organization=organization, is_deleted=False))
                stats['finance_vouchers'] = len(finance_vouchers)
                stats['voucher_entries'] = len(voucher_entries)
                self.stdout.write(f'  Topped up finance vouchers by {len(created_finance_vouchers)} to {len(finance_vouchers)}')
                self.stdout.write(
                    f'  Added {len(created_voucher_entries)} voucher entries to reach {len(voucher_entries)} total voucher entries'
                )
            else:
                finance_vouchers = existing_finance_vouchers
                voucher_entries = list(VoucherEntry.objects.filter(organization=organization, is_deleted=False))
                stats['finance_vouchers'] = len(finance_vouchers)
                stats['voucher_entries'] = len(voucher_entries)
                self.stdout.write(f'  Using existing {len(finance_vouchers)} finance vouchers')
                self.stdout.write(f'  Using existing {len(voucher_entries)} voucher entries')
        elif not skip_existing or not FinanceVoucher.objects.filter(organization=organization).exists():
            finance_vouchers, voucher_entries = self._create_finance_vouchers(
                organization,
                users,
                count=max(20, min(count, 30)),
            )
            stats['finance_vouchers'] = len(finance_vouchers)
            stats['voucher_entries'] = len(voucher_entries)
            self.stdout.write(f'  Created {len(finance_vouchers)} finance vouchers')
            self.stdout.write(f'  Created {len(voucher_entries)} voucher entries')
        else:
            finance_vouchers = list(FinanceVoucher.objects.filter(organization=organization, is_deleted=False))
            voucher_entries = list(VoucherEntry.objects.filter(organization=organization, is_deleted=False))
            stats['finance_vouchers'] = len(finance_vouchers)
            stats['voucher_entries'] = len(voucher_entries)
            self.stdout.write(f'  Using existing {len(finance_vouchers)} finance vouchers')
            self.stdout.write(f'  Using existing {len(voucher_entries)} voucher entries')

        # 10. Ensure Finance Integration Config
        finance_integration_config = self._get_or_create_finance_integration_config(
            organization,
            created_by=users[0] if users else None,
        )
        finance_integration_config_count = IntegrationConfig.objects.filter(
            organization=organization,
            enabled_modules__contains=[IntegrationModuleType.FINANCE],
            is_deleted=False,
        ).count()
        stats['integration_configs'] = finance_integration_config_count
        self.stdout.write(f'  Using existing {finance_integration_config_count} finance integration configs')

        # 11. Create Finance Integration Tasks and Logs
        if top_up_existing and finance_vouchers:
            existing_integration_tasks = list(
                IntegrationSyncTask.objects.filter(
                    organization=organization,
                    module_type=IntegrationModuleType.FINANCE,
                    is_deleted=False,
                )
            )
            existing_integration_logs = list(
                IntegrationLog.objects.filter(
                    organization=organization,
                    business_type='finance_voucher',
                    is_deleted=False,
                )
            )
            vouchers_without_logs = [
                voucher for voucher in finance_vouchers
                if not IntegrationLog.objects.filter(
                    organization=organization,
                    business_type='finance_voucher',
                    business_id=str(voucher.id),
                    is_deleted=False,
                ).exists()
            ]
            if len(existing_integration_logs) < finance_integration_target and vouchers_without_logs:
                created_tasks, created_logs = self._create_finance_integration_activity(
                    organization,
                    vouchers_without_logs,
                    users,
                    finance_integration_config,
                )
                integration_tasks = existing_integration_tasks + created_tasks
                integration_logs = existing_integration_logs + created_logs
                stats['integration_sync_tasks'] = len(integration_tasks)
                stats['integration_logs'] = len(integration_logs)
                self.stdout.write(
                    f'  Topped up finance integration sync tasks by {len(created_tasks)} to {len(integration_tasks)}'
                )
                self.stdout.write(
                    f'  Topped up finance integration logs by {len(created_logs)} to {len(integration_logs)}'
                )
            else:
                integration_tasks = existing_integration_tasks
                integration_logs = existing_integration_logs
                stats['integration_sync_tasks'] = len(integration_tasks)
                stats['integration_logs'] = len(integration_logs)
                self.stdout.write(f'  Using existing {len(integration_tasks)} finance integration sync tasks')
                self.stdout.write(f'  Using existing {len(integration_logs)} finance integration logs')
        elif finance_vouchers and (
            not skip_existing
            or not IntegrationLog.objects.filter(
                organization=organization,
                business_type='finance_voucher',
            ).exists()
        ):
            integration_tasks, integration_logs = self._create_finance_integration_activity(
                organization,
                finance_vouchers,
                users,
                finance_integration_config,
            )
            stats['integration_sync_tasks'] = len(integration_tasks)
            stats['integration_logs'] = len(integration_logs)
            self.stdout.write(f'  Created {len(integration_tasks)} finance integration sync tasks')
            self.stdout.write(f'  Created {len(integration_logs)} finance integration logs')
        else:
            integration_tasks = list(
                IntegrationSyncTask.objects.filter(
                    organization=organization,
                    module_type=IntegrationModuleType.FINANCE,
                    is_deleted=False,
                )
            )
            integration_logs = list(IntegrationLog.objects.filter(organization=organization, business_type='finance_voucher', is_deleted=False))
            stats['integration_sync_tasks'] = len(integration_tasks)
            stats['integration_logs'] = len(integration_logs)
            self.stdout.write(f'  Using existing {len(integration_tasks)} finance integration sync tasks')
            self.stdout.write(f'  Using existing {len(integration_logs)} finance integration logs')

        # 12. Create Consumable Categories
        if not skip_existing or not ConsumableCategory.objects.filter(organization=organization).exists():
            consumable_categories = self._create_consumable_categories(organization)
            stats['consumable_categories'] = len(consumable_categories)
            self.stdout.write(f'  Created {len(consumable_categories)} consumable categories')
        else:
            consumable_categories = list(ConsumableCategory.objects.filter(organization=organization, is_deleted=False))
            stats['consumable_categories'] = len(consumable_categories)
            self.stdout.write(f'  Using existing {len(consumable_categories)} consumable categories')

        # 13. Create Consumables
        if not skip_existing or not Consumable.objects.filter(organization=organization).exists():
            consumables = self._create_consumables(organization, consumable_categories, locations, suppliers, count=20)
            stats['consumables'] = len(consumables)
            self.stdout.write(f'  Created {len(consumables)} consumables')
        else:
            consumables = list(Consumable.objects.filter(organization=organization, is_deleted=False))
            stats['consumables'] = len(consumables)
            self.stdout.write(f'  Using existing {len(consumables)} consumables')

        # 14. Create Consumable Stock Transactions
        if not skip_existing or not ConsumableStock.objects.filter(organization=organization).exists():
            stock_transactions = self._create_consumable_stocks(consumables, users, count=min(count, 50))
            stats['consumable_stocks'] = len(stock_transactions)
            self.stdout.write(f'  Created {len(stock_transactions)} stock transactions')
        else:
            stock_transactions = list(ConsumableStock.objects.filter(organization=organization, is_deleted=False))
            stats['consumable_stocks'] = len(stock_transactions)
            self.stdout.write(f'  Using existing {len(stock_transactions)} stock transactions')

        # 15. Create Consumable Purchases
        if not skip_existing or not ConsumablePurchase.objects.filter(organization=organization).exists():
            consumable_purchases = self._create_consumable_purchases(organization, suppliers, consumables, users, count=min(count, 20))
            stats['consumable_purchases'] = len(consumable_purchases)
            self.stdout.write(f'  Created {len(consumable_purchases)} consumable purchases')
        else:
            consumable_purchases = list(ConsumablePurchase.objects.filter(organization=organization, is_deleted=False))
            stats['consumable_purchases'] = len(consumable_purchases)
            self.stdout.write(f'  Using existing {len(consumable_purchases)} consumable purchases')

        # 16. Create Consumable Issues
        if not skip_existing or not ConsumableIssue.objects.filter(organization=organization).exists():
            consumable_issues = self._create_consumable_issues(organization, departments, users, consumables, count=min(count, 20))
            stats['consumable_issues'] = len(consumable_issues)
            self.stdout.write(f'  Created {len(consumable_issues)} consumable issues')
        else:
            consumable_issues = list(ConsumableIssue.objects.filter(organization=organization, is_deleted=False))
            stats['consumable_issues'] = len(consumable_issues)
            self.stdout.write(f'  Using existing {len(consumable_issues)} consumable issues')

        # 17. Create Purchase Requests
        if not skip_existing or not PurchaseRequest.objects.filter(organization=organization).exists():
            purchase_requests = self._create_purchase_requests(organization, departments, users, asset_categories, count=min(count, 20))
            stats['purchase_requests'] = len(purchase_requests)
            self.stdout.write(f'  Created {len(purchase_requests)} purchase requests')
        else:
            purchase_requests = list(PurchaseRequest.objects.filter(organization=organization, is_deleted=False))
            stats['purchase_requests'] = len(purchase_requests)
            self.stdout.write(f'  Using existing {len(purchase_requests)} purchase requests')

        # 18. Create Asset Receipts
        if top_up_existing:
            asset_receipts, _ = self._seed_or_top_up_records(
                queryset=AssetReceipt.objects.filter(organization=organization, is_deleted=False),
                create_callback=lambda missing: self._create_asset_receipts(
                    organization,
                    users,
                    suppliers,
                    asset_categories,
                    count=missing,
                ),
                stats=stats,
                stats_key='asset_receipts',
                label='asset receipts',
                skip_existing=skip_existing,
                top_up_existing=top_up_existing,
                target_count=receipt_target,
            )
        elif not skip_existing or not AssetReceipt.objects.filter(organization=organization).exists():
            asset_receipts = self._create_asset_receipts(organization, users, suppliers, asset_categories, count=receipt_target)
            stats['asset_receipts'] = len(asset_receipts)
            self.stdout.write(f'  Created {len(asset_receipts)} asset receipts')
        else:
            asset_receipts = list(AssetReceipt.objects.filter(organization=organization, is_deleted=False))
            stats['asset_receipts'] = len(asset_receipts)
            self.stdout.write(f'  Using existing {len(asset_receipts)} asset receipts')

        # 19. Create Maintenance Records
        if not skip_existing or not Maintenance.objects.filter(organization=organization).exists():
            maintenance_records = self._create_maintenance_records(organization, assets, users, count=min(count, 20))
            stats['maintenance'] = len(maintenance_records)
            self.stdout.write(f'  Created {len(maintenance_records)} maintenance records')
        else:
            maintenance_records = list(Maintenance.objects.filter(organization=organization, is_deleted=False))
            stats['maintenance'] = len(maintenance_records)
            self.stdout.write(f'  Using existing {len(maintenance_records)} maintenance records')

        # 20. Create Maintenance Plans
        if top_up_existing:
            maintenance_plans, _ = self._seed_or_top_up_records(
                queryset=MaintenancePlan.objects.filter(organization=organization, is_deleted=False),
                create_callback=lambda missing: self._create_maintenance_plans(
                    organization,
                    asset_categories,
                    assets,
                    users,
                    count=missing,
                ),
                stats=stats,
                stats_key='maintenance_plans',
                label='maintenance plans',
                skip_existing=skip_existing,
                top_up_existing=top_up_existing,
                target_count=maintenance_plan_target,
            )
        elif not skip_existing or not MaintenancePlan.objects.filter(organization=organization).exists():
            maintenance_plans = self._create_maintenance_plans(
                organization,
                asset_categories,
                assets,
                users,
                count=maintenance_plan_target,
            )
            stats['maintenance_plans'] = len(maintenance_plans)
            self.stdout.write(f'  Created {len(maintenance_plans)} maintenance plans')
        else:
            maintenance_plans = list(MaintenancePlan.objects.filter(organization=organization, is_deleted=False))
            stats['maintenance_plans'] = len(maintenance_plans)
            self.stdout.write(f'  Using existing {len(maintenance_plans)} maintenance plans')

        # 21. Create Disposal Requests
        if top_up_existing:
            disposal_requests, _ = self._seed_or_top_up_records(
                queryset=DisposalRequest.objects.filter(organization=organization, is_deleted=False),
                create_callback=lambda missing: self._create_disposal_requests(
                    organization,
                    departments,
                    users,
                    assets,
                    count=missing,
                ),
                stats=stats,
                stats_key='disposal_requests',
                label='disposal requests',
                skip_existing=skip_existing,
                top_up_existing=top_up_existing,
                target_count=disposal_target,
            )
        elif not skip_existing or not DisposalRequest.objects.filter(organization=organization).exists():
            disposal_requests = self._create_disposal_requests(
                organization,
                departments,
                users,
                assets,
                count=disposal_target,
            )
            stats['disposal_requests'] = len(disposal_requests)
            self.stdout.write(f'  Created {len(disposal_requests)} disposal requests')
        else:
            disposal_requests = list(DisposalRequest.objects.filter(organization=organization, is_deleted=False))
            stats['disposal_requests'] = len(disposal_requests)
            self.stdout.write(f'  Using existing {len(disposal_requests)} disposal requests')

        # 22. Create Asset Pickups
        if top_up_existing:
            asset_pickups, _ = self._seed_or_top_up_records(
                queryset=AssetPickup.objects.filter(organization=organization, is_deleted=False),
                create_callback=lambda missing: self._create_asset_pickups(
                    organization,
                    departments,
                    users,
                    assets,
                    count=missing,
                ),
                stats=stats,
                stats_key='asset_pickups',
                label='asset pickups',
                skip_existing=skip_existing,
                top_up_existing=top_up_existing,
                target_count=pickup_target,
            )
        elif not skip_existing or not AssetPickup.objects.filter(organization=organization).exists():
            asset_pickups = self._create_asset_pickups(
                organization,
                departments,
                users,
                assets,
                count=pickup_target,
            )
            stats['asset_pickups'] = len(asset_pickups)
            self.stdout.write(f'  Created {len(asset_pickups)} asset pickups')
        else:
            asset_pickups = list(AssetPickup.objects.filter(organization=organization, is_deleted=False))
            stats['asset_pickups'] = len(asset_pickups)
            self.stdout.write(f'  Using existing {len(asset_pickups)} asset pickups')

        # 23. Create Asset Transfers
        if top_up_existing:
            asset_transfers, _ = self._seed_or_top_up_records(
                queryset=AssetTransfer.objects.filter(organization=organization, is_deleted=False),
                create_callback=lambda missing: self._create_asset_transfers(
                    organization,
                    departments,
                    users,
                    assets,
                    locations,
                    count=missing,
                ),
                stats=stats,
                stats_key='asset_transfers',
                label='asset transfers',
                skip_existing=skip_existing,
                top_up_existing=top_up_existing,
                target_count=transfer_target,
            )
        elif not skip_existing or not AssetTransfer.objects.filter(organization=organization).exists():
            asset_transfers = self._create_asset_transfers(
                organization,
                departments,
                users,
                assets,
                locations,
                count=transfer_target,
            )
            stats['asset_transfers'] = len(asset_transfers)
            self.stdout.write(f'  Created {len(asset_transfers)} asset transfers')
        else:
            asset_transfers = list(AssetTransfer.objects.filter(organization=organization, is_deleted=False))
            stats['asset_transfers'] = len(asset_transfers)
            self.stdout.write(f'  Using existing {len(asset_transfers)} asset transfers')

        # 24. Create Asset Returns
        if top_up_existing:
            asset_returns, _ = self._seed_or_top_up_records(
                queryset=AssetReturn.objects.filter(organization=organization, is_deleted=False),
                create_callback=lambda missing: self._create_asset_returns(
                    organization,
                    users,
                    assets,
                    locations,
                    project_allocations=project_assets,
                    count=missing,
                ),
                stats=stats,
                stats_key='asset_returns',
                label='asset returns',
                skip_existing=skip_existing,
                top_up_existing=top_up_existing,
                target_count=return_target,
            )
        elif not skip_existing or not AssetReturn.objects.filter(organization=organization).exists():
            asset_returns = self._create_asset_returns(
                organization,
                users,
                assets,
                locations,
                project_allocations=project_assets,
                count=return_target,
            )
            stats['asset_returns'] = len(asset_returns)
            self.stdout.write(f'  Created {len(asset_returns)} asset returns')
        else:
            asset_returns = list(AssetReturn.objects.filter(organization=organization, is_deleted=False))
            stats['asset_returns'] = len(asset_returns)
            self.stdout.write(f'  Using existing {len(asset_returns)} asset returns')

        # 25. Create Asset Loans
        if top_up_existing:
            asset_loans, _ = self._seed_or_top_up_records(
                queryset=AssetLoan.objects.filter(organization=organization, is_deleted=False),
                create_callback=lambda missing: self._create_asset_loans(
                    organization,
                    users,
                    assets,
                    count=missing,
                ),
                stats=stats,
                stats_key='asset_loans',
                label='asset loans',
                skip_existing=skip_existing,
                top_up_existing=top_up_existing,
                target_count=loan_target,
            )
        elif not skip_existing or not AssetLoan.objects.filter(organization=organization).exists():
            asset_loans = self._create_asset_loans(
                organization,
                users,
                assets,
                count=loan_target,
            )
            stats['asset_loans'] = len(asset_loans)
            self.stdout.write(f'  Created {len(asset_loans)} asset loans')
        else:
            asset_loans = list(AssetLoan.objects.filter(organization=organization, is_deleted=False))
            stats['asset_loans'] = len(asset_loans)
            self.stdout.write(f'  Using existing {len(asset_loans)} asset loans')

        # 26. Create Inventory Tasks
        if top_up_existing:
            inventory_tasks, created_inventory_tasks = self._seed_or_top_up_records(
                queryset=InventoryTask.objects.filter(organization=organization, is_deleted=False),
                create_callback=lambda missing: self._create_inventory_tasks(
                    organization,
                    departments,
                    asset_categories,
                    users,
                    count=missing,
                ),
                stats=stats,
                stats_key='inventory_tasks',
                label='inventory tasks',
                skip_existing=skip_existing,
                top_up_existing=top_up_existing,
                target_count=inventory_task_target,
            )
        elif not skip_existing or not InventoryTask.objects.filter(organization=organization).exists():
            inventory_tasks = self._create_inventory_tasks(
                organization,
                departments,
                asset_categories,
                users,
                count=inventory_task_target,
            )
            created_inventory_tasks = list(inventory_tasks)
            stats['inventory_tasks'] = len(inventory_tasks)
            self.stdout.write(f'  Created {len(inventory_tasks)} inventory tasks')
        else:
            inventory_tasks = list(InventoryTask.objects.filter(organization=organization, is_deleted=False))
            created_inventory_tasks = []
            stats['inventory_tasks'] = len(inventory_tasks)
            self.stdout.write(f'  Using existing {len(inventory_tasks)} inventory tasks')

        # 27. Create Inventory Snapshots and Scans
        if inventory_tasks and assets:
            if top_up_existing:
                tasks_missing_snapshots = [
                    task for task in inventory_tasks
                    if not task.snapshots.filter(is_deleted=False).exists()
                ]
                if tasks_missing_snapshots:
                    snapshots = list(InventorySnapshot.objects.filter(task__organization=organization, is_deleted=False))
                    new_snapshots = self._create_inventory_snapshots(tasks_missing_snapshots, assets, users)
                    snapshots.extend(new_snapshots)
                    stats['inventory_snapshots'] = len(snapshots)
                    self.stdout.write(
                        f'  Topped up inventory snapshots by {len(new_snapshots)} to {len(snapshots)}'
                    )
                else:
                    snapshots = list(InventorySnapshot.objects.filter(task__organization=organization, is_deleted=False))
                    stats['inventory_snapshots'] = len(snapshots)
                    self.stdout.write(f'  Using existing {len(snapshots)} inventory snapshots')
            elif not skip_existing or not InventorySnapshot.objects.filter(task__organization=organization).exists():
                snapshots = self._create_inventory_snapshots(inventory_tasks, assets, users)
                stats['inventory_snapshots'] = len(snapshots)
                self.stdout.write(f'  Created {len(snapshots)} inventory snapshots')
            else:
                snapshots = list(InventorySnapshot.objects.filter(task__organization=organization, is_deleted=False))
                stats['inventory_snapshots'] = len(snapshots)
                self.stdout.write(f'  Using existing {len(snapshots)} inventory snapshots')

            if top_up_existing:
                scans, _ = self._seed_or_top_up_records(
                    queryset=InventoryScan.objects.filter(task__organization=organization, is_deleted=False),
                    create_callback=lambda missing: self._create_inventory_scans(
                        inventory_tasks,
                        assets,
                        users,
                        count=missing,
                    ),
                    stats=stats,
                    stats_key='inventory_scans',
                    label='inventory scans',
                    skip_existing=skip_existing,
                    top_up_existing=top_up_existing,
                    target_count=inventory_scan_target,
                )
            elif not skip_existing or not InventoryScan.objects.filter(task__organization=organization).exists():
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

    def _resolve_target_count(self, requested_count, minimum=20, maximum=None):
        """Resolve a target count with a minimum floor and optional maximum cap."""
        target_count = max(minimum, int(requested_count or 0))
        if maximum is not None:
            target_count = min(target_count, maximum)
        return target_count

    def _seed_or_top_up_records(
        self,
        queryset,
        create_callback,
        stats,
        stats_key,
        label,
        skip_existing=False,
        top_up_existing=False,
        target_count=None,
    ):
        """Create fresh records or top up an existing queryset to a minimum count."""
        existing_records = list(queryset)
        existing_count = len(existing_records)

        if top_up_existing and target_count is not None:
            missing_count = max(0, target_count - existing_count)
            if missing_count > 0:
                created_records = list(create_callback(missing_count))
                records = existing_records + created_records
                stats[stats_key] = len(records)
                self.stdout.write(f'  Topped up {label} by {len(created_records)} to {len(records)}')
                return records, created_records

            stats[stats_key] = existing_count
            self.stdout.write(f'  Using existing {existing_count} {label}')
            return existing_records, []

        if not skip_existing or existing_count == 0:
            create_count = target_count if target_count is not None else existing_count
            created_records = list(create_callback(create_count))
            stats[stats_key] = len(created_records)
            self.stdout.write(f'  Created {len(created_records)} {label}')
            return created_records, created_records

        stats[stats_key] = existing_count
        self.stdout.write(f'  Using existing {existing_count} {label}')
        return existing_records, []

    def _next_prefixed_sequence(self, model_class, field_name, prefix, width, tracker=None):
        """Return the next numeric sequence for a prefix across existing and current run data."""
        tracker_key = (model_class._meta.label_lower, field_name, prefix)
        if tracker is not None and tracker_key in tracker:
            tracker[tracker_key] += 1
            return tracker[tracker_key]

        manager = getattr(model_class, 'all_objects', model_class.objects)
        existing_values = manager.filter(
            **{f'{field_name}__startswith': prefix}
        ).values_list(field_name, flat=True)

        last_sequence = 0
        for existing_value in existing_values:
            suffix = ''.join(ch for ch in str(existing_value)[len(prefix):] if ch.isdigit())
            if not suffix:
                continue
            last_sequence = max(last_sequence, int(suffix))

        next_sequence = last_sequence + 1
        if tracker is not None:
            tracker[tracker_key] = next_sequence
        return next_sequence

    def _seed_datetime(self, base_value, day_offset=0, hour=None, minute=None):
        """Convert a date-like seed value into a timezone-aware datetime."""
        if base_value is None:
            return None

        if isinstance(base_value, datetime):
            base_date = timezone.localtime(base_value).date() if timezone.is_aware(base_value) else base_value.date()
        elif isinstance(base_value, date):
            base_date = base_value
        else:
            raise TypeError(f'Unsupported seed datetime base value: {type(base_value)!r}')

        target_date = base_date + timedelta(days=day_offset)
        target_hour = random.randint(8, 18) if hour is None else hour
        target_minute = random.choice((0, 15, 30, 45)) if minute is None else minute
        naive_value = datetime.combine(target_date, dt_time(hour=target_hour, minute=target_minute))
        return timezone.make_aware(naive_value, timezone.get_current_timezone())

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
            ('Beijing Technology Co., Ltd.', 'Zhang San', '010-12345678', 'zhang@tech.com'),
            ('Shanghai Electronics Corp.', 'Li Si', '021-87654321', 'li@electronics.com'),
            ('Guangzhou Furniture Ltd.', 'Wang Wu', '020-11112222', 'wang@furniture.com'),
            ('Shenzhen Computer Systems', 'Zhao Liu', '0755-33334444', 'zhao@computer.com'),
            ('Hangzhou Office Supplies', 'Qian Qi', '0571-55556666', 'qian@office.com'),
            ('Chengdu Vehicle Services', 'Sun Ba', '028-77778888', 'sun@vehicle.com'),
            ('Wuhan Machinery Works', 'Zhou Jiu', '027-99990000', 'zhou@machinery.com'),
            ('Nanjing Equipment Inc.', 'Wu Shi', '025-12121212', 'wu@equipment.com'),
            ('Tianjin Materials Co.', 'Zheng Yi', '022-23232323', 'zheng@materials.com'),
            ('Xi\'an Industrial Supplies', 'Feng Er', '029-34343434', 'feng@industrial.com'),
        ]

        suppliers = []
        tracker = {}
        supplier_prefix = f'SUP{self._get_demo_org_code(organization)}'

        for name, contact, phone, email in suppliers_data[:count]:
            sequence = self._next_prefixed_sequence(
                Supplier,
                'code',
                supplier_prefix,
                width=3,
                tracker=tracker,
            )
            supplier = Supplier.objects.create(
                organization=organization,
                code=f'{supplier_prefix}{sequence:03d}',
                name=name,
                contact=contact,
                phone=phone,
                email=email,
                address=f'{name} Address, China'
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

    def _create_asset_projects(self, organization, departments, users, count=20):
        """Create project portfolio data for the project workspace."""
        if not departments or not users:
            return []

        project_types = ['research', 'development', 'infrastructure', 'implementation', 'other']
        statuses = ['planning', 'active', 'active', 'suspended', 'completed', 'cancelled']
        project_name_prefixes = [
            'Digital Upgrade',
            'Warehouse Refresh',
            'Factory Buildout',
            'Campus Network',
            'R&D Enablement',
            'Branch Expansion',
            'Security Hardening',
            'IT Renewal',
        ]
        projects = []

        for i in range(count):
            manager = users[i % len(users)]
            department = departments[i % len(departments)]
            status = statuses[i % len(statuses)]
            start_date = timezone.now().date() - timedelta(days=15 + (i * 9))
            planned_duration_days = 90 + (i % 4) * 45
            end_date = start_date + timedelta(days=planned_duration_days)
            total_milestones = 4 + (i % 4)

            actual_start_date = None
            actual_end_date = None
            if status in {'active', 'suspended', 'completed', 'cancelled'}:
                actual_start_date = start_date + timedelta(days=i % 5)
            if status in {'completed', 'cancelled'}:
                actual_end_date = end_date - timedelta(days=i % 7)

            if status == 'planning':
                completed_milestones = 0
            elif status == 'active':
                completed_milestones = min(total_milestones - 1, 1 + (i % max(total_milestones - 1, 1)))
            elif status == 'suspended':
                completed_milestones = min(total_milestones - 1, max(1, total_milestones // 2))
            else:
                completed_milestones = total_milestones

            planned_budget = Decimal(str(180000 + i * 15000))
            if status == 'planning':
                actual_cost = Decimal('0')
            elif status == 'active':
                actual_cost = (planned_budget * Decimal('0.35')).quantize(Decimal('0.01'))
            elif status == 'suspended':
                actual_cost = (planned_budget * Decimal('0.55')).quantize(Decimal('0.01'))
            else:
                actual_cost = (planned_budget * Decimal('0.88')).quantize(Decimal('0.01'))

            project = AssetProject.objects.create(
                organization=organization,
                project_name=f'{project_name_prefixes[i % len(project_name_prefixes)]} Project {i + 1:02d}',
                project_alias=f'PRJ-{i + 1:02d}',
                project_manager=manager,
                department=department,
                project_type=project_types[i % len(project_types)],
                status=status,
                start_date=start_date,
                end_date=end_date,
                actual_start_date=actual_start_date,
                actual_end_date=actual_end_date,
                planned_budget=planned_budget,
                actual_cost=actual_cost,
                description=f'Project {i + 1:02d} focuses on asset and workspace enablement for the {department.name} team.',
                technical_requirements='Requires coordinated asset allocation, member tracking, and return closure.',
                completed_milestones=completed_milestones,
                total_milestones=total_milestones,
                created_by=manager,
                updated_by=manager,
            )
            projects.append(project)

        return projects

    def _create_project_members(self, organization, projects, users):
        """Create project members for each seeded project."""
        if not projects or not users:
            return []

        memberships = []
        for index, project in enumerate(projects):
            manager_membership = ProjectMember.objects.create(
                organization=organization,
                project=project,
                user=project.project_manager,
                role='manager',
                is_primary=True,
                join_date=project.actual_start_date or project.start_date,
                is_active=project.status not in {'completed', 'cancelled'},
                responsibilities='Owns project delivery, asset planning, and approval decisions.',
                can_allocate_asset=True,
                can_view_cost=True,
                created_by=project.project_manager,
                updated_by=project.project_manager,
            )
            memberships.append(manager_membership)

            additional_users = [user for user in users if user.id != project.project_manager_id]
            random.shuffle(additional_users)
            additional_count = min(len(additional_users), 1 + (index % max(min(3, len(additional_users)), 1)))

            for member_index, user in enumerate(additional_users[:additional_count]):
                role = 'member' if member_index % 2 == 0 else 'observer'
                membership = ProjectMember.objects.create(
                    organization=organization,
                    project=project,
                    user=user,
                    role=role,
                    is_primary=False,
                    join_date=(project.actual_start_date or project.start_date) + timedelta(days=member_index + 1),
                    is_active=project.status not in {'completed', 'cancelled'} or member_index == 0,
                    responsibilities='Supports delivery milestones, asset usage, and project coordination.',
                    can_allocate_asset=role == 'member',
                    can_view_cost=role != 'observer',
                    created_by=project.project_manager,
                    updated_by=project.project_manager,
                )
                memberships.append(membership)

        return memberships

    def _create_project_assets(self, organization, projects, assets, users, locations, count=20):
        """Create project asset allocations with realistic lifecycle states."""
        if not projects or not assets or not users:
            return []

        allocation_total = min(len(assets), max(20, count))
        selected_assets = list(assets[:allocation_total])
        allocations = []

        for index, asset in enumerate(selected_assets):
            project = projects[index % len(projects)]
            allocated_by = users[index % len(users)]
            allocation_date = timezone.now().date() - timedelta(days=5 + index * 3)
            allocation_type = ['permanent', 'temporary', 'shared'][index % 3]

            if index % 6 == 0:
                return_status = 'transferred'
                actual_return_date = allocation_date + timedelta(days=18)
            else:
                return_status = 'in_use'
                actual_return_date = None

            allocation = ProjectAsset.objects.create(
                organization=organization,
                project=project,
                asset=asset,
                allocation_date=allocation_date,
                allocation_type=allocation_type,
                allocated_by=allocated_by,
                custodian=asset.custodian or project.project_manager,
                return_date=allocation_date + timedelta(days=90 if allocation_type != 'temporary' else 30),
                actual_return_date=actual_return_date,
                return_status=return_status,
                allocation_cost=asset.current_value or asset.purchase_price or Decimal('0'),
                depreciation_rate=Decimal('1.0000'),
                purpose=f'{project.project_name} asset enablement batch {(index % 5) + 1}',
                usage_location=getattr(random.choice(locations), 'name', '') if locations else '',
                notes='Seeded project allocation for workspace and return-flow regression coverage.',
                created_by=allocated_by,
                updated_by=allocated_by,
            )
            allocations.append(allocation)

        return allocations

    def _get_demo_org_code(self, organization):
        """Build a compact uppercase code for demo identifiers."""
        raw_value = (
            str(getattr(organization, 'code', '') or '').strip()
            or str(getattr(organization, 'name', '') or '').strip()
            or 'ORG'
        )
        normalized = ''.join(ch for ch in raw_value.upper() if ch.isalnum())
        return normalized[:8] or 'ORG'

    def _create_voucher_templates(self, organization, created_by=None, count=5):
        """Create voucher templates for finance object coverage."""
        template_definitions = [
            ('purchase', 'Asset Purchase Template', 'Standard asset purchase voucher'),
            ('depreciation', 'Depreciation Template', 'Monthly depreciation posting template'),
            ('disposal', 'Asset Disposal Template', 'Asset disposal gain/loss template'),
            ('inventory', 'Inventory Adjustment Template', 'Inventory gain/loss adjustment template'),
            ('other', 'General Journal Template', 'Generic finance journal template'),
        ]
        templates = []
        org_code = self._get_demo_org_code(organization)
        tracker = {}

        for index in range(count):
            business_type, name, description = template_definitions[index % len(template_definitions)]
            sequence = self._next_prefixed_sequence(
                VoucherTemplate,
                'code',
                f'{org_code}-VT-',
                width=2,
                tracker=tracker,
            )
            template = VoucherTemplate.objects.create(
                organization=organization,
                name=name if count <= len(template_definitions) else f'{name} {sequence:02d}',
                code=f'{org_code}-VT-{sequence:02d}',
                business_type=business_type,
                template_config={
                    'businessType': business_type,
                    'lines': [
                        {'accountCode': '1001', 'side': 'debit', 'description': f'{business_type} debit line'},
                        {'accountCode': '2202', 'side': 'credit', 'description': f'{business_type} credit line'},
                    ],
                },
                is_active=True,
                description=description,
                created_by=created_by,
                updated_by=created_by,
            )
            templates.append(template)

        return templates

    def _create_finance_vouchers(self, organization, users, count=20):
        """Create finance vouchers with balanced entries for the finance workspace."""
        if not users:
            return [], []

        voucher_types = ['purchase', 'depreciation', 'disposal', 'inventory', 'other']
        statuses = ['draft', 'submitted', 'approved', 'posted', 'rejected']
        entry_blueprints = {
            'purchase': [
                ('1601', 'Fixed Assets', 'debit'),
                ('2202', 'Accounts Payable', 'credit'),
            ],
            'depreciation': [
                ('6602', 'Depreciation Expense', 'debit'),
                ('1602', 'Accumulated Depreciation', 'credit'),
            ],
            'disposal': [
                ('6711', 'Asset Disposal Loss', 'debit'),
                ('1601', 'Fixed Assets', 'credit'),
            ],
            'inventory': [
                ('1901', 'Inventory Gain or Loss', 'debit'),
                ('1601', 'Fixed Assets', 'credit'),
            ],
            'other': [
                ('1002', 'Bank Deposit', 'debit'),
                ('6001', 'Other Income', 'credit'),
            ],
        }

        vouchers = []
        entries = []
        now = timezone.now()
        date_prefix = now.strftime('%Y%m')
        tracker = {}

        for index in range(count):
            business_type = voucher_types[index % len(voucher_types)]
            status = statuses[index % len(statuses)]
            owner = users[index % len(users)]
            voucher_date = now.date() - timedelta(days=index * 2)
            base_amount = Decimal(str(800 + (index * 135)))
            total_amount = base_amount.quantize(Decimal('0.01'))
            sequence = self._next_prefixed_sequence(
                FinanceVoucher,
                'voucher_no',
                f'JV{date_prefix}',
                width=4,
                tracker=tracker,
            )

            voucher = FinanceVoucher.objects.create(
                organization=organization,
                voucher_no=f'JV{date_prefix}{sequence:04d}',
                voucher_date=voucher_date,
                business_type=business_type,
                summary=f'{business_type.title()} voucher batch {sequence:02d}',
                total_amount=Decimal('0.00'),
                status=status,
                notes='' if status != 'rejected' else 'Seeded rejected voucher for finance workspace coverage.',
                erp_voucher_no=f'M18-{date_prefix}-{sequence:04d}' if status == 'posted' else '',
                posted_at=(now - timedelta(days=index)).replace(minute=0, second=0, microsecond=0) if status == 'posted' else None,
                posted_by=owner if status == 'posted' else None,
                created_by=owner,
                updated_by=owner,
            )
            vouchers.append(voucher)

            blueprint = entry_blueprints[business_type]
            for line_no, (account_code, account_name, side) in enumerate(blueprint, start=1):
                entry = VoucherEntry.objects.create(
                    organization=organization,
                    voucher=voucher,
                    account_code=account_code,
                    account_name=account_name,
                    debit_amount=total_amount if side == 'debit' else Decimal('0.00'),
                    credit_amount=total_amount if side == 'credit' else Decimal('0.00'),
                    description=f'{business_type.title()} entry line {line_no}',
                    line_no=line_no,
                    created_by=owner,
                    updated_by=owner,
                )
                entries.append(entry)

        return vouchers, entries

    def _get_or_create_finance_integration_config(self, organization, created_by=None):
        """Ensure a single finance integration config exists for finance demo logs."""
        config = IntegrationConfig.objects.filter(
            organization=organization,
            system_type=IntegrationSystemType.M18,
            is_deleted=False,
        ).first()
        if config is not None:
            updated_fields = []
            enabled_modules = list(config.enabled_modules or [])
            if IntegrationModuleType.FINANCE not in enabled_modules:
                enabled_modules.append(IntegrationModuleType.FINANCE)
                config.enabled_modules = enabled_modules
                updated_fields.append('enabled_modules')
            if not config.is_enabled:
                config.is_enabled = True
                updated_fields.append('is_enabled')
            if config.health_status != HealthStatus.HEALTHY:
                config.health_status = HealthStatus.HEALTHY
                updated_fields.append('health_status')
            if config.last_sync_status != SyncStatus.SUCCESS:
                config.last_sync_status = SyncStatus.SUCCESS
                updated_fields.append('last_sync_status')
            if not config.last_health_check_at:
                config.last_health_check_at = timezone.now()
                updated_fields.append('last_health_check_at')
            if created_by is not None and config.updated_by_id != getattr(created_by, 'id', None):
                config.updated_by = created_by
                updated_fields.append('updated_by')
            if updated_fields:
                config.save(update_fields=updated_fields)
            return config

        return IntegrationConfig.objects.create(
            organization=organization,
            system_type=IntegrationSystemType.M18,
            system_name='Demo M18 Finance',
            connection_config={'baseUrl': 'https://m18.demo.local/api', 'tenant': self._get_demo_org_code(organization)},
            enabled_modules=[IntegrationModuleType.FINANCE],
            sync_config={'mode': 'manual', 'retry': True},
            mapping_config={'voucher': {'voucherNo': 'externalVoucherNo'}},
            is_enabled=True,
            last_sync_status=SyncStatus.SUCCESS,
            health_status=HealthStatus.HEALTHY,
            last_health_check_at=timezone.now(),
            created_by=created_by,
            updated_by=created_by,
        )

    def _create_finance_integration_activity(self, organization, vouchers, users, config):
        """Create integration tasks and logs for seeded finance vouchers."""
        if not vouchers or not users or config is None:
            return [], []

        tasks = []
        logs = []
        now = timezone.now()
        task_counter = 0

        def create_attempt(voucher, owner, sequence, task_status, success, status_code, error_message, response_body, hours_ago):
            nonlocal task_counter
            task_counter += 1
            task_started = now - timedelta(hours=hours_ago)
            task_completed = task_started + timedelta(seconds=20 + sequence + task_counter)
            task = IntegrationSyncTask.objects.create(
                organization=organization,
                config=config,
                task_id=f'FIN-SEED-{voucher.voucher_no}-{sequence:02d}',
                module_type=IntegrationModuleType.FINANCE,
                direction=SyncDirection.PUSH,
                business_type='finance_voucher',
                sync_params={
                    'voucher_id': str(voucher.id),
                    'voucher_no': voucher.voucher_no,
                    'attempt': sequence,
                },
                status=task_status,
                total_count=1,
                success_count=1 if success else 0,
                failed_count=0 if success else 1,
                error_summary=[] if success else [{'voucherNo': voucher.voucher_no, 'message': error_message}],
                started_at=task_started,
                completed_at=task_completed,
                duration_ms=int((task_completed - task_started).total_seconds() * 1000),
                celery_task_id=f'celery-{voucher.voucher_no.lower()}-{sequence:02d}',
                created_by=owner,
                updated_by=owner,
            )
            tasks.append(task)

            log = IntegrationLog.objects.create(
                organization=organization,
                sync_task=task,
                system_type=IntegrationSystemType.M18,
                integration_type='m18_fi_voucher',
                action=SyncDirection.PUSH,
                request_method='POST',
                request_url=f'https://m18.demo.local/api/finance/vouchers/{voucher.voucher_no}',
                request_headers={'X-Org': self._get_demo_org_code(organization), 'Content-Type': 'application/json'},
                request_body={
                    'voucherId': str(voucher.id),
                    'voucherNo': voucher.voucher_no,
                    'attempt': sequence,
                    'trigger': 'seed',
                },
                status_code=status_code,
                response_body=response_body,
                response_headers={'X-Demo-Seed': 'true'},
                success=success,
                error_message=error_message,
                duration_ms=task.duration_ms,
                business_type='finance_voucher',
                business_id=str(voucher.id),
                external_id=voucher.erp_voucher_no or f'EXT-{voucher.voucher_no}-{sequence:02d}',
                created_by=owner,
                updated_by=owner,
            )
            logs.append(log)

        for index, voucher in enumerate(vouchers):
            if voucher.status in {'draft', 'submitted'}:
                continue

            owner = users[index % len(users)]
            if voucher.status == 'posted':
                create_attempt(
                    voucher=voucher,
                    owner=owner,
                    sequence=1,
                    task_status=SyncStatus.RUNNING,
                    success=False,
                    status_code=202,
                    error_message='Posting request accepted and waiting for ERP callback',
                    response_body={'success': True, 'status': 'queued', 'voucher_no': voucher.voucher_no},
                    hours_ago=(index * 2) + 2,
                )
                create_attempt(
                    voucher=voucher,
                    owner=owner,
                    sequence=2,
                    task_status=SyncStatus.SUCCESS,
                    success=True,
                    status_code=200,
                    error_message='',
                    response_body={
                        'success': True,
                        'external_voucher_no': voucher.erp_voucher_no,
                        'voucher_no': voucher.voucher_no,
                    },
                    hours_ago=(index * 2) + 1,
                )
            elif voucher.status == 'approved':
                create_attempt(
                    voucher=voucher,
                    owner=owner,
                    sequence=1,
                    task_status=SyncStatus.RUNNING,
                    success=False,
                    status_code=202,
                    error_message='Voucher push job queued for ERP execution',
                    response_body={'success': True, 'status': 'queued', 'voucher_no': voucher.voucher_no},
                    hours_ago=(index * 2) + 2,
                )
                create_attempt(
                    voucher=voucher,
                    owner=owner,
                    sequence=2,
                    task_status=SyncStatus.FAILED,
                    success=False,
                    status_code=500,
                    error_message='ERP connection timeout',
                    response_body={'success': False, 'message': 'ERP connection timeout'},
                    hours_ago=(index * 2) + 1,
                )
            else:
                create_attempt(
                    voucher=voucher,
                    owner=owner,
                    sequence=1,
                    task_status=SyncStatus.PENDING,
                    success=False,
                    status_code=400,
                    error_message='Voucher approval was rejected before ERP push',
                    response_body={'success': False, 'message': 'Voucher rejected by finance approver'},
                    hours_ago=(index * 2) + 2,
                )
                create_attempt(
                    voucher=voucher,
                    owner=owner,
                    sequence=2,
                    task_status=SyncStatus.FAILED,
                    success=False,
                    status_code=400,
                    error_message='Voucher is not ready for ERP posting',
                    response_body={'success': False, 'message': 'Voucher is not ready for ERP posting'},
                    hours_ago=(index * 2) + 1,
                )

        config.last_sync_at = now
        config.last_sync_status = SyncStatus.SUCCESS
        config.health_status = HealthStatus.HEALTHY
        config.updated_by = users[0]
        config.save(update_fields=['last_sync_at', 'last_sync_status', 'health_status', 'updated_by'])

        return tasks, logs

    def _create_consumable_categories(self, organization):
        """Create consumable categories."""
        categories_data = [
            'Office Paper',
            'Writing Instruments',
            'Desk Supplies',
            'Electronics Accessories',
            'Kitchen Supplies',
        ]

        categories = []
        tracker = {}
        category_prefix = f'CAT{self._get_demo_org_code(organization)}'

        for name in categories_data:
            sequence = self._next_prefixed_sequence(
                ConsumableCategory,
                'code',
                category_prefix,
                width=3,
                tracker=tracker,
            )
            category = ConsumableCategory.objects.create(
                organization=organization,
                code=f'{category_prefix}{sequence:03d}',
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
            {'category': 'Office Paper', 'name': 'A4 Copy Paper', 'brand': 'Double A', 'unit': '包', 'price': 25.00},
            {'category': 'Office Paper', 'name': 'A3 Copy Paper', 'brand': 'Double A', 'unit': '包', 'price': 35.00},
            {'category': 'Writing Instruments', 'name': 'Ballpoint Pen (Black)', 'brand': 'M&G', 'unit': '支', 'price': 1.50},
            {'category': 'Writing Instruments', 'name': 'Ballpoint Pen (Blue)', 'brand': 'M&G', 'unit': '支', 'price': 1.50},
            {'category': 'Writing Instruments', 'name': 'Gel Pen', 'brand': 'Pilot', 'unit': '支', 'price': 3.00},
            {'category': 'Writing Instruments', 'name': 'Mechanical Pencil', 'brand': 'Pentel', 'unit': '支', 'price': 5.00},
            {'category': 'Desk Supplies', 'name': 'Stapler', 'brand': 'Max', 'unit': '个', 'price': 15.00},
            {'category': 'Desk Supplies', 'name': 'Staples (Box)', 'brand': 'Max', 'unit': '盒', 'price': 5.00},
            {'category': 'Desk Supplies', 'name': 'Paper Clips', 'brand': 'Deli', 'unit': '盒', 'price': 3.00},
            {'category': 'Desk Supplies', 'name': 'Binder Clips', 'brand': 'Deli', 'unit': '盒', 'price': 8.00},
            {'category': 'Electronics Accessories', 'name': 'USB Cable (Type-C)', 'brand': 'Anker', 'unit': '根', 'price': 25.00},
            {'category': 'Electronics Accessories', 'name': 'HDMI Cable', 'brand': 'Baseus', 'unit': '根', 'price': 30.00},
            {'category': 'Electronics Accessories', 'name': 'Mouse Pad', 'brand': '3M', 'unit': '个', 'price': 20.00},
            {'category': 'Kitchen Supplies', 'name': 'Paper Cups (Pack)', 'brand': 'Generic', 'unit': '包', 'price': 10.00},
            {'category': 'Kitchen Supplies', 'name': 'Coffee Filters', 'brand': 'Melitta', 'unit': '盒', 'price': 15.00},
        ]

        consumables = []
        tracker = {}
        for i in range(count):
            template = consumable_templates[i % len(consumable_templates)]
            category = next((c for c in categories if c.name == template['category']), categories[0])

            current_stock = random.randint(20, 150)
            code_prefix = f'CON{datetime.now().strftime("%Y%m")}'
            sequence = self._next_prefixed_sequence(
                Consumable,
                'code',
                code_prefix,
                width=4,
                tracker=tracker,
            )

            consumable = Consumable.objects.create(
                organization=organization,
                code=f'{code_prefix}{sequence:04d}',
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
        tracker = {}

        for i in range(count):
            purchase_date = timezone.now().date() - timedelta(days=random.randint(1, 90))
            prefix = f'CP{purchase_date.strftime("%Y%m")}'
            sequence = self._next_prefixed_sequence(
                ConsumablePurchase,
                'purchase_no',
                prefix,
                width=4,
                tracker=tracker,
            )

            purchase = ConsumablePurchase.objects.create(
                organization=organization,
                purchase_no=f'{prefix}{sequence:04d}',
                purchase_date=purchase_date,
                supplier=random.choice(suppliers) if suppliers else None,
                total_amount=Decimal(str(random.uniform(100, 5000))),
                status=random.choice(['draft', 'approved', 'completed']),
                approved_by=random.choice(users) if users else None,
                approved_at=self._seed_datetime(purchase_date, day_offset=random.randint(1, 3)) if random.random() > 0.3 else None,
                received_by=random.choice(users) if users else None,
                received_at=self._seed_datetime(purchase_date, day_offset=random.randint(5, 10)) if random.random() > 0.5 else None,
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
        tracker = {}

        for i in range(count):
            issue_date = timezone.now().date() - timedelta(days=random.randint(1, 60))
            prefix = f'CI{issue_date.strftime("%Y%m")}'
            sequence = self._next_prefixed_sequence(
                ConsumableIssue,
                'issue_no',
                prefix,
                width=4,
                tracker=tracker,
            )

            issue = ConsumableIssue.objects.create(
                organization=organization,
                issue_no=f'{prefix}{sequence:04d}',
                issue_date=issue_date,
                applicant=random.choice(users) if users else None,
                department=organization,  # department field expects Organization instance
                issue_reason=f'Daily office supplies request {i+1}',
                status=random.choice(['draft', 'approved', 'completed']),
                approved_by=random.choice(users) if users else None,
                approved_at=self._seed_datetime(issue_date, day_offset=1) if random.random() > 0.3 else None,
                issued_by=random.choice(users) if users else None,
                issued_at=self._seed_datetime(issue_date, day_offset=random.randint(1, 3)) if random.random() > 0.5 else None,
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
        tracker = {}

        for i in range(count):
            request_date = timezone.now().date() - timedelta(days=random.randint(1, 120))
            prefix = f'PR{request_date.strftime("%Y%m")}'
            sequence = self._next_prefixed_sequence(
                PurchaseRequest,
                'request_no',
                prefix,
                width=4,
                tracker=tracker,
            )

            request = PurchaseRequest.objects.create(
                organization=organization,
                request_no=f'{prefix}{sequence:04d}',
                request_date=request_date,
                expected_date=request_date + timedelta(days=random.randint(15, 45)),
                status=random.choice(['draft', 'submitted', 'approved', 'processing', 'completed']),
                applicant=random.choice(users) if users else None,
                department=organization,  # department field expects Organization instance
                reason=f'Asset procurement request for project {i+1}',
                budget_amount=Decimal(str(random.uniform(10000, 200000))),
                approved_by=random.choice(users) if users else None,
                approved_at=self._seed_datetime(request_date, day_offset=random.randint(2, 7)) if random.random() > 0.4 else None,
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
        tracker = {}

        for i in range(count):
            receipt_date = timezone.now().date() - timedelta(days=random.randint(1, 365))
            prefix = f'RC{receipt_date.strftime("%Y%m")}'
            sequence = self._next_prefixed_sequence(
                AssetReceipt,
                'receipt_no',
                prefix,
                width=3,
                tracker=tracker,
            )

            receipt = AssetReceipt.objects.create(
                organization=organization,
                receipt_no=f'{prefix}{sequence:03d}',
                receipt_date=receipt_date,
                receipt_type=random.choice(['purchase', 'transfer', 'return']),
                supplier=random.choice(suppliers).name if suppliers else 'Unknown Supplier',
                delivery_no=f'DN{receipt_date.strftime("%Y%m%d")}{random.randint(100, 999)}',
                receiver=random.choice(users) if users else None,
                inspector=random.choice(users) if users else None,
                status=random.choice(['draft', 'submitted', 'inspecting', 'passed', 'rejected']),
                inspection_result='All items passed quality inspection' if random.random() > 0.2 else 'Some items defective',
                passed_at=self._seed_datetime(receipt_date, day_offset=1) if random.random() > 0.5 else None,
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
        tracker = {}

        for i in range(count):
            report_time = timezone.now() - timedelta(days=random.randint(1, 180))
            prefix = f'MT{report_time.strftime("%Y%m")}'
            sequence = self._next_prefixed_sequence(
                Maintenance,
                'maintenance_no',
                prefix,
                width=3,
                tracker=tracker,
            )

            maintenance = Maintenance.objects.create(
                organization=organization,
                maintenance_no=f'{prefix}{sequence:03d}',
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
        tracker = {}

        for i in range(count):
            start_date = timezone.now().date() + timedelta(days=random.randint(1, 30))
            end_date = start_date + timedelta(days=random.randint(180, 730)) if random.random() > 0.3 else None
            prefix = f'MP{datetime.now().strftime("%Y%m")}'
            sequence = self._next_prefixed_sequence(
                MaintenancePlan,
                'plan_code',
                prefix,
                width=3,
                tracker=tracker,
            )

            plan = MaintenancePlan.objects.create(
                organization=organization,
                plan_name=f'{random.choice(["Routine", "Preventive", "Periodic"])} Maintenance Plan {sequence}',
                plan_code=f'{prefix}{sequence:03d}',
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
        tracker = {}

        for i in range(count):
            request_date = timezone.now().date() - timedelta(days=random.randint(1, 90))
            prefix = f'DS{request_date.strftime("%Y%m")}'
            sequence = self._next_prefixed_sequence(
                DisposalRequest,
                'request_no',
                prefix,
                width=3,
                tracker=tracker,
            )

            request = DisposalRequest.objects.create(
                organization=organization,
                request_no=f'{prefix}{sequence:03d}',
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
                    appraised_at=self._seed_datetime(request_date, day_offset=random.randint(1, 5)) if random.random() > 0.5 else None,
                    disposal_executed=random.random() > 0.7,
                    executed_at=self._seed_datetime(request_date, day_offset=random.randint(10, 20)) if random.random() > 0.8 else None,
                    actual_residual_value=Decimal(str(random.uniform(50, 3000))) if random.random() > 0.6 else None,
                    buyer_info='Beijing Second-hand Market' if random.random() > 0.8 else None,
                    remark=f'Disposal item {j+1}'
                )

        return requests

    def _pick_distinct_assets(self, assets, count):
        """Return a unique asset subset for line-item creation."""
        asset_pool = list(assets or [])
        if not asset_pool or count <= 0:
            return []
        return random.sample(asset_pool, min(count, len(asset_pool)))

    def _create_asset_pickups(self, organization, departments, users, assets, count=15):
        """Create asset pickup orders."""
        statuses = ['draft', 'pending', 'approved', 'rejected', 'completed', 'cancelled']
        pickups = []
        tracker = {}

        for i in range(count):
            pickup_date = timezone.now().date() - timedelta(days=random.randint(1, 60))
            prefix = f'LY{pickup_date.strftime("%Y%m")}'
            sequence = self._next_prefixed_sequence(
                AssetPickup,
                'pickup_no',
                prefix,
                width=4,
                tracker=tracker,
            )

            pickup = AssetPickup.objects.create(
                organization=organization,
                pickup_no=f'{prefix}{sequence:04d}',
                applicant=random.choice(users) if users else None,
                department=random.choice(departments) if departments else None,
                pickup_date=pickup_date,
                pickup_reason=f'Asset pickup for {random.choice(["new project", "daily work", "business trip", "remote work"])}.',
                status=random.choice(statuses),
                approved_by=random.choice(users) if users and random.random() > 0.3 else None,
                approved_at=self._seed_datetime(pickup_date, day_offset=1) if random.random() > 0.5 else None,
                approval_comment='Approved' if random.random() > 0.7 else '',
                completed_at=self._seed_datetime(pickup_date, day_offset=random.randint(2, 5)) if random.random() > 0.6 else None
            )
            pickups.append(pickup)

            # Add items
            num_items = random.randint(1, min(3, len(assets))) if assets else 0
            for j, asset in enumerate(self._pick_distinct_assets(assets, num_items)):

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
        tracker = {}

        for i in range(count):
            transfer_date = timezone.now().date() - timedelta(days=random.randint(1, 90))
            prefix = f'TF{transfer_date.strftime("%Y%m")}'
            sequence = self._next_prefixed_sequence(
                AssetTransfer,
                'transfer_no',
                prefix,
                width=4,
                tracker=tracker,
            )

            from_dept = random.choice(departments) if departments else None
            to_dept = random.choice([d for d in departments] if departments else [])
            while from_dept and to_dept and from_dept.id == to_dept.id:
                to_dept = random.choice(departments)

            transfer = AssetTransfer.objects.create(
                organization=organization,
                transfer_no=f'{prefix}{sequence:04d}',
                from_department=from_dept,
                to_department=to_dept,
                transfer_date=transfer_date,
                transfer_reason=f'Asset transfer due to {random.choice(["department reorganization", "project requirements", "resource optimization"])}.',
                status=random.choice(statuses),
                from_approved_by=random.choice(users) if users and random.random() > 0.4 else None,
                from_approved_at=self._seed_datetime(transfer_date, day_offset=1) if random.random() > 0.5 else None,
                from_approve_comment='Approved for transfer' if random.random() > 0.7 else '',
                to_approved_by=random.choice(users) if users and random.random() > 0.4 else None,
                to_approved_at=self._seed_datetime(transfer_date, day_offset=random.randint(1, 3)) if random.random() > 0.5 else None,
                to_approve_comment='Accepted' if random.random() > 0.7 else '',
                completed_at=self._seed_datetime(transfer_date, day_offset=random.randint(3, 7)) if random.random() > 0.6 else None
            )
            transfers.append(transfer)

            # Add items
            num_items = random.randint(1, min(4, len(assets))) if assets else 0
            for j, asset in enumerate(self._pick_distinct_assets(assets, num_items)):

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

    def _create_asset_returns(self, organization, users, assets, locations, count=10, project_allocations=None):
        """Create asset return orders."""
        statuses = ['draft', 'pending', 'confirmed', 'completed', 'rejected', 'cancelled']
        returns = []
        available_assets = list(assets)
        available_project_allocations = [
            allocation for allocation in (project_allocations or [])
            if allocation.return_status == 'in_use'
        ]
        random.shuffle(available_assets)
        random.shuffle(available_project_allocations)
        tracker = {}

        for i in range(count):
            return_date = timezone.now().date() - timedelta(days=random.randint(1, 60))
            status = statuses[i % len(statuses)]
            prefix = f'RT{return_date.strftime("%Y%m")}'
            sequence = self._next_prefixed_sequence(
                AssetReturn,
                'return_no',
                prefix,
                width=4,
                tracker=tracker,
            )
            confirmed_at = None
            completed_at = None
            reject_reason = ''

            if status in {'confirmed', 'completed'}:
                confirmed_at = timezone.now() - timedelta(days=max(0, 4 - (i % 3)))
            if status == 'completed':
                completed_at = timezone.now() - timedelta(days=max(0, 2 - (i % 2)))
            if status == 'rejected':
                reject_reason = random.choice([
                    'Asset accessories are incomplete',
                    'Condition verification failed',
                    'Return record needs additional review',
                ])

            asset_return = AssetReturn.objects.create(
                organization=organization,
                return_no=f'{prefix}{sequence:04d}',
                returner=random.choice(users) if users else None,
                return_date=return_date,
                return_reason=f'Asset return due to {random.choice(["project completion", "resignation", "equipment upgrade", "no longer needed"])}.',
                status=status,
                return_location=random.choice(locations) if locations else None,
                confirmed_by=random.choice(users) if users and confirmed_at else None,
                confirmed_at=confirmed_at,
                reject_reason=reject_reason,
                completed_at=completed_at,
            )
            returns.append(asset_return)

            # Add items
            num_items = random.randint(1, 3)
            used_asset_ids = set()
            for j in range(num_items):
                project_allocation = None
                if available_project_allocations and (j == 0 or random.random() > 0.45):
                    project_allocation = available_project_allocations.pop()

                if project_allocation is not None:
                    asset = project_allocation.asset
                    used_asset_ids.add(asset.id)
                else:
                    remaining_assets = [asset for asset in available_assets if asset.id not in used_asset_ids]
                    if not remaining_assets:
                        remaining_assets = [asset for asset in assets if asset.id not in used_asset_ids]
                    asset = random.choice(remaining_assets) if remaining_assets else None
                    if asset is not None:
                        used_asset_ids.add(asset.id)

                if asset is None:
                    continue

                ReturnItem.objects.create(
                    organization=organization,
                    asset_return=asset_return,
                    asset=asset,
                    project_allocation=project_allocation,
                    asset_status=random.choice(['idle', 'maintenance', 'scrapped']),
                    condition_description=random.choice(['Good condition', 'Minor scratches', 'Needs cleaning', 'Requires maintenance']),
                    remark=f'Return item {j+1}'
                )

                if project_allocation is None:
                    continue

                if status in {'confirmed', 'completed'}:
                    project_allocation.return_status = 'returned'
                    project_allocation.actual_return_date = completed_at.date() if completed_at else confirmed_at.date()
                    project_allocation.notes = (
                        f'{project_allocation.notes}\nSeed demo return order {asset_return.return_no} confirmed.'
                    ).strip()
                    project_allocation.save(update_fields=['return_status', 'actual_return_date', 'notes', 'updated_at'])
                elif status == 'cancelled':
                    project_allocation.notes = (
                        f'{project_allocation.notes}\nSeed demo return order {asset_return.return_no} cancelled.'
                    ).strip()
                    project_allocation.save(update_fields=['notes', 'updated_at'])
                elif status == 'rejected':
                    project_allocation.notes = (
                        f'{project_allocation.notes}\nSeed demo return order {asset_return.return_no} rejected: {reject_reason}'
                    ).strip()
                    project_allocation.save(update_fields=['notes', 'updated_at'])

        return returns

    def _create_asset_loans(self, organization, users, assets, count=15):
        """Create asset loan orders."""
        statuses = ['draft', 'pending', 'approved', 'rejected', 'borrowed', 'overdue', 'returned', 'cancelled']
        conditions = ['good', 'minor_damage', 'major_damage', 'lost']
        loans = []
        tracker = {}

        for i in range(count):
            borrow_date = timezone.now().date() - timedelta(days=random.randint(1, 120))
            expected_return = borrow_date + timedelta(days=random.randint(7, 60))
            prefix = f'LN{borrow_date.strftime("%Y%m")}'
            sequence = self._next_prefixed_sequence(
                AssetLoan,
                'loan_no',
                prefix,
                width=4,
                tracker=tracker,
            )

            is_returned = random.random() > 0.5
            actual_return = borrow_date + timedelta(days=random.randint(1, 30)) if is_returned else None

            loan = AssetLoan.objects.create(
                organization=organization,
                loan_no=f'{prefix}{sequence:04d}',
                borrower=random.choice(users) if users else None,
                borrow_date=borrow_date,
                expected_return_date=expected_return,
                actual_return_date=actual_return,
                loan_reason=f'Asset loan for {random.choice(["business trip", "client presentation", "remote work", "temporary project"])}.',
                status='returned' if is_returned else random.choice(['draft', 'pending', 'approved', 'borrowed', 'overdue', 'cancelled']),
                approved_by=random.choice(users) if users and random.random() > 0.3 else None,
                approved_at=self._seed_datetime(borrow_date, hour=random.randint(8, 18)) if random.random() > 0.5 else None,
                approval_comment='Approved' if random.random() > 0.8 else '',
                lent_by=random.choice(users) if users and random.random() > 0.4 else None,
                lent_at=self._seed_datetime(borrow_date, day_offset=random.randint(0, 2)) if random.random() > 0.5 else None,
                returned_at=self._seed_datetime(actual_return, day_offset=1) if is_returned and random.random() > 0.5 else None,
                return_confirmed_by=random.choice(users) if users and is_returned and random.random() > 0.4 else None,
                asset_condition=random.choice(conditions) if is_returned else '',
                return_comment='Returned in good condition' if is_returned and random.random() > 0.7 else ''
            )
            loans.append(loan)

            # Add items
            num_items = random.randint(1, min(2, len(assets))) if assets else 0
            for j, asset in enumerate(self._pick_distinct_assets(assets, num_items)):

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
                started_at=self._seed_datetime(planned_date, day_offset=1) if random.random() > 0.5 else None,
                completed_at=self._seed_datetime(planned_date, day_offset=random.randint(3, 10)) if random.random() > 0.6 else None,
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
        available_asset_count = len(assets)

        if not tasks or available_asset_count == 0:
            return snapshots

        for task in tasks:
            # Create snapshots for some assets
            max_snapshots = min(50, available_asset_count)
            min_snapshots = min(10, max_snapshots)
            num_snapshots = random.randint(min_snapshots, max_snapshots)
            selected_assets = random.sample(assets, min(num_snapshots, available_asset_count))

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
