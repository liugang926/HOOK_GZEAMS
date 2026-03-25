# Demo Data Management Command - Quick Start

## Document Information
| Project | Description |
|---------|-------------|
| Command Name | `create_demo_data` |
| Version | 1.4 |
| Created Date | 2026-03-20 |
| Author | Codex |
| File Location | `backend/apps/common/management/commands/create_demo_data.py` |

---

## Overview

This Django management command generates comprehensive demo data for all business objects in the GZEAMS system. It creates 20-50 realistic records for testing, demonstration, and development purposes, and now includes project-oriented relationship data plus finance workspace and ERP integration chains for unified workspace verification. Fresh-organization first runs and `--skip-existing --top-up-existing` reruns have both been verified in Docker without unique-key collisions or `DateTimeField` runtime warnings.

---

## Command Location

**File Path:** `/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/common/management/commands/create_demo_data.py`

**Lines of Code:** 2,510 lines

---

## Usage

### Basic Usage

```bash
# Create demo data with default settings (30 records per model)
python manage.py create_demo_data

# Create custom number of records
python manage.py create_demo_data --count 50

# Use specific organization
python manage.py create_demo_data --organization <ORG_ID>

# Skip models that already have data
python manage.py create_demo_data --skip-existing

# Top up existing models to the requested minimum count
python manage.py create_demo_data --count 20 --skip-existing --top-up-existing

# Combined options
python manage.py create_demo_data --count 40 --organization <ORG_ID> --skip-existing
```

### Command Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--count` | Integer | 30 | Number of records to create for each model |
| `--organization` | String | First org | Organization ID to use (uses first organization if not specified) |
| `--skip-existing` | Flag | False | Skip models that already have data |
| `--top-up-existing` | Flag | False | Top up existing records to the requested minimum count instead of leaving partial data untouched |

---

## Data Models Created

### 1. Organizations & Users
- **Organization**: Uses existing or creates default
- **Users**: 5 demo users (admin, Zhang Wei, Li Na, Wang Feng, Liu Yang)
- **Departments**: 5 departments (IT, HR, Finance, Operations, Marketing)

### 2. Assets (Core Module)
| Model | Records | Description |
|-------|---------|-------------|
| `AssetCategory` | 5 | Computer Equipment, Office Equipment, Furniture, Vehicles, Machinery |
| `Location` | ~40 | Building hierarchy (Buildings > Floors > Rooms) + Warehouse |
| `Supplier` | 10 | 10 Chinese suppliers with contact info |
| `Asset` | 30-50 | Desktops, laptops, servers, printers, furniture, vehicles |

### 3. Asset Project Workspace
| Model | Records | Description |
|-------|---------|-------------|
| `AssetProject` | 20-30 | Multi-status project portfolio records for planning, active, suspended, completed, and cancelled workspaces |
| `ProjectMember` | 40-80 | Manager/member/observer combinations with primary member and cost visibility flags |
| `ProjectAsset` | 20-30 | Project asset allocations with `in_use / returned / transferred` lifecycle coverage |

### 4. Asset Operations
| Model | Records | Description |
|-------|---------|-------------|
| `AssetPickup` | 15-30 | Employee asset pickup requests with unique asset line items |
| `AssetTransfer` | 15-30 | Inter-department transfers with dual approval and unique asset line items |
| `AssetReturn` | 10-30 | Asset return orders with condition checks, including project allocation linkage when available |
| `AssetLoan` | 15-30 | Temporary asset loans with return tracking |

### 5. Finance Workspace & ERP Integration
| Model | Records | Description |
|-------|---------|-------------|
| `VoucherTemplate` | 5 | Finance voucher templates for purchase, depreciation, disposal, inventory, and general journal scenarios |
| `FinanceVoucher` | 20+ | Balanced vouchers with `draft / submitted / approved / posted / rejected` status coverage |
| `VoucherEntry` | 40+ | Debit/credit voucher lines with balanced totals for each seeded voucher |
| `IntegrationConfig` | 1 | Finance-enabled M18 integration configuration for the current organization |
| `IntegrationSyncTask` | 20+ | Finance sync tasks with queued, success, and failed execution states |
| `IntegrationLog` | 20+ | Finance voucher integration logs linked to sync tasks and ERP response payloads |

