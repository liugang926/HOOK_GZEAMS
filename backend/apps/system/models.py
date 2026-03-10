"""
Core metadata models for the low-code business object engine.

This module contains the core models that enable dynamic business object
configuration without code changes.

Note: BusinessRule and RuleExecution models are in apps.system.models.business_rule
"""
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from apps.common.models import BaseModel
from apps.common.managers import GlobalMetadataManager


class BusinessObject(BaseModel):
    """
    Business Object - defines a configurable entity.

    Examples: Asset, AssetPickup, AssetTransfer, InventoryTask, etc.

    Inherits from BaseModel:
    - organization: Multi-tenant data isolation (FIELD KEPT for future use)
    - is_deleted: Soft delete support
    - created_at, updated_at: Audit timestamps
    - created_by: User who created this record
    - custom_fields: Additional metadata storage

    Note: Uses GlobalMetadataManager instead of TenantManager because
    BusinessObject definitions are shared across all organizations.
    Individual organizations can customize layouts via PageLayout.
    """

    # Use GlobalMetadataManager - metadata is NOT organization-filtered
    objects = GlobalMetadataManager()
    # Keep all_objects for admin access to all records including deleted
    all_objects = models.Manager()

    # === Basic Information ===
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        db_comment='Business object code (unique identifier)'
    )
    name = models.CharField(
        max_length=100,
        db_comment='Business object name'
    )
    name_en = models.CharField(
        max_length=100,
        blank=True,
        db_comment='English name'
    )
    description = models.TextField(
        blank=True,
        db_comment='Description'
    )

    # === Feature Flags ===
    enable_workflow = models.BooleanField(
        default=False,
        db_comment='Enable workflow/approval process'
    )
    enable_version = models.BooleanField(
        default=True,
        db_comment='Enable version control'
    )
    enable_soft_delete = models.BooleanField(
        default=True,
        db_comment='Enable soft delete for dynamic data'
    )

    # === Default Layouts ===
    default_form_layout = models.ForeignKey(
        'PageLayout',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_for_form',
        db_comment='Default form layout'
    )
    default_list_layout = models.ForeignKey(
        'PageLayout',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_for_list',
        db_comment='Default list layout'
    )

    # === Hybrid Architecture Flags ===
    is_hardcoded = models.BooleanField(
        default=False,
        db_comment='True for core Django models, False for metadata-driven objects'
    )
    django_model_path = models.CharField(
        max_length=200,
        blank=True,
        db_comment='Python path to Django model (e.g., apps.assets.models.Asset)'
    )

    # === Data Table Configuration ===
    table_name = models.CharField(
        max_length=100,
        blank=True,
        db_comment='Custom table name (default: dynamic_data_{code})'
    )

    # === Custom Actions ===
    actions = models.JSONField(
        default=list,
        blank=True,
        db_comment='Custom action definitions (e.g., buttons, triggers)'
    )

    # === Menu Configuration ===
    menu_category = models.CharField(
        max_length=50,
        blank=True,
        db_comment='Menu category for automated routing'
    )
    is_menu_hidden = models.BooleanField(
        default=False,
        db_comment='Hide from automated sidebar menu'
    )
    menu_config = models.JSONField(
        default=dict,
        blank=True,
        db_comment='Menu configuration (icon, group, order, show_in_menu)'
    )

    class Meta:
        db_table = 'business_objects'
        verbose_name = 'Business Object'
        verbose_name_plural = 'Business Objects'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['organization', 'code']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_table_name(self):
        """Get the table name for dynamic data storage."""
        return self.table_name or f"dynamic_data_{self.code.lower()}"

    @property
    def field_count(self):
        """Return the number of field definitions."""
        if self.is_hardcoded:
            return self.model_fields.count()
        return self.field_definitions.count()

    @property
    def layout_count(self):
        """Return the number of page layouts."""
        return self.page_layouts.count()

    def get_django_model(self):
        """Get the Django model class for hardcoded objects."""
        if not self.is_hardcoded or not self.django_model_path:
            return None
        try:
            from django.utils.module_loading import import_string
            return import_string(self.django_model_path)
        except ImportError:
            return None


class FieldDefinition(BaseModel):
    """
    Field Definition - defines a field in a business object.

    Supports 20+ field types including text, number, select, user reference,
    formula calculation, and sub-table (master-detail).

    Inherits from BaseModel for audit trails.
    Uses GlobalMetadataManager because field definitions are shared
    across all organizations for each BusinessObject.

    Note: Individual organizations can customize field display via
    PageLayout configuration, not by modifying FieldDefinition.
    """

    # Use GlobalMetadataManager - field definitions are NOT organization-filtered
    objects = GlobalMetadataManager()
    # Keep all_objects for admin access
    all_objects = models.Manager()

    # Field Type Choices
    FIELD_TYPE_CHOICES = [
        # Basic types
        ('text', 'Text'),
        ('textarea', 'Text Area'),
        ('number', 'Number'),
        ('currency', 'Currency'),
        ('percent', 'Percentage'),
        ('date', 'Date'),
        ('datetime', 'Date Time'),
        ('boolean', 'Boolean'),
        # Selection types
        ('select', 'Select'),
        ('multi_select', 'Multi Select'),
        ('radio', 'Radio'),
        ('checkbox', 'Checkbox'),
        # Reference types
        ('user', 'User'),
        ('department', 'Department'),
        ('reference', 'Reference'),
        ('asset', 'Asset'),
        # Advanced types
        ('formula', 'Formula'),
        ('sub_table', 'Sub Table'),
        ('file', 'File'),
        ('image', 'Image'),
        ('rich_text', 'Rich Text'),
        ('qr_code', 'QR Code'),
        ('barcode', 'Barcode'),
        ('location', 'Location'),
    ]

    # === Association ===
    business_object = models.ForeignKey(
        BusinessObject,
        on_delete=models.CASCADE,
        related_name='field_definitions',
        db_comment='Business object this field belongs to'
    )

    # === Basic Information ===
    code = models.CharField(
        max_length=50,
        db_comment='Field code (unique within business object)'
    )
    name = models.CharField(
        max_length=100,
        db_comment='Field display name'
    )

    # === Field Type ===
    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPE_CHOICES,
        default='text',
        db_comment='Field type'
    )

    # === Validation Flags ===
    is_required = models.BooleanField(
        default=False,
        db_comment='Is field required'
    )
    is_unique = models.BooleanField(
        default=False,
        db_comment='Is field value unique'
    )
    is_readonly = models.BooleanField(
        default=False,
        db_comment='Is field read-only'
    )
    is_system = models.BooleanField(
        default=False,
        db_comment='Is system field (cannot be deleted)'
    )
    is_searchable = models.BooleanField(
        default=False,
        db_comment='Is field searchable in global search'
    )

    # === Display Configuration ===
    show_in_list = models.BooleanField(
        default=False,
        db_comment='Show in list view'
    )
    show_in_detail = models.BooleanField(
        default=True,
        db_comment='Show in detail view'
    )
    show_in_filter = models.BooleanField(
        default=False,
        db_comment='Show as filter option'
    )
    show_in_form = models.BooleanField(
        default=True,
        db_comment='Show in create/edit forms'
    )
    sort_order = models.IntegerField(
        default=0,
        db_comment='Display order'
    )

    # === Reverse Relation Handling ===
    # These fields identify reverse relations (e.g., maintenance_records from Maintenance -> Asset)
    is_reverse_relation = models.BooleanField(
        default=False,
        db_comment='True if this field represents a reverse relation (related_name)'
    )
    reverse_relation_model = models.CharField(
        max_length=200,
        blank=True,
        db_comment='Path to model that owns this relation (e.g., apps.lifecycle.models.Maintenance)'
    )
    reverse_relation_field = models.CharField(
        max_length=100,
        blank=True,
        db_comment='FK field name on related model (e.g., asset)'
    )
    RELATION_DISPLAY_CHOICES = [
        ('inline_editable', 'Inline Editable Table'),
        ('inline_readonly', 'Inline Read-Only Table'),
        ('tab_readonly', 'Tab Read-Only Table'),
        ('hidden', 'Hidden'),
    ]
    relation_display_mode = models.CharField(
        max_length=20,
        choices=RELATION_DISPLAY_CHOICES,
        default='tab_readonly',
        db_comment='How to display reverse relations'
    )

    # === Column Display Configuration (List View) ===
    column_width = models.IntegerField(
        null=True,
        blank=True,
        db_comment='Column width in pixels'
    )
    min_column_width = models.IntegerField(
        null=True,
        blank=True,
        db_comment='Minimum column width'
    )
    fixed = models.CharField(
        max_length=10,
        choices=[('left', 'Left'), ('right', 'Right')],
        blank=True,
        db_comment='Fixed column position'
    )
    sortable = models.BooleanField(
        default=True,
        db_comment='Is column sortable'
    )

    # === Default Value ===
    default_value = models.TextField(
        blank=True,
        db_comment='Default value (supports variables: {current_user}, {today}, {now})'
    )

    # === Options Configuration (for select, multi_select, etc.) ===
    options = models.JSONField(
        default=list,
        blank=True,
        db_comment='Options for select fields: [{"value": "v1", "label": "Option1"}]'
    )

    # === Reference Configuration ===
    reference_object = models.CharField(
        max_length=50,
        blank=True,
        db_comment='Referenced business object code (for reference type)'
    )
    reference_display_field = models.CharField(
        max_length=50,
        default='name',
        blank=True,
        db_comment='Display field for reference'
    )
    reference_filters = models.JSONField(
        default=dict,
        blank=True,
        db_comment='Filters for reference fields: {"department": "current_user.department"}'
    )

    # === Number Field Configuration ===
    decimal_places = models.IntegerField(
        default=0,
        db_comment='Decimal places for number/currency fields'
    )
    min_value = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True,
        db_comment='Minimum value'
    )
    max_value = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True,
        db_comment='Maximum value'
    )

    # === Text Field Configuration ===
    max_length = models.IntegerField(
        default=255,
        db_comment='Maximum length for text fields'
    )
    placeholder = models.CharField(
        max_length=200,
        blank=True,
        db_comment='Placeholder text'
    )
    regex_pattern = models.CharField(
        max_length=500,
        blank=True,
        db_comment='Regex validation pattern'
    )

    # === Formula Field Configuration ===
    formula = models.TextField(
        blank=True,
        db_comment='Formula expression (e.g., {field1} + {field2})'
    )

    # === Sub Table Configuration ===
    sub_table_fields = models.JSONField(
        default=list,
        blank=True,
        db_comment='Sub-table field definitions'
    )

    # === Validation Logic ===
    validation_rules = models.JSONField(
        default=list,
        blank=True,
        db_comment='Advanced validation rules (JSON logic)'
    )

    class Meta:
        db_table = 'field_definitions'
        verbose_name = 'Field Definition'
        verbose_name_plural = 'Field Definitions'
        unique_together = [['organization', 'business_object', 'code']]
        indexes = [
            models.Index(fields=['organization', 'business_object', 'code']),
            models.Index(fields=['organization', 'field_type']),
            models.Index(fields=['sort_order']),
        ]

    def __str__(self):
        return f"{self.business_object.name}.{self.code} ({self.name})"

    def clean(self):
        """Validate field definition constraints."""
        # Reference type must have reference_object
        if self.field_type == 'reference' and not self.reference_object:
            raise ValidationError({
                'reference_object': 'Reference field must specify a reference_object.'
            })

        # Formula type must have formula
        if self.field_type == 'formula' and not self.formula:
            raise ValidationError({
                'formula': 'Formula field must specify a formula expression.'
            })

        # Sub table type must have sub_table_fields
        if self.field_type == 'sub_table' and not self.sub_table_fields:
            raise ValidationError({
                'sub_table_fields': 'Sub table field must specify sub_table_fields.'
            })


