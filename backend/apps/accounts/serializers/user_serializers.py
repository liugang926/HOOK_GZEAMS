"""
Serializers for User model.

Provides serializers for user data in API responses.
"""
from rest_framework import serializers
from django.contrib.auth.models import AbstractUser

from apps.accounts.models import User, UserOrganization
from apps.common.serializers.base import BaseModelSerializer, BaseModelWithAuditSerializer


class UserOrganizationSerializer(serializers.ModelSerializer):
    """Serializer for UserOrganization through model."""

    organization_name = serializers.CharField(
        source='organization.name',
        read_only=True
    )
    organization_code = serializers.CharField(
        source='organization.code',
        read_only=True
    )
    role_display = serializers.CharField(
        source='get_role_display',
        read_only=True
    )

    class Meta:
        model = UserOrganization
        fields = [
            'id',
            'organization',
            'organization_name',
            'organization_code',
            'role',
            'role_display',
            'is_active',
            'is_primary',
            'joined_at',
            'invited_by',
        ]
        read_only_fields = ['id', 'joined_at']


class UserSerializer(BaseModelSerializer):
    """
    Serializer for User model.

    Provides basic user information for API responses.
    Extends BaseModelSerializer for consistency.
    """

    full_name = serializers.SerializerMethodField()
    organizations = UserOrganizationSerializer(
        source='user_orgs',
        many=True,
        read_only=True
    )
    current_organization_name = serializers.CharField(
        source='current_organization.name',
        read_only=True,
        allow_null=True
    )
    org_role = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = User
        fields = BaseModelSerializer.Meta.fields + [
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'is_active',
            'is_staff',
            'is_superuser',
            'current_organization',
            'current_organization_name',
            'organizations',
            'org_role',
            'date_joined',
            'last_login',
            'wework_userid',
            'dingtalk_userid',
            'feishu_userid',
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + [
            'username',
            'date_joined',
            'last_login',
            'wework_userid',
            'dingtalk_userid',
            'feishu_userid',
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
        }

    def get_full_name(self, obj):
        """Get user's full name."""
        return obj.get_full_name() or obj.username

    def get_org_role(self, obj):
        """Get user's role in current organization."""
        if obj.current_organization_id:
            role = obj.get_org_role(obj.current_organization_id)
            return role
        return None


class UserBasicSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for User model.

    Used for nested representations where minimal user info is needed.
    """

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
        ]
        read_only_fields = ['id', 'username']

    def get_full_name(self, obj):
        """Get user's full name."""
        return obj.get_full_name() or obj.username


class UserListSerializer(BaseModelSerializer):
    """
    Optimized serializer for user list views.
    """

    full_name = serializers.SerializerMethodField()
    organization_count = serializers.SerializerMethodField()
    current_organization_name = serializers.CharField(
        source='current_organization.name',
        read_only=True,
        allow_null=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = User
        fields = BaseModelSerializer.Meta.fields + [
            'username',
            'email',
            'full_name',
            'is_active',
            'is_staff',
            'current_organization_name',
            'organization_count',
            'date_joined',
        ]

    def get_full_name(self, obj):
        """Get user's full name."""
        return obj.get_full_name() or obj.username

    def get_organization_count(self, obj):
        """Get number of organizations user belongs to."""
        return obj.user_orgs.filter(is_active=True).count()


class UserDetailSerializer(BaseModelWithAuditSerializer):
    """
    Full serializer for user detail views.

    Includes all user information with organization memberships.
    """

    full_name = serializers.SerializerMethodField()
    organizations = UserOrganizationSerializer(
        source='user_orgs',
        many=True,
        read_only=True
    )
    accessible_organizations = serializers.SerializerMethodField()
    primary_organization = serializers.SerializerMethodField()

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = User
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'is_active',
            'is_staff',
            'is_superuser',
            'current_organization',
            'organizations',
            'accessible_organizations',
            'primary_organization',
            'date_joined',
            'last_login',
            'wework_userid',
            'wework_unionid',
            'dingtalk_userid',
            'dingtalk_unionid',
            'feishu_userid',
            'feishu_unionid',
        ]
        read_only_fields = BaseModelWithAuditSerializer.Meta.read_only_fields + [
            'username',
            'date_joined',
            'last_login',
        ]

    def get_full_name(self, obj):
        """Get user's full name."""
        return obj.get_full_name() or obj.username

    def get_accessible_organizations(self, obj):
        """Get list of organizations user has access to."""
        orgs = obj.get_accessible_organizations()
        return [
            {
                'id': str(org.id),
                'name': org.name,
                'code': org.code,
                'org_type': org.org_type,
            }
            for org in orgs
        ]

    def get_primary_organization(self, obj):
        """Get user's primary organization."""
        primary = obj.get_primary_organization()
        if primary:
            return {
                'id': str(primary.id),
                'name': primary.name,
                'code': primary.code,
            }
        return None


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users.

    Handles password hashing and initial organization assignment.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    organization_id = serializers.CharField(
        write_only=True,
        required=False,
        allow_null=True
    )
    role = serializers.ChoiceField(
        choices=['admin', 'member', 'auditor'],
        write_only=True,
        required=False,
        default='member'
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'password_confirm',
            'organization_id',
            'role',
        ]

    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match'
            })
        return attrs

    def create(self, validated_data):
        """Create new user with hashed password."""
        from django.contrib.auth.hashers import make_password

        # Remove non-model fields
        password = validated_data.pop('password')
        password_confirm = validated_data.pop('password_confirm')
        organization_id = validated_data.pop('organization_id', None)
        role = validated_data.pop('role', 'member')

        # Hash password
        validated_data['password'] = make_password(password)

        # Create user
        user = User.objects.create(**validated_data)

        # Add to organization if specified
        if organization_id:
            UserOrganization.objects.create(
                user=user,
                organization_id=organization_id,
                role=role,
                is_primary=True
            )

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user information.

    Allows partial updates of user profile.
    """

    class Meta:
        model = User
        fields = [
            'email',
            'first_name',
            'last_name',
            'current_organization',
        ]

    def update(self, instance, validated_data):
        """Update user instance."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change operation.
    """

    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Validate password change."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Passwords do not match'
            })
        return attrs

    def validate_old_password(self, value):
        """Validate old password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Incorrect password')
        return value


class UserSelectorSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for user selection components.

    Optimized for dropdown/autocomplete components with minimal fields.
    """

    label = serializers.SerializerMethodField()
    value = serializers.CharField(source='id')
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['value', 'username', 'full_name', 'email', 'label']

    def get_full_name(self, obj):
        """Get user's full name."""
        return obj.get_full_name() or obj.username

    def get_label(self, obj):
        """
        Display label for select component.

        Returns full name if available, otherwise username.
        """
        full_name = obj.get_full_name()
        if full_name:
            return f"{full_name} ({obj.username})"
        return obj.username
