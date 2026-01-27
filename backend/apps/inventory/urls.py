"""
URL configuration for inventory app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.inventory.viewsets import (
    InventoryTaskViewSet,
    InventoryScanViewSet,
    InventorySnapshotViewSet,
    InventoryDifferenceViewSet,
)

app_name = 'inventory'

router = DefaultRouter()
router.register(r'tasks', InventoryTaskViewSet, basename='inventory-task')
router.register(r'scans', InventoryScanViewSet, basename='inventory-scan')
router.register(r'snapshots', InventorySnapshotViewSet, basename='inventory-snapshot')
router.register(r'differences', InventoryDifferenceViewSet, basename='inventory-difference')

urlpatterns = [
    path('inventory/', include(router.urls)),
]
