"""
URL configuration for projects module.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import (
    AssetProjectViewSet,
    ProjectAssetViewSet,
    ProjectMemberViewSet,
)

app_name = 'projects'

router = DefaultRouter()
router.register(r'projects', AssetProjectViewSet, basename='asset-project')
router.register(r'allocations', ProjectAssetViewSet, basename='project-asset')
router.register(r'members', ProjectMemberViewSet, basename='project-member')

urlpatterns = [
    path('', include(router.urls)),
]
