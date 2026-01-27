"""
Finance Module Django Admin Configuration

Admin interface for financial vouchers, voucher entries, and voucher templates.
"""
from django.contrib import admin
from .models import FinanceVoucher, VoucherEntry, VoucherTemplate


class VoucherEntryInline(admin.TabularInline):
    """Inline admin for voucher entries"""
    model = VoucherEntry
    extra = 0
    fields = ['line_no', 'account_code', 'account_name', 'debit_amount', 'credit_amount', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FinanceVoucher)
class FinanceVoucherAdmin(admin.ModelAdmin):
    """Admin for Finance Voucher"""
    list_display = [
        'voucher_no', 'voucher_date', 'business_type', 'summary',
        'total_amount', 'status', 'erp_voucher_no', 'created_at'
    ]
    list_filter = ['business_type', 'status', 'voucher_date', 'created_at']
    search_fields = ['voucher_no', 'summary', 'notes', 'erp_voucher_no']
    ordering = ['-voucher_date', '-created_at']
    readonly_fields = ['created_at', 'updated_at', 'posted_at']
    inlines = [VoucherEntryInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('voucher_no', 'voucher_date', 'business_type', 'summary', 'total_amount')
        }),
        ('Status', {
            'fields': ('status', 'notes')
        }),
        ('ERP Integration', {
            'fields': ('erp_voucher_no', 'posted_at', 'posted_by'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(VoucherEntry)
class VoucherEntryAdmin(admin.ModelAdmin):
    """Admin for Voucher Entry"""
    list_display = [
        'voucher', 'line_no', 'account_code', 'account_name',
        'debit_amount', 'credit_amount', 'created_at'
    ]
    list_filter = ['voucher__business_type', 'created_at']
    search_fields = [
        'voucher__voucher_no', 'account_code', 'account_name', 'description'
    ]
    ordering = ['voucher', 'line_no']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(VoucherTemplate)
class VoucherTemplateAdmin(admin.ModelAdmin):
    """Admin for Voucher Template"""
    list_display = [
        'code', 'name', 'business_type', 'is_active', 'created_at'
    ]
    list_filter = ['business_type', 'is_active', 'created_at']
    search_fields = ['code', 'name', 'description']
    ordering = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'business_type', 'is_active')
        }),
        ('Template Configuration', {
            'fields': ('template_config', 'description')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
