from apps.common.services.base_crud import BaseCRUDService
from .models import Software, SoftwareLicense, LicenseAllocation


class SoftwareService(BaseCRUDService):
    """Software Catalog Service"""

    def __init__(self):
        super().__init__(Software)

    def get_by_code(self, code: str):
        """Get software by code."""
        return self.model_class.objects.filter(code=code).first()


class SoftwareLicenseService(BaseCRUDService):
    """Software License Service"""

    def __init__(self):
        super().__init__(SoftwareLicense)

    def get_expiring_licenses(self, organization_id: str, days: int = 30):
        """Get licenses expiring within specified days."""
        from django.utils import timezone
        from datetime import timedelta

        delta = timezone.now().date() + timedelta(days=days)

        return self.model_class.objects.filter(
            organization_id=organization_id,
            expiry_date__lte=delta,
            status='active'
        )

    def get_over_utilized_licenses(self, organization_id: str):
        """Get licenses with utilization over 100%."""
        licenses = self.model_class.objects.filter(
            organization_id=organization_id,
            status='active'
        )

        over_utilized = []
        for license in licenses:
            if license.utilization_rate() > 100:
                over_utilized.append(license)

        return over_utilized

    def allocate_license(self, license_id: str, asset_id: str,
                         allocated_by: str, allocation_key: str = None,
                         notes: str = None):
        """Allocate a license to an asset."""
        from django.utils import timezone

        license = self.get(license_id)

        if license.available_units() <= 0:
            raise ValueError('No available licenses')

        from apps.assets.models import Asset
        asset = Asset.objects.get(id=asset_id)

        allocation = LicenseAllocation.objects.create(
            organization_id=license.organization_id,
            license_id=license_id,
            asset_id=asset_id,
            allocated_by_id=allocated_by,
            allocated_date=timezone.now().date(),
            allocation_key=allocation_key,
            notes=notes or '',
            created_by_id=allocated_by
        )

        return allocation

    def deallocate_license(self, allocation_id: str, deallocated_by: str):
        """Deallocate a license from an asset."""
        from datetime import date

        allocation = LicenseAllocation.objects.get(id=allocation_id)

        if allocation.is_active and allocation.license.used_units > 0:
            allocation.license.used_units -= 1
            allocation.license.save()

        allocation.is_active = False
        allocation.deallocated_date = date.today()
        allocation.deallocated_by_id = deallocated_by
        allocation.save()

        return allocation


class LicenseAllocationService(BaseCRUDService):
    """License Allocation Service"""

    def __init__(self):
        super().__init__(LicenseAllocation)

    def get_by_asset(self, asset_id: str):
        """Get allocations for an asset."""
        return self.model_class.objects.filter(asset_id=asset_id, is_active=True)

    def get_by_license(self, license_id: str):
        """Get allocations for a license."""
        return self.model_class.objects.filter(license_id=license_id)


__all__ = [
    'SoftwareService',
    'SoftwareLicenseService',
    'LicenseAllocationService',
]
