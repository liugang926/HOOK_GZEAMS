"""
Insurance management URL configuration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import (
    InsuranceCompanyViewSet,
    InsurancePolicyViewSet,
    InsuredAssetViewSet,
    PremiumPaymentViewSet,
    ClaimRecordViewSet,
    PolicyRenewalViewSet,
)

app_name = 'insurance'

router = DefaultRouter()
router.register(r'companies', InsuranceCompanyViewSet, basename='insurance-company')
router.register(r'policies', InsurancePolicyViewSet, basename='insurance-policy')
router.register(r'insured-assets', InsuredAssetViewSet, basename='insured-asset')
router.register(r'payments', PremiumPaymentViewSet, basename='premium-payment')
router.register(r'claims', ClaimRecordViewSet, basename='claim-record')
router.register(r'renewals', PolicyRenewalViewSet, basename='policy-renewal')

urlpatterns = [
    path('', include(router.urls)),
]
