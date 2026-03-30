"""
Services for Asset models.
"""
from .category_service import AssetCategoryService
from .asset_service import (
    SupplierService,
    LocationService,
    AssetStatusLogService,
    AssetService,
)
from .operation_service import (
    AssetPickupService,
    AssetTransferService,
    AssetReturnService,
    AssetLoanService,
)
from .tag_service import AssetTagRelationService, AssetTagService, TagGroupService

__all__ = [
    'AssetCategoryService',
    'SupplierService',
    'LocationService',
    'AssetStatusLogService',
    'AssetService',
    'AssetPickupService',
    'AssetTransferService',
    'AssetReturnService',
    'AssetLoanService',
    'TagGroupService',
    'AssetTagService',
    'AssetTagRelationService',
]
