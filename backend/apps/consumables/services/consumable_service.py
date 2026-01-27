"""
Business Services for Consumable Management.

All services inherit from BaseCRUDService for standard CRUD operations
and extend with business-specific methods for:
- Category hierarchy management
- Stock transaction recording
- Purchase order workflow
- Issue order workflow
"""
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q, Sum, F
from apps.common.services.base_crud import BaseCRUDService
from apps.consumables.models import (
    ConsumableCategory,
    Consumable,
    ConsumableStock,
    ConsumablePurchase,
    PurchaseItem,
    ConsumableIssue,
    IssueItem,
    ConsumableIssue,
    IssueItem,
    TransactionType,
)


# ========== Category Service ==========

class ConsumableCategoryService(BaseCRUDService):
    """
    Service for Consumable Category operations.

    Extends BaseCRUDService with category-specific methods.
    """

    def __init__(self):
        super().__init__(ConsumableCategory)

    def get_tree(self, organization_id: str = None):
        """
        Get category tree structure.

        Args:
            organization_id: Filter by organization

        Returns:
            List of root categories with nested children
        """
        queryset = self.model_class.objects.filter(is_deleted=False)
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        roots = queryset.filter(parent__isnull=True).order_by('path')
        return [self._build_tree_node(category) for category in roots]

    def _build_tree_node(self, category):
        """Recursively build tree node with children."""
        node = {
            'id': str(category.id),
            'code': category.code,
            'name': category.name,
            'level': category.level,
            'path': category.path,
            'is_active': category.is_active,
            'enable_alert': category.enable_alert,
            'min_stock': category.min_stock,
            'max_stock': category.max_stock,
            'reorder_point': category.reorder_point,
            'unit': category.unit,
            'children': []
        }

        children = category.children.filter(is_deleted=False).order_by('path')
        for child in children:
            node['children'].append(self._build_tree_node(child))

        return node

    def get_children(self, category_id: str):
        """Get direct children of a category."""
        try:
            category = self.model_class.objects.get(id=category_id)
            return list(category.children.filter(is_deleted=False))
        except ConsumableCategory.DoesNotExist:
            return []

    def get_consumables(self, category_id: str, include_descendants: bool = False):
        """
        Get consumables in a category.

        Args:
            category_id: Category ID
            include_descendants: Include consumables from descendant categories

        Returns:
            QuerySet of consumables
        """
        queryset = Consumable.objects.filter(is_deleted=False)

        if include_descendants:
            category_ids = [category_id]
            try:
                category = ConsumableCategory.objects.get(id=category_id)
                # Get all descendant IDs
                category_ids.extend(self._get_all_descendant_ids(category))
            except ConsumableCategory.DoesNotExist:
                pass
            queryset = queryset.filter(category_id__in=category_ids)
        else:
            queryset = queryset.filter(category_id=category_id)

        return queryset

    def _get_all_descendant_ids(self, category):
        """Recursively get all descendant category IDs."""
        ids = []
        for child in category.children.filter(is_deleted=False):
            ids.append(str(child.id))
            ids.extend(self._get_all_descendant_ids(child))
        return ids


# ========== Consumable Service ==========

