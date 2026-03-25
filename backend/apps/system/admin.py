"""
Django Admin configuration for System module.

Provides admin interface for:
- BusinessObject: Business object definitions
- FieldDefinition: Field definitions for custom objects
- ModelFieldDefinition: Field definitions for hardcoded models
- PageLayout: Form and list layout configurations
- DynamicData: Dynamic data records
"""
from django.contrib import admin

from apps.system.models import (
    BusinessObject,
    FieldDefinition,
    ModelFieldDefinition,
    PageLayout,
    DynamicData,
)


@admin.register(BusinessObject)
class BusinessObjectAdmin(admin.ModelAdmin):
    """Admin interface for Business Object."""

    list_display = [
        'code', 'name', 'name_en', 'is_hardcoded',
        'enable_workflow', 'enable_version',
        'field_count', 'layout_count'
    ]
    list_filter = ['is_hardcoded', 'enable_workflow', 'enable_version']
    search_fields = ['code', 'name', 'name_en']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    ordering = ['code']

    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'name_en', 'description')
        }),
        ('Feature Flags', {
            'fields': ('enable_workflow', 'enable_version', 'enable_soft_delete')
        }),
        ('Default Layouts', {
            'fields': ('default_form_layout', 'default_list_layout')
        }),
        ('Hybrid Architecture', {
            'fields': ('is_hardcoded', 'django_model_path', 'table_name')
        }),
        ('Audit', {
            'fields': ('organization', 'is_deleted', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',),
        }),
    )

    def field_count(self, obj):
        """Get number of field definitions."""
        if obj.is_hardcoded:
            return obj.model_fields.filter(is_deleted=False).count()
        return obj.field_definitions.filter(is_deleted=False).count()
    field_count.short_description = 'Fields'

    def layout_count(self, obj):
        """Get number of page layouts."""
        return obj.page_layouts.filter(is_deleted=False).count()
    layout_count.short_description = 'Layouts'


