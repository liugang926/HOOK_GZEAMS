"""
URL Configuration for IT Assets app.

Registers all ViewSets with router for REST API endpoints.
"""
from rest_framework import routers
from apps.it_assets.viewsets import (
    ITAssetInfoViewSet,
    SoftwareViewSet,
    SoftwareLicenseViewSet,
    LicenseAllocationViewSet,
    ITMaintenanceRecordViewSet,
    ConfigurationChangeViewSet,
)

app_router = routers.DefaultRouter()

# IT Asset Info endpoints
app_router.register(r'it-assets', ITAssetInfoViewSet, basename='it-asset')

# Software endpoints
app_router.register(r'software', SoftwareViewSet, basename='software')

# Software License endpoints
app_router.register(r'licenses', SoftwareLicenseViewSet, basename='software-license')

# License Allocation endpoints
app_router.register(r'license-allocations', LicenseAllocationViewSet, basename='license-allocation')

# IT Maintenance Record endpoints
app_router.register(r'maintenance', ITMaintenanceRecordViewSet, basename='it-maintenance')

# Configuration Change endpoints
app_router.register(r'configuration-changes', ConfigurationChangeViewSet, basename='configuration-change')

urlpatterns = app_router.urls
