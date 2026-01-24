from django.contrib import admin
from .models import Software, SoftwareLicense, LicenseAllocation


@admin.register(Software)
class SoftwareAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'version', 'vendor', 'software_type', 'is_active']
    list_filter = ['software_type', 'is_active', 'created_at']
    search_fields = ['code', 'name', 'vendor', 'version']
    ordering = ['name']


@admin.register(SoftwareLicense)
class SoftwareLicenseAdmin(admin.ModelAdmin):
    list_display = ['license_no', 'software', 'total_units', 'used_units', 'status', 'expiry_date']
    list_filter = ['status', 'software__software_type', 'purchase_date', 'expiry_date']
    search_fields = ['license_no', 'software__name', 'agreement_no']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LicenseAllocation)
class LicenseAllocationAdmin(admin.ModelAdmin):
    list_display = ['license', 'asset', 'allocated_date', 'is_active', 'deallocated_date']
    list_filter = ['is_active', 'allocated_date', 'deallocated_date']
    search_fields = ['asset__asset_code', 'asset__asset_name', 'license__software__name']
    ordering = ['-allocated_date']
