"""
Core metadata models for the low-code business object engine.

This module contains the core models that enable dynamic business object
configuration without code changes.
"""
from django.db import models
from django.core.exceptions import ValidationError
from apps.common.models import BaseModel


class BusinessObject(BaseModel):
    """
    Business Object - defines a configurable entity.

    Examples: Asset, AssetPickup, AssetTransfer, InventoryTask, etc.

    Inherits from BaseModel:
    - organization: Multi-tenant data isolation
    - is_deleted: Soft delete support
    - created_at, updated_at: Audit timestamps
    - created_by: User who created this record
    - custom_fields: Additional metadata storage
    """

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

    Inherits from BaseModel for organization isolation and audit trails.
    """

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
    sort_order = models.IntegerField(
        default=0,
        db_comment='Display order'
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

    Inherits from BaseModel for organization isolation and audit trails.
    """

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
        'BooleanField': 'boolean',
        'NullBooleanField': 'boolean',
        'ForeignKey': 'reference',
        'ManyToManyField': 'multi_select',
        'OneToOneField': 'reference',
        'UUIDField': 'text',
        'EmailField': 'text',
        'URLField': 'text',
        'FileField': 'file',
        'ImageField': 'image',
        'JSONField': 'textarea',
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
        field_type = cls.DJANGO_FIELD_TYPE_MAP.get(django_type, 'text')

        # Handle ForeignKey special case
        reference_path = ''
        if isinstance(field, django_models.ForeignKey):
            reference_path = f"{field.related_model.__module__}.{field.related_model.__name__}"
            # Determine reference type based on related model
            if field.related_model.__name__ == 'User':
                field_type = 'user'
            elif 'Organization' in field.related_model.__name__:
                field_type = 'department'

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
            decimal_places=getattr(field, 'decimal_places', None),
            max_digits=getattr(field, 'max_digits', None),
            max_length=getattr(field, 'max_length', None),
        )


class PageLayout(BaseModel):
    """
    Page Layout - defines the layout configuration for forms, lists, etc.

    The layout_config is a JSON structure defining:
    - Sections with column layout
    - Field grouping and ordering
    - Conditional visibility rules
    - Field permissions (read-only, hidden)

    Inherits from BaseModel for organization isolation and audit trails.
    """

    # Layout Type Choices
    LAYOUT_TYPE_CHOICES = [
        ('form', 'Form'),
        ('list', 'List'),
        ('detail', 'Detail'),
        ('search', 'Search'),
    ]

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
        db_comment='Layout type'
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

    def clean(self):
        """Validate layout configuration."""
        if self.layout_type == 'form' and not self.layout_config.get('sections'):
            raise ValidationError({
                'layout_config': 'Form layout must contain sections.'
            })

        if self.layout_type == 'list' and not self.layout_config.get('columns'):
            raise ValidationError({
                'layout_config': 'List layout must contain columns.'
            })

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
    """

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
    """

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
    """

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
    """

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
    # Hash for deduplication
    file_hash = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        db_comment='SHA256 hash for deduplication'
    )

    class Meta:
        db_table = 'system_files'
        verbose_name = 'System File'
        verbose_name_plural = 'System Files'
        indexes = [
            models.Index(fields=['organization', 'biz_type', 'biz_id']),
            models.Index(fields=['organization', 'file_hash']),
        ]

    def __str__(self):
        return f"{self.file_name} ({self.file_type})"

    @property
    def url(self):
        """Get file URL."""
        from django.conf import settings
        return f"{settings.MEDIA_URL}{self.file_path}"


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
