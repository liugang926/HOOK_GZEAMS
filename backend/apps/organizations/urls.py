"""
URL configuration for Organizations app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.organizations.viewsets import (
    OrganizationViewSet,
    DepartmentViewSet,
    UserDepartmentViewSet,
)

router = DefaultRouter()
# Organization management
router.register(r'organizations', OrganizationViewSet, basename='organization')
# Department management (full CRUD + batch operations)
router.register(r'departments', DepartmentViewSet, basename='department')
# User-Department association management (full CRUD + batch operations)
router.register(r'user-departments', UserDepartmentViewSet, basename='user-department')

app_name = 'organizations'

urlpatterns = [
    path('', include(router.urls)),
]
