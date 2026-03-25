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
import json

from django.contrib import admin
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
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


class MultipleFileInput(forms.ClearableFileInput):
    """Allow selecting multiple files in Django admin."""

    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Return a list of uploaded files instead of a single file."""

    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            return [single_file_clean(item, initial) for item in data]
        return [single_file_clean(data, initial)]


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
    image_uploads = MultipleFileField(
        label=_('Upload Images'),
        required=False,
        help_text=_('Upload image files here. Uploaded file IDs will be appended to the images JSON list.'),
    )
    attachment_uploads = MultipleFileField(
        label=_('Upload Attachments'),
        required=False,
        help_text=_('Upload attachment files here. Uploaded file IDs will be appended to the attachments JSON list.'),
    )

    class Meta:
        model = Asset
        fields = '__all__'
        widgets = {
            'images': forms.Textarea(attrs={'rows': 4, 'style': 'font-family: monospace;'}),
            'attachments': forms.Textarea(attrs={'rows': 4, 'style': 'font-family: monospace;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically load choices from Dictionary
        self.fields['asset_status'].choices = get_dictionary_choices('ASSET_STATUS')
        self.fields['unit'].choices = get_dictionary_choices('UNIT')
        self.fields['image_uploads'].widget.attrs.update({'accept': 'image/*', 'multiple': True})
        self.fields['attachment_uploads'].widget.attrs.update({'multiple': True})
        self.fields['images'].help_text = _(
            'Advanced field: stores a JSON array of SystemFile IDs. Prefer "Upload Images" above.'
        )
        self.fields['attachments'].help_text = _(
            'Advanced field: stores a JSON array of SystemFile IDs. Prefer "Upload Attachments" above.'
        )

        for field_name in ('images', 'attachments'):
            value = self.initial.get(field_name, getattr(self.instance, field_name, None))
            if isinstance(value, list):
                self.initial[field_name] = json.dumps(value, indent=2, ensure_ascii=False, cls=DjangoJSONEncoder)
            elif isinstance(value, str) and value:
                self.initial[field_name] = json.dumps([value], indent=2, ensure_ascii=False, cls=DjangoJSONEncoder)

    def _normalize_system_file_value(self, value):
        if value in (None, '', []):
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, dict):
            candidate = value.get('id') or value.get('fileId') or value.get('value')
            return [candidate] if isinstance(candidate, str) and candidate else []
        if isinstance(value, list):
            normalized = []
            for item in value:
                if isinstance(item, str) and item and item not in normalized:
                    normalized.append(item)
                    continue
                if isinstance(item, dict):
                    candidate = item.get('id') or item.get('fileId') or item.get('value')
                    if isinstance(candidate, str) and candidate and candidate not in normalized:
                        normalized.append(candidate)
            return normalized
        raise forms.ValidationError(_('This field must be a JSON array of SystemFile IDs.'))

    def clean_images(self):
        return self._normalize_system_file_value(self.cleaned_data.get('images'))

    def clean_attachments(self):
        return self._normalize_system_file_value(self.cleaned_data.get('attachments'))


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
        'net_value', 'residual_value', 'images_preview', 'attachments_preview',
        'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by'
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
            'fields': (
                'images_preview', 'image_uploads', 'images',
                'attachments_preview', 'attachment_uploads', 'attachments',
                'remarks',
            ),
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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        upload_summary = []

        image_ids = self._save_uploaded_files(
            request=request,
            obj=obj,
            uploaded_files=form.cleaned_data.get('image_uploads') or [],
            field_name='images',
        )
        if image_ids:
            upload_summary.append(_('images: %(count)s') % {'count': len(image_ids)})

        attachment_ids = self._save_uploaded_files(
            request=request,
            obj=obj,
            uploaded_files=form.cleaned_data.get('attachment_uploads') or [],
            field_name='attachments',
        )
        if attachment_ids:
            upload_summary.append(_('attachments: %(count)s') % {'count': len(attachment_ids)})

        if upload_summary:
            self.message_user(
                request,
                _('Uploaded and linked files successfully (%(summary)s).') % {'summary': ', '.join(upload_summary)},
                level=messages.SUCCESS,
            )

    def _save_uploaded_files(self, request, obj, uploaded_files, field_name):
        if not uploaded_files:
            return []

        organization_id = getattr(obj, 'organization_id', None)
        if not organization_id:
            self.message_user(
                request,
                _('Cannot upload %(field)s because this asset has no organization.') % {'field': field_name},
                level=messages.ERROR,
            )
            return []

        from apps.system.services.file_storage import FileStorageService

        service = FileStorageService()
        current_ids = self._extract_file_ids(getattr(obj, field_name, []))
        created_ids = []

        for uploaded_file in uploaded_files:
            result = service.save_file(
                file=uploaded_file,
                organization_id=str(organization_id),
                object_code='Asset',
                instance_id=obj.id,
                field_code=field_name,
                description=f'Uploaded from Django admin for asset {obj.asset_code or obj.id}',
            )
            if not result.get('success') or not result.get('data'):
                error_message = result.get('error', {}).get('message') or _('Unknown upload error')
                self.message_user(
                    request,
                    _('Failed to upload %(name)s: %(message)s') % {
                        'name': getattr(uploaded_file, 'name', field_name),
                        'message': error_message,
                    },
                    level=messages.ERROR,
                )
                continue

            file_id = str(result['data'].id)
            if file_id not in current_ids:
                current_ids.append(file_id)
            created_ids.append(file_id)

        if created_ids:
            setattr(obj, field_name, current_ids)
            obj.save(update_fields=[field_name])

        return created_ids

    def _extract_file_ids(self, value):
        if not value:
            return []
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return [value]
        if isinstance(value, str):
            return [value]
        if not isinstance(value, list):
            return []

        ids = []
        for item in value:
            if isinstance(item, str) and item and item not in ids:
                ids.append(item)
                continue
            if isinstance(item, dict):
                candidate = item.get('id') or item.get('fileId') or item.get('value')
                if isinstance(candidate, str) and candidate and candidate not in ids:
                    ids.append(candidate)
        return ids

    def _render_file_preview(self, obj, field_name, image_only=False):
        if not getattr(obj, 'pk', None):
            return _('Save the asset first, then upload files here.')

        file_ids = self._extract_file_ids(getattr(obj, field_name, []))
        if not file_ids:
            return _('No linked files')

        from apps.system.models import SystemFile

        file_map = {
            str(file_obj.id): file_obj
            for file_obj in SystemFile.objects.filter(id__in=file_ids, is_deleted=False)
        }
        rows = []
        for file_id in file_ids:
            file_obj = file_map.get(file_id)
            if not file_obj:
                rows.append(
                    '<li><code>{}</code> <span style="color:#888;">(missing SystemFile record)</span></li>'.format(file_id)
                )
                continue

            admin_url = reverse('admin:system_systemfile_change', args=[file_obj.pk])
            preview_link = ''
            if image_only:
                preview_link = f' <a href="{file_obj.url}" target="_blank">preview</a>'

            rows.append(
                '<li><a href="{admin_url}">{name}</a> <code>{file_id}</code>{preview}</li>'.format(
                    admin_url=admin_url,
                    name=file_obj.file_name,
                    file_id=file_id,
                    preview=preview_link,
                )
            )

        return format_html('<ul style="margin:0; padding-left:18px;">{}</ul>', format_html(''.join(rows)))

    def images_preview(self, obj):
        return self._render_file_preview(obj, 'images', image_only=True)
    images_preview.short_description = _('Current Images')

    def attachments_preview(self, obj):
        return self._render_file_preview(obj, 'attachments')
    attachments_preview.short_description = _('Current Attachments')


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
