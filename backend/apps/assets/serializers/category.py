"""
Serializers for Asset Category.
"""
from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from apps.assets.models import AssetCategory


class AssetCategorySerializer(BaseModelSerializer):
    """Serializer for AssetCategory CRUD operations."""

    parent_name = serializers.CharField(source='parent.name', read_only=True)
    parent_code = serializers.CharField(source='parent.code', read_only=True)
    depreciation_method_display = serializers.CharField(
        source='get_depreciation_method_display',
        read_only=True
    )
    has_children = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = AssetCategory
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'parent', 'parent_name', 'parent_code', 'full_name',
            'level', 'sort_order', 'is_custom', 'is_active',
            'depreciation_method', 'depreciation_method_display',
            'default_useful_life', 'residual_rate', 'has_children',
        ]
        # Allow parent to be nullable for root categories
        extra_kwargs = {
            'parent': {'required': False, 'allow_null': True}
        }

    def get_has_children(self, obj):
        """Check if category has children."""
        return obj.children.filter(is_deleted=False).exists()

    def validate(self, data):
        """Custom validation."""
        # Check if code already exists (within organization)
        if 'code' in data:
            code = data['code']
            org_id = self.context.get('organization_id')

            if org_id:
                queryset = AssetCategory.objects.filter(
                    organization_id=org_id,
                    code=code,
                    is_deleted=False
                )

                # Exclude current instance for updates
                if self.instance:
                    queryset = queryset.exclude(id=self.instance.id)

                if queryset.exists():
                    raise serializers.ValidationError({
                        'code': 'Category code already exists in this organization.'
                    })

        # Prevent circular reference in parent
        parent = data.get('parent')
        if parent and self.instance:
            if self._is_descendant(parent, self.instance):
                raise serializers.ValidationError({
                    'parent': 'Cannot set a descendant as parent.'
                })

        return data

    def _is_descendant(self, parent, child):
        """Check if parent is a descendant of child (circular reference)."""
        current = child
        while current.parent_id:
            if current.parent_id == parent.id:
                return True
            current = current.parent
        return False


class AssetCategoryTreeSerializer(serializers.Serializer):
    """Serializer for category tree response."""

    id = serializers.UUIDField()
    code = serializers.CharField()
    name = serializers.CharField()
    full_name = serializers.CharField()
    level = serializers.IntegerField()
    is_custom = serializers.BooleanField()
    is_active = serializers.BooleanField()
    depreciation_method = serializers.CharField()
    default_useful_life = serializers.IntegerField()
    residual_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    sort_order = serializers.IntegerField()
    children = serializers.ListField(
        child=serializers.Serializer(),
        required=False
    )


class AssetCategoryCreateSerializer(AssetCategorySerializer):
    """Serializer for creating categories with simplified output."""

    class Meta(AssetCategorySerializer.Meta):
        fields = [
            'id', 'code', 'name', 'parent', 'full_name', 'level',
            'is_custom', 'depreciation_method', 'default_useful_life',
            'residual_rate', 'sort_order', 'is_active'
        ]


class AssetCategoryListSerializer(BaseModelSerializer):
    """Optimized serializer for list views."""

    class Meta(BaseModelSerializer.Meta):
        model = AssetCategory
        fields = [
            'id', 'code', 'name', 'full_name', 'level', 'is_custom',
            'is_active', 'sort_order'
        ]


class AddChildSerializer(serializers.Serializer):
    """Serializer for add_child action."""

    code = serializers.CharField(max_length=50, required=True)
    name = serializers.CharField(max_length=200, required=True)
    depreciation_method = serializers.ChoiceField(
        choices=AssetCategory.DEPRECIATION_METHODS,
        default='straight_line'
    )
    default_useful_life = serializers.IntegerField(default=60)
    residual_rate = serializers.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    sort_order = serializers.IntegerField(default=0)
    is_active = serializers.BooleanField(default=True)