class ConsumableService(BaseCRUDService):
    """
    Service for Consumable operations.

    Extends BaseCRUDService with stock management methods.
    """

    def __init__(self):
        super().__init__(Consumable)

    def check_low_stock(self, organization_id: str = None, category_id: str = None):
        """
        Check for consumables with low stock.

        Args:
            organization_id: Filter by organization
            category_id: Filter by category

        Returns:
            QuerySet of consumables at or below reorder point
        """
        queryset = Consumable.objects.filter(
            is_deleted=False,
            available_stock__lte=F('reorder_point')
        )

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return queryset.order_by('available_stock')

    def check_out_of_stock(self, organization_id: str = None):
        """
        Check for consumables that are out of stock.

        Args:
            organization_id: Filter by organization

        Returns:
            QuerySet of consumables with zero available stock
        """
        queryset = Consumable.objects.filter(
            is_deleted=False,
            available_stock=0
        )

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        return queryset

    def get_stock_transactions(self, consumable_id: str):
        """Get stock transactions for a consumable."""
        return ConsumableStock.objects.filter(
            consumable_id=consumable_id,
            is_deleted=False
        ).order_by('-created_at')

    def adjust_stock(self, consumable_id: str, quantity: int,
                    transaction_type: str, user=None,
                    source_type='', source_id='', source_no='', remark=''):
        """
        Manually adjust consumable stock.

        Args:
            consumable_id: Consumable ID
            quantity: Quantity change (positive or negative)
            transaction_type: Type of transaction
            user: User performing the adjustment
            source_type: Source type
            source_id: Source ID
            source_no: Source number
            remark: Remarks

        Returns:
            Created stock transaction
        """
        try:
            consumable = Consumable.objects.get(id=consumable_id)
        except Consumable.DoesNotExist:
            raise ValidationError({'consumable_id': 'Consumable not found'})

        # Validate stock won't go negative
        if consumable.available_stock + quantity < 0:
            raise ValidationError({
                'quantity': 'Insufficient stock for this operation'
            })

        # Create transaction and update stock
        transaction = ConsumableStock.create_transaction(
            consumable=consumable,
            transaction_type=transaction_type,
            quantity=quantity,
            source_type=source_type,
            source_id=source_id,
            source_no=source_no,
            handler=user,
            remark=remark
        )

        return transaction

    def get_by_code(self, code: str, organization_id: str = None):
        """Get consumable by code."""
        queryset = self.model_class.objects.filter(code=code, is_deleted=False)
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        return queryset.first()

    def get_stock_summary(self, organization_id: str = None, category_id: str = None):
        """
        Get stock summary statistics.

        Args:
            organization_id: Filter by organization
            category_id: Filter by category

        Returns:
            Dictionary with stock statistics
        """
        queryset = Consumable.objects.filter(is_deleted=False)

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        total_consumables = queryset.count()
        low_stock_count = queryset.filter(
            available_stock__lte=F('reorder_point')
        ).count()
        out_of_stock_count = queryset.filter(available_stock=0).count()

        # Calculate total value
        total_value = queryset.aggregate(
            total=Sum(F('current_stock') * F('average_price'))
        )['total'] or 0

        return {
            'total_consumables': total_consumables,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'total_value': float(total_value),
        }


# ========== Purchase Service ==========

