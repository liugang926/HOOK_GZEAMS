"""
Django Admin configuration for Asset models.

Provides admin interface for:
- AssetCategory: Asset classification with tree structure
- Supplier: Supplier/ vendor information
- Location: Physical location hierarchy
- Asset: Main asset records
- AssetStatusLog: Status change history
- AssetPickup: Asset pickup operations
- AssetTransfer: Asset transfer operations
- AssetReturn: Asset return operations
- AssetLoan: Asset loan operations
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from .models import (
    AssetCategory,
    Supplier,
    Location,
    Asset,
    AssetStatusLog,
    AssetPickup,
    PickupItem,
    AssetTransfer,
    TransferItem,
    AssetReturn,
    ReturnItem,
    AssetLoan,
    LoanItem,
)


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    """Admin interface for Asset Category."""

    list_display = ['code', 'name', 'parent', 'level', 'is_custom', 'is_active', 'sort_order']
    list_filter = ['level', 'is_custom', 'is_active']
    search_fields = ['code', 'name', 'full_name']
    readonly_fields = ['full_name', 'level', 'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by']
    ordering = ['sort_order', 'code']

    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'parent', 'full_name', 'level')
        }),
        ('Configuration', {
            'fields': ('depreciation_method', 'default_useful_life', 'residual_rate')
        }),
        ('Settings', {
            'fields': ('is_custom', 'is_active', 'sort_order')
        }),
        ('Audit', {
            'fields': ('organization', 'is_deleted', 'created_at', 'created_by')
        }),
    )


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Admin interface for Supplier."""

    list_display = ['code', 'name', 'contact', 'phone', 'email']
    list_filter = ['organization']
    search_fields = ['code', 'name', 'contact', 'email']
    ordering = ['code']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Admin interface for Location."""

    list_display = ['name', 'parent', 'path', 'level', 'location_type']
    list_filter = ['level', 'location_type']
    search_fields = ['name', 'path']
    readonly_fields = ['path', 'level']
    ordering = ['path']


from django import forms


def get_dictionary_choices(code):
    """Dynamically get choices from Dictionary by code."""
    try:
        from apps.system.services import DictionaryService
        from django.utils.translation import get_language
        items = DictionaryService.get_items(code)
        if items:
            lang = get_language()
            choices = []
            for item in items:
                label = item['name']
                if lang and lang.startswith('en') and item.get('name_en'):
                    label = item['name_en']
                choices.append((item['code'], label))
            return choices
        import logging
        logging.warning(f'{code} dictionary has no items')
        return []
    except Exception as e:
        import logging
        logging.error(f'Failed to load {code} dictionary: {e}')
        return []


class AssetAdminForm(forms.ModelForm):
    """Custom form for Asset with dynamic choices."""

    asset_status = forms.ChoiceField(
        choices=[],
        label=_('Asset Status'),
        required=True
    )
    unit = forms.ChoiceField(
        choices=[],
        label=_('Unit'),
        required=False
    )

    class Meta:
        model = Asset
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically load choices from Dictionary
        self.fields['asset_status'].choices = get_dictionary_choices('ASSET_STATUS')
        self.fields['unit'].choices = get_dictionary_choices('UNIT')


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """Admin interface for Asset with dynamic status choices."""

    form = AssetAdminForm

    list_display = [
        'asset_code', 'asset_name', 'asset_category', 'department',
        'location', 'asset_status_display', 'purchase_price', 'purchase_date'
    ]
    list_filter = [
        'asset_category', 'department',
        'location', 'purchase_date'
    ]
    search_fields = [
        'asset_code', 'asset_name', 'specification', 'brand',
        'model', 'serial_number', 'qr_code', 'rfid_code'
    ]
    readonly_fields = [
        'asset_code', 'qr_code', 'current_value', 'accumulated_depreciation',
        'net_value', 'residual_value', 'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by'
    ]
    ordering = ['-created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'asset_code', 'qr_code', 'rfid_code', 'asset_name',
                'asset_category', 'specification', 'brand', 'model',
                'unit', 'serial_number'
            )
        }),
        ('Financial Information', {
            'fields': (
                'purchase_price', 'current_value', 'accumulated_depreciation',
                'net_value', 'residual_value', 'purchase_date',
                'depreciation_start_date', 'useful_life', 'residual_rate'
            )
        }),
        ('Supplier Information', {
            'fields': ('supplier', 'supplier_order_no', 'invoice_no')
        }),
        ('Usage Information', {
            'fields': ('department', 'location', 'custodian', 'user')
        }),
        ('Status', {
            'fields': ('asset_status',)
        }),
        ('Attachments', {
            'fields': ('images', 'attachments', 'remarks'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('organization', 'is_deleted', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def asset_status_display(self, obj):
        """Display status label from Dictionary."""
        return obj.get_status_label()
    asset_status_display.short_description = _('Asset Status')


@admin.register(AssetStatusLog)
class AssetStatusLogAdmin(admin.ModelAdmin):
    """Admin interface for Asset Status Log."""

    list_display = ['asset', 'old_status', 'new_status', 'created_by', 'created_at']
    list_filter = ['old_status', 'new_status', 'created_at']
    search_fields = ['asset__asset_code', 'asset__asset_name', 'reason']
    readonly_fields = ['asset', 'old_status', 'new_status', 'created_by', 'created_at', 'updated_at', 'updated_by', 'deleted_by']
    ordering = ['-created_at']


class PickupItemInline(admin.TabularInline):
    """Inline admin for PickupItem."""

    model = PickupItem
    extra = 0
    readonly_fields = ['asset', 'snapshot_original_location']
    fields = ['asset', 'quantity', 'snapshot_original_location', 'snapshot_original_custodian', 'remark']


class AssetPickupAdminForm(forms.ModelForm):
    status = forms.ChoiceField(label=_('Status'))

    class Meta:
        model = AssetPickup
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = get_dictionary_choices('PICKUP_STATUS')


@admin.register(AssetPickup)
class AssetPickupAdmin(admin.ModelAdmin):
    """Admin interface for Asset Pickup."""

    form = AssetPickupAdminForm
    list_display = ['pickup_no', 'applicant', 'department', 'status_display', 'pickup_date']
    list_filter = ['status', 'pickup_date']
    search_fields = ['pickup_no', 'applicant__username', 'applicant__email']
    readonly_fields = ['pickup_no', 'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by']
    inlines = [PickupItemInline]
    ordering = ['-created_at']

    def status_display(self, obj):
        return obj.get_status_label()
    status_display.short_description = _('Status')


class TransferItemInline(admin.TabularInline):
    """Inline admin for TransferItem."""

    model = TransferItem
    extra = 0
    readonly_fields = ['asset']
    fields = ['asset', 'from_location', 'from_custodian', 'to_location', 'remark']


class AssetTransferAdminForm(forms.ModelForm):
    status = forms.ChoiceField(label=_('Status'))

    class Meta:
        model = AssetTransfer
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = get_dictionary_choices('TRANSFER_STATUS')


@admin.register(AssetTransfer)
class AssetTransferAdmin(admin.ModelAdmin):
    """Admin interface for Asset Transfer."""

    form = AssetTransferAdminForm
    list_display = ['transfer_no', 'from_department', 'to_department', 'status_display', 'transfer_date']
    list_filter = ['status', 'transfer_date']
    search_fields = ['transfer_no']
    readonly_fields = ['transfer_no', 'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by']
    inlines = [TransferItemInline]
    ordering = ['-created_at']

    def status_display(self, obj):
        return obj.get_status_label()
    status_display.short_description = _('Status')


class ReturnItemInline(admin.TabularInline):
    """Inline admin for ReturnItem."""

    model = ReturnItem
    extra = 0
    readonly_fields = ['asset']
    fields = ['asset', 'asset_status', 'condition_description', 'remark']


class AssetReturnAdminForm(forms.ModelForm):
    status = forms.ChoiceField(label=_('Status'))

    class Meta:
        model = AssetReturn
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = get_dictionary_choices('RETURN_STATUS')


@admin.register(AssetReturn)
class AssetReturnAdmin(admin.ModelAdmin):
    """Admin interface for Asset Return."""

    form = AssetReturnAdminForm
    list_display = ['return_no', 'returner', 'status_display', 'return_date']
    list_filter = ['status', 'return_date']
    search_fields = ['return_no', 'returner__username']
    readonly_fields = ['return_no', 'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by']
    inlines = [ReturnItemInline]
    ordering = ['-created_at']

    def status_display(self, obj):
        return obj.get_status_label()
    status_display.short_description = _('Status')


class LoanItemInline(admin.TabularInline):
    """Inline admin for LoanItem."""

    model = LoanItem
    extra = 0
    readonly_fields = ['asset']
    fields = ['asset', 'remark']


class AssetLoanAdminForm(forms.ModelForm):
    status = forms.ChoiceField(label=_('Status'))

    class Meta:
        model = AssetLoan
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = get_dictionary_choices('LOAN_STATUS')


@admin.register(AssetLoan)
class AssetLoanAdmin(admin.ModelAdmin):
    """Admin interface for Asset Loan."""

    form = AssetLoanAdminForm
    list_display = ['loan_no', 'borrower', 'status_display', 'borrow_date', 'expected_return_date', 'actual_return_date']
    list_filter = ['status', 'borrow_date']
    search_fields = ['loan_no', 'borrower__username']
    readonly_fields = ['loan_no', 'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by']
    inlines = [LoanItemInline]
    ordering = ['-created_at']

    def status_display(self, obj):
        return obj.get_status_label()
    status_display.short_description = '状态'
