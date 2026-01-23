"""
Service layer for Department business logic.
"""
from typing import List, Dict, Any
from apps.organizations.models import Department
from apps.common.services.base_crud import BaseCRUDService


class DepartmentService(BaseCRUDService):
    """
    Service class for Department operations.

    Provides business logic for department tree operations,
    path calculations, and select option generation.
    """

    def __init__(self):
        """Initialize service with Department model."""
        super().__init__(Department)

    def get_tree(self, organization_id: str) -> List[Dict[str, Any]]:
        """
        Get full department tree for organization.

        Args:
            organization_id: Organization UUID

        Returns:
            List of root department dicts with nested children
        """
        def build_tree(parent_id=None) -> List[Dict[str, Any]]:
            """Recursively build department tree."""
            departments = Department.objects.filter(
                organization_id=organization_id,
                parent_id=parent_id,
                is_deleted=False,
                is_active=True
            ).order_by('order', 'name')

            result = []
            for dept in departments:
                children = build_tree(dept.id)
                result.append({
                    'id': str(dept.id),
                    'code': dept.code,
                    'name': dept.name,
                    'level': dept.level,
                    'full_path': dept.full_path,
                    'full_path_name': dept.full_path_name,
                    'is_active': dept.is_active,
                    'order': dept.order,
                    'children': children
                })
            return result

        return build_tree()

    def get_department_path(self, department_id: str) -> List[Dict[str, Any]]:
        """
        Get breadcrumb path from root to department.

        Args:
            department_id: Department UUID

        Returns:
            List of department dicts from root to target
        """
        department = Department.objects.get(id=department_id)
        path = []
        current = department

        while current and not current.is_deleted:
            path.append({
                'id': str(current.id),
                'code': current.code,
                'name': current.name,
                'level': current.level,
                'full_path_name': current.full_path_name
            })
            current = current.parent

        return list(reversed(path))

    def get_select_options(self, organization_id: str) -> List[Dict[str, Any]]:
        """
        Get departments formatted for select dropdown.

        Args:
            organization_id: Organization UUID

        Returns:
            List of dicts with value, label, and code
        """
        departments = Department.objects.filter(
            organization_id=organization_id,
            is_deleted=False,
            is_active=True
        ).order_by('level', 'order', 'name')

        options = []
        for dept in departments:
            path = self.get_department_path(dept.id)
            path_name = ' / '.join([p['name'] for p in path])
            options.append({
                'value': str(dept.id),
                'label': path_name,
                'code': dept.code,
                'level': dept.level
            })

        return options
