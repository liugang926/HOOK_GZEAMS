"""
SSO ViewSets

All viewsets inherit from BaseModelViewSetWithBatch for automatic
organization filtering, soft delete, and batch operations.
"""
from apps.sso.views.wework_views import (
    WeWorkConfigViewSet,
    UserMappingViewSet,
)

__all__ = [
    'WeWorkConfigViewSet',
    'UserMappingViewSet',
]
