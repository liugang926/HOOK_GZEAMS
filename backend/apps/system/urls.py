"""
URL configuration for the metadata-driven low-code engine.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.system.viewsets import (
    BusinessObjectViewSet,
    FieldDefinitionViewSet,
    PageLayoutViewSet,
    DynamicDataViewSet,
    DynamicSubTableDataViewSet,
    UserColumnPreferenceViewSet,
    TabConfigViewSet,
)

router = DefaultRouter()
router.register(r'business-objects', BusinessObjectViewSet, basename='business-object')
router.register(r'field-definitions', FieldDefinitionViewSet, basename='field-definition')
router.register(r'page-layouts', PageLayoutViewSet, basename='page-layout')
router.register(r'dynamic-data', DynamicDataViewSet, basename='dynamic-data')
router.register(r'sub-table-data', DynamicSubTableDataViewSet, basename='sub-table-data')
router.register(r'column-preferences', UserColumnPreferenceViewSet, basename='columnpreference')
router.register(r'tab-configs', TabConfigViewSet, basename='tabconfig')

app_name = 'system'

urlpatterns = [
    path('', include(router.urls)),
]
