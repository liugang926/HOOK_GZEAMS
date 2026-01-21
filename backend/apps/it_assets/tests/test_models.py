import pytest
import uuid
from django.test import TestCase
from apps.it_assets.models import ITAssetInfo, Software, SoftwareLicense
from apps.assets.models import Asset, AssetCategory, Location
from apps.organizations.models import Organization
from apps.accounts.models import User


class ITAssetInfoModelTest(TestCase):
    def setUp(self):
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Org {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            organization=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='COMPUTER',
            name='Computer Equipment',
            created_by=self.user
        )
        self.location = Location.objects.create(
            name=f'Test Location {self.unique_suffix}',
            path=f'Test Location {self.unique_suffix}',
            organization=self.org
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_code=f'ASSET{self.unique_suffix}',
            asset_name='Test Laptop',
            asset_category=self.category,
            location=self.location,
            purchase_price=10000,
            purchase_date='2026-01-01',
            created_by=self.user
        )

    def test_create_it_asset_info(self):
        """Test creating IT asset info with hardware specs"""
        it_info = ITAssetInfo.objects.create(
            organization=self.org,
            asset=self.asset,
            cpu_model='Intel Core i7-12700K',
            cpu_cores=12,
            ram_capacity=32,
            ram_type='DDR5',
            disk_type='NVMe',
            disk_capacity=1024,
            mac_address='00:1A:2B:3C:4D:5E',
            ip_address='192.168.1.100',
            os_name='Windows 11 Pro',
            os_version='22H2',
            created_by=self.user
        )

        assert it_info.asset == self.asset
        assert it_info.cpu_model == 'Intel Core i7-12700K'
        assert it_info.ram_capacity == 32
        assert it_info.mac_address == '00:1A:2B:3C:4D:5E'

    def test_get_full_config(self):
        """Test full configuration summary"""
        it_info = ITAssetInfo.objects.create(
            organization=self.org,
            asset=self.asset,
            cpu_model='Intel Core i7',
            ram_capacity=32,
            ram_type='DDR5',
            disk_capacity=1024,
            created_by=self.user
        )

        config = it_info.get_full_config()
        assert 'Intel Core i7' in config
        assert '32GB' in config
        assert '1024GB' in config


class SoftwareModelTest(TestCase):
    def setUp(self):
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Org {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            organization=self.org
        )

    def test_create_software(self):
        """Test creating software entry"""
        software = Software.objects.create(
            organization=self.org,
            name='Microsoft Office 2021',
            vendor='Microsoft',
            version='2021',
            category='Productivity',
            license_type='commercial',
            created_by=self.user
        )

        assert software.name == 'Microsoft Office 2021'
        assert software.vendor == 'Microsoft'
        assert software.version == '2021'
        assert software.category == 'Productivity'
        assert software.license_type == 'commercial'

    def test_software_str(self):
        """Test software string representation"""
        software = Software.objects.create(
            organization=self.org,
            name='Adobe Photoshop',
            vendor='Adobe',
            version='CC 2024',
            created_by=self.user
        )

        assert str(software) == 'Adobe Photoshop CC 2024'


class SoftwareLicenseModelTest(TestCase):
    def setUp(self):
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Org {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            organization=self.org
        )
        self.software = Software.objects.create(
            organization=self.org,
            name='Microsoft Office 2021',
            vendor='Microsoft',
            version='2021',
            created_by=self.user
        )

    def test_create_software_license(self):
        """Test creating software license"""
        from datetime import date

        license = SoftwareLicense.objects.create(
            organization=self.org,
            software=self.software,
            license_key='XXXXX-XXXXX-XXXXX-XXXXX-XXXXX',
            seats=10,
            seats_used=3,
            purchase_date=date.today(),
            expiry_date=date(2027, 12, 31),
            cost=5000,
            created_by=self.user
        )

        assert license.software == self.software
        assert license.license_key == 'XXXXX-XXXXX-XXXXX-XXXXX-XXXXX'
        assert license.seats == 10
        assert license.seats_used == 3
        assert license.expiry_date.year == 2027

    def test_license_available_seats(self):
        """Test available seats calculation"""
        from datetime import date

        license = SoftwareLicense.objects.create(
            organization=self.org,
            software=self.software,
            license_key='KEY-1234',
            seats=10,
            seats_used=3,
            created_by=self.user
        )

        assert license.available_seats() == 7

    def test_license_is_expired(self):
        """Test license expiry check"""
        from datetime import date, timedelta

        # Expired license
        expired_license = SoftwareLicense.objects.create(
            organization=self.org,
            software=self.software,
            license_key='KEY-EXPIRED',
            seats=1,
            expiry_date=date.today() - timedelta(days=1),
            created_by=self.user
        )
        assert expired_license.is_expired() is True

        # Valid license
        valid_license = SoftwareLicense.objects.create(
            organization=self.org,
            software=self.software,
            license_key='KEY-VALID',
            seats=1,
            expiry_date=date.today() + timedelta(days=30),
            created_by=self.user
        )
        assert valid_license.is_expired() is False
