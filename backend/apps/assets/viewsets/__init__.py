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
    AssetTransferViewSet,
    AssetReturnViewSet,
    AssetLoanViewSet,
)

__all__ = [
    'AssetCategoryViewSet',
    'AssetViewSet',
    'SupplierViewSet',
    'LocationViewSet',
    'AssetStatusLogViewSet',
    'AssetPickupViewSet',
    'AssetTransferViewSet',
    'AssetReturnViewSet',
    'AssetLoanViewSet',
]
