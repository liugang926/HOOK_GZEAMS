from rest_framework import routers
from django.urls import path
from apps.depreciation.viewsets import (
    DepreciationConfigViewSet,
    DepreciationRecordViewSet,
    DepreciationRunViewSet,
)

app_router = routers.DefaultRouter()

# Depreciation configuration endpoints
app_router.register(r'configs', DepreciationConfigViewSet, basename='depreciation-config')
# Compatibility alias for legacy frontend paths: /api/depreciation/config/...
app_router.register(r'config', DepreciationConfigViewSet, basename='depreciation-config-compat')

# Depreciation record endpoints
app_router.register(r'records', DepreciationRecordViewSet, basename='depreciation-record')

# Depreciation run endpoints
app_router.register(r'runs', DepreciationRunViewSet, basename='depreciation-run')

urlpatterns = [
    *app_router.urls,
    # Compatibility path aliases used by frontend adapters
    path(
        'report/export/',
        DepreciationRecordViewSet.as_view({'get': 'export_report'}),
        name='depreciation-report-export'
    ),
    path(
        'assets/<uuid:asset_id>/detail/',
        DepreciationRecordViewSet.as_view({'get': 'asset_detail'}),
        name='depreciation-asset-detail'
    ),
]
