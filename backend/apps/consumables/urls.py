"""
URL Configuration for Consumable Management app.

Registers all ViewSets with router for REST API endpoints.
"""
from rest_framework import routers
from apps.consumables.viewsets import (
    ConsumableCategoryViewSet,
    ConsumableViewSet,
    ConsumableStockViewSet,
    ConsumablePurchaseViewSet,
    ConsumableIssueViewSet,
)

app_router = routers.DefaultRouter()

# Category endpoints
app_router.register(r'categories', ConsumableCategoryViewSet, basename='consumable-category')

# Consumable endpoints
app_router.register(r'consumables', ConsumableViewSet, basename='consumable')

# Stock transaction endpoints
app_router.register(r'stock', ConsumableStockViewSet, basename='consumable-stock')

# Purchase order endpoints
app_router.register(r'purchases', ConsumablePurchaseViewSet, basename='consumable-purchase')

# Issue order endpoints
app_router.register(r'issues', ConsumableIssueViewSet, basename='consumable-issue')

urlpatterns = app_router.urls
