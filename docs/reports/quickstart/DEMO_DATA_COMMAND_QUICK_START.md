# Demo Data Management Command - Quick Start

## Document Information
| Project | Description |
|---------|-------------|
| Command Name | `create_demo_data` |
| Version | 1.0 |
| Created Date | 2026-01-28 |
| Author | Claude (Anthropic) |
| File Location | `backend/apps/common/management/commands/create_demo_data.py` |

---

## Overview

This Django management command generates comprehensive demo data for all business objects in the GZEAMS system. It creates 20-50 realistic records for testing, demonstration, and development purposes.

---

## Command Location

**File Path:** `C:\Users\ND\Desktop\Notting_Project\NEWSEAMS\backend\apps\common\management\commands\create_demo_data.py`

**Lines of Code:** 1,255 lines

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

# Combined options
python manage.py create_demo_data --count 40 --organization <ORG_ID> --skip-existing
```

### Command Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--count` | Integer | 30 | Number of records to create for each model |
| `--organization` | String | First org | Organization ID to use (uses first organization if not specified) |
| `--skip-existing` | Flag | False | Skip models that already have data |

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

### 3. Asset Operations
| Model | Records | Description |
|-------|---------|-------------|
| `AssetPickup` | 15-30 | Employee asset pickup requests with items |
| `AssetTransfer` | 15-30 | Inter-department transfers with dual approval |
| `AssetReturn` | 10-30 | Asset return orders with condition checks |
| `AssetLoan` | 15-30 | Temporary asset loans with return tracking |

### 4. Consumables
| Model | Records | Description |
|-------|---------|-------------|
| `ConsumableCategory` | 5 | Paper, Writing Instruments, Desk Supplies, etc. |
| `Consumable` | 20 | Office supplies with stock tracking |
| `ConsumableStock` | 30-50 | Stock transaction history |
| `ConsumablePurchase` | 20-30 | Purchase orders with items |
| `ConsumableIssue` | 20-30 | Distribution to departments |

### 5. Lifecycle Management
| Model | Records | Description |
|-------|---------|-------------|
| `PurchaseRequest` | 20-30 | Asset procurement requests with approval workflow |
| `AssetReceipt` | 15-30 | Goods receipt with quality inspection |
| `Maintenance` | 20-30 | Repair records with costs and verification |
| `MaintenancePlan` | 10 | Scheduled maintenance plans |
| `DisposalRequest` | 10-30 | Asset disposal with technical appraisal |

### 6. Inventory Management
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

### 3. Status Variety
- Multiple status choices for each model
- Realistic status progression (draft → submitted → approved → completed)
- Timestamps that make sense (approved_at after created_at)

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

```
Starting demo data creation...
  Created 5 asset categories
  Created 38 locations
  Created 10 suppliers
  Created 30 assets
  Created 5 consumable categories
  Created 20 consumables
  Created 50 stock transactions
  Created 20 consumable purchases
  Created 20 consumable issues
  Created 20 purchase requests
  Created 15 asset receipts
  Created 20 maintenance records
  Created 10 maintenance plans
  Created 10 disposal requests
  Created 15 asset pickups
  Created 15 asset transfers
  Created 10 asset returns
  Created 15 asset loans
  Created 10 inventory tasks
  Created 150 inventory snapshots
  Created 50 inventory scans

=== Demo Data Creation Summary ===
Organization: Default Organization
  asset_categories: 5
  locations: 38
  suppliers: 10
  assets: 30
  consumable_categories: 5
  consumables: 20
  consumable_stocks: 50
  consumable_purchases: 20
  consumable_issues: 20
  purchase_requests: 20
  asset_receipts: 15
  maintenance: 20
  maintenance_plans: 10
  disposal_requests: 10
  asset_pickups: 15
  asset_transfers: 15
  asset_returns: 10
  asset_loans: 15
  inventory_tasks: 10
  inventory_snapshots: 150
  inventory_scans: 50

Total records created: 628
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

5. **Data Integrity**: All foreign keys properly validated
   - Parent organizations must exist
   - Required related objects created first

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
