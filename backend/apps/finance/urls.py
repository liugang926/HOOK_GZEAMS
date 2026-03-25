"""
Finance Module URL Configuration

Routes for financial vouchers, voucher entries, and voucher templates.
"""
from rest_framework import routers
from apps.finance.viewsets import (
    FinanceVoucherViewSet,
    VoucherEntryViewSet,
    VoucherTemplateViewSet,
)

app_router = routers.DefaultRouter()

# Finance voucher endpoints
app_router.register(r'vouchers', FinanceVoucherViewSet, basename='finance-voucher')

# Voucher entry endpoints
app_router.register(r'entries', VoucherEntryViewSet, basename='voucher-entry')

# Voucher template endpoints
app_router.register(r'templates', VoucherTemplateViewSet, basename='voucher-template')

urlpatterns = app_router.urls
