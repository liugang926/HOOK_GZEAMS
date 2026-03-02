"""
Create test data for GZEAMS system.

This script creates sample Asset, Category, Location, and Supplier records
to populate the empty database for testing.
"""
import os
import sys

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django BEFORE importing models
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Now import models after Django is configured
from apps.assets.models import Asset, AssetCategory, Location, Supplier
from apps.organizations.models import Organization
from apps.accounts.models import User
from datetime import date


def create_test_data():
    """Create sample test data for the system."""

    # Get existing organization and user
    org = Organization.objects.first()
    if not org:
        print("❌ No organization found. Please create an organization first.")
        return

    user = User.objects.first()
    if not user:
        print("❌ No user found. Please create a user first.")
        return

    print(f"✅ Using organization: {org.name} (ID: {org.id})")
    print(f"✅ Using user: {user.username} (ID: {user.id})")

    # Create Categories
    print("\n📁 Creating Asset Categories...")
    categories_data = [
        {'code': '2001', 'name': 'Computer Equipment', 'sort_order': 1},
        {'code': '2002', 'name': 'Office Equipment', 'sort_order': 2},
        {'code': '2003', 'name': 'Furniture & Fixtures', 'sort_order': 3},
        {'code': '2004', 'name': 'Vehicles', 'sort_order': 4},
        {'code': '2005', 'name': 'Software Licenses', 'sort_order': 5},
    ]

    categories = []
    for cat_data in categories_data:
        cat, created = AssetCategory.objects.get_or_create(
            organization=org,
            code=cat_data['code'],
            defaults={
                'name': cat_data['name'],
                'sort_order': cat_data['sort_order'],
                'is_custom': False,
                'is_active': True,
                'created_by': user,
            }
        )
        categories.append(cat)
        if created:
            print(f"  ✅ Created category: {cat.code} - {cat.name}")
        else:
            print(f"  ℹ️  Category already exists: {cat.code} - {cat.name}")

    # Create Locations (Location doesn't have 'code' field)
    print("\n📍 Creating Locations...")
    locations_data = [
        {'name': 'Headquarters', 'location_type': 'building', 'level': 0},
        {'name': 'Office A', 'location_type': 'area', 'level': 1},
        {'name': 'Office B', 'location_type': 'area', 'level': 1},
        {'name': 'Warehouse', 'location_type': 'warehouse', 'level': 1},
        {'name': 'Server Room', 'location_type': 'room', 'level': 1},
    ]

    locations = []
    for loc_data in locations_data:
        # Create or get location
        location, created = Location.objects.get_or_create(
            organization=org,
            name=loc_data['name'],
            defaults={
                'location_type': loc_data['location_type'],
                'created_by': user,
            }
        )
        locations.append(location)
        if created:
            print(f"  ✅ Created location: {location.path}")
        else:
            print(f"  ℹ️  Location already exists: {location.path}")

    # Create Suppliers
    print("\n🏢 Creating Suppliers...")
    suppliers_data = [
        {'code': 'SUP001', 'name': 'Tech Solutions Inc.', 'contact': 'John Smith', 'phone': '123-456-7890'},
        {'code': 'SUP002', 'name': 'Office Supplies Co.', 'contact': 'Jane Doe', 'phone': '098-765-4321'},
        {'code': 'SUP003', 'name': 'Furniture World', 'contact': 'Bob Johnson', 'phone': '555-123-4567'},
    ]

    suppliers = []
    for sup_data in suppliers_data:
        supplier, created = Supplier.objects.get_or_create(
            organization=org,
            code=sup_data['code'],
            defaults={
                'name': sup_data['name'],
                'contact': sup_data['contact'],
                'phone': sup_data['phone'],
                'created_by': user,
            }
        )
        suppliers.append(supplier)
        if created:
            print(f"  ✅ Created supplier: {supplier.code} - {supplier.name}")
        else:
            print(f"  ℹ️  Supplier already exists: {supplier.code} - {supplier.name}")

    # Create Assets
    print("\n💼 Creating Assets...")
    assets_data = [
        {
            'asset_name': 'MacBook Pro 16"',
            'category': categories[0],  # Computer Equipment
            'specification': 'M2 Max, 32GB RAM, 1TB SSD',
            'brand': 'Apple',
            'model': 'MacBook Pro 16"',
            'purchase_price': 3299.00,
            'purchase_date': date(2024, 1, 15),
            'location': locations[1],  # Office A
            'supplier': suppliers[0],
            'asset_status': 'in_use',
        },
        {
            'asset_name': 'Dell XPS 15',
            'category': categories[0],  # Computer Equipment
            'specification': 'i7-13700H, 16GB RAM, 512GB SSD',
            'brand': 'Dell',
            'model': 'XPS 15 9530',
            'purchase_price': 1899.00,
            'purchase_date': date(2024, 2, 10),
            'location': locations[2],  # Office B
            'supplier': suppliers[0],
            'asset_status': 'in_use',
        },
        {
            'asset_name': 'Office Chair',
            'category': categories[2],  # Furniture & Fixtures
            'specification': 'Ergonomic mesh chair',
            'brand': 'Herman Miller',
            'model': 'Aeron',
            'purchase_price': 1295.00,
            'purchase_date': date(2024, 3, 5),
            'location': locations[1],  # Office A
            'supplier': suppliers[2],
            'asset_status': 'in_use',
        },
        {
            'asset_name': 'Standing Desk',
            'category': categories[2],  # Furniture & Fixtures
            'specification': 'Electric height-adjustable desk',
            'brand': 'Vari',
            'model': 'Electric Standing Desk',
            'purchase_price': 699.00,
            'purchase_date': date(2024, 3, 10),
            'location': locations[2],  # Office B
            'supplier': suppliers[2],
            'asset_status': 'in_use',
        },
        {
            'asset_name': 'HP LaserJet Printer',
            'category': categories[1],  # Office Equipment
            'specification': 'Multifunction laser printer',
            'brand': 'HP',
            'model': 'LaserJet Pro MFP M479fdw',
            'purchase_price': 549.00,
            'purchase_date': date(2024, 4, 1),
            'location': locations[1],  # Office A
            'supplier': suppliers[1],
            'asset_status': 'idle',
        },
        {
            'asset_name': 'Windows Server 2022',
            'category': categories[4],  # Software Licenses
            'specification': 'Server license, 16 cores',
            'brand': 'Microsoft',
            'model': 'Windows Server 2022 Datacenter',
            'purchase_price': 4599.00,
            'purchase_date': date(2024, 1, 20),
            'location': locations[4],  # Server Room
            'supplier': suppliers[0],
            'asset_status': 'in_use',
        },
        {
            'asset_name': 'Company Car - Toyota Camry',
            'category': categories[3],  # Vehicles
            'specification': '2024 Model, Hybrid',
            'brand': 'Toyota',
            'model': 'Camry Hybrid LE',
            'purchase_price': 28500.00,
            'purchase_date': date(2024, 5, 1),
            'location': locations[0],  # Headquarters
            'supplier': suppliers[0],
            'asset_status': 'in_use',
        },
        {
            'asset_name': 'iPad Pro 12.9"',
            'category': categories[0],  # Computer Equipment
            'specification': 'M2, 256GB, Wi-Fi + Cellular',
            'brand': 'Apple',
            'model': 'iPad Pro 12.9" M2',
            'purchase_price': 1199.00,
            'purchase_date': date(2024, 2, 20),
            'location': locations[1],  # Office A
            'supplier': suppliers[0],
            'asset_status': 'idle',
        },
    ]

    assets_created = 0
    for asset_data in assets_data:
        # Check if asset with similar name already exists
        existing = Asset.objects.filter(
            organization=org,
            asset_name=asset_data['asset_name']
        ).first()

        if existing:
            print(f"  ℹ️  Asset already exists: {existing.asset_code} - {existing.asset_name}")
            continue

        asset = Asset.objects.create(
            organization=org,
            asset_name=asset_data['asset_name'],
            asset_category=asset_data['category'],
            specification=asset_data.get('specification', ''),
            brand=asset_data.get('brand', ''),
            model=asset_data.get('model', ''),
            purchase_price=asset_data['purchase_price'],
            current_value=asset_data['purchase_price'],  # Initially same as purchase price
            purchase_date=asset_data['purchase_date'],
            depreciation_start_date=asset_data['purchase_date'],
            useful_life=60,  # 5 years in months
            residual_rate=5.00,
            location=asset_data.get('location'),
            supplier=asset_data.get('supplier'),
            custodian=user,
            asset_status=asset_data['asset_status'],
            created_by=user,
        )
        assets_created += 1
        print(f"  ✅ Created asset: {asset.asset_code} - {asset.asset_name}")

    print(f"\n📊 Summary:")
    print(f"  - Categories: {len(categories)}")
    print(f"  - Locations: {len(locations)}")
    print(f"  - Suppliers: {len(suppliers)}")
    print(f"  - New Assets Created: {assets_created}")

    # Verify final counts
    print(f"\n🔍 Current Database Counts:")
    print(f"  - AssetCategory: {AssetCategory.objects.filter(organization=org, is_deleted=False).count()}")
    print(f"  - Location: {Location.objects.filter(organization=org, is_deleted=False).count()}")
    print(f"  - Supplier: {Supplier.objects.filter(organization=org, is_deleted=False).count()}")
    print(f"  - Asset: {Asset.objects.filter(organization=org, is_deleted=False).count()}")


if __name__ == '__main__':
    create_test_data()
    print("\n✅ Test data creation completed!")