### 6. Consumables
| Model | Records | Description |
|-------|---------|-------------|
| `ConsumableCategory` | 5 | Paper, Writing Instruments, Desk Supplies, etc. |
| `Consumable` | 20 | Office supplies with stock tracking |
| `ConsumableStock` | 30-50 | Stock transaction history |
| `ConsumablePurchase` | 20-30 | Purchase orders with items |
| `ConsumableIssue` | 20-30 | Distribution to departments |

### 7. Lifecycle Management
| Model | Records | Description |
|-------|---------|-------------|
| `PurchaseRequest` | 20-30 | Asset procurement requests with approval workflow |
| `AssetReceipt` | 15-30 | Goods receipt with quality inspection |
| `Maintenance` | 20-30 | Repair records with costs and verification |
| `MaintenancePlan` | 10 | Scheduled maintenance plans |
| `DisposalRequest` | 10-30 | Asset disposal with technical appraisal |

### 8. Inventory Management
| Model | Records | Description |
|-------|---------|-------------|
| `InventoryTask` | 10 | Full/partial/department/category inventory tasks |
| `InventorySnapshot` | Varies | Asset snapshots at task creation |
| `InventoryScan` | 30-50 | Scan records with discrepancy tracking |

---

## Features

### 1. Realistic Chinese Data
- Company names: Beijing Technology Co., Ltd., Shanghai Electronics Corp.
- Person names: Zhang Wei, Li Na, Wang Feng, Liu Yang
- Locations: Building A/B with floor/room hierarchy
- Asset names: Mix of English brands with Chinese context

### 2. Valid Relationships
- Foreign key relationships are properly linked
- Parent-child hierarchies (categories, locations, departments)
- Many-to-many relationships properly created
- Project workspaces include members, allocations, and project-linked asset return records
- Finance workspaces include `FinanceVoucher -> VoucherEntry -> IntegrationSyncTask -> IntegrationLog` chains

### 3. Status Variety
- Multiple status choices for each model
- Realistic status progression (draft → submitted → approved → completed)
- Timestamps that make sense (approved_at after created_at)
- Finance vouchers cover `draft / submitted / approved / posted / rejected`
- Finance integration tasks cover `pending / running / success / failed`

### 4. Financial Accuracy
- Purchase prices, current values, accumulated depreciation
- Total costs calculated from labor + material + other
- Net book values (original - accumulated depreciation)

### 5. Audit Trail
- All records include created_by, created_at, updated_at
- Soft delete support (is_deleted flag)
- Organization isolation enforced

---

## Demo Users Created

| Username | Full Name | Email | Role |
|----------|-----------|-------|------|
| `admin` | Administrator | admin@demo.com | Administrator |
| `user1` | Zhang Wei | zhang.wei@demo.com | Member |
| `user2` | Li Na | li.na@demo.com | Member |
| `user3` | Wang Feng | wang.feng@demo.com | Member |
| `user4` | Liu Yang | liu.yang@demo.com | Member |

**Default Password:** `demo123456`

---

## Sample Output

Representative output for a `--count 20` baseline run is shown below. Actual totals vary by existing data, top-up mode, and related snapshot counts.

