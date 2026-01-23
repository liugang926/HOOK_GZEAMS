"""
Services for Asset models.
"""
from apps.common.services.base_crud import BaseCRUDService
from apps.assets.models import AssetCategory


class AssetCategoryService(BaseCRUDService):
    """Service layer for AssetCategory business logic."""

    def __init__(self):
        super().__init__(AssetCategory)

    def get_tree(self, organization_id):
        """
        Get category tree for organization.

        Args:
            organization_id: Organization UUID

        Returns:
            List of category tree nodes with nested children
        """
        return AssetCategory.get_tree(organization_id)

    def add_child(self, parent_id, data, organization_id, user):
        """
        Add child category to parent.

        Args:
            parent_id: UUID of parent category
            data: Dictionary of child category data
            organization_id: Organization UUID
            user: User creating the child

        Returns:
            Created child category instance
        """
        try:
            parent = self.model_class.objects.get(
                id=parent_id,
                organization_id=organization_id,
                is_deleted=False
            )
        except AssetCategory.DoesNotExist:
            raise ValueError('Parent category not found')

        # Create child category
        child_data = {
            **data,
            'parent_id': parent.id,
            'organization_id': organization_id,
            'is_custom': True,
        }

        return self.create(child_data, user)

    def can_delete(self, category_id, organization_id):
        """
        Check if category can be deleted.

        Args:
            category_id: UUID of category
            organization_id: Organization UUID

        Returns:
            True if category can be deleted, False otherwise
        """
        try:
            category = self.model_class.objects.get(
                id=category_id,
                organization_id=organization_id,
                is_deleted=False
            )
            return category.can_delete()
        except AssetCategory.DoesNotExist:
            return False

    def get_by_code(self, code, organization_id):
        """
        Get category by code within organization.

        Args:
            code: Category code
            organization_id: Organization UUID

        Returns:
            AssetCategory instance or None
        """
        try:
            return self.model_class.objects.get(
                code=code,
                organization_id=organization_id,
                is_deleted=False
            )
        except AssetCategory.DoesNotExist:
            return None

    def get_category_path(self, category_id):
        """
        Get breadcrumb path from root to category.

        Args:
            category_id: UUID of category

        Returns:
            List of category dictionaries from root to target category
        """
        category = self.model_class.objects.get(id=category_id)
        path = []
        current = category

        while current:
            path.append({
                'id': str(current.id),
                'code': current.code,
                'name': current.name,
                'full_name': current.full_name,
                'level': current.level
            })
            current = current.parent

        return list(reversed(path))
