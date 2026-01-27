"""
SSO Services

All services inherit from BaseCRUDService for automatic
CRUD methods and consistent behavior.
"""
from apps.sso.services.sso_service import (
    SSOService,
    WeWorkConfigService,
    UserMappingService,
    WeWorkSSOService,
)

__all__ = [
    'SSOService',
    'WeWorkConfigService',
    'UserMappingService',
    'WeWorkSSOService',
]
