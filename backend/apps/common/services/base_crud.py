from typing import Dict, List, Optional, Any, Type
from django.db import models
from django.core.paginator import Paginator
from django.db.models import Q, QuerySet
from apps.common.models import BaseModel


class BaseCRUDService:
    """
    Base service providing standard CRUD operations for BaseModel-derived models.

    Automatically handles:
    - Organization isolation in all operations
    - Soft delete instead of hard delete
    - Audit field management (created_by, updated_by)
    - Complex queries with filters, search, and ordering
    - Pagination support
    - Batch operations

    Usage:
        class AssetService(BaseCRUDService):
            def __init__(self):
                super().__init__(Asset)

            def get_by_code(self, code: str):
                return self.query(filters={'code__exact': code}).first()
    """

    def __init__(self, model_class: Type[BaseModel]):
        """
        Initialize service with a model class.

        Args:
            model_class: Django model class inheriting from BaseModel
        """
        if not issubclass(model_class, BaseModel):
            raise TypeError(f"{model_class.__name__} must inherit from BaseModel")
        self.model_class = model_class

    def create(self, data: Dict, user, **kwargs) -> BaseModel:
        """
        Create a new record with automatic organization and created_by setting.

        Args:
            data: Dictionary of field values
            user: User instance creating the record
            **kwargs: Additional parameters (e.g., organization_id)

        Returns:
            Created model instance
        """
        # Auto-set created_by if user provided
        if user and 'created_by_id' not in data and 'created_by' not in data:
            data['created_by_id'] = user.id

        # Auto-set organization_id from thread-local context if not provided
        if 'organization_id' not in data and 'organization' not in data:
            from apps.common.middleware import get_current_organization
            org_id = get_current_organization()
            if org_id:
                data['organization_id'] = org_id

        return self.model_class.objects.create(**data)

    def update(self, instance_id: str, data: Dict, user=None) -> BaseModel:
        """
        Update an existing record with organization validation.

        Args:
            instance_id: UUID of the record to update
            data: Dictionary of field values to update
            user: User instance performing the update

        Returns:
            Updated model instance
        """
        instance = self.get(instance_id)

        # Auto-set updated_by if model has this field and user provided
        if user and hasattr(self.model_class, 'updated_by'):
            data['updated_by_id'] = user.id

        for key, value in data.items():
            setattr(instance, key, value)

        instance.save()
        return instance

    def delete(self, instance_id: str, user=None) -> bool:
        """
        Soft delete a record.

        Args:
            instance_id: UUID of the record to delete
            user: User performing the deletion

        Returns:
            True if successful
        """
        instance = self.get(instance_id)
        instance.soft_delete(user=user)
        return True

    def restore(self, instance_id: str) -> BaseModel:
        """
        Restore a soft-deleted record.

        Args:
            instance_id: UUID of the record to restore

        Returns:
            Restored model instance
        """
        # Use all_objects to include deleted records
        instance = self.get(instance_id, allow_deleted=True)
        instance.is_deleted = False
        instance.deleted_at = None
        if hasattr(instance, 'deleted_by'):
            instance.deleted_by = None
        instance.save()
        return instance

    def get(self, instance_id: str, allow_deleted: bool = False) -> BaseModel:
        """
        Get a single record by ID with organization validation.

        Args:
            instance_id: UUID of the record
            allow_deleted: If True, allow fetching deleted records

        Returns:
            Model instance

        Raises:
            model_class.DoesNotExist: If record not found
        """
        # Use all_objects when allow_deleted is True to bypass TenantManager filtering
        # TenantManager.get_queryset() automatically filters out is_deleted=True records
        if allow_deleted:
            queryset = self.model_class.all_objects
        else:
            queryset = self.model_class.objects.filter(is_deleted=False)

        return queryset.get(id=instance_id)

    def query(
        self,
        filters: Optional[Dict] = None,
        search: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        order_by: Optional[str] = None
    ) -> QuerySet:
        """
        Query records with filters, search, and ordering.

        Args:
            filters: Dictionary of field filters
            search: Search keyword
            search_fields: List of fields to search in
            order_by: Ordering specification (e.g., '-created_at')

        Returns:
            Filtered QuerySet
        """
        queryset = self.model_class.objects.filter(is_deleted=False)

        # Apply filters
        if filters:
            q = Q()
            for key, value in filters.items():
                if '__' in key:  # Lookup already specified
                    q &= Q(**{key: value})
                else:  # Exact match
                    q &= Q(**{key: value})
            queryset = queryset.filter(q)

        # Apply search
        if search and search_fields:
            search_q = Q()
            for field in search_fields:
                search_q |= Q(**{f"{field}__icontains": search})
            queryset = queryset.filter(search_q)

        # Apply ordering
        if order_by:
            queryset = queryset.order_by(order_by)

        return queryset

    def paginate(
        self,
        queryset: QuerySet,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Paginate a QuerySet.

        Args:
            queryset: QuerySet to paginate
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dictionary with pagination data:
            {
                'count': total_count,
                'next': next_url or None,
                'previous': previous_url or None,
                'results': list of items
            }
        """
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        # Build next/previous URLs (simplified)
        next_url = None
        if page_obj.has_next():
            next_url = f"?page={page + 1}"

        previous_url = None
        if page_obj.has_previous():
            previous_url = f"?page={page - 1}"

        return {
            'count': paginator.count,
            'next': next_url,
            'previous': previous_url,
            'results': list(page_obj.object_list)
        }

    def batch_delete(self, ids: List[str], user) -> Dict[str, Any]:
        """
        Batch soft delete multiple records.

        Args:
            ids: List of record UUIDs to delete
            user: User performing the deletion

        Returns:
            Dictionary with summary and results:
            {
                'total': 3,
                'succeeded': 2,
                'failed': 1,
                'results': [
                    {'id': uuid1, 'success': true},
                    {'id': uuid2, 'success': false, 'error': 'Not found'}
                ]
            }
        """
        results = []
        succeeded = 0
        failed = 0

        for record_id in ids:
            try:
                self.delete(record_id, user)
                results.append({'id': record_id, 'success': True})
                succeeded += 1
            except self.model_class.DoesNotExist:
                results.append({'id': record_id, 'success': False, 'error': 'Not found'})
                failed += 1
            except Exception as e:
                results.append({'id': record_id, 'success': False, 'error': str(e)})
                failed += 1

        return {
            'total': len(ids),
            'succeeded': succeeded,
            'failed': failed,
            'results': results
        }
