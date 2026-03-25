"""
URL routes for SLA dashboard APIs.
"""

from django.urls import path

from apps.workflows.views.sla_dashboard import (
    SLADashboardView,
    SLAAlertConfigViewSet,
    SLATrendView,
)

app_name = 'sla'

urlpatterns = [
    path('dashboard', SLADashboardView.as_view(), name='dashboard'),
    path('alerts/config', SLAAlertConfigViewSet.as_view(), name='alert-config'),
    path('trends', SLATrendView.as_view(), name='trends'),
]
