"""
URL Configuration for Lifecycle Management app.

Registers all ViewSets with router for REST API endpoints.
"""
from rest_framework import routers
from apps.lifecycle.viewsets import (
    PurchaseRequestViewSet,
    AssetReceiptViewSet,
    MaintenanceViewSet,
    MaintenancePlanViewSet,
    MaintenanceTaskViewSet,
    DisposalRequestViewSet,
)

app_router = routers.DefaultRouter()

# Purchase request endpoints
app_router.register(r'purchase-requests', PurchaseRequestViewSet, basename='purchase-request')

# Asset receipt endpoints
app_router.register(r'asset-receipts', AssetReceiptViewSet, basename='asset-receipt')

# Maintenance endpoints
app_router.register(r'maintenance', MaintenanceViewSet, basename='maintenance')

# Maintenance plan endpoints
app_router.register(r'maintenance-plans', MaintenancePlanViewSet, basename='maintenance-plan')

# Maintenance task endpoints
app_router.register(r'maintenance-tasks', MaintenanceTaskViewSet, basename='maintenance-task')

# Disposal request endpoints
app_router.register(r'disposal-requests', DisposalRequestViewSet, basename='disposal-request')

urlpatterns = app_router.urls