class ModelFieldDefinition(BaseModel):
    """
    Model Field Definition - exposes fields from hardcoded Django models.

    This model stores metadata about fields of hardcoded Django models,
    allowing them to be visible and selectable in the low-code configuration UI.

    Unlike FieldDefinition (which is for low-code dynamic fields),
    ModelFieldDefinition is read-only and auto-generated from Django model metadata.

    Uses GlobalMetadataManager for cross-organization metadata access.
    """

    # Use GlobalMetadataManager for cross-organization access
    objects = GlobalMetadataManager()
    all_objects = models.Manager()  # For accessing soft-deleted records

    # Field Type Mapping (Django to Metadata)
    DJANGO_FIELD_TYPE_MAP = {
        'CharField': 'text',
        'TextField': 'textarea',
        'IntegerField': 'number',
        'BigIntegerField': 'number',
        'DecimalField': 'currency',
        'FloatField': 'number',
        'DateField': 'date',
        'DateTimeField': 'datetime',
        'TimeField': 'time',
        'BooleanField': 'boolean',
        'NullBooleanField': 'boolean',
        'ForeignKey': 'reference',
        'ManyToManyField': 'multi_select',
        'OneToOneField': 'reference',
        'UUIDField': 'text',
        'EmailField': 'email',
        'URLField': 'url',
        'FileField': 'file',
        'ImageField': 'image',
        'JSONField': 'json',
    }

    # === Association ===
    business_object = models.ForeignKey(
        BusinessObject,
        on_delete=models.CASCADE,
        related_name='model_fields',
        db_comment='Business object (hardcoded) this field belongs to'
    )

    # === Basic Information ===
    field_name = models.CharField(
        max_length=100,
        db_comment='Actual Django field name'
    )
    display_name = models.CharField(
        max_length=100,
        db_comment='Field display name'
    )
    display_name_en = models.CharField(
        max_length=100,
        blank=True,
        db_comment='English display name'
    )

    # === Field Type ===
    field_type = models.CharField(
        max_length=50,
        db_comment='Mapped field type (see DJANGO_FIELD_TYPE_MAP)'
    )
    django_field_type = models.CharField(
        max_length=50,
        db_comment='Original Django field type (e.g., CharField)'
    )

    # === Validation Flags ===
    is_required = models.BooleanField(
        default=False,
        db_comment='Is field required (not null)'
    )
    is_readonly = models.BooleanField(
        default=False,
        db_comment='Is field read-only (not editable)'
    )
    is_editable = models.BooleanField(
        default=True,
        db_comment='Is field editable in forms'
    )
    is_unique = models.BooleanField(
        default=False,
        db_comment='Is field value unique'
    )

    # === Display Configuration ===
    show_in_list = models.BooleanField(
        default=True,
        db_comment='Show in list view'
    )
    show_in_detail = models.BooleanField(
        default=True,
        db_comment='Show in detail view'
    )
    show_in_form = models.BooleanField(
        default=True,
        db_comment='Show in create/edit forms'
    )
    sort_order = models.IntegerField(
        default=0,
        db_comment='Display order'
    )

    # === Reference Configuration (for ForeignKey) ===
    reference_model_path = models.CharField(
        max_length=200,
        blank=True,
        db_comment='Referenced model path for ForeignKey fields'
    )
    reference_display_field = models.CharField(
        max_length=50,
        default='name',
        blank=True,
        db_comment='Display field for referenced model'
    )

    # === Number Field Configuration ===
    decimal_places = models.IntegerField(
        null=True,
        blank=True,
        db_comment='Decimal places for number fields'
    )
    max_digits = models.IntegerField(
        null=True,
        blank=True,
        db_comment='Maximum digits for decimal fields'
    )

    # === Text Field Configuration ===
    max_length = models.IntegerField(
        null=True,
        blank=True,
        db_comment='Maximum length for text fields'
    )

    class Meta:
        db_table = 'model_field_definitions'
        verbose_name = 'Model Field Definition'
        verbose_name_plural = 'Model Field Definitions'
        unique_together = [['organization', 'business_object', 'field_name']]
        indexes = [
            models.Index(fields=['organization', 'business_object', 'field_name']),
            models.Index(fields=['organization', 'business_object', 'sort_order']),
            models.Index(fields=['field_type']),
        ]

    def __str__(self):
        return f"{self.business_object.name}.{self.field_name} ({self.display_name})"

    @classmethod
    def get_metadata_field_type(cls, field):
        """
        Resolve a Django model field into a metadata field_type.

        Shared helper to keep field type mapping consistent across
        metadata sync and ModelFieldDefinition creation.
        """
        from django.db import models as django_models

        django_type = field.__class__.__name__
        field_name_lower = field.name.lower()

        # QR code fields: CharField with 'qr' and 'code' in name
        if isinstance(field, django_models.CharField):
            if 'qr' in field_name_lower and 'code' in field_name_lower:
                return 'qr_code'

        # JSONField special handling for image/file storage
        if isinstance(field, django_models.JSONField):
            if 'image' in field_name_lower or 'photo' in field_name_lower or 'picture' in field_name_lower:
                return 'image'
            if 'attachment' in field_name_lower or 'file' in field_name_lower or 'document' in field_name_lower:
                return 'file'

        # ForeignKey special handling
        if isinstance(field, django_models.ForeignKey):
            related_name = getattr(field.related_model, '__name__', '')
            if related_name == 'User':
                return 'user'
            if related_name == 'Department' or 'Organization' in related_name:
                return 'department'
            if related_name == 'Location':
                return 'location'
            if related_name == 'Asset':
                return 'asset'
            return 'reference'

        # Choices should be rendered as select
        if hasattr(field, 'choices') and field.choices:
            return 'select'

        return cls.DJANGO_FIELD_TYPE_MAP.get(django_type, 'text')

    @classmethod
    def from_django_field(cls, business_object, field):
        """
        Create ModelFieldDefinition from a Django model field.

        Args:
            business_object: BusinessObject instance (must be hardcoded)
            field: Django model field instance

        Returns:
            ModelFieldDefinition instance (not saved)
        """
        from django.db import models as django_models

        # Get Django field type name
        django_type = field.__class__.__name__

        # Map to metadata field type
        field_type = cls.get_metadata_field_type(field)

        # Handle ForeignKey special case
        reference_path = ''
        reference_display_field = 'name'
        if isinstance(field, django_models.ForeignKey):
            reference_path = f"{field.related_model.__module__}.{field.related_model.__name__}"
            related_name = getattr(field.related_model, '__name__', '')
            if related_name == 'User':
                reference_display_field = 'username'
            elif related_name == 'Location':
                reference_display_field = 'path'

        return cls(
            business_object=business_object,
            field_name=field.name,
            display_name=getattr(field, 'verbose_name', field.name) or field.name,
            display_name_en='',  # Can be set via translation
            field_type=field_type,
            django_field_type=django_type,
            is_required=not field.null and not field.blank,
            is_readonly=not field.editable,
            is_editable=field.editable,
            is_unique=getattr(field, 'unique', False),
            reference_model_path=reference_path,
            reference_display_field=reference_display_field,
            decimal_places=getattr(field, 'decimal_places', None),
            max_digits=getattr(field, 'max_digits', None),
            max_length=getattr(field, 'max_length', None),
        )


