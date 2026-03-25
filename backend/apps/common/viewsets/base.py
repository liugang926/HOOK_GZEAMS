from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from apps.common.models import BaseModel
from apps.common.managers import TenantManager
from apps.common.middleware import (
    get_current_organization,
    normalize_organization_id,
    set_current_organization,
)


class BatchOperationMixin:
    """
    Mixin providing standard batch operation endpoints.

    Provides:
    - batch_delete(): Batch soft delete
    - batch_restore(): Batch restore
    - batch_update(): Batch field update
    """

    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        """
        Batch soft delete multiple records.

        Request body:
        {
            "ids": ["uuid1", "uuid2", "uuid3"]
        }

        Response:
        {
            "success": true,
            "message": "Batch delete completed",
            "summary": {"total": 3, "succeeded": 3, "failed": 0},
            "results": [...]
        }
        """
        ids = request.data.get('ids', [])
        if not ids:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'ids parameter cannot be empty'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the service from the viewset
        service = getattr(self, 'service', None)
        if not service:
            # Fallback to direct model operations
            results = []
            succeeded = 0
            failed = 0

            # Get the model class for exception handling
            model_class = None
            queryset_attr = getattr(self, 'queryset', None)
            if queryset_attr is not None:
                model_class = queryset_attr.model
            elif hasattr(self, 'model'):
                model_class = self.model

            # Use appropriate exception handling
            if model_class is not None:
                not_found_exc = model_class.DoesNotExist
            else:
                not_found_exc = Exception

            for record_id in ids:
                try:
                    instance = self.get_queryset().get(id=record_id)
                    instance.soft_delete(request.user)
                    results.append({'id': str(record_id), 'success': True})
                    succeeded += 1
                except not_found_exc:
                    results.append({'id': str(record_id), 'success': False, 'error': 'Not found'})
                    failed += 1
                except Exception as e:
                    results.append({'id': str(record_id), 'success': False, 'error': str(e)})
                    failed += 1
        else:
            result = service.batch_delete(ids, request.user)
            results = result['results']
            succeeded = result['succeeded']
            failed = result['failed']

        response_data = {
            'success': True,
            'message': 'Batch delete completed',
            'summary': {
                'total': len(ids),
                'succeeded': succeeded,
                'failed': failed
            },
            'results': results
        }

        http_status = status.HTTP_200_OK if failed == 0 else status.HTTP_207_MULTI_STATUS
        return Response(response_data, status=http_status)

    @action(detail=False, methods=['post'])
    def batch_restore(self, request):
        """
        Batch restore multiple soft-deleted records.

        Request body:
        {
            "ids": ["uuid1", "uuid2", "uuid3"]
        }
        """
        ids = request.data.get('ids', [])
        if not ids:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'ids parameter cannot be empty'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        results = []
        succeeded = 0
        failed = 0

        # Get the model class for restore
        queryset_attr = getattr(self, 'queryset', None)
        if queryset_attr is not None:
            model_class = queryset_attr.model
        elif hasattr(self, 'model'):
            model_class = self.model
        else:
            return Response({
                'success': False,
                'error': {
                    'code': 'SERVER_ERROR',
                    'message': 'Cannot determine model class for restore'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        for record_id in ids:
            try:
                instance = self._get_all_objects_queryset(model_class).get(id=record_id)
                instance.is_deleted = False
                instance.deleted_at = None
                if hasattr(instance, 'deleted_by'):
                    instance.deleted_by = None
                instance.save()
                results.append({'id': str(record_id), 'success': True})
                succeeded += 1
            except Exception as e:
                results.append({'id': str(record_id), 'success': False, 'error': str(e)})
                failed += 1

        return Response({
            'success': True,
            'message': 'Batch restore completed',
            'summary': {
                'total': len(ids),
                'succeeded': succeeded,
                'failed': failed
            },
            'results': results
        })

    @action(detail=False, methods=['post'])
    def batch_update(self, request):
        """
        Batch update fields on multiple records.

        Request body:
        {
            "ids": ["uuid1", "uuid2"],
            "data": {"status": "active"}
        }
        """
        ids = request.data.get('ids', [])
        update_data = request.data.get('data', {})

        if not ids:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'ids parameter cannot be empty'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        results = []
        succeeded = 0
        failed = 0

        for record_id in ids:
            try:
                instance = self.get_queryset().get(id=record_id)
                for key, value in update_data.items():
                    setattr(instance, key, value)
                instance.save()
                results.append({'id': str(record_id), 'success': True})
                succeeded += 1
            except Exception as e:
                results.append({'id': str(record_id), 'success': False, 'error': str(e)})
                failed += 1

        return Response({
            'success': True,
            'message': 'Batch update completed',
            'summary': {
                'total': len(ids),
                'succeeded': succeeded,
                'failed': failed
            },
            'results': results
        })


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for all BaseModel-derived models.

    Automatically provides:
    - Organization isolation in get_queryset
    - Soft delete filtering (excludes deleted records by default)
    - Audit field management (created_by, updated_by)
    - Standard CRUD actions

    Override perform_create, perform_update, perform_destroy
    to customize behavior if needed.
    """

    def initial(self, request, *args, **kwargs):
        """Resolve organization context after DRF authentication completes."""
        super().initial(request, *args, **kwargs)

        model_class = self._get_model_class()
        if self._is_tenant_scoped_model(model_class):
            self._resolve_organization_id()

    def _get_model_class(self):
        """Resolve the model class managed by this viewset."""
        queryset_attr = getattr(self, 'queryset', None)
        if queryset_attr is not None:
            return queryset_attr.model

        serializer_class = None
        if hasattr(self, 'get_serializer_class'):
            serializer_class = self.get_serializer_class()
        else:
            serializer_class = getattr(self, 'serializer_class', None)

        serializer_meta = getattr(serializer_class, 'Meta', None)
        return getattr(serializer_meta, 'model', None)

    def _is_tenant_scoped_model(self, model_class=None):
        """Check whether the model uses tenant-aware isolation."""
        resolved_model_class = model_class or self._get_model_class()
        default_manager = getattr(resolved_model_class, '_default_manager', None)
        return isinstance(default_manager, TenantManager)

    def _bind_request_organization(self, organization_id, organization=None):
        """Persist the resolved organization on request and thread-local state."""
        normalized_org_id = normalize_organization_id(organization_id)
        if not normalized_org_id or not hasattr(self, 'request'):
            return None

        set_current_organization(normalized_org_id)
        self.request.organization_id = normalized_org_id

        if organization is not None:
            self.request.current_organization = organization

        session = getattr(self.request, 'session', None)
        if session is not None:
            try:
                session['current_organization_id'] = normalized_org_id
            except Exception:
                pass

        return normalized_org_id

    def _validate_organization_access(self, organization_id):
        """Ensure the authenticated user can access the resolved organization."""
        normalized_org_id = normalize_organization_id(organization_id)
        user = getattr(getattr(self, 'request', None), 'user', None)
        if not normalized_org_id or not user or not getattr(user, 'is_authenticated', False):
            return normalized_org_id

        from apps.common.services.organization_service import BaseOrganizationService

        if BaseOrganizationService.check_organization_access(user, normalized_org_id):
            return normalized_org_id

        raise PermissionDenied(
            f'User does not have access to organization: {normalized_org_id}'
        )

    def _resolve_organization_id(self):
        """Resolve the effective organization for the current request."""
        if not hasattr(self, 'request'):
            return None

        organization_id = normalize_organization_id(
            getattr(self.request, 'organization_id', None)
        )
        if organization_id:
            self._validate_organization_access(organization_id)
            return self._bind_request_organization(organization_id)

        raw_request = getattr(self.request, '_request', self.request)
        meta = getattr(raw_request, 'META', {}) or {}
        organization_id = normalize_organization_id(
            meta.get('HTTP_X_ORGANIZATION_ID')
        )
        if organization_id:
            self._validate_organization_access(organization_id)
            return self._bind_request_organization(organization_id)

        session = getattr(raw_request, 'session', None) or getattr(self.request, 'session', None)
        if session is not None:
            organization_id = normalize_organization_id(
                session.get('current_organization_id')
            )
            if organization_id:
                self._validate_organization_access(organization_id)
                return self._bind_request_organization(organization_id)

        organization_id = normalize_organization_id(get_current_organization())
        if organization_id:
            self._validate_organization_access(organization_id)
            return self._bind_request_organization(organization_id)

        user = getattr(self.request, 'user', None)
        if user and getattr(user, 'is_authenticated', False):
            default_organization = user.ensure_default_organization()
            if default_organization:
                organization_id = self._validate_organization_access(
                    default_organization.id
                )
                return self._bind_request_organization(
                    organization_id,
                    organization=default_organization,
                )

        return None

    def _get_all_objects_queryset(self, model_class):
        """Return all records scoped to the current organization when required."""
        queryset = model_class.all_objects.all()
        if not self._is_tenant_scoped_model(model_class):
            return queryset

        organization_id = self._resolve_organization_id()
        if not organization_id:
            return queryset.none()

        return queryset.filter(organization_id=organization_id)

    def get_queryset(self):
        """Filter out soft-deleted records and apply organization isolation."""
        model_class = self._get_model_class()

        if self._is_tenant_scoped_model(model_class):
            organization_id = self._resolve_organization_id()
            if not organization_id:
                return model_class.all_objects.none()

            queryset = model_class.all_objects.filter(
                is_deleted=False,
                organization_id=organization_id,
            )
            return queryset

        # Use getattr to safely get queryset, fall back to get_queryset from parent
        queryset = getattr(self, 'queryset', None)
        if queryset is None:
            queryset = super().get_queryset()

        queryset = queryset.filter(is_deleted=False)
        return queryset

    def perform_create(self, serializer):
        """Set created_by and organization on create."""
        model_class = self._get_model_class()
        save_kwargs = {'created_by': self.request.user}

        if self._is_tenant_scoped_model(model_class):
            organization_id = self._resolve_organization_id()
            if not organization_id:
                raise ValidationError(
                    {'organization': 'Organization context is required.'}
                )
            save_kwargs['organization_id'] = organization_id

        serializer.save(**save_kwargs)

    def perform_update(self, serializer):
        """Set updated_by on update."""
        if hasattr(self.request.user, 'id'):
            serializer.save(updated_by=self.request.user)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        """Perform soft delete instead of hard delete."""
        instance.soft_delete(user=self.request.user)

    @action(detail=False, methods=['get'])
    def deleted(self, request):
        """
        List soft-deleted records.

        GET /api/{resource}/deleted/

        Returns paginated list of soft-deleted records in BaseResponse format.
        """
        # Get all deleted records (user must have permission)
        queryset_attr = getattr(self, 'queryset', None)
        if queryset_attr is None:
            # Fallback: get from get_queryset and add is_deleted filter
            base_queryset = super().get_queryset()
            queryset = base_queryset.filter(is_deleted=True)
        else:
            queryset = self._get_all_objects_queryset(queryset_attr.model).filter(
                is_deleted=True
            )

        model_class = getattr(queryset, 'model', None) or self._get_model_class()
        if queryset_attr is None and self._is_tenant_scoped_model(model_class):
            organization_id = self._resolve_organization_id()
            if not organization_id:
                queryset = queryset.none()
            else:
                queryset = queryset.filter(organization_id=organization_id)

        # Use DRF's standard pagination for consistency
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Fallback for non-paginated requests
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': {
                'count': queryset.count(),
                'next': None,
                'previous': None,
                'results': serializer.data
            }
        })

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """
        Restore a soft-deleted record.

        POST /api/{resource}/{id}/restore/
        """
        queryset_attr = getattr(self, 'queryset', None)
        if queryset_attr is None:
            # Fallback: try to get the model from serializer
            serializer_class = self.get_serializer_class()
            model_class = getattr(serializer_class, 'Meta', None)
            if model_class and hasattr(model_class, 'model'):
                instance = self._get_all_objects_queryset(model_class.model).get(id=pk)
            else:
                raise NotImplementedError("Cannot determine model class for restore")
        else:
            instance = self._get_all_objects_queryset(queryset_attr.model).get(id=pk)
        instance.is_deleted = False
        instance.deleted_at = None
        if hasattr(instance, 'deleted_by'):
            instance.deleted_by = None
        instance.save()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Restore successful',
            'data': serializer.data
        })


class BaseModelViewSetWithBatch(BatchOperationMixin, BaseModelViewSet):
    """
    Base ViewSet with batch operation support.

    Inherits from both BatchOperationMixin and BaseModelViewSet
    to provide all standard CRUD + batch operation endpoints.

    This is the recommended ViewSet to use for most resources.
    """
    pass  # All functionality inherited from parent classes
