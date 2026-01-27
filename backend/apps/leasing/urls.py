"""
Leasing management URL configuration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import (
    LeaseContractViewSet, LeaseItemViewSet,
    RentPaymentViewSet, LeaseReturnViewSet, LeaseExtensionViewSet
)

app_name = 'leasing'

router = DefaultRouter()
router.register(r'lease-contracts', LeaseContractViewSet, basename='lease-contract')
router.register(r'lease-items', LeaseItemViewSet, basename='lease-item')
router.register(r'rent-payments', RentPaymentViewSet, basename='rent-payment')
router.register(r'lease-returns', LeaseReturnViewSet, basename='lease-return')
router.register(r'lease-extensions', LeaseExtensionViewSet, basename='lease-extension')

urlpatterns = [
    path('', include(router.urls)),
]