```
Starting demo data creation...
  Created 5 asset categories
  Created 38 locations
  Created 10 suppliers
  Created 30 assets
  Created 20 asset projects
  Created 59 project members
  Created 20 project asset allocations
  Created 5 voucher templates
  Created 20 finance vouchers
  Created 40 voucher entries
  Created 1 finance integration configs
  Created 24 finance integration sync tasks
  Created 24 finance integration logs
  Created 5 consumable categories
  Created 20 consumables
  Created 50 stock transactions
  Created 20 consumable purchases
  Created 20 consumable issues
  Created 20 purchase requests
  Created 20 asset receipts
  Created 20 maintenance records
  Created 20 maintenance plans
  Created 20 disposal requests
  Created 20 asset pickups
  Created 20 asset transfers
  Created 20 asset returns
  Created 20 asset loans
  Created 20 inventory tasks
  Created 300 inventory snapshots
  Created 50 inventory scans

=== Demo Data Creation Summary ===
Organization: Default Organization
  asset_categories: 5
  locations: 38
  suppliers: 10
  assets: 30
  asset_projects: 20
  project_members: 59
  project_assets: 20
  voucher_templates: 5
  finance_vouchers: 20
  voucher_entries: 40
  integration_configs: 1
  integration_sync_tasks: 24
  integration_logs: 24
  consumable_categories: 5
  consumables: 20
  consumable_stocks: 50
  consumable_purchases: 20
  consumable_issues: 20
  purchase_requests: 20
  asset_receipts: 20
  maintenance: 20
  maintenance_plans: 20
  disposal_requests: 20
  asset_pickups: 20
  asset_transfers: 20
  asset_returns: 20
  asset_loans: 20
  inventory_tasks: 20
  inventory_snapshots: 300
  inventory_scans: 50

Total records created: 961
Demo data creation completed!
```

---

## Typical Use Cases

### 1. Development Environment Setup
```bash
# After running migrations
python manage.py migrate
python manage.py sync_schemas

# Create comprehensive demo data
python manage.py create_demo_data --count 50
```

### 2. Testing Scenarios
```bash
# Create smaller dataset for quick testing
python manage.py create_demo_data --count 20
```

### 3. Demonstration / Presentation
```bash
# Create rich dataset for demos
python manage.py create_demo_data --count 40
```

### 4. Incremental Data Addition
```bash
# Add more data without affecting existing records
python manage.py create_demo_data --count 30 --skip-existing
```

Note:
- `--skip-existing` keeps existing model data as-is. If a previous partial run left fewer than the target count for a model, rerunning with this flag will not top up that model automatically.
- Add `--top-up-existing` when you want the command to raise existing low-count business objects to the requested minimum.

---

## Data Cleanup

To remove all demo data and start fresh:

```sql
-- Soft delete all records (recommended)
UPDATE assets SET is_deleted = true;
UPDATE asset_pickups SET is_deleted = true;
-- ... repeat for other models

-- Or hard delete (use with caution)
DELETE FROM inventory_scans;
DELETE FROM inventory_snapshots;
DELETE FROM inventory_tasks;
-- ... repeat for other models in correct order (respect foreign keys)
```

Or use Django shell:
```python
from apps.assets.models import Asset
from apps.common.models import BaseModel

# Soft delete all BaseModel-derived records
for model in [Asset, AssetPickup, AssetTransfer, ...]:
    model.objects.all().update(is_deleted=True)
```

---

## Important Notes

1. **Organization Requirement**: An organization must exist before running this command
   - Creates default organization if none exists
   - Or use `--organization` to specify existing org

2. **User Accounts**: Creates 5 demo users with password `demo123456`
   - Change passwords in production environments
   - Users are linked to the organization automatically

3. **ID Generation**: Uses sequence services for auto-generated codes
   - Asset codes: ZC + YYYYMM + NNNN
   - Pickup/Transfer/Return codes: LY/TF/RT + YYYYMM + NNNN
   - Inventory codes: PD + YYYYMM + NNNN

4. **Performance**: Large counts (100+) may take several minutes
   - Recommended: 20-50 for development
   - Use `--skip-existing` to avoid duplicates
   - Use a clean organization or remove incomplete seed data first if you need exact target counts for every object
   - Use `--top-up-existing` to repair interrupted or older demo datasets that still have less than 20 document records