class ObjectRelationDefinition(BaseModel):
    """
    Object Relation Definition - unified relation contract for runtime pages.

    Supports:
    - direct_fk: target object has a direct FK/OneToOne to parent object
    - through_line_item: target object is connected through an intermediate object
    - derived_query: target object is resolved by comparing two key fields
    """

    objects = GlobalMetadataManager()
    all_objects = models.Manager()

    RELATION_KIND_CHOICES = [
        ('direct_fk', 'Direct FK'),
        ('through_line_item', 'Through Line Item'),
        ('derived_query', 'Derived Query'),
    ]

    DISPLAY_MODE_CHOICES = [
        ('inline_editable', 'Inline Editable'),
        ('inline_readonly', 'Inline Readonly'),
        ('tab_readonly', 'Tab Readonly'),
        ('hidden', 'Hidden'),
    ]

    relation_code = models.CharField(
        max_length=80,
        db_comment='Stable relation code (unique within parent object)'
    )
    parent_object_code = models.CharField(
        max_length=50,
        db_index=True,
        db_comment='Parent business object code'
    )
    target_object_code = models.CharField(
        max_length=50,
        db_index=True,
        db_comment='Target business object code'
    )
    relation_kind = models.CharField(
        max_length=30,
        choices=RELATION_KIND_CHOICES,
        default='direct_fk',
        db_comment='Relation strategy kind'
    )

    # direct_fk
    target_fk_field = models.CharField(
        max_length=100,
        blank=True,
        db_comment='FK field on target model for direct_fk'
    )

    # through_line_item
    through_object_code = models.CharField(
        max_length=50,
        blank=True,
        db_comment='Intermediate business object code for through relation'
    )
    through_parent_fk_field = models.CharField(
        max_length=100,
        blank=True,
        db_comment='FK field on through model pointing to parent object'
    )
    through_target_fk_field = models.CharField(
        max_length=100,
        blank=True,
        db_comment='FK field on through model pointing to target object'
    )

    # derived_query
    derived_parent_key_field = models.CharField(
        max_length=100,
        blank=True,
        db_comment='Field on parent object used as derived query key'
    )
    derived_target_key_field = models.CharField(
        max_length=100,
        blank=True,
        db_comment='Field on target object used as derived query key'
    )

    # display metadata (localizable through existing translation framework)
    relation_name = models.CharField(
        max_length=120,
        blank=True,
        db_comment='Display name override'
    )
    relation_name_en = models.CharField(
        max_length=120,
        blank=True,
        db_comment='English display name override'
    )
    display_mode = models.CharField(
        max_length=20,
        choices=DISPLAY_MODE_CHOICES,
        default='inline_readonly',
        db_comment='Runtime display mode'
    )

    DISPLAY_TIER_CHOICES = [
        ('L1', 'Line Item (Inline in Details)'),
        ('L2', 'Business Related (Default)'),
        ('L3', 'Extended Related (Collapsed)'),
    ]
    display_tier = models.CharField(
        max_length=2,
        choices=DISPLAY_TIER_CHOICES,
        default='L2',
        db_comment='Display tier: L1=inline detail, L2=related tab, L3=collapsed'
    )
    sort_order = models.IntegerField(
        default=0,
        db_comment='Display order within parent object'
    )
    is_active = models.BooleanField(
        default=True,
        db_comment='Whether relation is active'
    )
    extra_config = models.JSONField(
        default=dict,
        blank=True,
        db_comment='Additional relation options'
    )

    class Meta:
        db_table = 'object_relation_definitions'
        verbose_name = 'Object Relation Definition'
        verbose_name_plural = 'Object Relation Definitions'
        unique_together = [['parent_object_code', 'relation_code']]
        indexes = [
            models.Index(fields=['parent_object_code', 'sort_order']),
            models.Index(fields=['parent_object_code', 'is_active']),
            models.Index(fields=['target_object_code']),
            models.Index(fields=['relation_kind']),
        ]

    def __str__(self):
        return f"{self.parent_object_code}.{self.relation_code} -> {self.target_object_code}"


