"""
ViewSets for Consumable Management.

All ViewSets inherit from BaseModelViewSetWithBatch for standard CRUD operations
and extend with custom actions for business workflows.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import BaseResponse
from apps.consumables.models import (
    ConsumableCategory,
    Consumable,
    ConsumableStock,
    ConsumablePurchase,
    PurchaseItem,
    ConsumableIssue,
    IssueItem,
)
from apps.consumables.serializers.base import (
    # Category serializers
    ConsumableCategoryListSerializer,
    ConsumableCategoryDetailSerializer,
    ConsumableCategoryCreateSerializer,
    ConsumableCategoryUpdateSerializer,
    # Consumable serializers
    ConsumableListSerializer,
    ConsumableDetailSerializer,
    ConsumableCreateSerializer,
    ConsumableUpdateSerializer,
    # Stock serializers
    ConsumableStockListSerializer,
    ConsumableStockSerializer,
    # Purchase serializers
    ConsumablePurchaseListSerializer,
    ConsumablePurchaseDetailSerializer,
    ConsumablePurchaseCreateSerializer,
    ConsumablePurchaseUpdateSerializer,
    PurchaseItemSerializer,
    PurchaseItemCreateSerializer,
    PurchaseApprovalSerializer,
    # Issue serializers
    ConsumableIssueListSerializer,
    ConsumableIssueDetailSerializer,
    ConsumableIssueCreateSerializer,
    ConsumableIssueUpdateSerializer,
    IssueItemSerializer,
    IssueItemCreateSerializer,
    IssueApprovalSerializer,
)
from apps.consumables.filters.consumable_filter import (
    ConsumableCategoryFilter,
    ConsumableFilter,
    ConsumableStockFilter,
    ConsumablePurchaseFilter,
    ConsumableIssueFilter,
)
from apps.consumables.services.consumable_service import (
    ConsumableCategoryService,
    ConsumableService,
    ConsumablePurchaseService,
    ConsumableIssueService,
)


# ========== Category ViewSet ==========

class ConsumableCategoryViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Consumable Category operations.

    Provides:
    - Standard CRUD operations
    - Tree structure operations
    - Batch operations
    """
    queryset = ConsumableCategory.objects.all()
    filterset_class = ConsumableCategoryFilter
    search_fields = ['code', 'name']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return ConsumableCategoryListSerializer
        elif self.action == 'create':
            return ConsumableCategoryCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ConsumableCategoryUpdateSerializer
        return ConsumableCategoryDetailSerializer

    def create(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return BaseResponse.created(
            data=serializer.data,
            message='Category created successfully'
        )

    def list(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """
        Get category tree structure.

        GET /api/consumables/categories/tree/
        """
        service = ConsumableCategoryService()
        tree = service.get_tree(organization_id=request.user.organization_id)
        return BaseResponse.success(data=tree)

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """
        Get direct children of a category.

        GET /api/consumables/categories/{id}/children/
        """
        try:
            service = ConsumableCategoryService()
            children = service.get_children(category_id=pk)
            serializer = ConsumableCategoryListSerializer(children, many=True)
            return BaseResponse.success(data=serializer.data)
        except Exception as e:
            return BaseResponse.error(
                code='INTERNAL_ERROR',
                message='Failed to get children',
                details=str(e)
            )

    @action(detail=True, methods=['get'])
    def consumables(self, request, pk=None):
        """
        Get consumables in this category.

        GET /api/consumables/categories/{id}/consumables/
        Query params: include_descendants=true
        """
        service = ConsumableCategoryService()
        include_descendants = request.query_params.get('include_descendants', 'false').lower() == 'true'
        consumables = service.get_consumables(
            category_id=pk,
            include_descendants=include_descendants
        )
        serializer = ConsumableListSerializer(consumables, many=True)
        return BaseResponse.success(data=serializer.data)


# ========== Consumable ViewSet ==========

class ConsumableViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Consumable operations.

    Provides:
    - Standard CRUD operations
    - Stock status queries
    - Stock adjustment
    - Low stock alerts
    """
    queryset = Consumable.objects.all()
    filterset_class = ConsumableFilter
    search_fields = ['code', 'name', 'specification', 'brand']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return ConsumableListSerializer
        elif self.action == 'create':
            return ConsumableCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ConsumableUpdateSerializer
        return ConsumableDetailSerializer

    def create(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return BaseResponse.created(
            data=serializer.data,
            message='Consumable created successfully'
        )

    def list(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """
        Get consumables with low stock.

        GET /api/consumables/low_stock/
        """
        service = ConsumableService()
        consumables = service.check_low_stock(
            organization_id=request.user.organization_id,
            category_id=request.query_params.get('category_id')
        )
        serializer = ConsumableListSerializer(consumables, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """
        Get consumables that are out of stock.

        GET /api/consumables/out_of_stock/
        """
        service = ConsumableService()
        consumables = service.check_out_of_stock(
            organization_id=request.user.organization_id
        )
        serializer = ConsumableListSerializer(consumables, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get stock summary statistics.

        GET /api/consumables/summary/
        """
        service = ConsumableService()
        summary = service.get_stock_summary(
            organization_id=request.user.organization_id,
            category_id=request.query_params.get('category_id')
        )
        return BaseResponse.success(data=summary)

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """
        Get stock transactions for a consumable.

        GET /api/consumables/{id}/transactions/
        """
        service = ConsumableService()
        transactions = service.get_stock_transactions(consumable_id=pk)
        serializer = ConsumableStockListSerializer(transactions, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=True, methods=['post'])
    def adjust_stock(self, request, pk=None):
        """
        Manually adjust consumable stock.

        POST /api/consumables/{id}/adjust_stock/
        Body: {
            "quantity": 10,
            "transaction_type": "inventory_add",
            "remark": "Optional remark"
        }
        """
        serializer = PurchaseApprovalSerializer(data=request.data)
        if serializer.is_valid():
            try:
                service = ConsumableService()
                transaction = service.adjust_stock(
                    consumable_id=pk,
                    quantity=serializer.validated_data.get('quantity', 0),
                    transaction_type=serializer.validated_data.get('transaction_type', 'adjustment'),
                    user=request.user,
                    source_type='manual_adjustment',
                    remark=serializer.validated_data.get('remark', '')
                )
                result_serializer = ConsumableStockSerializer(transaction)
                return BaseResponse.success(
                    message='Stock adjusted successfully',
                    data=result_serializer.data
                )
            except Exception as e:
                return BaseResponse.error(
                    code='VALIDATION_ERROR',
                    message='Invalid data',
                    details=str(e)
                )
        return BaseResponse.error(code='VALIDATION_ERROR', message='Invalid data', details=serializer.errors)


# ========== Stock ViewSet ==========

class ConsumableStockViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Stock Transaction operations.

    Provides:
    - Read-only access to stock transactions
    - Filtering by consumable, type, date
    """
    queryset = ConsumableStock.objects.all()
    serializer_class = ConsumableStockListSerializer
    filterset_class = ConsumableStockFilter
    search_fields = ['source_no', 'remark']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return ConsumableStockSerializer
        return ConsumableStockListSerializer

    def perform_create(self, serializer):
        """Disable direct creation - transactions are created by services"""
        return Response(
            {'detail': 'Cannot create transactions directly. Use purchase/issue operations.'},
            status=status.HTTP_403_FORBIDDEN
        )


# ========== Purchase ViewSet ==========

class ConsumablePurchaseViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Purchase Order operations.

    Provides:
    - Standard CRUD operations
    - Purchase workflow: submit -> approve -> receive -> complete
    - Custom actions for workflow transitions
    """
    queryset = ConsumablePurchase.objects.all()
    filterset_class = ConsumablePurchaseFilter
    search_fields = ['purchase_no', 'supplier__name', 'remark']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return ConsumablePurchaseListSerializer
        elif self.action == 'create':
            return ConsumablePurchaseCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ConsumablePurchaseUpdateSerializer
        return ConsumablePurchaseDetailSerializer

    def create(self, request, *args, **kwargs):
        """Create purchase order with items"""
        serializer = ConsumablePurchaseCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                service = ConsumablePurchaseService()
                purchase = service.create_with_items(
                    data=serializer.validated_data,
                    user=request.user
                )
                result_serializer = ConsumablePurchaseDetailSerializer(purchase)
                return BaseResponse.success(
                    message='Purchase order created successfully',
                    data=result_serializer.data
                )
            except Exception as e:
                return BaseResponse.error(
                    code='INTERNAL_ERROR',
                    message='Purchase order creation failed',
                    details=str(e)
                )
        return BaseResponse.error(code='VALIDATION_ERROR', message='Invalid data', details=serializer.errors)

    def list(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Submit purchase order for approval.

        POST /api/consumables/purchases/{id}/submit/
        """
        try:
            service = ConsumablePurchaseService()
            purchase = service.submit_for_approval(purchase_id=pk)
            serializer = ConsumablePurchaseDetailSerializer(purchase)
            return BaseResponse.success(
                message='Purchase order submitted for approval',
                data=serializer.data
            )
        except Exception as e:
            return BaseResponse.error(code='INTERNAL_ERROR', message='Submit failed', details=str(e))

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve or reject purchase order.

        POST /api/consumables/purchases/{id}/approve/
        Body: {"approval": "approved", "comment": "Optional comment"}
        """
        serializer = PurchaseApprovalSerializer(data=request.data)
        if serializer.is_valid():
            try:
                service = ConsumablePurchaseService()
                purchase = service.approve(
                    purchase_id=pk,
                    user=request.user,
                    approval=serializer.validated_data['approval'],
                    comment=serializer.validated_data.get('comment', '')
                )
                serializer = ConsumablePurchaseDetailSerializer(purchase)
                return BaseResponse.success(
                    message=f'Purchase order {serializer.validated_data["approval"]}',
                    data=serializer.data
                )
            except Exception as e:
                return BaseResponse.error(code='INTERNAL_ERROR', message='Approval failed', details=str(e))
        return BaseResponse.error(code='VALIDATION_ERROR', message='Invalid data', details=serializer.errors)

    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        """
        Receive purchase order - updates stock.

        POST /api/consumables/purchases/{id}/receive/
        """
        try:
            service = ConsumablePurchaseService()
            purchase = service.receive(purchase_id=pk, user=request.user)
            serializer = ConsumablePurchaseDetailSerializer(purchase)
            return BaseResponse.success(
                message='Purchase order received and stock updated',
                data=serializer.data
            )
        except Exception as e:
            return BaseResponse.error(code='INTERNAL_ERROR', message='Receive failed', details=str(e))

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark purchase order as completed.

        POST /api/consumables/purchases/{id}/complete/
        """
        try:
            service = ConsumablePurchaseService()
            purchase = service.complete(purchase_id=pk)
            serializer = ConsumablePurchaseDetailSerializer(purchase)
            return BaseResponse.success(
                message='Purchase order completed',
                data=serializer.data
            )
        except Exception as e:
            return BaseResponse.error(code='INTERNAL_ERROR', message='Complete failed', details=str(e))

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel purchase order.

        POST /api/consumables/purchases/{id}/cancel/
        Body: {"reason": "Optional reason"}
        """
        reason = request.data.get('reason', '')
        try:
            service = ConsumablePurchaseService()
            purchase = service.cancel(purchase_id=pk, reason=reason)
            serializer = ConsumablePurchaseDetailSerializer(purchase)
            return BaseResponse.success(
                message='Purchase order cancelled',
                data=serializer.data
            )
        except Exception as e:
            return BaseResponse.error(code='INTERNAL_ERROR', message='Cancel failed', details=str(e))


# ========== Issue ViewSet ==========

class ConsumableIssueViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Issue Order operations.

    Provides:
    - Standard CRUD operations
    - Issue workflow: submit -> approve -> issue -> complete
    - Custom actions for workflow transitions
    """
    queryset = ConsumableIssue.objects.all()
    filterset_class = ConsumableIssueFilter
    search_fields = ['issue_no', 'applicant__username', 'department__name', 'remark']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return ConsumableIssueListSerializer
        elif self.action == 'create':
            return ConsumableIssueCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ConsumableIssueUpdateSerializer
        return ConsumableIssueDetailSerializer

    def create(self, request, *args, **kwargs):
        """Create issue order with items"""
        serializer = ConsumableIssueCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                service = ConsumableIssueService()
                issue = service.create_with_items(
                    data=serializer.validated_data,
                    user=request.user
                )
                result_serializer = ConsumableIssueDetailSerializer(issue)
                return BaseResponse.success(
                    message='Issue order created successfully',
                    data=result_serializer.data
                )
            except Exception as e:
                return BaseResponse.error(
                    code='INTERNAL_ERROR',
                    message='Issue order creation failed',
                    details=str(e)
                )
        return BaseResponse.error(code='VALIDATION_ERROR', message='Invalid data', details=serializer.errors)

    def list(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Submit issue order for approval.

        POST /api/consumables/issues/{id}/submit/
        """
        try:
            service = ConsumableIssueService()
            issue = service.submit_for_approval(issue_id=pk)
            serializer = ConsumableIssueDetailSerializer(issue)
            return BaseResponse.success(
                message='Issue order submitted for approval',
                data=serializer.data
            )
        except Exception as e:
            return BaseResponse.error(code='INTERNAL_ERROR', message='Submit failed', details=str(e))

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve or reject issue order.

        POST /api/consumables/issues/{id}/approve/
        Body: {"approval": "approved", "comment": "Optional comment"}
        """
        serializer = IssueApprovalSerializer(data=request.data)
        if serializer.is_valid():
            try:
                service = ConsumableIssueService()
                issue = service.approve(
                    issue_id=pk,
                    user=request.user,
                    approval=serializer.validated_data['approval'],
                    comment=serializer.validated_data.get('comment', '')
                )
                serializer = ConsumableIssueDetailSerializer(issue)
                return BaseResponse.success(
                    message=f'Issue order {serializer.validated_data["approval"]}',
                    data=serializer.data
                )
            except Exception as e:
                return BaseResponse.error(code='INTERNAL_ERROR', message='Approval failed', details=str(e))
        return BaseResponse.error(code='VALIDATION_ERROR', message='Invalid data', details=serializer.errors)

    @action(detail=True, methods=['post'])
    def issue(self, request, pk=None):
        """
        Issue items - reduce stock.

        POST /api/consumables/issues/{id}/issue/
        """
        try:
            service = ConsumableIssueService()
            issue = service.issue(issue_id=pk, user=request.user)
            serializer = ConsumableIssueDetailSerializer(issue)
            return BaseResponse.success(
                message='Items issued successfully',
                data=serializer.data
            )
        except Exception as e:
            return BaseResponse.error(code='INTERNAL_ERROR', message='Issue failed', details=str(e))

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark issue order as completed.

        POST /api/consumables/issues/{id}/complete/
        """
        try:
            service = ConsumableIssueService()
            issue = service.complete(issue_id=pk)
            serializer = ConsumableIssueDetailSerializer(issue)
            return BaseResponse.success(
                message='Issue order completed',
                data=serializer.data
            )
        except Exception as e:
            return BaseResponse.error(code='INTERNAL_ERROR', message='Complete failed', details=str(e))

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel issue order.

        POST /api/consumables/issues/{id}/cancel/
        Body: {"reason": "Optional reason"}
        """
        reason = request.data.get('reason', '')
        try:
            service = ConsumableIssueService()
            issue = service.cancel(issue_id=pk, reason=reason)
            serializer = ConsumableIssueDetailSerializer(issue)
            return BaseResponse.success(
                message='Issue order cancelled',
                data=serializer.data
            )
        except Exception as e:
            return BaseResponse.error(code='INTERNAL_ERROR', message='Cancel failed', details=str(e))