5. **Data Integrity**: All foreign keys properly validated
   - Parent organizations must exist
   - Required related objects created first
   - Date-based workflow timestamps are generated as timezone-aware datetimes to avoid `DateTimeField` runtime warnings during seed runs
   - Prefix-based document and master-data codes now derive from sequence-safe helpers, so fresh organizations do not collide with legacy demo data from other organizations
   - Verified reruns with `--skip-existing --top-up-existing` keep completed datasets stable and avoid duplicate inserts

---

## Troubleshooting

### Error: "No organization found"
**Solution**: Create an organization first or check the organization ID
```python
from apps.organizations.models import Organization
org = Organization.objects.create(name='Demo Org', code='DEMO')
```

### Error: "No users found"
**Solution**: The command creates users automatically. If this fails, check User model configuration.

### Warning: "Using existing X categories"
**Solution**: This is normal when using `--skip-existing`. The command uses existing data instead of creating duplicates.

### Need to repair low-count demo data after an interrupted run
**Solution**: Use top-up mode to fill partial data instead of recreating everything.
```bash
python manage.py create_demo_data --count 20 --skip-existing --top-up-existing
```

### Fresh organization seed used to hit unique code collisions
**Current Status**: Fixed. Supplier, consumable category, consumable, purchase request, and other prefixed codes now use organization-aware or numeric max-sequence generation, so first-time runs in new organizations are sequence-safe even when older organizations already contain legacy demo codes.

---

## Code Structure

### Main Methods

| Method | Purpose |
|--------|---------|
| `handle()` | Main entry point, orchestrates data creation |
| `_get_organization()` | Get or validate organization |
| `_get_or_create_users()` | Create demo users with org links |
| `_get_or_create_departments()` | Create department hierarchy |
| `_create_asset_categories()` | Create asset category tree |
| `_create_locations()` | Create building/floor/room hierarchy |
| `_create_suppliers()` | Create supplier records |
| `_create_assets()` | Create assets with FK relationships |
| `_create_consumables()` | Create consumable items |
| `_create_*_operations()` | Create pickup/transfer/return/loan records |
| `_create_*_lifecycle()` | Create maintenance/disposal records |
| `_create_inventory_*()` | Create inventory tasks and scans |

### Helper Methods

- Random data selection from lists
- Date calculations with realistic ranges
- Decimal/float financial calculations
- Foreign key relationship validation

---

## Extending the Command

To add more models or customize data:

1. **Add new model creation method**
   ```python
   def _create_new_model(self, organization, ...):
       records = []
       for i in range(count):
           record = NewModel.objects.create(
               organization=organization,
               # ... fields
           )
           records.append(record)
       return records
   ```

2. **Call from handle() method**
   ```python
   # In handle() method
   if not skip_existing or not NewModel.objects.filter(organization=organization).exists():
       new_records = self._create_new_model(organization, ...)
       stats['new_model'] = len(new_records)
   ```

3. **Add to statistics output**
   ```python
   self.stdout.write(f'  Created {len(new_records)} new model records')
   ```

---

## Related Files

- **Models**: `backend/apps/{module}/models.py`
- **Base Classes**: `backend/apps/common/models.py`
- **Management Commands**: `backend/apps/common/management/commands/`

---

## Support

For issues or questions:
1. Check Django logs: `logs/django.log`
2. Verify database connections
3. Ensure all migrations are run
4. Check foreign key relationships exist

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-28 | Initial release with full model coverage |
| 1.1 | 2026-03-20 | Added asset project relationship seed, finance voucher seed, and finance integration seed documentation |
| 1.2 | 2026-03-20 | Added top-up mode for repairing partial demo data and documented 20+ document object replenishment |
| 1.3 | 2026-03-21 | Replaced date-based workflow timestamps with timezone-aware datetimes to suppress seed-time runtime warnings |
| 1.4 | 2026-03-21 | Hardened cross-organization sequence generation and documented verified fresh-run plus rerun stability in Docker |