class PageLayout(BaseModel):
    """
    Page Layout - defines UI layout for forms and lists.

    Supports tabbed sections, column configurations, and field
    visibility rules.

    Inherits from BaseModel for audit trails.
    Uses GlobalMetadataManager because while organizations CAN
    have custom layouts, the base layout definitions are global.

    Organization-specific customization is handled via the
    organization ForeignKey on this model.
    """

    # Use GlobalMetadataManager - layouts are NOT organization-filtered by default
    # The organization field allows filtering for org-specific layouts
    objects = GlobalMetadataManager()
    all_objects = models.Manager()

    # Layout Mode Choices - New unified system (3 modes)
    # - edit: Form layout for creating/editing records (includes legacy form + detail)
    # - readonly: Read-only detail view for viewing records
    # - search: Search form with horizontal layout
    LAYOUT_MODE_CHOICES = [
        ('edit', 'Edit'),
        ('readonly', 'Readonly'),
        ('search', 'Search'),
    ]

    # Legacy Layout Type Choices - Kept for backward compatibility
    # @deprecated Use LAYOUT_MODE_CHOICES instead
    # Mapping: form->edit, detail->readonly, list->(auto-generated), search->search
    LAYOUT_TYPE_CHOICES = [
        ('form', 'Form'),
        ('list', 'List'),
        ('detail', 'Detail'),
        ('search', 'Search'),
    ]

    # Legacy type to mode mapping
    _LEGACY_TYPE_TO_MODE = {
        'form': 'edit',
        'detail': 'readonly',
        'list': 'edit',  # List layouts are auto-generated from FieldDefinition
        'search': 'search',
    }

    # Status Choices
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    # === Association ===
    business_object = models.ForeignKey(
        BusinessObject,
        on_delete=models.CASCADE,
        related_name='page_layouts',
        db_comment='Business object this layout belongs to'
    )

    # === Basic Information ===
    layout_code = models.CharField(
        max_length=50,
        db_comment='Layout code (unique within business object)'
    )
    layout_name = models.CharField(
        max_length=100,
        db_comment='Layout display name'
    )
    layout_type = models.CharField(
        max_length=20,
        choices=LAYOUT_TYPE_CHOICES,
        default='form',
        db_comment='Layout type (deprecated: use mode instead)'
    )
    # New view mode choices (Dual Mode Layout)
    VIEW_MODE_CHOICES = [
        ('Detail', 'Detail View'),
        ('Compact', 'Compact View'),
    ]
    
    # New mode field - use this instead of layout_type
    mode = models.CharField(
        max_length=20,
        choices=LAYOUT_MODE_CHOICES,
        default='edit',
        blank=True,
        db_comment='Layout display mode (edit/readonly/search)'
    )
    view_mode = models.CharField(
        max_length=20,
        choices=VIEW_MODE_CHOICES,
        default='Detail',
        db_comment='View mode (Detail or Compact)'
    )
    description = models.TextField(
        blank=True,
        db_comment='Layout description'
    )

    # === Layout Configuration ===
    layout_config = models.JSONField(
        default=dict,
        db_comment='JSON layout configuration'
    )

    # === Layout Priority & Context ===
    # Layout priority determines which layout to apply when multiple exist
    PRIORITY_CHOICES = [
        ('user', 'User Level'),      # User personal preference
        ('role', 'Role Level'),      # Role-based layout
        ('org', 'Organization Level'),  # Organization-specific
        ('global', 'Global Level'),   # System-wide custom layout
        ('default', 'Default Layout'),  # Auto-generated from FieldDefinition
    ]
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='global',
        db_comment='Layout priority level (user > role > org > global > default)'
    )

    # Context type for more granular layout control
    CONTEXT_TYPE_CHOICES = [
        ('form_create', 'Create Form'),
        ('form_edit', 'Edit Form'),
        ('detail', 'Detail View'),
        ('list', 'List View'),
        ('search', 'Search Form'),
    ]
    context_type = models.CharField(
        max_length=20,
        choices=CONTEXT_TYPE_CHOICES,
        blank=True,
        db_comment='Specific context within layout_type (e.g., form_create vs form_edit)'
    )

    # === Differential Configuration ===
    # Stores only changes from default layout (merge pattern)
    # Default layout is auto-generated from FieldDefinition.sort_order
    diff_config = models.JSONField(
        default=dict,
        db_comment='''
        Differential configuration storing only changes from default layout.
        Structure:
        {
            "fieldOrder": ["code", "name", "category"],  // Custom sort order
            "sections": [
                {
                    "id": "section_basic",
                    "fields": [
                        {
                            "fieldCode": "code",
                            "span": 24,           // Custom column span
                            "readonly": true,     // Override field definition
                            "visible": false,     // Hide field
                            "required": true      // Override required
                        }
                    ]
                }
            ]
        }
        '''
    )

    # === Status and Version ===
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_comment='Layout status'
    )
    version = models.CharField(
        max_length=20,
        default='1.0.0',
        db_comment='Version number'
    )
    parent_version = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        db_comment='Parent version for version tracking'
    )

    # === Display Settings ===
    is_default = models.BooleanField(
        default=False,
        db_comment='Is this the default layout for its type'
    )
    is_active = models.BooleanField(
        default=True,
        db_comment='Is layout active'
    )

    # === Publishing Info ===
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        db_comment='Publication timestamp'
    )
    published_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='published_layouts',
        db_comment='User who published this layout'
    )

    class Meta:
        db_table = 'page_layouts'
        verbose_name = 'Page Layout'
        verbose_name_plural = 'Page Layouts'
        unique_together = [['organization', 'business_object', 'layout_code']]
        indexes = [
            models.Index(fields=['organization', 'business_object', 'layout_code']),
            models.Index(fields=['organization', 'business_object', 'layout_type']),
            models.Index(fields=['organization', 'business_object', 'layout_type', 'is_default']),
            models.Index(fields=['is_active']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.business_object.name}.{self.layout_code} ({self.layout_name})"

    @property
    def effective_mode(self) -> str:
        """
        Get the effective layout mode.
        Returns the mode field if set, otherwise derives from legacy layout_type.
        """
        if self.mode:
            return self.mode
        # Auto-derive mode from legacy layout_type for backward compatibility
        return self._LEGACY_TYPE_TO_MODE.get(self.layout_type, 'edit')

    def save(self, *args, **kwargs):
        """
        Override save to auto-set mode from layout_type for backward compatibility.
        If mode is not explicitly set, derive it from layout_type.
        """
        if not self.mode:
            self.mode = self._LEGACY_TYPE_TO_MODE.get(self.layout_type, 'edit')
        super().save(*args, **kwargs)

    def clean(self):
        """Validate layout configuration."""
        # Get effective mode for validation
        effective_mode = self.effective_mode

        # All modes now use sections-based configuration
        if effective_mode in ('edit', 'readonly') and not self.layout_config.get('sections'):
            raise ValidationError({
                'layout_config': 'Layout must contain sections.'
            })

        # Search mode also uses sections but with horizontal layout
        if effective_mode == 'search' and not self.layout_config.get('sections'):
            # Search layouts can be empty (will use default)
            pass

    def publish(self, user):
        """
        Publish the layout.

        Args:
            user: User who is publishing the layout
        """
        from django.utils import timezone

        # If already published, save parent version
        if self.status == 'published':
            self.parent_version = self.version

        # Update version
        if self.parent_version:
            major, minor, _ = self.parent_version.split('.')
            self.version = f"{major}.{int(minor) + 1}.0"
        else:
            self.version = "1.0.0"

        # Update status
        self.status = 'published'
        self.published_at = timezone.now()
        self.published_by = user
        self.save()

        # Create history record
        LayoutHistory.objects.create(
            layout=self,
            version=self.version,
            config_snapshot=self.layout_config,
            published_by=user,
            action='publish'
        )


class LayoutHistory(BaseModel):
    """
    Layout History - tracks version history of layouts.

    Stores snapshots of layout configurations for each published version,
    enabling rollback and comparison between versions.

    Inherits from BaseModel for organization isolation and audit trails.
    """

    # Action Choices
    ACTION_CHOICES = [
        ('publish', 'Publish'),
        ('update', 'Update'),
        ('rollback', 'Rollback'),
    ]

    # === Association ===
    layout = models.ForeignKey(
        PageLayout,
        on_delete=models.CASCADE,
        related_name='histories',
        db_comment='Associated layout'
    )

    # === Version Info ===
    version = models.CharField(
        max_length=20,
        db_comment='Version number'
    )
    config_snapshot = models.JSONField(
        db_comment='Configuration snapshot at this version'
    )

    # === Publishing Info ===
    published_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='layout_histories',
        db_comment='User who created this version'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        default='publish',
        db_comment='Action that created this history entry'
    )

    # === Change Summary ===
    change_summary = models.TextField(
        blank=True,
        db_comment='Summary of changes in this version'
    )

    class Meta:
        db_table = 'layout_histories'
        verbose_name = 'Layout History'
        verbose_name_plural = 'Layout Histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['layout', 'version']),
            models.Index(fields=['layout', '-created_at']),
        ]

    def __str__(self):
        return f"{self.layout.layout_name} - {self.version}"


