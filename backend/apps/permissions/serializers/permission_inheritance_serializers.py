"""
Serializers for PermissionInheritance and DepartmentPermissionInheritance models.
"""
from rest_framework import serializers

from apps.common.serializers.base import BaseModelSerializer
from apps.permissions.models.permission_inheritance import PermissionInheritance
from apps.permissions.models.department_permission_inheritance import DepartmentPermissionInheritance


class PermissionInheritanceSerializer(BaseModelSerializer):
    """
    Serializer for PermissionInheritance - list view.
    """
    parent_role_display = serializers.CharField(
        source='parent_role.name',
        read_only=True,
        allow_null=True
    )
    child_role_display = serializers.CharField(
        source='child_role.name',
        read_only=True,
        allow_null=True
    )
    inheritance_type_display = serializers.CharField(
        source='get_inheritance_type_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = PermissionInheritance
        fields = BaseModelSerializer.Meta.fields + [
            'parent_role',
            'parent_role_display',
            'child_role',
            'child_role_display',
            'inheritance_type',
            'inheritance_type_display',
            'permission_types',
            'is_active',
            'priority',
            'description',
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields


class PermissionInheritanceDetailSerializer(PermissionInheritanceSerializer):
    """
    Detailed serializer for PermissionInheritance.
    """
    parent_role = serializers.SerializerMethodField()
    child_role = serializers.SerializerMethodField()

    class Meta(PermissionInheritanceSerializer.Meta):
        fields = PermissionInheritanceSerializer.Meta.fields

    def get_parent_role(self, obj):
        """Get parent role data."""
        if obj.parent_role:
            return {
                'id': str(obj.parent_role.id),
                'name': obj.parent_role.name,
                'code': obj.parent_role.code,
            }
        return None

    def get_child_role(self, obj):
        """Get child role data."""
        if obj.child_role:
            return {
                'id': str(obj.child_role.id),
                'name': obj.child_role.name,
                'code': obj.child_role.code,
            }
        return None


class PermissionInheritanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating PermissionInheritance."""

    parent_role_code = serializers.CharField(write_only=True, required=False)
    child_role_code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = PermissionInheritance
        fields = [
            'parent_role',
            'child_role',
            'parent_role_code',
            'child_role_code',
            'inheritance_type',
            'permission_types',
            'is_active',
            'priority',
            'description',
        ]

    def validate(self, attrs):
        """Validate that parent and child are different."""
        parent_role = attrs.get('parent_role')
        child_role = attrs.get('child_role')

        # Try to get from codes if not set
        if not parent_role:
            parent_role_code = attrs.get('parent_role_code')
            if parent_role_code:
                from apps.accounts.models import Role
                try:
                    attrs['parent_role'] = Role.objects.get(code=parent_role_code, is_deleted=False)
                except Role.DoesNotExist:
                    raise serializers.ValidationError({
                        'parent_role_code': ['Role with this code does not exist.']
                    })

        if not child_role:
            child_role_code = attrs.get('child_role_code')
            if child_role_code:
                from apps.accounts.models import Role
                try:
                    attrs['child_role'] = Role.objects.get(code=child_role_code, is_deleted=False)
                except Role.DoesNotExist:
                    raise serializers.ValidationError({
                        'child_role_code': ['Role with this code does not exist.']
                    })

        if attrs.get('parent_role') and attrs.get('child_role'):
            if attrs['parent_role'].id == attrs['child_role'].id:
                raise serializers.ValidationError({
                    'non_field_errors': ['Parent and child roles cannot be the same.']
                })

        return attrs

    def to_representation(self, instance):
        """Use detail serializer for response."""
        return PermissionInheritanceDetailSerializer(instance, context=self.context).data


class DepartmentPermissionInheritanceSerializer(BaseModelSerializer):
    """
    Serializer for DepartmentPermissionInheritance - list view.
    """
    source_department_display = serializers.CharField(
        source='source_department.name',
        read_only=True
    )
    target_department_display = serializers.CharField(
        source='target_department.name',
        read_only=True
    )
    inheritance_type_display = serializers.CharField(
        source='get_inheritance_type_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = DepartmentPermissionInheritance
        fields = BaseModelSerializer.Meta.fields + [
            'source_department',
            'source_department_display',
            'target_department',
            'target_department_display',
            'inheritance_type',
            'inheritance_type_display',
            'is_active',
            'allow_override',
            'priority',
            'description',
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields


class DepartmentPermissionInheritanceDetailSerializer(DepartmentPermissionInheritanceSerializer):
    """
    Detailed serializer for DepartmentPermissionInheritance.
    """
    source_department = serializers.SerializerMethodField()
    target_department = serializers.SerializerMethodField()

    class Meta(DepartmentPermissionInheritanceSerializer.Meta):
        fields = DepartmentPermissionInheritanceSerializer.Meta.fields

    def get_source_department(self, obj):
        """Get source department data."""
        if obj.source_department:
            return {
                'id': str(obj.source_department.id),
                'name': obj.source_department.name,
                'code': obj.source_department.code,
            }
        return None

    def get_target_department(self, obj):
        """Get target department data."""
        if obj.target_department:
            return {
                'id': str(obj.target_department.id),
                'name': obj.target_department.name,
                'code': obj.target_department.code,
            }
        return None


class DepartmentPermissionInheritanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating DepartmentPermissionInheritance."""

    source_department_code = serializers.CharField(write_only=True, required=False)
    target_department_code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = DepartmentPermissionInheritance
        fields = [
            'source_department',
            'target_department',
            'source_department_code',
            'target_department_code',
            'inheritance_type',
            'is_active',
            'allow_override',
            'priority',
            'description',
        ]

    def validate(self, attrs):
        """Validate that source and target are different."""
        source_department = attrs.get('source_department')
        target_department = attrs.get('target_department')

        # Try to get from codes if not set
        if not source_department:
            source_department_code = attrs.get('source_department_code')
            if source_department_code:
                from apps.organizations.models import Department
                try:
                    attrs['source_department'] = Department.objects.get(
                        code=source_department_code,
                        is_deleted=False
                    )
                except Department.DoesNotExist:
                    raise serializers.ValidationError({
                        'source_department_code': ['Department with this code does not exist.']
                    })

        if not target_department:
            target_department_code = attrs.get('target_department_code')
            if target_department_code:
                from apps.organizations.models import Department
                try:
                    attrs['target_department'] = Department.objects.get(
                        code=target_department_code,
                        is_deleted=False
                    )
                except Department.DoesNotExist:
                    raise serializers.ValidationError({
                        'target_department_code': ['Department with this code does not exist.']
                    })

        if attrs.get('source_department') and attrs.get('target_department'):
            if attrs['source_department'].id == attrs['target_department'].id:
                raise serializers.ValidationError({
                    'non_field_errors': ['Source and target departments cannot be the same.']
                })

        return attrs

    def to_representation(self, instance):
        """Use detail serializer for response."""
        return DepartmentPermissionInheritanceDetailSerializer(instance, context=self.context).data