class ConsumablePurchaseService(BaseCRUDService):
    """
    Service for Purchase Order operations.

    Extends BaseCRUDService with purchase workflow methods.
    """

    def __init__(self):
        super().__init__(ConsumablePurchase)

    def create_with_items(self, data: dict, user):
        """
        Create purchase order with items.

        Args:
            data: Dictionary with purchase_date, supplier_id, items, remark
            user: User creating the purchase

        Returns:
            Created purchase order
        """
        items_data = data.pop('items', [])

        # Set organization from user
        data['organization_id'] = user.organization_id
        data['created_by'] = user

        purchase = ConsumablePurchase.objects.create(**data)

        # Create items - copy item_data to avoid mutating input
        total_amount = 0
        for item_data in items_data:
            # Create a copy to avoid mutating the original dict
            item_kwargs = {
                'purchase': purchase,
                'organization_id': user.organization_id,
                'created_by': user,
                'consumable_id': item_data['consumable_id'],
                'quantity': item_data['quantity'],
                'unit_price': item_data['unit_price'],
                'remark': item_data.get('remark', '')
            }

            amount = item_kwargs['quantity'] * item_kwargs['unit_price']
            item_kwargs['amount'] = amount
            total_amount += amount

            PurchaseItem.objects.create(**item_kwargs)

        purchase.total_amount = total_amount
        purchase.save()

        return purchase

    def submit_for_approval(self, purchase_id: str):
        """
        Submit purchase order for approval.

        Args:
            purchase_id: Purchase order ID

        Returns:
            Updated purchase order
        """
        purchase = self.get(purchase_id)

        if purchase.status not in ['draft']:
            raise ValidationError({
                'status': f'Cannot submit purchase with status {purchase.get_status_label()}'
            })

        purchase.status = 'pending'
        purchase.save()

        return purchase

    def approve(self, purchase_id: str, user, approval: str, comment: str = ''):
        """
        Approve or reject a purchase order.

        Args:
            purchase_id: Purchase order ID
            user: User approving
            approval: 'approved' or 'rejected'
            comment: Approval comment

        Returns:
            Updated purchase order
        """
        purchase = self.get(purchase_id)

        if purchase.status != 'pending':
            raise ValidationError({
                'status': f'Cannot approve purchase with status {purchase.get_status_label()}'
            })

        purchase.approved_by = user
        purchase.approved_at = timezone.now()
        purchase.approval_comment = comment

        if approval == 'approved':
            purchase.status = 'approved'
        else:
            purchase.status = 'cancelled'

        purchase.save()
        return purchase

    def receive(self, purchase_id: str, user):
        """
        Receive purchase order - updates stock.

        Args:
            purchase_id: Purchase order ID
            user: User receiving goods

        Returns:
            Updated purchase order
        """
        purchase = self.get(purchase_id)

        if purchase.status not in ['approved']:
            raise ValidationError({
                'status': f'Cannot receive purchase with status {purchase.get_status_label()}'
            })

        # Process each item
        for item in purchase.items.all():
            # Create stock transaction
            ConsumableStock.create_transaction(
                consumable=item.consumable,
                transaction_type=TransactionType.PURCHASE,
                quantity=item.quantity,
                source_type='purchase',
                source_id=str(purchase.id),
                source_no=purchase.purchase_no,
                handler=user,
                remark=f'Purchase receipt - {purchase.supplier.name if purchase.supplier else "Unknown"}'
            )

            # Update consumable purchase price
            item.consumable.purchase_price = item.unit_price
            item.consumable.save()

        purchase.status = 'received'
        purchase.received_by = user
        purchase.received_at = timezone.now()
        purchase.save()

        return purchase

    def complete(self, purchase_id: str):
        """
        Mark purchase order as completed.

        Args:
            purchase_id: Purchase order ID

        Returns:
            Updated purchase order
        """
        purchase = self.get(purchase_id)

        if purchase.status != 'received':
            raise ValidationError({
                'status': f'Cannot complete purchase with status {purchase.get_status_label()}'
            })

        purchase.status = 'completed'
        purchase.save()

        return purchase

    def cancel(self, purchase_id: str, reason: str = ''):
        """
        Cancel a purchase order.

        Args:
            purchase_id: Purchase order ID
            reason: Cancellation reason

        Returns:
            Updated purchase order
        """
        purchase = self.get(purchase_id)

        if purchase.status in ['completed', 'received']:
            raise ValidationError({
                'status': f'Cannot cancel purchase with status {purchase.get_status_label()}'
            })

        purchase.status = 'cancelled'
        if reason:
            purchase.remark = f"{purchase.remark}\n\nCancelled: {reason}".strip()
        purchase.save()

        return purchase

    def get_by_purchase_no(self, purchase_no: str):
        """Get purchase order by number."""
        return self.model_class.objects.filter(
            purchase_no=purchase_no,
            is_deleted=False
        ).first()


# ========== Issue Service ==========