class DynamicData(BaseModel):
    """
    Dynamic Data - stores actual data for business objects.

    Uses PostgreSQL JSONB (dynamic_fields) to store flexible,
    schema-less data based on field definitions.

    Inherits from BaseModel for organization isolation and audit trails.
    """

    # === Association ===
    business_object = models.ForeignKey(
        BusinessObject,
        on_delete=models.CASCADE,
        related_name='dynamic_data_set',
        db_comment='Business object this data belongs to'
    )

    # === Data Number ===
    data_no = models.CharField(
        max_length=50,
        db_index=True,
        db_comment='Auto-generated data number (e.g., ASSET202401010001)'
    )

    # === Status ===
    status = models.CharField(
        max_length=50,
        default='draft',
        db_index=True,
        db_comment='Data status (draft, submitted, approved, etc.)'
    )

    # === Dynamic Fields Data ===
    dynamic_fields = models.JSONField(
        default=dict,
        db_comment='Dynamic field data stored as PostgreSQL JSONB'
    )

    # === Additional Metadata ===
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_comment='Submission timestamp'
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        db_comment='Approval timestamp'
    )
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_dynamic_data',
        db_comment='User who approved this data'
    )

    class Meta:
        db_table = 'dynamic_data'
        verbose_name = 'Dynamic Data'
        verbose_name_plural = 'Dynamic Data'
        indexes = [
            models.Index(fields=['organization', 'business_object']),
            models.Index(fields=['organization', 'business_object', 'created_by']),
            models.Index(fields=['organization', 'business_object', 'status']),
            models.Index(fields=['data_no']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.business_object.name} - {self.data_no}"

    def get_field_value(self, field_code):
        """
        Get value of a specific field.

        Args:
            field_code: Field code to retrieve

        Returns:
            Field value or None if not found
        """
        return self.dynamic_fields.get(field_code)

    def set_field_value(self, field_code, value):
        """
        Set value of a specific field.

        Args:
            field_code: Field code to set
            value: Value to set
        """
        self.dynamic_fields[field_code] = value

    def get_sub_table_data(self, field_code):
        """
        Get sub-table data for a specific field.

        Args:
            field_code: Sub-table field code

        Returns:
            List of sub-table rows (queryset of DynamicSubTableData)
        """
        field_def = self.business_object.field_definitions.filter(
            code=field_code,
            field_type='sub_table'
        ).first()

        if not field_def:
            return []

        return DynamicSubTableData.objects.filter(
            parent_data=self,
            field_definition=field_def
        ).order_by('row_order')


class DynamicSubTableData(BaseModel):
    """
    Dynamic Sub-Table Data - stores row data for sub-table fields.

    This model enables master-detail relationships within dynamic data.
    Each row belongs to a parent DynamicData record and a specific
    FieldDefinition (sub-table field).

    Inherits from BaseModel for organization isolation and audit trails.
    """

    # === Association ===
    parent_data = models.ForeignKey(
        DynamicData,
        on_delete=models.CASCADE,
        related_name='sub_table_rows',
        db_comment='Parent dynamic data record'
    )
    field_definition = models.ForeignKey(
        FieldDefinition,
        on_delete=models.CASCADE,
        related_name='sub_table_data',
        db_comment='Field definition (sub-table type)'
    )

    # === Row Ordering ===
    row_order = models.IntegerField(
        default=0,
        db_comment='Row display order'
    )

    # === Row Data ===
    row_data = models.JSONField(
        default=dict,
        db_comment='Row data stored as PostgreSQL JSONB'
    )

    class Meta:
        db_table = 'dynamic_sub_table_data'
        verbose_name = 'Dynamic Sub-Table Data'
        verbose_name_plural = 'Dynamic Sub-Table Data'
        unique_together = [['parent_data', 'field_definition', 'row_order']]
        indexes = [
            models.Index(fields=['organization', 'parent_data', 'field_definition']),
            models.Index(fields=['parent_data', 'row_order']),
        ]

    def __str__(self):
        return f"{self.parent_data.data_no} - {self.field_definition.code} - Row {self.row_order}"

    def get_cell_value(self, field_code):
        """
        Get value of a cell in this row.

        Args:
            field_code: Field code within sub-table

        Returns:
            Cell value or None if not found
        """
        return self.row_data.get(field_code)

    def set_cell_value(self, field_code, value):
        """
        Set value of a cell in this row.

        Args:
            field_code: Field code within sub-table
            value: Value to set
        """
        self.row_data[field_code] = value


# =============================================================================
# PUBLIC SYSTEM MODELS
# =============================================================================
# These models provide foundational functionality used across all business modules.
# They enable dynamic configuration without code changes.


class DictionaryType(BaseModel):
    """
    Dictionary Type - defines a category of dictionary items.

    Examples: ASSET_STATUS, UNIT, ASSET_BRAND, INVENTORY_DISCREPANCY_TYPE

    Benefits:
    - Dynamic configuration of options without code changes
    - Multi-tenant support (organization-specific dictionaries)
    - Audit trail for all changes

    Inherits from BaseModel for organization isolation and audit trails.
    Uses GlobalMetadataManager because dictionary types are global metadata
    that can be shared across organizations.
    """

    # Use GlobalMetadataManager - metadata is NOT organization-filtered
    objects = GlobalMetadataManager()
    # Keep all_objects for admin access
    all_objects = models.Manager()

    code = models.CharField(
        max_length=50,
        db_index=True,
        db_comment='Dictionary type code (e.g., ASSET_STATUS)'
    )
    name = models.CharField(
        max_length=100,
        db_comment='Display name'
    )
    name_en = models.CharField(
        max_length=100,
        blank=True,
        db_comment='English name'
    )
    description = models.TextField(
        blank=True,
        db_comment='Description'
    )
    is_system = models.BooleanField(
        default=False,
        db_comment='System dictionary (cannot be deleted by users)'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        db_comment='Is this dictionary type active'
    )
    sort_order = models.IntegerField(
        default=0,
        db_comment='Display order'
    )

    class Meta:
        db_table = 'dictionary_types'
        verbose_name = 'Dictionary Type'
        verbose_name_plural = 'Dictionary Types'
        unique_together = [['organization', 'code']]
        ordering = ['sort_order', 'code']
        indexes = [
            models.Index(fields=['organization', 'code']),
            models.Index(fields=['organization', 'is_active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class DictionaryItem(BaseModel):
    """
    Dictionary Item - a single option within a dictionary type.

    Examples: For ASSET_STATUS: in_use, idle, maintenance, scrapped

    Inherits from BaseModel for organization isolation and audit trails.
    Uses GlobalMetadataManager because dictionary items are global metadata
    that can be shared across organizations.
    """

    # Use GlobalMetadataManager - metadata is NOT organization-filtered
    objects = GlobalMetadataManager()
    # Keep all_objects for admin access
    all_objects = models.Manager()

    dictionary_type = models.ForeignKey(
        DictionaryType,
        on_delete=models.CASCADE,
        related_name='items',
        db_comment='Parent dictionary type'
    )
    code = models.CharField(
        max_length=50,
        db_comment='Item code (unique within dictionary type)'
    )
    name = models.CharField(
        max_length=100,
        db_comment='Display name'
    )
    name_en = models.CharField(
        max_length=100,
        blank=True,
        db_comment='English name'
    )
    description = models.TextField(
        blank=True,
        db_comment='Description'
    )
    # Extra metadata for different use cases
    color = models.CharField(
        max_length=20,
        blank=True,
        db_comment='Display color (e.g., #FF5733, success, warning)'
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        db_comment='Icon name (e.g., el-icon-check)'
    )
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        db_comment='Additional metadata (JSON)'
    )
    is_default = models.BooleanField(
        default=False,
        db_comment='Is this the default option'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        db_comment='Is this item active'
    )
    sort_order = models.IntegerField(
        default=0,
        db_comment='Display order within dictionary type'
    )

    class Meta:
        db_table = 'dictionary_items'
        verbose_name = 'Dictionary Item'
        verbose_name_plural = 'Dictionary Items'
        unique_together = [['organization', 'dictionary_type', 'code']]
        ordering = ['sort_order', 'code']
        indexes = [
            models.Index(fields=['organization', 'dictionary_type', 'code']),
            models.Index(fields=['organization', 'dictionary_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.dictionary_type.code}.{self.code} - {self.name}"


class SequenceRule(BaseModel):
    """
    Sequence Rule - defines a rule for generating unique sequential codes.

    Examples: ASSET_CODE, PICKUP_NO, TRANSFER_NO

    Pattern Variables:
    - {YYYY}: 4-digit year
    - {YY}: 2-digit year
    - {MM}: 2-digit month
    - {DD}: 2-digit day
    - {SEQ}: Sequential number (padded according to seq_length)

    Example pattern: "ZC{YYYY}{MM}{SEQ}" -> "ZC2026010001"

    Inherits from BaseModel for organization isolation and audit trails.
    Uses GlobalMetadataManager because sequence rules are global metadata
    that can be shared across organizations.
    """

    # Use GlobalMetadataManager - metadata is NOT organization-filtered
    objects = GlobalMetadataManager()
    # Keep all_objects for admin access
    all_objects = models.Manager()

    code = models.CharField(
        max_length=50,
        db_index=True,
        db_comment='Sequence rule code (e.g., ASSET_CODE)'
    )
    name = models.CharField(
        max_length=100,
        db_comment='Display name'
    )
    prefix = models.CharField(
        max_length=20,
        blank=True,
        db_comment='Static prefix (e.g., ZC, LY, TF)'
    )
    pattern = models.CharField(
        max_length=100,
        default='{PREFIX}{YYYY}{MM}{SEQ}',
        db_comment='Pattern with variables: {PREFIX}, {YYYY}, {YY}, {MM}, {DD}, {SEQ}'
    )
    seq_length = models.IntegerField(
        default=4,
        db_comment='Sequence number padding length (e.g., 4 -> 0001)'
    )
    current_value = models.BigIntegerField(
        default=0,
        db_comment='Current sequence value'
    )
    reset_period = models.CharField(
        max_length=20,
        choices=[
            ('never', 'Never Reset'),
            ('yearly', 'Reset Yearly'),
            ('monthly', 'Reset Monthly'),
            ('daily', 'Reset Daily'),
        ],
        default='monthly',
        db_comment='When to reset sequence counter'
    )
    last_reset_date = models.DateField(
        null=True,
        blank=True,
        db_comment='Date of last reset'
    )
    description = models.TextField(
        blank=True,
        db_comment='Description'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        db_comment='Is this rule active'
    )

    class Meta:
        db_table = 'sequence_rules'
        verbose_name = 'Sequence Rule'
        verbose_name_plural = 'Sequence Rules'
        unique_together = [['organization', 'code']]
        indexes = [
            models.Index(fields=['organization', 'code']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class SystemConfig(BaseModel):
    """
    System Configuration - key-value store for system-wide settings.

    Examples:
    - QR_CODE_TEMPLATE: "QR-{asset_code}-{org_code}"
    - DEFAULT_DEPRECIATION_METHOD: "straight_line"
    - ENABLE_EMAIL_NOTIFICATIONS: true

    Inherits from BaseModel for organization isolation and audit trails.
    Uses GlobalMetadataManager because system configs are global metadata
    that can be shared across organizations.
    """

    # Use GlobalMetadataManager - metadata is NOT organization-filtered
    objects = GlobalMetadataManager()
    # Keep all_objects for admin access
    all_objects = models.Manager()

    config_key = models.CharField(
        max_length=100,
        db_index=True,
        db_comment='Configuration key'
    )
    config_value = models.TextField(
        db_comment='Configuration value (stored as string, parsed by value_type)'
    )
    value_type = models.CharField(
        max_length=20,
        choices=[
            ('string', 'String'),
            ('integer', 'Integer'),
            ('float', 'Float'),
            ('boolean', 'Boolean'),
            ('json', 'JSON'),
        ],
        default='string',
        db_comment='Value type for parsing'
    )
    name = models.CharField(
        max_length=100,
        db_comment='Display name'
    )
    description = models.TextField(
        blank=True,
        db_comment='Description'
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        db_comment='Configuration category (for grouping)'
    )
    is_system = models.BooleanField(
        default=False,
        db_comment='System config (cannot be deleted by users)'
    )
    is_encrypted = models.BooleanField(
        default=False,
        db_comment='Is value encrypted (for sensitive data)'
    )

    class Meta:
        db_table = 'system_configs'
        verbose_name = 'System Configuration'
        verbose_name_plural = 'System Configurations'
        unique_together = [['organization', 'config_key']]
        indexes = [
            models.Index(fields=['organization', 'config_key']),
            models.Index(fields=['organization', 'category']),
        ]

    def __str__(self):
        return f"{self.config_key} = {self.config_value[:50]}"

    def get_typed_value(self):
        """Get value parsed according to value_type."""
        import json
        if self.value_type == 'integer':
            return int(self.config_value)
        elif self.value_type == 'float':
            return float(self.config_value)
        elif self.value_type == 'boolean':
            return self.config_value.lower() in ('true', '1', 'yes')
        elif self.value_type == 'json':
            return json.loads(self.config_value)
        return self.config_value


class MenuGroup(BaseModel):
    """
    Menu Group - first-class navigation category model.

    Default groups are hard-locked: they must exist and cannot be deleted,
    but their visibility and ordering can still be adjusted.
    """

    objects = GlobalMetadataManager()
    all_objects = models.Manager()

    code = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        db_comment='Stable menu group code'
    )
    name = models.CharField(
        max_length=100,
        db_comment='Display name or fallback translation label'
    )
    translation_key = models.CharField(
        max_length=200,
        blank=True,
        db_comment='Optional i18n key for group label'
    )
    icon = models.CharField(
        max_length=100,
        default='Menu',
        db_comment='Element Plus icon'
    )
    sort_order = models.PositiveIntegerField(
        default=999,
        db_comment='Display order'
    )
    is_visible = models.BooleanField(
        default=True,
        db_comment='Whether this group is visible in the navigation'
    )
    is_locked = models.BooleanField(
        default=False,
        db_comment='Locked groups cannot be deleted'
    )
    is_system = models.BooleanField(
        default=False,
        db_comment='Default system group'
    )

    class Meta:
        db_table = 'menu_groups'
        verbose_name = 'Menu Group'
        verbose_name_plural = 'Menu Groups'
        ordering = ['sort_order', 'code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['sort_order']),
            models.Index(fields=['is_visible']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class MenuEntry(BaseModel):
    """
    Menu Entry - unified navigation entry model.

    Supports both business-object-backed entries and static/system pages.
    """

    objects = GlobalMetadataManager()
    all_objects = models.Manager()

    SOURCE_TYPE_CHOICES = [
        ('business_object', 'Business Object'),
        ('static', 'Static Page'),
    ]

    source_type = models.CharField(
        max_length=30,
        choices=SOURCE_TYPE_CHOICES,
        db_index=True,
        db_comment='Entry source type'
    )
    source_code = models.CharField(
        max_length=100,
        db_index=True,
        db_comment='Stable source identifier'
    )
    code = models.CharField(
        max_length=100,
        db_index=True,
        db_comment='Menu entry code'
    )
    name = models.CharField(
        max_length=100,
        db_comment='Display name fallback'
    )
    name_en = models.CharField(
        max_length=100,
        blank=True,
        db_comment='English display name fallback'
    )
    translation_key = models.CharField(
        max_length=200,
        blank=True,
        db_comment='Optional i18n key for entry label'
    )
    route_path = models.CharField(
        max_length=255,
        db_comment='Frontend route path'
    )
    icon = models.CharField(
        max_length=100,
        default='Document',
        db_comment='Element Plus icon'
    )
    sort_order = models.PositiveIntegerField(
        default=999,
        db_comment='Display order within the group'
    )
    is_visible = models.BooleanField(
        default=True,
        db_comment='Whether this entry is visible in the navigation'
    )
    is_locked = models.BooleanField(
        default=False,
        db_comment='Locked entries cannot be deleted'
    )
    is_system = models.BooleanField(
        default=False,
        db_comment='Default system entry'
    )
    menu_group = models.ForeignKey(
        'MenuGroup',
        on_delete=models.PROTECT,
        related_name='entries',
        db_comment='Owning menu group'
    )
    business_object = models.ForeignKey(
        'BusinessObject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='menu_entries',
        db_comment='Linked business object for dynamic entries'
    )

    class Meta:
        db_table = 'menu_entries'
        verbose_name = 'Menu Entry'
        verbose_name_plural = 'Menu Entries'
        ordering = ['menu_group__sort_order', 'sort_order', 'code']
        constraints = [
            models.UniqueConstraint(
                fields=['source_type', 'source_code'],
                name='uniq_menu_entry_source'
            )
        ]
        indexes = [
            models.Index(fields=['source_type', 'source_code']),
            models.Index(fields=['code']),
            models.Index(fields=['sort_order']),
            models.Index(fields=['is_visible']),
        ]

    def __str__(self):
        return f"{self.code} ({self.source_type})"


class SystemFile(BaseModel):
    """
    System File - unified attachment/file management.

    Provides a centralized table for all file uploads across the system.
    Business objects reference SystemFile through ManyToMany or ForeignKey.

    Inherits from BaseModel for organization isolation and audit trails.
    """

    file_name = models.CharField(
        max_length=255,
        db_comment='Original file name'
    )
    file_path = models.CharField(
        max_length=500,
        db_comment='Storage path (relative to MEDIA_ROOT)'
    )
    file_size = models.BigIntegerField(
        default=0,
        db_comment='File size in bytes'
    )
    file_type = models.CharField(
        max_length=100,
        blank=True,
        db_comment='MIME type (e.g., image/png, application/pdf)'
    )
    file_extension = models.CharField(
        max_length=20,
        blank=True,
        db_comment='File extension (e.g., .pdf, .jpg)'
    )
    biz_type = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        db_comment='Business type (e.g., asset_image, contract_attachment)'
    )
    biz_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        db_comment='Business object ID (for direct linking)'
    )
    description = models.TextField(
        blank=True,
        db_comment='File description'
    )
    # Thumbnail for images
    thumbnail_path = models.CharField(
        max_length=500,
        blank=True,
        db_comment='Thumbnail path (for images)'
    )
    # Image dimensions (for image files)
    width = models.IntegerField(
        null=True,
        blank=True,
        db_comment='Image width in pixels'
    )
    height = models.IntegerField(
        null=True,
        blank=True,
        db_comment='Image height in pixels'
    )
    # Compression tracking
    is_compressed = models.BooleanField(
        default=False,
        db_comment='Whether file has been compressed'
    )
    original_file_id = models.UUIDField(
        null=True,
        blank=True,
        db_comment='Original file ID if this is a compressed version'
    )
    # Dynamic object reference (for field-based attachments)
    object_code = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        db_comment='Business object code (e.g., contract, asset)'
    )
    instance_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        db_comment='Business object instance ID'
    )
    field_code = models.CharField(
        max_length=100,
        blank=True,
        db_comment='Field code in the object (e.g., contract_files)'
    )
    # Hash for deduplication
    file_hash = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        db_comment='SHA256 hash for deduplication'
    )
    # Watermarked image path (for image files with watermark)
    watermarked_path = models.CharField(
        max_length=500,
        blank=True,
        db_comment='Watermarked image path (for images)'
    )

    class Meta:
        db_table = 'system_files'
        verbose_name = 'System File'
        verbose_name_plural = 'System Files'
        indexes = [
            models.Index(fields=['organization', 'biz_type', 'biz_id']),
            models.Index(fields=['organization', 'file_hash']),
            models.Index(fields=['organization', 'object_code', 'instance_id']),
            models.Index(fields=['organization', 'object_code', 'instance_id', 'field_code']),
        ]

    def __str__(self):
        return f"{self.file_name} ({self.file_type})"

    @property
    def url(self):
        """Get file URL."""
        from django.conf import settings
        return f"{settings.MEDIA_URL}{self.file_path}"

    @property
    def thumbnail_url(self):
        """Get thumbnail URL if available."""
        from django.conf import settings
        if self.thumbnail_path:
            return f"{settings.MEDIA_URL}{self.thumbnail_path}"
        return self.url  # Fallback to original if no thumbnail

    @property
    def watermarked_url(self):
        """Get watermarked image URL if available."""
        from django.conf import settings
        if self.watermarked_path:
            return f"{settings.MEDIA_URL}{self.watermarked_path}"
        return None


class Tag(BaseModel):
    """
    Tag - for tagging and categorizing business objects.

    Provides a flexible tagging system that can be attached to any model.

    Inherits from BaseModel for organization isolation and audit trails.
    """

    name = models.CharField(
        max_length=50,
        db_comment='Tag name'
    )
    color = models.CharField(
        max_length=20,
        default='#409EFF',
        db_comment='Tag color (hex or semantic name)'
    )
    description = models.TextField(
        blank=True,
        db_comment='Tag description'
    )
    biz_type = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        db_comment='Business type this tag applies to (empty = all)'
    )
    usage_count = models.IntegerField(
        default=0,
        db_comment='Number of times this tag is used'
    )

    class Meta:
        db_table = 'tags'
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        unique_together = [['organization', 'name', 'biz_type']]
        ordering = ['-usage_count', 'name']
        indexes = [
            models.Index(fields=['organization', 'name']),
            models.Index(fields=['organization', 'biz_type']),
        ]

    def __str__(self):
        return self.name


class Comment(BaseModel):
    """
    Comment - for adding comments/notes to business objects.

    Provides a centralized commenting system for any model.

    Inherits from BaseModel for organization isolation and audit trails.
    """

    biz_type = models.CharField(
        max_length=50,
        db_index=True,
        db_comment='Business object type (e.g., Asset, InventoryTask)'
    )
    biz_id = models.UUIDField(
        db_index=True,
        db_comment='Business object ID'
    )
    content = models.TextField(
        db_comment='Comment content'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        db_comment='Parent comment (for threaded replies)'
    )
    # Mentions
    mentioned_users = models.ManyToManyField(
        'accounts.User',
        blank=True,
        related_name='mentioned_in_comments',
        db_comment='Users mentioned in this comment'
    )
    # Attachments
    attachments = models.ManyToManyField(
        SystemFile,
        blank=True,
        related_name='comments',
        db_comment='Attachments on this comment'
    )
    is_pinned = models.BooleanField(
        default=False,
        db_comment='Is comment pinned'
    )

    class Meta:
        db_table = 'comments'
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'biz_type', 'biz_id']),
            models.Index(fields=['organization', 'biz_type', 'biz_id', '-created_at']),
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        return f"Comment on {self.biz_type}:{self.biz_id} by {self.created_by}"


class UserColumnPreference(BaseModel):
    """
    User-level column display preferences.

    Stores user-specific column configurations for list views.
    Inherits from BaseModel for organization isolation and audit trails.
    """

    # === Association ===
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='column_preferences',
        db_comment='User who owns this preference'
    )

    # === Configuration Identifier ===
    object_code = models.CharField(
        max_length=50,
        db_index=True,
        db_comment='Business object code (e.g., asset, procurement_request)'
    )

    # === Configuration Data ===
    column_config = models.JSONField(
        default=dict,
        db_comment='Column configuration (JSON): {columns: [...], columnOrder: [...]}'
    )

    # === Metadata ===
    config_name = models.CharField(
        max_length=50,
        default='default',
        db_comment='Configuration name (allows multiple configs per object)'
    )
    is_default = models.BooleanField(
        default=True,
        db_comment='Is this the default configuration for this object'
    )

    class Meta:
        db_table = 'system_user_column_preference'
        verbose_name = 'User Column Preference'
        verbose_name_plural = 'User Column Preferences'
        unique_together = [['user', 'object_code', 'config_name']]
        indexes = [
            models.Index(fields=['user', 'object_code']),
            models.Index(fields=['user', 'object_code', 'is_default']),
        ]

    def __str__(self):
        return f"{self.user.username}.{self.object_code}.{self.config_name}"


