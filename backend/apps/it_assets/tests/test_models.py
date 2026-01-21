import pytest
import uuid
from django.test import TestCase
from apps.it_assets.models import ITAssetInfo
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
