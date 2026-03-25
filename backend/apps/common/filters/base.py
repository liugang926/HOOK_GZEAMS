import django_filters


class BaseModelFilter(django_filters.FilterSet):
    """
    Base FilterSet for all models inheriting from BaseModel.

    Automatically provides filters for:
    - created_at: Date range filter
    - updated_at: Date range filter
    - created_by: UUID filter
    - is_deleted: Boolean filter

    Inherit this class and add your model-specific filters.
    """

    # Time range filters for created_at
    created_at_from = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created From'
    )
    created_at_to = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Created To'
    )

    # Time range filters for updated_at
    updated_at_from = django_filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='gte',
        label='Updated From'
    )
    updated_at_to = django_filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='lte',
        label='Updated To'
    )

    # User filter
    created_by = django_filters.UUIDFilter(
        field_name='created_by_id',
        label='Created By ID'
    )

    # Soft delete filter
    is_deleted = django_filters.BooleanFilter(
        field_name='is_deleted',
        label='Is Deleted'
    )

    class Meta:
        # Abstract base class - no model defined here
        abstract = True
        # Define fields list for child classes to extend
        fields = ['created_at_from', 'created_at_to', 'updated_at_from',
                  'updated_at_to', 'created_by', 'is_deleted']