class TabConfig(BaseModel):
    """
    Tab configuration for forms and detail pages.

    Stores tab layout settings with position, style, and behavior options.
    Inherits from BaseModel for organization isolation and audit trails.
    """

    # === Association ===
    business_object = models.ForeignKey(
        BusinessObject,
        on_delete=models.CASCADE,
        related_name='tab_configs',
        db_comment='Business object this config applies to'
    )

    # === Configuration Identifier ===
    name = models.CharField(
        max_length=50,
        db_comment='Configuration name (e.g., form_tabs, detail_tabs)'
    )

    # === Display Options ===
    position = models.CharField(
        max_length=10,
        choices=[
            ('top', 'Top'),
            ('left', 'Left'),
            ('right', 'Right'),
            ('bottom', 'Bottom')
        ],
        default='top',
        db_comment='Tab position'
    )
    type_style = models.CharField(
        max_length=20,
        choices=[
            ('', 'Default'),
            ('card', 'Card'),
            ('border-card', 'Border Card')
        ],
        default='',
        db_comment='Tab style type'
    )
    stretch = models.BooleanField(
        default=False,
        db_comment='Stretch tabs to fill width'
    )

    # === Behavior Options ===
    lazy = models.BooleanField(
        default=True,
        db_comment='Lazy load tab content'
    )
    animated = models.BooleanField(
        default=True,
        db_comment='Animated tab transitions'
    )
    addable = models.BooleanField(
        default=False,
        db_comment='Allow adding new tabs'
    )
    draggable = models.BooleanField(
        default=False,
        db_comment='Allow dragging to reorder tabs'
    )

    # === Tab Configuration ===
    tabs_config = models.JSONField(
        default=list,
        db_comment='Tab definitions: [{id, title, icon, closable, disabled, content, ...}]'
    )

    # === Status ===
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        db_comment='Is this configuration active'
    )

    class Meta:
        db_table = 'system_tab_config'
        verbose_name = 'Tab Configuration'
        verbose_name_plural = 'Tab Configurations'
        unique_together = [['business_object', 'name', 'organization']]
        indexes = [
            models.Index(fields=['business_object', 'name', 'is_active']),
        ]

    def __str__(self):
        return f"{self.business_object.code}.{self.name}"


