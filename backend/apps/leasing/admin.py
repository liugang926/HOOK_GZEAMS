"""
Leasing management admin configuration.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    LeaseContract, LeaseItem, RentPayment,
    LeaseReturn, LeaseExtension
)


@admin.register(LeaseContract)
class LeaseContractAdmin(admin.ModelAdmin):
    """Lease Contract Admin."""
    list_display = [
        'contract_no', 'lessee_name', 'start_date', 'end_date',
        'status', 'payment_type', 'total_rent', 'deposit_amount', 'is_active_display'
    ]
    list_filter = ['status', 'payment_type', 'lessee_type', 'created_at']
    search_fields = ['contract_no', 'lessee_name', 'lessee_contact', 'lessee_phone']
    readonly_fields = [
        'contract_no', 'is_active_display', 'days_remaining_display',
        'total_days_display', 'unpaid_amount_display',
        'created_at', 'updated_at', 'created_by', 'approved_by', 'approved_at'
    ]
    date_hierarchy = 'created_at'
    fieldsets = (
        (_('Contract Information'), {
            'fields': ('contract_no', 'contract_name')
        }),
        (_('Lessee Information'), {
            'fields': (
                'lessee_name', 'lessee_type', 'lessee_contact',
                'lessee_phone', 'lessee_email', 'lessee_address', 'lessee_id_number'
            )
        }),
        (_('Lease Period'), {
            'fields': ('start_date', 'end_date', 'actual_start_date', 'actual_end_date')
        }),
        (_('Financial Terms'), {
            'fields': ('payment_type', 'total_rent', 'deposit_amount', 'deposit_paid')
        }),
        (_('Status'), {
            'fields': ('status', 'is_active_display', 'days_remaining_display', 'total_days_display')
        }),
        (_('Approval'), {
            'fields': ('approved_by', 'approved_at')
        }),
        (_('Financial Summary'), {
            'fields': ('unpaid_amount_display',)
        }),
        (_('Terms'), {
            'fields': ('terms', 'notes')
        }),
        (_('Audit'), {
            'fields': (
                'id', 'created_at', 'updated_at', 'created_by',
                'updated_by', 'deleted_at', 'deleted_by', 'is_deleted'
            ),
            'classes': ('collapse',)
        }),
    )

    def is_active_display(self, obj):
        """Display active status."""
        return obj.is_active()
    is_active_display.short_description = _('Is Active')
    is_active_display.boolean = True

    def days_remaining_display(self, obj):
        """Display days remaining."""
        return obj.days_remaining()
    days_remaining_display.short_description = _('Days Remaining')

    def total_days_display(self, obj):
        """Display total days."""
        return obj.total_days()
    total_days_display.short_description = _('Total Days')

    def unpaid_amount_display(self, obj):
        """Display unpaid amount."""
        return obj.unpaid_amount()
    unpaid_amount_display.short_description = _('Unpaid Amount')


class LeaseItemInline(admin.TabularInline):
    """Inline admin for LeaseItem."""
    model = LeaseItem
    extra = 0
    readonly_fields = ['days_leased', 'total_rent']
    fields = [
        'asset', 'daily_rate', 'insured_value',
        'actual_start_date', 'actual_end_date',
        'start_condition', 'return_condition', 'damage_description',
        'days_leased', 'total_rent'
    ]

    def days_leased(self, obj):
        return obj.days_leased
    days_leased.short_description = _('Days Leased')

    def total_rent(self, obj):
        return obj.total_rent
    total_rent.short_description = _('Total Rent')


class RentPaymentInline(admin.TabularInline):
    """Inline admin for RentPayment."""
    model = RentPayment
    extra = 0
    readonly_fields = ['payment_no', 'outstanding_amount', 'is_overdue']
    fields = [
        'payment_no', 'due_date', 'amount', 'paid_amount',
        'outstanding_amount', 'is_overdue', 'status', 'paid_date', 'payment_method'
    ]

    def outstanding_amount(self, obj):
        return obj.outstanding_amount
    outstanding_amount.short_description = _('Outstanding')

    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.short_description = _('Is Overdue')
    is_overdue.boolean = True


@admin.register(LeaseItem)
class LeaseItemAdmin(admin.ModelAdmin):
    """Lease Item Admin."""
    list_display = [
        'contract_link', 'asset_link', 'daily_rate',
        'start_condition', 'return_condition', 'days_leased', 'total_rent'
    ]
    list_filter = ['start_condition', 'return_condition', 'created_at']
    search_fields = ['contract__contract_no', 'asset__asset_name', 'asset__asset_code']
    readonly_fields = [
        'days_leased', 'total_rent',
        'created_at', 'updated_at', 'created_by'
    ]

    def contract_link(self, obj):
        """Display clickable link to contract."""
        if obj.contract:
            return format_html(
                '<a href="/admin/leasing/leasecontract/{}/change/">{}</a>',
                obj.contract.id,
                obj.contract.contract_no
            )
        return '-'
    contract_link.short_description = _('Contract')

    def asset_link(self, obj):
        """Display clickable link to asset."""
        if obj.asset:
            return format_html(
                '<a href="/admin/assets/asset/{}/change/">{}</a>',
                obj.asset.id,
                obj.asset.asset_name
            )
        return '-'
    asset_link.short_description = _('Asset')

    def days_leased(self, obj):
        return obj.days_leased
    days_leased.short_description = _('Days Leased')

    def total_rent(self, obj):
        return obj.total_rent
    total_rent.short_description = _('Total Rent')


@admin.register(RentPayment)
class RentPaymentAdmin(admin.ModelAdmin):
    """Rent Payment Admin."""
    list_display = [
        'payment_no', 'contract_link', 'due_date', 'amount',
        'paid_amount', 'outstanding_amount', 'status', 'is_overdue'
    ]
    list_filter = ['status', 'due_date', 'paid_date']
    search_fields = ['payment_no', 'contract__contract_no', 'contract__lessee_name']
    readonly_fields = [
        'payment_no', 'outstanding_amount', 'is_overdue',
        'created_at', 'updated_at', 'created_by'
    ]
    date_hierarchy = 'due_date'

    def contract_link(self, obj):
        """Display clickable link to contract."""
        if obj.contract:
            return format_html(
                '<a href="/admin/leasing/leasecontract/{}/change/">{}</a>',
                obj.contract.id,
                obj.contract.contract_no
            )
        return '-'
    contract_link.short_description = _('Contract')

    def outstanding_amount(self, obj):
        return obj.outstanding_amount
    outstanding_amount.short_description = _('Outstanding')

    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.short_description = _('Is Overdue')
    is_overdue.boolean = True


@admin.register(LeaseReturn)
class LeaseReturnAdmin(admin.ModelAdmin):
    """Lease Return Admin."""
    list_display = [
        'return_no', 'contract_link', 'asset_link', 'return_date',
        'condition', 'damage_fee', 'deposit_deduction', 'refund_amount'
    ]
    list_filter = ['condition', 'return_date']
    search_fields = ['return_no', 'contract__contract_no', 'asset__asset_name']
    readonly_fields = [
        'return_no',
        'created_at', 'updated_at', 'created_by'
    ]
    date_hierarchy = 'return_date'

    def contract_link(self, obj):
        """Display clickable link to contract."""
        if obj.contract:
            return format_html(
                '<a href="/admin/leasing/leasecontract/{}/change/">{}</a>',
                obj.contract.id,
                obj.contract.contract_no
            )
        return '-'
    contract_link.short_description = _('Contract')

    def asset_link(self, obj):
        """Display clickable link to asset."""
        if obj.asset:
            return format_html(
                '<a href="/admin/assets/asset/{}/change/">{}</a>',
                obj.asset.id,
                obj.asset.asset_name
            )
        return '-'
    asset_link.short_description = _('Asset')


@admin.register(LeaseExtension)
class LeaseExtensionAdmin(admin.ModelAdmin):
    """Lease Extension Admin."""
    list_display = [
        'extension_no', 'contract_link', 'original_end_date',
        'new_end_date', 'additional_days', 'additional_rent'
    ]
    list_filter = ['created_at', 'approved_at']
    search_fields = ['extension_no', 'contract__contract_no']
    readonly_fields = [
        'extension_no', 'additional_days',
        'created_at', 'updated_at', 'created_by', 'approved_by', 'approved_at'
    ]
    date_hierarchy = 'created_at'

    def contract_link(self, obj):
        """Display clickable link to contract."""
        if obj.contract:
            return format_html(
                '<a href="/admin/leasing/leasecontract/{}/change/">{}</a>',
                obj.contract.id,
                obj.contract.contract_no
            )
        return '-'
    contract_link.short_description = _('Contract')

    def additional_days(self, obj):
        return obj.additional_days
    additional_days.short_description = _('Days Added')
