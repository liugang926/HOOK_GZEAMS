"""
Filters for Asset Operation Models (Pickup, Transfer, Return, Loan).

All filters inherit from BaseModelFilter for common field filtering.
"""
import django_filters
from django.db.models import Q
from apps.common.filters.base import BaseModelFilter
from apps.assets.models import (
    AssetPickup,
    AssetTransfer,
    AssetReturn,
    AssetLoan,
)


# Status choices for filtering (correspond to Dictionary entries)
PICKUP_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

TRANSFER_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('pending', 'Pending Approval'),
    ('out_approved', 'Out Department Approved'),
    ('approved', 'Both Approved'),
    ('rejected', 'Rejected'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

RETURN_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

LOAN_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('borrowed', 'Borrowed'),
    ('returned', 'Returned'),
    ('overdue', 'Overdue'),
    ('cancelled', 'Cancelled'),
]


# ========== Pickup Order Filter ==========

class AssetPickupFilter(BaseModelFilter):
    """Filter for Asset Pickup Order list endpoint"""

    pickup_no = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text='Filter by pickup order number'
    )
    status = django_filters.ChoiceFilter(
        choices=PICKUP_STATUS_CHOICES,
        help_text='Filter by status'
    )
    applicant = django_filters.UUIDFilter(
        field_name='applicant_id',
        help_text='Filter by applicant ID'
    )
    department = django_filters.UUIDFilter(
        field_name='department_id',
        help_text='Filter by department ID'
    )
    pickup_date_from = django_filters.DateFilter(
        field_name='pickup_date',
        lookup_expr='gte',
        help_text='Filter by pickup date (from)'
    )
    pickup_date_to = django_filters.DateFilter(
        field_name='pickup_date',
        lookup_expr='lte',
        help_text='Filter by pickup date (to)'
    )

    # Search across multiple fields
    search = django_filters.CharFilter(
        method='filter_search',
        help_text='Search by pickup number, applicant name, or reason'
    )

    def filter_search(self, queryset, name, value):
        """Search across pickup_no, applicant__username, and pickup_reason"""
        return queryset.filter(
            Q(pickup_no__icontains=value) |
            Q(applicant__username__icontains=value) |
            Q(applicant__email__icontains=value) |
            Q(pickup_reason__icontains=value)
        )

    class Meta:
        model = AssetPickup
        fields = [
            'pickup_no', 'status', 'applicant', 'department',
            'pickup_date_from', 'pickup_date_to', 'search'
        ]


# ========== Transfer Order Filter ==========

class AssetTransferFilter(BaseModelFilter):
    """Filter for Asset Transfer Order list endpoint"""

    transfer_no = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text='Filter by transfer order number'
    )
    status = django_filters.ChoiceFilter(
        choices=TRANSFER_STATUS_CHOICES,
        help_text='Filter by status'
    )
    from_department = django_filters.UUIDFilter(
        field_name='from_department_id',
        help_text='Filter by source department ID'
    )
    to_department = django_filters.UUIDFilter(
        field_name='to_department_id',
        help_text='Filter by target department ID'
    )
    transfer_date_from = django_filters.DateFilter(
        field_name='transfer_date',
        lookup_expr='gte',
        help_text='Filter by transfer date (from)'
    )
    transfer_date_to = django_filters.DateFilter(
        field_name='transfer_date',
        lookup_expr='lte',
        help_text='Filter by transfer date (to)'
    )

    # Search across multiple fields
    search = django_filters.CharFilter(
        method='filter_search',
        help_text='Search by transfer number or reason'
    )

    def filter_search(self, queryset, name, value):
        """Search across transfer_no and transfer_reason"""
        return queryset.filter(
            Q(transfer_no__icontains=value) |
            Q(transfer_reason__icontains=value)
        )

    class Meta:
        model = AssetTransfer
        fields = [
            'transfer_no', 'status', 'from_department', 'to_department',
            'transfer_date_from', 'transfer_date_to', 'search'
        ]


# ========== Return Order Filter ==========

class AssetReturnFilter(BaseModelFilter):
    """Filter for Asset Return Order list endpoint"""

    return_no = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text='Filter by return order number'
    )
    status = django_filters.ChoiceFilter(
        choices=RETURN_STATUS_CHOICES,
        help_text='Filter by status'
    )
    returner = django_filters.UUIDFilter(
        field_name='returner_id',
        help_text='Filter by returner ID'
    )
    return_location = django_filters.UUIDFilter(
        field_name='return_location_id',
        help_text='Filter by return location ID'
    )
    return_date_from = django_filters.DateFilter(
        field_name='return_date',
        lookup_expr='gte',
        help_text='Filter by return date (from)'
    )
    return_date_to = django_filters.DateFilter(
        field_name='return_date',
        lookup_expr='lte',
        help_text='Filter by return date (to)'
    )

    # Search across multiple fields
    search = django_filters.CharFilter(
        method='filter_search',
        help_text='Search by return number, returner name, or reason'
    )

    def filter_search(self, queryset, name, value):
        """Search across return_no, returner__username, and return_reason"""
        return queryset.filter(
            Q(return_no__icontains=value) |
            Q(returner__username__icontains=value) |
            Q(returner__email__icontains=value) |
            Q(return_reason__icontains=value)
        )

    class Meta:
        model = AssetReturn
        fields = [
            'return_no', 'status', 'returner', 'return_location',
            'return_date_from', 'return_date_to', 'search'
        ]


# ========== Loan Order Filter ==========

class AssetLoanFilter(BaseModelFilter):
    """Filter for Asset Loan Order list endpoint"""

    loan_no = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text='Filter by loan order number'
    )
    status = django_filters.ChoiceFilter(
        choices=LOAN_STATUS_CHOICES,
        help_text='Filter by status'
    )
    borrower = django_filters.UUIDFilter(
        field_name='borrower_id',
        help_text='Filter by borrower ID'
    )
    borrow_date_from = django_filters.DateFilter(
        field_name='borrow_date',
        lookup_expr='gte',
        help_text='Filter by borrow date (from)'
    )
    borrow_date_to = django_filters.DateFilter(
        field_name='borrow_date',
        lookup_expr='lte',
        help_text='Filter by borrow date (to)'
    )
    expected_return_date_from = django_filters.DateFilter(
        field_name='expected_return_date',
        lookup_expr='gte',
        help_text='Filter by expected return date (from)'
    )
    expected_return_date_to = django_filters.DateFilter(
        field_name='expected_return_date',
        lookup_expr='lte',
        help_text='Filter by expected return date (to)'
    )
    is_overdue = django_filters.BooleanFilter(
        method='filter_is_overdue',
        help_text='Filter for overdue loans only'
    )

    # Search across multiple fields
    search = django_filters.CharFilter(
        method='filter_search',
        help_text='Search by loan number, borrower name, or reason'
    )

    def filter_search(self, queryset, name, value):
        """Search across loan_no, borrower__username, and loan_reason"""
        return queryset.filter(
            Q(loan_no__icontains=value) |
            Q(borrower__username__icontains=value) |
            Q(borrower__email__icontains=value) |
            Q(loan_reason__icontains=value)
        )

    def filter_is_overdue(self, queryset, name, value):
        """Filter for overdue loans"""
        if value:
            from django.utils import timezone
            return queryset.filter(
                status='borrowed',
                expected_return_date__lt=timezone.now().date()
            )
        return queryset

    class Meta:
        model = AssetLoan
        fields = [
            'loan_no', 'status', 'borrower',
            'borrow_date_from', 'borrow_date_to',
            'expected_return_date_from', 'expected_return_date_to',
            'is_overdue', 'search'
        ]