# =============================================================================
# Business Rule Models
# =============================================================================

class RuleType(models.TextChoices):
    """Business rule type choices."""
    VALIDATION = 'validation', '校验规则'
    VISIBILITY = 'visibility', '显示规则'
    COMPUTED = 'computed', '计算规则'
    TRIGGER = 'trigger', '触发规则'
    LINKAGE = 'linkage', '联动规则'


class TriggerEvent(models.TextChoices):
    """Rule trigger event choices."""
    CREATE = 'create', '创建时'
    UPDATE = 'update', '更新时'
    DELETE = 'delete', '删除时'
    STATUS_CHANGE = 'status_change', '状态变更时'
    FIELD_CHANGE = 'field_change', '字段变更时'
    SUBMIT = 'submit', '提交时'
    APPROVE = 'approve', '审批时'


class BusinessRule(BaseModel):
    """
    Business Rule - defines configurable business logic.

    Rules can control:
    - Field visibility based on conditions
    - Field validation beyond basic type checks
    - Computed field values
    - Automatic field updates on value changes
    - Event-triggered actions

    Uses JSON Logic (https://jsonlogic.com/) for condition expressions.
    """

    business_object = models.ForeignKey(
        BusinessObject,
        on_delete=models.CASCADE,
        related_name='business_rules',
        db_comment='Business object this rule belongs to'
    )
    rule_code = models.CharField(max_length=50, db_comment='Rule code')
    rule_name = models.CharField(max_length=100, db_comment='Rule display name')
    description = models.TextField(blank=True, db_comment='Rule description')
    rule_type = models.CharField(
        max_length=20,
        choices=RuleType.choices,
        default=RuleType.VALIDATION,
        db_comment='Type of rule'
    )
    priority = models.IntegerField(default=0, db_comment='Execution priority (higher=first)')
    is_active = models.BooleanField(default=True, db_comment='Is rule currently active')
    condition = models.JSONField(default=dict, blank=True, db_comment='JSON Logic condition')
    action = models.JSONField(default=dict, db_comment='Action to perform')
    target_field = models.CharField(max_length=50, blank=True, db_comment='Target field code')
    trigger_events = models.JSONField(default=list, blank=True, db_comment='Trigger events')
    error_message = models.CharField(max_length=500, blank=True, db_comment='Error message')
    error_message_en = models.CharField(max_length=500, blank=True, db_comment='English error message')

    class Meta:
        db_table = 'business_rules'
        verbose_name = 'Business Rule'
        verbose_name_plural = 'Business Rules'
        unique_together = [['organization', 'business_object', 'rule_code']]
        ordering = ['-priority', 'rule_type', 'rule_code']
        indexes = [
            models.Index(fields=['organization', 'business_object', 'rule_type']),
            models.Index(fields=['organization', 'business_object', 'is_active']),
        ]

    def __str__(self):
        return f"{self.business_object.code}.{self.rule_code} ({self.rule_name})"


class RuleExecution(BaseModel):
    """Rule Execution Log - tracks rule evaluation history."""

    rule = models.ForeignKey(
        BusinessRule,
        on_delete=models.CASCADE,
        related_name='executions',
        db_comment='The rule that was executed'
    )
    target_record_id = models.UUIDField(db_comment='ID of the record being evaluated')
    target_record_type = models.CharField(max_length=50, db_comment='Business object code')
    trigger_event = models.CharField(max_length=50, db_comment='Event that triggered execution')
    input_data = models.JSONField(default=dict, db_comment='Input data for evaluation')
    condition_result = models.BooleanField(db_comment='Whether condition was true')
    action_executed = models.BooleanField(default=False, db_comment='Whether action executed')
    execution_result = models.JSONField(default=dict, db_comment='Execution result')
    executed_at = models.DateTimeField(auto_now_add=True, db_comment='Execution timestamp')
    execution_time_ms = models.IntegerField(null=True, db_comment='Execution time in ms')
    has_error = models.BooleanField(default=False, db_comment='Whether an error occurred')
    error_message = models.TextField(blank=True, db_comment='Error message if failed')

    class Meta:
        db_table = 'rule_executions'
        verbose_name = 'Rule Execution'
        verbose_name_plural = 'Rule Executions'
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['rule', '-executed_at']),
            models.Index(fields=['target_record_id']),
        ]

    def __str__(self):
        status = "✓" if self.condition_result else "✗"
        return f"{self.rule.rule_code} {status} @ {self.executed_at}"


# =============================================================================
# Configuration Lifecycle Management Models
# =============================================================================

class PackageType(models.TextChoices):
    """Package type choices."""
    FULL = 'full', '完整导出'
    PARTIAL = 'partial', '部分导出'
    DIFF = 'diff', '差异导出'


class ImportStrategy(models.TextChoices):
    """Import strategy choices."""
    MERGE = 'merge', '合并'
    REPLACE = 'replace', '替换'
    SKIP = 'skip', '跳过已存在'


