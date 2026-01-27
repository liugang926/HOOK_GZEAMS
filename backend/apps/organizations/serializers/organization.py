"""
Serializers for Organization model.
"""
from rest_framework import serializers
from apps.organizations.models import Organization, Department, UserDepartment
from apps.common.serializers.base import BaseModelSerializer


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization CRUD operations."""

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'code', 'org_type', 'org_type_display',
            'parent', 'parent_name', 'level', 'path',
            'contact_person', 'contact_phone', 'email', 'address',
            'credit_code', 'is_active', 'is_deleted',
            'invite_code', 'invite_code_expires_at',
            'created_at', 'updated_at', 'created_by',
        ]
        read_only_fields = ['id', 'level', 'path', 'created_at', 'updated_at']

    parent_name = serializers.CharField(source='parent.name', read_only=True)
    org_type_display = serializers.CharField(
        source='get_org_type_display',
        read_only=True
    )
    is_invite_code_valid = serializers.BooleanField(read_only=True)

    def validate(self, attrs):
        """Validate organization constraints."""
        parent = attrs.get('parent')

        # Prevent circular references
        if parent:
            instance = self.instance
            if instance and instance.pk:
                # Check if parent is a descendant of current org
                if parent.get_all_children().filter(id=instance.pk).exists():
                    raise serializers.ValidationError({
                        'parent': 'Cannot set a descendant organization as parent.'
                    })

        return attrs


class OrganizationTreeSerializer(serializers.ModelSerializer):
    """Serializer for Organization tree representation."""

    children = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'code', 'org_type', 'level', 'path',
            'is_active', 'children'
        ]

    def get_children(self, obj):
        """Get child organizations recursively."""
        children = obj.children.filter(is_deleted=False, is_active=True)
        return OrganizationTreeSerializer(children, many=True).data


class OrganizationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    class Meta:
        model = Organization
        fields = ['id', 'name', 'code', 'org_type', 'is_active', 'level']


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating organizations."""

    class Meta:
        model = Organization
        fields = [
            'name', 'code', 'org_type', 'parent',
            'contact_person', 'contact_phone', 'email', 'address'
        ]

    def validate_code(self, value):
        """Ensure code is unique."""
        instance = self.instance
        queryset = Organization.objects.filter(code=value)
        if instance and instance.pk:
            queryset = queryset.exclude(pk=instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('Organization code must be unique.')
        return value


# =============================================================================
# Department Serializers
# =============================================================================

class DepartmentSerializer(BaseModelSerializer):
    """Serializer for Department CRUD operations."""

    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    leader_name = serializers.CharField(source='leader.real_name', read_only=True, allow_null=True)
    leader_username = serializers.CharField(source='leader.username', read_only=True, allow_null=True)

    class Meta(BaseModelSerializer.Meta):
        model = Department
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'parent', 'parent_name', 'level', 'path',
            'full_path', 'full_path_name', 'leader', 'leader_name',
            'leader_username', 'order', 'is_active',
            'wework_dept_id', 'dingtalk_dept_id', 'feishu_dept_id',
        ]

    def validate(self, attrs):
        """Validate department constraints."""
        parent = attrs.get('parent')

        # Prevent circular references
        if parent:
            instance = self.instance
            if instance and instance.pk:
                # Check if parent is a descendant of current dept
                descendant_ids = instance.get_descendant_ids()
                if parent.id in descendant_ids:
                    raise serializers.ValidationError({
                        'parent': 'Cannot set a descendant department as parent.'
                    })

        return attrs


class DepartmentTreeSerializer(DepartmentSerializer):
    """Serializer for Department tree representation."""

    children = serializers.SerializerMethodField()

    class Meta(DepartmentSerializer.Meta):
        fields = DepartmentSerializer.Meta.fields + ['children']

    def get_children(self, obj):
        """Get child departments recursively."""
        children = obj.children.filter(is_deleted=False, is_active=True)
        return DepartmentTreeSerializer(children, many=True).data


class DepartmentListSerializer(BaseModelSerializer):
    """Lightweight serializer for department list views."""

    leader_name = serializers.CharField(source='leader.real_name', read_only=True, allow_null=True)

    class Meta(BaseModelSerializer.Meta):
        model = Department
        fields = [
            'id', 'code', 'name', 'full_path_name', 'level',
            'leader', 'leader_name', 'is_active', 'order'
        ]


class DepartmentCreateSerializer(BaseModelSerializer):
    """Serializer for creating departments."""

    class Meta(BaseModelSerializer.Meta):
        model = Department
        fields = [
            'code', 'name', 'parent', 'leader', 'order',
            'is_active', 'organization'
        ]


# =============================================================================
# UserDepartment Serializers
# =============================================================================

class UserDepartmentSerializer(BaseModelSerializer):
    """Serializer for UserDepartment CRUD operations."""

    user_name = serializers.CharField(source='user.real_name', read_only=True, allow_null=True)
    user_username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    department_name = serializers.CharField(source='department.full_path_name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = UserDepartment
        fields = BaseModelSerializer.Meta.fields + [
            'user', 'user_name', 'user_username',
            'department', 'department_name', 'department_code',
            'is_primary', 'is_asset_department', 'position', 'is_leader',
            'wework_department_order', 'is_primary_in_wework',
        ]


class UserDepartmentListSerializer(BaseModelSerializer):
    """Lightweight serializer for user department list views."""

    user_name = serializers.CharField(source='user.real_name', read_only=True, allow_null=True)
    department_name = serializers.CharField(source='department.full_path_name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = UserDepartment
        fields = [
            'id', 'user', 'user_name', 'department', 'department_name',
            'is_primary', 'is_leader', 'position'
        ]


class UserDepartmentCreateSerializer(BaseModelSerializer):
    """Serializer for creating user department associations."""

    class Meta(BaseModelSerializer.Meta):
        model = UserDepartment
        fields = [
            'user', 'department', 'is_primary', 'is_asset_department',
            'position', 'is_leader', 'wework_department_order',
            'is_primary_in_wework', 'organization'
        ]


class SetPrimaryDepartmentSerializer(serializers.Serializer):
    """Serializer for setting user's primary department."""

    department_id = serializers.UUIDField(required=True)

    def validate_department_id(self, value):
        """Validate department exists."""
        if not Department.objects.filter(id=value, is_deleted=False).exists():
            raise serializers.ValidationError('Department not found.')
        return value
