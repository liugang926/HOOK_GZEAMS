"""
ViewSets for Asset models.
"""
from .category import AssetCategoryViewSet
from .asset import (
    AssetViewSet,
    SupplierViewSet,
    LocationViewSet,
    AssetStatusLogViewSet,
)
from .operation import (
    AssetPickupViewSet,
    PickupItemViewSet,
    AssetTransferViewSet,
    TransferItemViewSet,
    AssetReturnViewSet,
    ReturnItemViewSet,
    AssetLoanViewSet,
    LoanItemViewSet,
)
from .tag import AssetTagViewSet, TagGroupViewSet

__all__ = [
    'AssetCategoryViewSet',
    'AssetViewSet',
    'SupplierViewSet',
    'LocationViewSet',
    'AssetStatusLogViewSet',
    'AssetPickupViewSet',
    'PickupItemViewSet',
    'AssetTransferViewSet',
    'TransferItemViewSet',
    'AssetReturnViewSet',
    'ReturnItemViewSet',
    'AssetLoanViewSet',
    'LoanItemViewSet',
    'TagGroupViewSet',
    'AssetTagViewSet',
]
