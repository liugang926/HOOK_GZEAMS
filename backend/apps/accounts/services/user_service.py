"""
Services for User management.

Provides business logic for user CRUD operations, organization management,
and user authentication.
"""
from typing import Dict, List, Optional, Any
from django.db.models import QuerySet
from django.utils import timezone

from apps.accounts.models import User, UserOrganization
from apps.common.services.base_crud import BaseCRUDService


class UserService(BaseCRUDService):
    """
    Service for User management operations.

    Handles user CRUD, organization membership, and role management.
    """

    def __init__(self):
        # User model extends AbstractUser and BaseModel
        super().__init__(User)

    def get_accessible_users(
        self,
        organization_id: str,
        filters: Optional[Dict] = None
    ) -> QuerySet:
        """
        Get users that have access to a specific organization.

        Args:
            organization_id: Organization ID
            filters: Optional filter dict

        Returns:
            QuerySet of filtered users
        """
        # Get user IDs that are members of this organization
        user_ids = UserOrganization.objects.filter(
            organization_id=organization_id,
            is_active=True
        ).values_list('user_id', flat=True)

        queryset = User.objects.filter(
            id__in=user_ids,
            is_deleted=False
        )

        if filters:
            if 'search' in filters:
                search = filters['search']
                queryset = queryset.filter(
                    username__icontains=search
                ) | queryset.filter(
                    email__icontains=search
                ) | queryset.filter(
                    first_name__icontains=search
                ) | queryset.filter(
                    last_name__icontains=search
                )

            if 'is_active' in filters:
                queryset = queryset.filter(is_active=filters['is_active'])

        return queryset.order_by('-date_joined')

    def add_to_organization(
        self,
        user_id: str,
        organization_id: str,
        role: str = 'member',
        is_primary: bool = False,
        invited_by: Optional[str] = None
    ) -> UserOrganization:
        """
        Add a user to an organization.

        Args:
            user_id: User ID
            organization_id: Organization ID
            role: Role (admin, member, auditor)
            is_primary: Whether this is the primary organization
            invited_by: User ID of who sent the invitation

        Returns:
            UserOrganization instance
        """
        user_org, created = UserOrganization.objects.get_or_create(
            user_id=user_id,
            organization_id=organization_id,
            defaults={
                'role': role,
                'is_primary': is_primary,
                'invited_by_id': invited_by,
            }
        )

        if not created:
            # Update existing
            user_org.role = role
            user_org.is_active = True
            user_org.save()

        return user_org

    def remove_from_organization(
        self,
        user_id: str,
        organization_id: str
    ) -> bool:
        """
        Remove a user from an organization (soft delete).

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            True if successful
        """
        try:
            user_org = UserOrganization.objects.get(
                user_id=user_id,
                organization_id=organization_id
            )
            user_org.is_active = False
            user_org.save()
            return True
        except UserOrganization.DoesNotExist:
            return False

    def update_org_role(
        self,
        user_id: str,
        organization_id: str,
        role: str
    ) -> bool:
        """
        Update user role in an organization.

        Args:
            user_id: User ID
            organization_id: Organization ID
            role: New role (admin, member, auditor)

        Returns:
            True if successful
        """
        try:
            user_org = UserOrganization.objects.get(
                user_id=user_id,
                organization_id=organization_id,
                is_active=True
            )
            user_org.role = role
            user_org.save()
            return True
        except UserOrganization.DoesNotExist:
            return False

    def switch_organization(
        self,
        user_id: str,
        organization_id: str
    ) -> bool:
        """
        Switch user's current organization.

        Args:
            user_id: User ID
            organization_id: Organization ID to switch to

        Returns:
            True if successful
        """
        try:
            user = User.objects.get(id=user_id)
            return user.switch_organization(organization_id)
        except User.DoesNotExist:
            return False

    def get_user_stats(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Get user statistics for an organization.

        Args:
            organization_id: Organization ID

        Returns:
            Dict with user counts by role
        """
        user_orgs = UserOrganization.objects.filter(
            organization_id=organization_id,
            is_active=True
        )

        return {
            'total': user_orgs.count(),
            'admins': user_orgs.filter(role='admin').count(),
            'members': user_orgs.filter(role='member').count(),
            'auditors': user_orgs.filter(role='auditor').count(),
        }

    def deactivate_user(
        self,
        user_id: str
    ) -> bool:
        """
        Deactivate a user account.

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        try:
            user = User.objects.get(id=user_id)
            user.is_active = False
            user.save()
            return True
        except User.DoesNotExist:
            return False

    def activate_user(
        self,
        user_id: str
    ) -> bool:
        """
        Activate a user account.

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        try:
            user = User.objects.get(id=user_id)
            user.is_active = True
            user.save()
            return True
        except User.DoesNotExist:
            return False
