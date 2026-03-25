"""
Django Admin configuration for Consumable models.

Provides admin interface for:
- ConsumableCategory: Consumable classification
- Consumable: Consumable item records
- ConsumableStock: Stock levels
- ConsumablePurchase: Purchase orders
- ConsumableIssue: Issue/Allocation records
"""
from django.contrib import admin

from .models import (
    ConsumableCategory,
    Consumable,
    ConsumableStock,
    ConsumablePurchase,
    PurchaseItem,
    ConsumableIssue,
    IssueItem,
)
from django import forms
from django.utils.translation import gettext_lazy as _
from apps.system.services import DictionaryService
import logging

logger = logging.getLogger(__name__)


def get_dictionary_choices(dictionary_code):
    """Helper to get choices from DictionaryService"""
    try:
        from django.utils.translation import get_language
        items = DictionaryService.get_items(dictionary_code)
        lang = get_language()
        choices = []
        for item in items:
            label = item['name']
            if lang and lang.startswith('en') and item.get('name_en'):
                label = item['name_en']
            choices.append((item['code'], label))
        return choices
    except Exception as e:
        logger.warning(f"Failed to load dictionary {dictionary_code}: {e}")
        return []


class ConsumableCategoryAdminForm(forms.ModelForm):
    unit = forms.ChoiceField(required=False, label=_('Unit'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit'].choices = get_dictionary_choices('UNIT')

    class Meta:
        model = ConsumableCategory
        fields = '__all__'


class ConsumableAdminForm(forms.ModelForm):
    status = forms.ChoiceField(required=False, label=_('Status'))
    unit = forms.ChoiceField(required=False, label=_('Unit'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = get_dictionary_choices('CONSUMABLE_STATUS')
        self.fields['unit'].choices = get_dictionary_choices('UNIT')

    class Meta:
        model = Consumable
        fields = '__all__'


class ConsumablePurchaseAdminForm(forms.ModelForm):
    status = forms.ChoiceField(required=False, label=_('Status'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = get_dictionary_choices('CONSUMABLE_PURCHASE_STATUS')

    class Meta:
        model = ConsumablePurchase
        fields = '__all__'


class ConsumableIssueAdminForm(forms.ModelForm):
    status = forms.ChoiceField(required=False, label=_('Status'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = get_dictionary_choices('CONSUMABLE_ISSUE_STATUS')

    class Meta:
        model = ConsumableIssue
        fields = '__all__'


@admin.register(ConsumableCategory)
class ConsumableCategoryAdmin(admin.ModelAdmin):
    """Admin interface for Consumable Category."""

    form = ConsumableCategoryAdminForm
    list_display = ['code', 'name', 'parent', 'level', 'path', 'unit', 'is_active']
    list_filter = ['level', 'is_active']
    search_fields = ['code', 'name']
    readonly_fields = ['level', 'path', 'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by']
    ordering = ['code']


@admin.register(Consumable)
class ConsumableAdmin(admin.ModelAdmin):
    """Admin interface for Consumable."""

    form = ConsumableAdminForm
    list_display = ['code', 'name', 'category', 'unit', 'purchase_price', 'status_display', 'warehouse']
    list_filter = ['category', 'status']
    search_fields = ['code', 'name', 'specification']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by']
    ordering = ['code']

    def status_display(self, obj):
        return obj.get_status_label()
    status_display.short_description = _('Status')


@admin.register(ConsumableStock)
class ConsumableStockAdmin(admin.ModelAdmin):
    """Admin interface for Consumable Stock."""

    list_display = ['consumable', 'transaction_type', 'quantity', 'before_stock', 'after_stock', 'created_at']
    list_filter = ['transaction_type']
    search_fields = ['consumable__code', 'consumable__name', 'source_no']
    readonly_fields = ['created_at', 'created_by']
    ordering = ['-created_at']


class PurchaseItemInline(admin.TabularInline):
    """Inline admin for PurchaseItem."""

    model = PurchaseItem
    extra = 0


@admin.register(ConsumablePurchase)
class ConsumablePurchaseAdmin(admin.ModelAdmin):
    """Admin interface for Consumable Purchase."""

    form = ConsumablePurchaseAdminForm
    list_display = ['purchase_no', 'supplier', 'purchase_date', 'total_amount', 'status_display']
    list_filter = ['status', 'purchase_date']
    search_fields = ['purchase_no', 'supplier__name']
    readonly_fields = ['purchase_no', 'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by']
    inlines = [PurchaseItemInline]
    ordering = ['-created_at']

    def status_display(self, obj):
        return obj.get_status_label()
    status_display.short_description = _('Status')


class IssueItemInline(admin.TabularInline):
    """Inline admin for IssueItem."""

    model = IssueItem
    extra = 0


@admin.register(ConsumableIssue)
class ConsumableIssueAdmin(admin.ModelAdmin):
    """Admin interface for Consumable Issue."""

    form = ConsumableIssueAdminForm
    list_display = ['issue_no', 'applicant', 'department', 'issue_date', 'status_display']
    list_filter = ['status', 'issue_date']
    search_fields = ['issue_no', 'applicant__username']
    readonly_fields = ['issue_no', 'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_by']
    inlines = [IssueItemInline]
    ordering = ['-created_at']

    def status_display(self, obj):
        return obj.get_status_label()
    status_display.short_description = _('Status')