class ImportStatus(models.TextChoices):
    """Import status choices."""
    PENDING = 'pending', '待处理'
    IN_PROGRESS = 'in_progress', '进行中'
    SUCCESS = 'success', '成功'
    PARTIAL = 'partial', '部分成功'
    FAILED = 'failed', '失败'
    ROLLED_BACK = 'rolled_back', '已回滚'


class ConfigPackage(BaseModel):
    """
    Configuration Package - for exporting/importing business object configurations.
    
    Enables configuration versioning, environment deployment, and backup/restore.
    """

    name = models.CharField(
        max_length=100,
        db_comment='Package name'
    )
    version = models.CharField(
        max_length=20,
        db_comment='Semantic version (e.g., 1.0.0)'
    )
    description = models.TextField(
        blank=True,
        db_comment='Package description'
    )
    package_type = models.CharField(
        max_length=20,
        choices=PackageType.choices,
        default=PackageType.FULL,
        db_comment='Type of package'
    )

    # Included objects
    included_objects = models.JSONField(
        default=list,
        db_comment='List of business object codes included'
    )

    # Configuration content
    config_data = models.JSONField(
        default=dict,
        db_comment='Serialized configuration data'
    )

    # Export metadata
    exported_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='exported_packages',
        db_comment='User who exported this package'
    )
    exported_at = models.DateTimeField(
        auto_now_add=True,
        db_comment='Export timestamp'
    )
    source_environment = models.CharField(
        max_length=50,
        blank=True,
        db_comment='Source environment name (dev/staging/prod)'
    )

    # Validation
    checksum = models.CharField(
        max_length=64,
        blank=True,
        db_comment='SHA256 checksum of config_data for integrity'
    )
    is_valid = models.BooleanField(
        default=True,
        db_comment='Whether package passed validation'
    )
    validation_errors = models.JSONField(
        default=list,
        blank=True,
        db_comment='Validation error messages if any'
    )

    class Meta:
        db_table = 'config_packages'
        verbose_name = 'Configuration Package'
        verbose_name_plural = 'Configuration Packages'
        ordering = ['-exported_at']
        indexes = [
            models.Index(fields=['organization', 'name']),
            models.Index(fields=['organization', '-exported_at']),
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"


class ConfigImportLog(BaseModel):
    """
    Configuration Import Log - tracks import history and enables rollback.
    """

    package = models.ForeignKey(
        ConfigPackage,
        on_delete=models.CASCADE,
        related_name='import_logs',
        db_comment='The package that was imported'
    )
    imported_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='config_imports',
        db_comment='User who performed the import'
    )
    imported_at = models.DateTimeField(
        auto_now_add=True,
        db_comment='Import timestamp'
    )
    target_environment = models.CharField(
        max_length=50,
        blank=True,
        db_comment='Target environment name'
    )
    import_strategy = models.CharField(
        max_length=20,
        choices=ImportStrategy.choices,
        default=ImportStrategy.MERGE,
        db_comment='Import strategy used'
    )
    status = models.CharField(
        max_length=20,
        choices=ImportStatus.choices,
        default=ImportStatus.PENDING,
        db_comment='Import status'
    )

    # Import results
    import_result = models.JSONField(
        default=dict,
        db_comment='Import result details'
    )
    objects_created = models.IntegerField(
        default=0,
        db_comment='Number of objects created'
    )
    objects_updated = models.IntegerField(
        default=0,
        db_comment='Number of objects updated'
    )
    objects_skipped = models.IntegerField(
        default=0,
        db_comment='Number of objects skipped'
    )
    objects_failed = models.IntegerField(
        default=0,
        db_comment='Number of objects failed'
    )

    # Rollback data
    rollback_data = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        db_comment='Data snapshot for rollback'
    )
    can_rollback = models.BooleanField(
        default=True,
        db_comment='Whether this import can be rolled back'
    )
    rolled_back_at = models.DateTimeField(
        null=True,
        blank=True,
        db_comment='When rollback was performed'
    )

    # Error tracking
    error_message = models.TextField(
        blank=True,
        db_comment='Error message if import failed'
    )

    class Meta:
        db_table = 'config_import_logs'
        verbose_name = 'Configuration Import Log'
        verbose_name_plural = 'Configuration Import Logs'
        ordering = ['-imported_at']
        indexes = [
            models.Index(fields=['package', '-imported_at']),
            models.Index(fields=['organization', '-imported_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Import {self.package.name} v{self.package.version} @ {self.imported_at}"


# =============================================================================
# Internationalization (i18n) Models
# =============================================================================

class Language(BaseModel):
    """
    Language - system supported language configuration.

    Defines available languages for the internationalization system.
    Uses GlobalMetadataManager because language configurations are shared
    across all organizations.
    """

    # Use GlobalMetadataManager - language configs are NOT organization-filtered
    objects = GlobalMetadataManager()
    all_objects = models.Manager()

    code = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        db_comment='Language code (BCP 47 standard, e.g., zh-CN, en-US)'
    )
    name = models.CharField(
        max_length=50,
        db_comment='Language display name (e.g., Chinese (Simplified))'
    )
    native_name = models.CharField(
        max_length=50,
        db_comment='Native language name (e.g., 简体中文)'
    )
    is_default = models.BooleanField(
        default=False,
        db_index=True,
        db_comment='Is this the default language'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        db_comment='Is this language active'
    )
    sort_order = models.IntegerField(
        default=0,
        db_comment='Display order'
    )
    flag_emoji = models.CharField(
        max_length=10,
        blank=True,
        db_comment='Flag emoji (e.g., 🇨🇳, 🇺🇸)'
    )
    locale = models.CharField(
        max_length=10,
        blank=True,
        db_comment='Locale code for frontend (e.g., zhCN, enUS)'
    )

    class Meta:
        db_table = 'languages'
        verbose_name = 'Language'
        verbose_name_plural = 'Languages'
        ordering = ['sort_order', 'code']
        indexes = [
            models.Index(fields=['is_default', 'is_active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Translation(BaseModel):
    """
    Translation - unified translation storage for i18n system.

    Hybrid design supporting both:
    1. namespace/key pattern for static content (labels, buttons, messages)
    2. GenericForeignKey pattern for dynamic object translations

    Uses GlobalMetadataManager because translations are shared metadata.
    """

    # Use GlobalMetadataManager - translations are NOT organization-filtered
    objects = GlobalMetadataManager()
    all_objects = models.Manager()

    # Namespace/Key pattern (for static content)
    namespace = models.CharField(
        max_length=50,
        blank=True,
        default='',
        db_index=True,
        db_comment='Translation namespace (e.g., asset, common, dictionary)'
    )
    key = models.CharField(
        max_length=200,
        blank=True,
        default='',
        db_index=True,
        db_comment='Translation key (e.g., status.idle, button.save)'
    )

    # GenericForeignKey pattern (for dynamic object translations)
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        db_comment='Content type for GenericForeignKey'
    )
    object_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        db_comment='Object ID for GenericForeignKey (UUID to match BaseModel)'
    )
    content_object = GenericForeignKey(
        'content_type',
        'object_id'
    )
    field_name = models.CharField(
        max_length=50,
        blank=True,
        default='',
        db_comment='Field name being translated (e.g., name, description)'
    )

    # Translation content
    language_code = models.CharField(
        max_length=10,
        db_index=True,
        db_comment='Target language code (e.g., en-US, ja-JP)'
    )
    text = models.TextField(
        db_comment='Translated text'
    )

    # Metadata
    context = models.CharField(
        max_length=200,
        blank=True,
        db_comment='Context for disambiguation'
    )
    type = models.CharField(
        max_length=20,
        default='label',
        db_comment='Translation type: label, message, enum, object_field'
    )
    is_system = models.BooleanField(
        default=False,
        db_comment='Is this a system translation (not editable by users)'
    )

    class Meta:
        db_table = 'translations'
        verbose_name = 'Translation'
        verbose_name_plural = 'Translations'
        # Use conditional unique constraints to avoid NULL issues
        constraints = [
            models.UniqueConstraint(
                fields=['namespace', 'key', 'language_code'],
                condition=models.Q(namespace__gt='', key__gt=''),
                name='unique_namespace_key_lang'
            ),
            models.UniqueConstraint(
                fields=['content_type', 'object_id', 'field_name', 'language_code'],
                condition=models.Q(content_type__isnull=False, object_id__isnull=False),
                name='unique_gfk_field_lang'
            ),
        ]
        indexes = [
            models.Index(fields=['namespace', 'key', 'language_code']),
            models.Index(fields=['content_type', 'object_id', 'language_code']),
            models.Index(fields=['language_code', 'type']),
            models.Index(fields=['is_system']),
        ]

    def __str__(self):
        if self.namespace and self.key:
            return f"{self.namespace}:{self.key}[{self.language_code}]"
        elif self.content_object:
            return f"{self.content_type}:{self.object_id}.{self.field_name}[{self.language_code}]"
        return f"Translation[{self.language_code}]"


# Register split models that live outside models.py so Django app loading,
# ContentType creation, and apps.get_model('system', ...) remain consistent.
from .activity_log import ActivityLog  # noqa: E402,F401
