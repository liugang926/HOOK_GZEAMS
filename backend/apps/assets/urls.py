"""
URL configuration for Asset app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.assets.viewsets import (
    AssetCategoryViewSet,
    AssetViewSet,
    SupplierViewSet,
    LocationViewSet,
    AssetStatusLogViewSet,
    AssetPickupViewSet,
    AssetTransferViewSet,
    AssetReturnViewSet,
    AssetLoanViewSet,
)

router = DefaultRouter()

# Asset Category endpoints
router.register(r'categories', AssetCategoryViewSet, basename='assetcategory')

# Asset-related endpoints (register specific paths first)
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'status-logs', AssetStatusLogViewSet, basename='assetstatuslog')

# Operation endpoints
router.register(r'pickups', AssetPickupViewSet, basename='asset-pickup')
router.register(r'transfers', AssetTransferViewSet, basename='asset-transfer')
router.register(r'returns', AssetReturnViewSet, basename='asset-return')
router.register(r'loans', AssetLoanViewSet, basename='asset-loan')

# Asset endpoints (register empty path last to avoid catching other URLs)
router.register(r'', AssetViewSet, basename='asset')

app_name = 'assets'

urlpatterns = [
    path('', include(router.urls)),
]