class ConsumableIssueService(BaseCRUDService):
    """
    Service for Issue Order operations.

    Extends BaseCRUDService with issue workflow methods.
    """

    def __init__(self):
        super().__init__(ConsumableIssue)

    def create_with_items(self, data: dict, user):
        """
        Create issue order with items.

        Args:
            data: Dictionary with issue_date, applicant_id, department_id, issue_reason, items, remark
            user: User creating the issue

        Returns:
            Created issue order
        """
        items_data = data.pop('items', [])

        # Set organization from user
        data['organization_id'] = user.organization_id
        data['created_by'] = user

        issue = ConsumableIssue.objects.create(**data)

        # Create items with stock snapshot
        for item_data in items_data:
            consumable_id = item_data['consumable_id']
            try:
                consumable = Consumable.objects.get(id=consumable_id)
            except Consumable.DoesNotExist:
                raise ValidationError({
                    'items': f'Consumable {consumable_id} not found'
                })

            # Validate stock availability
            if consumable.available_stock < item_data['quantity']:
                raise ValidationError({
                    'items': f'Insufficient stock for {consumable.name}. Available: {consumable.available_stock}, Requested: {item_data["quantity"]}'
                })

            # Lock stock
            consumable.locked_stock += item_data['quantity']
            consumable.available_stock -= item_data['quantity']
            consumable.save()

            item_data['issue'] = issue
            item_data['organization_id'] = user.organization_id
            item_data['snapshot_before_stock'] = consumable.current_stock

            IssueItem.objects.create(**item_data)

        return issue

    def submit_for_approval(self, issue_id: str):
        """
        Submit issue order for approval.

        Args:
            issue_id: Issue order ID

        Returns:
            Updated issue order
        """
        issue = self.get(issue_id)

        if issue.status not in ['draft']:
            raise ValidationError({
                'status': f'Cannot submit issue with status {issue.get_status_label()}'
            })

        issue.status = 'pending'
        issue.save()

        return issue

    def approve(self, issue_id: str, user, approval: str, comment: str = ''):
        """
        Approve or reject an issue order.

        Args:
            issue_id: Issue order ID
            user: User approving
            approval: 'approved' or 'rejected'
            comment: Approval comment

        Returns:
            Updated issue order
        """
        issue = self.get(issue_id)

        if issue.status != 'pending':
            raise ValidationError({
                'status': f'Cannot approve issue with status {issue.get_status_label()}'
            })

        issue.approved_by = user
        issue.approved_at = timezone.now()
        issue.approval_comment = comment

        if approval == 'approved':
            issue.status = 'approved'
        else:
            issue.status = 'rejected'
            # Release locked stock
            self._release_locked_stock(issue)

        issue.save()
        return issue

    def _release_locked_stock(self, issue: ConsumableIssue):
        """Release locked stock when issue is rejected or cancelled."""
        for item in issue.items.all():
            consumable = item.consumable
            consumable.locked_stock -= item.quantity
            consumable.available_stock += item.quantity
            consumable.save()

    def issue(self, issue_id: str, user):
        """
        Issue items - reduce stock.

        Args:
            issue_id: Issue order ID
            user: User issuing items

        Returns:
            Updated issue order
        """
        issue = self.get(issue_id)

        if issue.status != 'approved':
            raise ValidationError({
                'status': f'Cannot issue items with status {issue.get_status_label()}'
            })

        # Process each item
        for item in issue.items.all():
            consumable = item.consumable

            # Create stock transaction (negative quantity)
            ConsumableStock.create_transaction(
                consumable=consumable,
                transaction_type=TransactionType.ISSUE,
                quantity=-item.quantity,
                source_type='issue',
                source_id=str(issue.id),
                source_no=issue.issue_no,
                handler=user,
                remark=f'Issued to {issue.applicant.username} - {issue.department.name if issue.department else "Unknown"}'
            )

            # Release locked stock (already reduced available_stock when created)
            consumable.locked_stock -= item.quantity
            consumable.save()

        issue.status = 'issued'
        issue.issued_by = user
        issue.issued_at = timezone.now()
        issue.save()

        return issue

    def complete(self, issue_id: str):
        """
        Mark issue order as completed.

        Args:
            issue_id: Issue order ID

        Returns:
            Updated issue order
        """
        issue = self.get(issue_id)

        if issue.status != 'issued':
            raise ValidationError({
                'status': f'Cannot complete issue with status {issue.get_status_label()}'
            })

        issue.status = 'completed'
        issue.save()

        return issue

    def cancel(self, issue_id: str, reason: str = ''):
        """
        Cancel an issue order.

        Args:
            issue_id: Issue order ID
            reason: Cancellation reason

        Returns:
            Updated issue order
        """
        issue = self.get(issue_id)

        if issue.status in ['issued', 'completed']:
            raise ValidationError({
                'status': f'Cannot cancel issue with status {issue.get_status_label()}'
            })

        issue.status = 'rejected'
        if reason:
            issue.remark = f"{issue.remark}\n\nCancelled: {reason}".strip()

        # Release locked stock
        self._release_locked_stock(issue)
        issue.save()

        return issue

    def get_by_issue_no(self, issue_no: str):
        """Get issue order by number."""
        return self.model_class.objects.filter(
            issue_no=issue_no,
            is_deleted=False
        ).first()