@admin.register(FieldDefinition)
class FieldDefinitionAdmin(admin.ModelAdmin):
    """Admin interface for Field Definition (custom objects)."""

    list_display = [
        'code', 'name', 'business_object', 'field_type',
        'is_required', 'is_readonly', 'show_in_list',
        'sort_order'
    ]
    list_filter = ['field_type', 'is_required', 'is_readonly', 'show_in_list']
    search_fields = ['code', 'name', 'business_object__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['business_object', 'sort_order']


@admin.register(ModelFieldDefinition)
class ModelFieldDefinitionAdmin(admin.ModelAdmin):
    """Admin interface for Model Field Definition (hardcoded models)."""

    list_display = [
        'field_name', 'display_name', 'business_object',
        'field_type', 'django_field_type',
        'is_required', 'is_readonly', 'show_in_list',
        'sort_order'
    ]
    list_filter = ['field_type', 'is_required', 'is_readonly', 'show_in_list']
    search_fields = ['field_name', 'display_name', 'business_object__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['business_object', 'sort_order']


@admin.register(PageLayout)
class PageLayoutAdmin(admin.ModelAdmin):
    """Admin interface for Page Layout."""

    list_display = [
        'layout_code', 'layout_name', 'business_object',
        'layout_type', 'is_default', 'is_active'
    ]
    list_filter = ['layout_type', 'is_default', 'is_active']
    search_fields = ['layout_code', 'layout_name', 'business_object__name']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    ordering = ['business_object', 'layout_type', 'layout_code']

    fieldsets = (
        ('Basic Information', {
            'fields': ('business_object', 'layout_code', 'layout_name', 'layout_type')
        }),
        ('Configuration', {
            'fields': ('layout_config', 'is_default', 'is_active')
        }),
        ('Audit', {
            'fields': ('organization', 'is_deleted', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',),
        }),
    )


@admin.register(DynamicData)
class DynamicDataAdmin(admin.ModelAdmin):
    """Admin interface for Dynamic Data."""

    list_display = [
        'data_no', 'business_object', 'status',
        'created_by', 'created_at'
    ]
    list_filter = ['business_object', 'status']
    search_fields = ['data_no']
    readonly_fields = ['data_no', 'created_at', 'updated_at', 'created_by']
    ordering = ['-created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('business_object', 'data_no', 'status')
        }),
        ('Dynamic Fields', {
            'fields': ('dynamic_fields',),
            'classes': ('collapse',),
        }),
        ('Audit', {
            'fields': ('organization', 'is_deleted', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',),
        }),
    )


# =============================================================================
# PUBLIC SYSTEM MODELS ADMIN
# =============================================================================

from apps.system.models import (
    DictionaryType,
    DictionaryItem,
    SequenceRule,
    SystemConfig,
    SystemFile,
    Tag,
    Comment,
)


class DictionaryItemInline(admin.TabularInline):
    """Inline admin for Dictionary Items within Dictionary Type."""
    model = DictionaryItem
    extra = 1
    fields = ['code', 'name', 'color', 'icon', 'is_default', 'is_active', 'sort_order']
    ordering = ['sort_order', 'code']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)


@admin.register(DictionaryType)
class DictionaryTypeAdmin(admin.ModelAdmin):
    """Admin interface for Dictionary Type with inline items."""

    list_display = ['code', 'name', 'is_system', 'is_active', 'sort_order', 'item_count']
    list_filter = ['is_system', 'is_active']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    ordering = ['sort_order', 'code']
    inlines = [DictionaryItemInline]

    fieldsets = (
        ('Basic information', {
            'fields': ('code', 'name', 'description')
        }),
        ('Settings', {
            'fields': ('is_system', 'is_active', 'sort_order')
        }),
        ('Audit', {
            'fields': ('organization', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',),
        }),
    )

    def item_count(self, obj):
        return obj.items.filter(is_deleted=False).count()
    item_count.short_description = 'Items'


@admin.register(DictionaryItem)
class DictionaryItemAdmin(admin.ModelAdmin):
    """Admin interface for Dictionary Item."""

    list_display = ['code', 'name', 'dictionary_type', 'color', 'is_default', 'is_active', 'sort_order']
    list_filter = ['dictionary_type', 'is_default', 'is_active']
    search_fields = ['code', 'name', 'dictionary_type__code']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    exclude = ['name_en']
    ordering = ['dictionary_type', 'sort_order', 'code']


@admin.register(SequenceRule)
class SequenceRuleAdmin(admin.ModelAdmin):
    """Admin interface for Sequence Rule."""

    list_display = ['code', 'name', 'prefix', 'pattern', 'current_value', 'reset_period', 'is_active']
    list_filter = ['reset_period', 'is_active']
    search_fields = ['code', 'name']
    readonly_fields = ['current_value', 'last_reset_date', 'created_at', 'updated_at', 'created_by']
    ordering = ['code']


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    """Admin interface for System Configuration."""

    list_display = ['config_key', 'name', 'value_type', 'category', 'is_system', 'config_value_preview']
    list_filter = ['value_type', 'category', 'is_system']
    search_fields = ['config_key', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    ordering = ['category', 'config_key']

    def config_value_preview(self, obj):
        return obj.config_value[:50] + '...' if len(obj.config_value) > 50 else obj.config_value
    config_value_preview.short_description = 'Value'


@admin.register(SystemFile)
class SystemFileAdmin(admin.ModelAdmin):
    """Admin interface for System File."""

    list_display = ['file_name', 'file_type', 'file_size_display', 'biz_type', 'created_at']
    list_filter = ['file_type', 'biz_type']
    search_fields = ['file_name', 'description']
    readonly_fields = ['file_hash', 'created_at', 'updated_at', 'created_by']
    ordering = ['-created_at']

    def file_size_display(self, obj):
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / 1024 / 1024:.1f} MB"
    file_size_display.short_description = 'Size'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin interface for Tag."""

    list_display = ['name', 'color', 'biz_type', 'usage_count']
    list_filter = ['biz_type']
    search_fields = ['name', 'description']
    readonly_fields = ['usage_count', 'created_at', 'updated_at', 'created_by']
    ordering = ['-usage_count', 'name']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin interface for Comment."""

    list_display = ['content_preview', 'biz_type', 'biz_id', 'created_by', 'is_pinned', 'created_at']
    list_filter = ['biz_type', 'is_pinned']
    search_fields = ['content', 'biz_type']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    ordering = ['-created_at']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
