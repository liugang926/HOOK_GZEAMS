"""
Asset Receipt Service

Business service for asset receipt operations including:
- CRUD operations via BaseCRUDService
- Quality inspection workflow
- Asset card generation (stub)
"""
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q
from apps.common.services.base_crud import BaseCRUDService
from apps.lifecycle.models import (
    AssetReceipt,
    AssetReceiptItem,
    AssetReceiptStatus,
)


class AssetReceiptService(BaseCRUDService):
    """
    Service for Asset Receipt operations.

    Extends BaseCRUDService with receipt workflow methods.
    """

    def __init__(self):
        super().__init__(AssetReceipt)

    def create_with_items(self, data: dict, user):
        """
        Create asset receipt with items.

        Args:
            data: Dictionary containing receipt data and items
            user: Current user creating the receipt

        Returns:
            Created AssetReceipt instance
        """
        items_data = data.pop('items', [])

        # Set receiver from user
        data['receiver'] = user
        data['organization_id'] = user.organization_id

        asset_receipt = AssetReceipt.objects.create(**data)

        # Create items
        for idx, item_data in enumerate(items_data, start=1):
            item_data['sequence'] = idx
            item_data['organization_id'] = user.organization_id
            AssetReceiptItem.objects.create(
                asset_receipt=asset_receipt,
                **item_data
            )

        return asset_receipt

    def submit_for_inspection(self, receipt_id: str):
        """
        Submit asset receipt for inspection.

        Args:
            receipt_id: Asset receipt ID

        Returns:
            Updated AssetReceipt instance

        Raises:
            ValidationError: If receipt is not in draft status
        """
        receipt = self.get(receipt_id)

        if receipt.status != AssetReceiptStatus.DRAFT:
            raise ValidationError({
                'status': f'Cannot submit receipt with status {receipt.get_status_display()}'
            })

        receipt.status = AssetReceiptStatus.INSPECTING
        receipt.save()

        return receipt

    def record_inspection_result(self, receipt_id: str, inspector, result: str, passed: bool = True):
        """
        Record inspection result for asset receipt.

        Args:
            receipt_id: Asset receipt ID
            inspector: User performing inspection
            result: Inspection result description
            passed: True if inspection passed, False if rejected

        Returns:
            Updated AssetReceipt instance

        Raises:
            ValidationError: If receipt is not in inspecting status
        """
        receipt = self.get(receipt_id)

        if receipt.status != AssetReceiptStatus.INSPECTING:
            raise ValidationError({
                'status': f'Cannot record inspection for receipt with status {receipt.get_status_display()}'
            })

        receipt.inspector = inspector
        receipt.inspection_result = result

        if passed:
            receipt.status = AssetReceiptStatus.PASSED
            receipt.passed_at = timezone.now()
        else:
            receipt.status = AssetReceiptStatus.REJECTED

        receipt.save()

        return receipt

    def cancel(self, receipt_id: str, reason: str = None):
        """
        Cancel asset receipt.

        Args:
            receipt_id: Asset receipt ID
            reason: Cancellation reason

        Returns:
            Updated AssetReceipt instance
        """
        receipt = self.get(receipt_id)

        if receipt.status in [AssetReceiptStatus.PASSED, AssetReceiptStatus.CANCELLED]:
            raise ValidationError({
                'status': f'Cannot cancel receipt with status {receipt.get_status_display()}'
            })

        receipt.status = AssetReceiptStatus.CANCELLED
        receipt.save()

        return receipt

    def generate_asset_cards(self, receipt_id: str):
        """
        Generate asset cards from passed receipt items.

        STUB IMPLEMENTATION: Marks items as having generated assets.

        Args:
            receipt_id: Asset receipt ID

        Returns:
            Updated AssetReceipt instance

        Raises:
            ValidationError: If receipt is not passed
        """
        receipt = self.get(receipt_id)

        if receipt.status != AssetReceiptStatus.PASSED:
            raise ValidationError({
                'status': 'Can only generate asset cards from passed receipts'
            })

        # STUB: Mark items as having generated assets
        # In production, this would create Asset records
        for item in receipt.items.all():
            if not item.asset_generated and item.qualified_quantity > 0:
                # Here you would create Asset records
                # For now, just mark as generated
                item.asset_generated = True
                item.save()

        return receipt

    def get_by_status(self, status: str, organization_id: str = None):
        """
        Get asset receipts by status.

        Args:
            status: Status to filter by
            organization_id: Filter by organization

        Returns:
            QuerySet of asset receipts with given status
        """
        queryset = AssetReceipt.objects.filter(
            status=status,
            is_deleted=False
        )

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        return queryset.order_by('-created_at')

    def get_pending_inspection(self, organization_id: str = None):
        """
        Get all receipts pending inspection.

        Args:
            organization_id: Filter by organization

        Returns:
            QuerySet of receipts awaiting inspection
        """
        return self.get_by_status(AssetReceiptStatus.INSPECTING, organization_id)

    def get_passed_receipts(self, organization_id: str = None):
        """
        Get all passed receipts ready for asset generation.

        Args:
            organization_id: Filter by organization

        Returns:
            QuerySet of passed receipts
        """
        return self.get_by_status(AssetReceiptStatus.PASSED, organization_id)

    def calculate_total_amount(self, receipt_id: str):
        """
        Calculate total amount from receipt items.

        Args:
            receipt_id: Asset receipt ID

        Returns:
            Total amount as Decimal
        """
        receipt = self.get(receipt_id)
        return sum(item.total_amount for item in receipt.items.all())

    def get_receipt_items_summary(self, receipt_id: str):
        """
        Get summary of receipt items.

        Args:
            receipt_id: Asset receipt ID

        Returns:
            Dictionary with items summary
        """
        receipt = self.get(receipt_id)
        items = receipt.items.all()

        return {
            'total_items': items.count(),
            'total_ordered': sum(item.ordered_quantity for item in items),
            'total_received': sum(item.received_quantity for item in items),
            'total_qualified': sum(item.qualified_quantity for item in items),
            'total_defective': sum(item.defective_quantity for item in items),
            'total_amount': sum(item.total_amount for item in items),
            'assets_generated': sum(1 for item in items if item.asset_generated),
        }
