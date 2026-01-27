"""
Dynamic Data Service - handles CRUD operations for dynamic business object data.

This service provides the business logic layer for creating, reading, updating,
and deleting dynamic data records based on business object metadata.
"""
import re
from typing import Dict, List, Any, Optional
from django.db import transaction
from django.db.models import Q, Count
from django.utils import timezone
from simpleeval import simple_eval, InvalidExpression
from apps.system.models import BusinessObject, DynamicData, DynamicSubTableData, FieldDefinition
from apps.common.services.base_crud import BaseCRUDService


class DynamicDataService(BaseCRUDService):
    """
    Dynamic Data Service for managing business object data.

    Inherits from BaseCRUDService which provides:
    - Standard CRUD methods
    - Organization isolation
    - Pagination support
    """

    def __init__(self, business_object_code: str):
        """
        Initialize with a business object code.

        Args:
            business_object_code: The code of the business object to manage
        """
        super().__init__(DynamicData)
        self.bo_code = business_object_code
        self._metadata_service = None
        self._business_object = None

    @property
    def metadata_service(self):
        """Lazy load metadata service."""
        if self._metadata_service is None:
            from apps.system.services.metadata_service import MetadataService
            self._metadata_service = MetadataService()
        return self._metadata_service

    @property
    def business_object(self) -> Optional[BusinessObject]:
        """Get the business object for this service."""
        if self._business_object is None:
            self._business_object = self.metadata_service.get_business_object(
                self.bo_code
            )
        return self._business_object

    def query(
        self,
        filters: Dict = None,
        search: str = None,
        page: int = 1,
        page_size: int = 20,
        sort: str = None
    ) -> Dict:
        """
        Query dynamic data with pagination, filtering, and search.

        Args:
            filters: Dict of field filters (e.g., {'status': 'active'})
            search: Search string (searches all searchable fields)
            page: Page number (1-indexed)
            page_size: Items per page
            sort: Sort field (prefix with '-' for descending)

        Returns:
            Dict containing:
                - items: List of data records
                - total: Total count of matching records
                - page: Current page number
                - page_size: Items per page
        """
        if not self.business_object:
            raise ValueError(f"Business object '{self.bo_code}' does not exist.")

        # Build base queryset
        qs = DynamicData.objects.filter(
            business_object=self.business_object,
            is_deleted=False
        )

        # Apply filters
        if filters:
            for field_code, value in filters.items():
                # Handle special fields
                if field_code in ['status', 'data_no', 'created_at', 'updated_at']:
                    qs = qs.filter(**{field_code: value})
                else:
                    # JSONB field query
                    qs = qs.filter(**{f'dynamic_fields__{field_code}': value})

        # Apply search
        if search:
            searchable_fields = self.business_object.field_definitions.filter(
                is_searchable=True
            )
            search_q = Q()
            for field in searchable_fields:
                search_q |= Q(**{f'dynamic_fields__{field.code}__icontains': search})
            qs = qs.filter(search_q)

        # Apply sorting
        if sort:
            if sort.startswith('-'):
                field_name = sort[1:]
                if field_name in ['created_at', 'updated_at', 'data_no', 'status']:
                    qs = qs.order_by(f'-{field_name}')
                else:
                    qs = qs.order_by(f'-dynamic_fields__{field_name}')
            else:
                if sort in ['created_at', 'updated_at', 'data_no', 'status']:
                    qs = qs.order_by(sort)
                else:
                    qs = qs.order_by(f'dynamic_fields__{sort}')
        else:
            qs = qs.order_by('-created_at')

        # Get total count before pagination
        total = qs.count()

        # Apply pagination
        start = (page - 1) * page_size
        items = qs[start:start + page_size]

        # Serialize results
        return {
            'items': [self._serialize_data(item) for item in items],
            'total': total,
            'page': page,
            'page_size': page_size
        }

    def get(self, data_id: str) -> Optional[Dict]:
        """
        Get a single data record by ID.

        Args:
            data_id: UUID of the data record

        Returns:
            Serialized data dict or None if not found
        """
        try:
            data = DynamicData.objects.get(
                id=data_id,
                business_object=self.business_object,
                is_deleted=False
            )
            return self._serialize_data(data, include_all_fields=True)
        except DynamicData.DoesNotExist:
            return None

    @transaction.atomic
    def create(self, data: Dict, status: str = 'draft') -> Dict:
        """
        Create a new dynamic data record.

        Args:
            data: Dict of field values (e.g., {'name': 'Test', 'quantity': 10})
            status: Initial status (default: 'draft')

        Returns:
            The created data record
        """
        if not self.business_object:
            raise ValueError(f"Business object '{self.bo_code}' does not exist.")

        # Get field definitions for validation
        field_defs = {
            f.code: f
            for f in self.business_object.field_definitions.all()
        }

        # Validate required fields
        for field_code, field_def in field_defs.items():
            if field_def.is_required and field_code not in data:
                raise ValueError(f"Required field '{field_def.name}' is missing.")

        # Process default values
        processed_data = data.copy()
        for field_code, field_def in field_defs.items():
            if field_code not in processed_data and field_def.default_value:
                processed_data[field_code] = self._parse_default_value(
                    field_def.default_value
                )

        # Calculate formula fields
        processed_data = self._calculate_formulas(processed_data, field_defs)

        # Generate data number
        data_no = self._generate_data_no()

        # Create the record
        dynamic_data = DynamicData.objects.create(
            business_object=self.business_object,
            data_no=data_no,
            dynamic_fields=processed_data,
            status=status
        )

        return self._serialize_data(dynamic_data, include_all_fields=True)

    @transaction.atomic
    def update(self, data_id: str, data: Dict) -> Dict:
        """
        Update an existing dynamic data record.

        Args:
            data_id: UUID of the data record
            data: Dict of field values to update

        Returns:
            The updated data record
        """
        try:
            dynamic_data = DynamicData.objects.get(
                id=data_id,
                business_object=self.business_object,
                is_deleted=False
            )
        except DynamicData.DoesNotExist:
            raise ValueError(f"Data record '{data_id}' does not exist.")

        # Merge with existing data
        current_fields = dynamic_data.dynamic_fields.copy()
        current_fields.update(data)

        # Recalculate formulas
        field_defs = {
            f.code: f
            for f in self.business_object.field_definitions.all()
        }
        current_fields = self._calculate_formulas(current_fields, field_defs)

        # Update the record
        dynamic_data.dynamic_fields = current_fields
        dynamic_data.save()

        return self._serialize_data(dynamic_data, include_all_fields=True)

    def _serialize_data(
        self,
        data: DynamicData,
        include_all_fields: bool = False
    ) -> Dict:
        """
        Serialize a DynamicData record to dict.

        Args:
            data: The DynamicData instance
            include_all_fields: If True, include all fields;
                               if False, only include show_in_list fields

        Returns:
            Serialized data dict
        """
        field_defs = {
            f.code: f
            for f in self.business_object.field_definitions.all()
        }

        result = {
            'id': str(data.id),
            'data_no': data.data_no,
            'status': data.status,
            'created_at': data.created_at.isoformat() if data.created_at else None,
            'updated_at': data.updated_at.isoformat() if data.updated_at else None,
            'created_by': str(data.created_by_id) if data.created_by_id else None,
            'submitted_at': data.submitted_at.isoformat() if data.submitted_at else None,
            'approved_at': data.approved_at.isoformat() if data.approved_at else None,
        }

        # Add dynamic fields
        for field_code, field_def in field_defs.items():
            value = data.dynamic_fields.get(field_code)

            # Only return list fields if not including all
            if not include_all_fields and not field_def.show_in_list:
                continue

            result[field_code] = value

        return result

    def _generate_data_no(self) -> str:
        """
        Generate a unique data number.

        Format: {OBJECT_CODE}{YYYYMMDD}{SEQUENCE}
        Example: ASSET202401010001

        Returns:
            Generated data number
        """
        prefix = self.bo_code.upper()
        date_str = timezone.now().strftime('%Y%m%d')

        # Find today's max sequence number
        today_prefix = f"{prefix}{date_str}"
        max_no = DynamicData.objects.filter(
            business_object=self.business_object,
            data_no__startswith=today_prefix
        ).order_by('-data_no').first()

        if max_no:
            # Extract sequence and increment
            try:
                seq = int(max_no.data_no[-4:]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        return f"{today_prefix}{seq:04d}"

    def _parse_default_value(self, value: str) -> Any:
        """
        Parse default value with variable substitution.

        Supported variables:
        - {current_user}: Current user ID
        - {today}: Today's date (YYYY-MM-DD)
        - {now}: Current timestamp (ISO format)

        Args:
            value: Default value string

        Returns:
            Parsed value
        """
        if not isinstance(value, str):
            return value

        variables = {
            '{current_user}': self._get_current_user_id,
            '{today}': lambda: timezone.now().date().isoformat(),
            '{now}': lambda: timezone.now().isoformat(),
        }

        result = value
        for var, getter in variables.items():
            if var in result:
                try:
                    replacement = getter() if callable(getter) else getter
                    result = result.replace(var, str(replacement))
                except Exception:
                    # If variable resolution fails, keep original
                    pass

        return result

    def _calculate_formulas(self, data: Dict, field_defs: Dict) -> Dict:
        """
        Calculate formula fields.

        Formulas support simple expressions like:
        - {field1} + {field2}
        - {price} * {quantity}
        - {amount} * 0.1

        Args:
            data: Field values dict
            field_defs: Field definitions dict

        Returns:
            Updated data dict with calculated formulas
        """
        for field_code, field_def in field_defs.items():
            if field_def.field_type == 'formula' and field_def.formula:
                try:
                    # Parse formula expression
                    expression = field_def.formula

                    # Replace field references with actual values
                    for fc, fv in data.items():
                        expression = re.sub(
                            rf'\{{{fc}\}}',
                            str(fv) if fv is not None else '0',
                            expression
                        )

                    # Calculate result
                    result = simple_eval(expression)
                    data[field_code] = result

                except (InvalidExpression, ValueError, TypeError):
                    # Set to 0 on calculation error
                    data[field_code] = 0

        return data

    def _get_current_user_id(self) -> Optional[str]:
        """Get current user ID from request context."""
        try:
            from apps.common.middleware import get_current_organization
            from django.contrib.auth.middleware import get_user

            # Try to get user from thread-local context
            import threading
            thread_local = getattr(threading.current_thread(), 'request', None)
            if thread_local and hasattr(thread_local, 'user'):
                return str(thread_local.user.id)
        except Exception:
            pass
        return None

    def get_sub_table_rows(
        self,
        data_id: str,
        field_code: str
    ) -> List[Dict]:
        """
        Get all rows for a sub-table field.

        Args:
            data_id: Parent data record ID
            field_code: Sub-table field code

        Returns:
            List of sub-table rows
        """
        try:
            data = DynamicData.objects.get(id=data_id)
            field_def = self.business_object.field_definitions.get(
                code=field_code,
                field_type='sub_table'
            )

            rows = DynamicSubTableData.objects.filter(
                parent_data=data,
                field_definition=field_def,
                is_deleted=False
            ).order_by('row_order')

            return [
                {
                    'id': str(row.id),
                    'row_order': row.row_order,
                    'row_data': row.row_data
                }
                for row in rows
            ]

        except (DynamicData.DoesNotExist, FieldDefinition.DoesNotExist):
            return []

    @transaction.atomic
    def add_sub_table_row(
        self,
        data_id: str,
        field_code: str,
        row_data: Dict
    ) -> Dict:
        """
        Add a new row to a sub-table.

        Args:
            data_id: Parent data record ID
            field_code: Sub-table field code
            row_data: Row cell values

        Returns:
            The created row
        """
        try:
            parent = DynamicData.objects.get(id=data_id)
            field_def = self.business_object.field_definitions.get(
                code=field_code,
                field_type='sub_table'
            )

            # Get next row order
            max_order = parent.sub_table_rows.filter(
                field_definition=field_def
            ).order_by('-row_order').first()
            row_order = (max_order.row_order + 1) if max_order else 0

            row = DynamicSubTableData.objects.create(
                parent_data=parent,
                field_definition=field_def,
                row_order=row_order,
                row_data=row_data
            )

            return {
                'id': str(row.id),
                'row_order': row.row_order,
                'row_data': row.row_data
            }

        except (DynamicData.DoesNotExist, FieldDefinition.DoesNotExist) as e:
            raise ValueError(f"Cannot add row: {str(e)}")

    @transaction.atomic
    def update_sub_table_row(
        self,
        row_id: str,
        row_data: Dict,
        row_order: int = None
    ) -> Dict:
        """
        Update a sub-table row.

        Args:
            row_id: Row ID
            row_data: New row data
            row_order: New row order (optional)

        Returns:
            The updated row
        """
        try:
            row = DynamicSubTableData.objects.get(id=row_id, is_deleted=False)

            if row_data is not None:
                # Merge with existing data
                current_data = row.row_data.copy()
                current_data.update(row_data)
                row.row_data = current_data

            if row_order is not None:
                row.row_order = row_order

            row.save()

            return {
                'id': str(row.id),
                'row_order': row.row_order,
                'row_data': row.row_data
            }

        except DynamicSubTableData.DoesNotExist:
            raise ValueError(f"Row '{row_id}' does not exist.")

    @transaction.atomic
    def delete_sub_table_row(self, row_id: str) -> bool:
        """
        Delete a sub-table row (soft delete).

        Args:
            row_id: Row ID

        Returns:
            True if deleted, False otherwise
        """
        try:
            row = DynamicSubTableData.objects.get(id=row_id)
            row.soft_delete()
            return True
        except DynamicSubTableData.DoesNotExist:
            return False
