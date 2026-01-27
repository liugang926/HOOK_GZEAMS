"""
Insurance management admin configuration.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    InsuranceCompany, InsurancePolicy, InsuredAsset,
    PremiumPayment, ClaimRecord, PolicyRenewal
)


@admin.register(InsuranceCompany)
class InsuranceCompanyAdmin(admin.ModelAdmin):
    """Insurance Company Admin."""

    list_display = [
        'code', 'name', 'short_name', 'company_type',
        'contact_person', 'contact_phone', 'is_active_display'
    ]
    list_filter = ['company_type', 'is_active', 'created_at']
    search_fields = ['code', 'name', 'short_name', 'contact_person']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'created_by',
        'updated_by', 'deleted_at', 'deleted_by', 'is_deleted'
    ]
    fieldsets = (
        (_('Company Information'), {
            'fields': ('code', 'name', 'short_name', 'company_type')
        }),
        (_('Contact Information'), {
            'fields': (
                'contact_person', 'contact_phone', 'contact_email',
                'website', 'address'
            )
        }),
        (_('Claims Contact'), {
            'fields': ('claims_phone', 'claims_email')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Notes'), {
            'fields': ('notes',)
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
        return obj.is_active
    is_active_display.short_description = _('Active')
    is_active_display.boolean = True


class InsuredAssetInline(admin.TabularInline):
    """Inline admin for InsuredAsset."""

    model = InsuredAsset
    extra = 0
    readonly_fields = ['asset_code', 'asset_name', 'insured_amount', 'premium_amount']
    fields = [
        'asset', 'asset_code', 'asset_name',
        'insured_amount', 'premium_amount',
        'asset_location', 'asset_usage',
        'valuation_method', 'valuation_date',
        'notes'
    ]

    def asset_code(self, obj):
        return obj.asset.asset_code if obj.asset else '-'
    asset_code.short_description = _('Asset Code')

    def asset_name(self, obj):
        return obj.asset.asset_name if obj.asset else '-'
    asset_name.short_description = _('Asset Name')


class PremiumPaymentInline(admin.TabularInline):
    """Inline admin for PremiumPayment."""

    model = PremiumPayment
    extra = 0
    readonly_fields = ['payment_no', 'outstanding_amount', 'is_overdue']
    fields = [
        'payment_no', 'due_date', 'amount', 'paid_amount',
        'outstanding_amount', 'is_overdue', 'status',
        'paid_date', 'payment_method', 'payment_reference'
    ]

    def outstanding_amount(self, obj):
        return obj.outstanding_amount
    outstanding_amount.short_description = _('Outstanding')

    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.short_description = _('Is Overdue')
    is_overdue.boolean = True


@admin.register(InsurancePolicy)
class InsurancePolicyAdmin(admin.ModelAdmin):
    """Insurance Policy Admin."""

    list_display = [
        'policy_no', 'company_name', 'insurance_type',
        'start_date', 'end_date', 'status',
        'total_premium', 'is_active_display',
        'days_until_expiry_display', 'is_expiring_soon_display'
    ]
    list_filter = ['status', 'insurance_type', 'payment_frequency', 'created_at']
    search_fields = ['policy_no', 'policy_name', 'company__name']
    readonly_fields = [
        'is_active_display', 'days_until_expiry_display',
        'is_expiring_soon_display', 'unpaid_premium_display',
        'total_insured_assets_display', 'total_claims_display',
        'id', 'created_at', 'updated_at', 'created_by',
        'updated_by', 'deleted_at', 'deleted_by', 'is_deleted'
    ]
    date_hierarchy = 'start_date'
    inlines = [InsuredAssetInline, PremiumPaymentInline]
    fieldsets = (
        (_('Policy Information'), {
            'fields': ('policy_no', 'policy_name', 'company')
        }),
        (_('Insurance Type'), {
            'fields': ('insurance_type', 'coverage_type')
        }),
        (_('Period'), {
            'fields': ('start_date', 'end_date', 'renewal_date')
        }),
        (_('Financial'), {
            'fields': (
                'total_insured_amount', 'total_premium', 'payment_frequency',
                'deductible_amount', 'deductible_type'
            )
        }),
        (_('Status'), {
            'fields': (
                'status', 'is_active_display',
                'days_until_expiry_display', 'is_expiring_soon_display'
            )
        }),
        (_('Statistics'), {
            'fields': (
                'unpaid_premium_display', 'total_insured_assets_display',
                'total_claims_display'
            )
        }),
        (_('Documents'), {
            'fields': ('policy_document',)
        }),
        (_('Terms'), {
            'fields': ('coverage_description', 'exclusion_clause', 'notes')
        }),
        (_('Audit'), {
            'fields': (
                'id', 'created_at', 'updated_at', 'created_by',
                'updated_by', 'deleted_at', 'deleted_by', 'is_deleted'
            ),
            'classes': ('collapse',)
        }),
    )

    def company_name(self, obj):
        return obj.company.name if obj.company else '-'
    company_name.short_description = _('Company')

    def is_active_display(self, obj):
        return obj.is_active
    is_active_display.short_description = _('Is Active')
    is_active_display.boolean = True

    def days_until_expiry_display(self, obj):
        return obj.days_until_expiry
    days_until_expiry_display.short_description = _('Days Until Expiry')

    def is_expiring_soon_display(self, obj):
        return obj.is_expiring_soon
    is_expiring_soon_display.short_description = _('Expiring Soon')
    is_expiring_soon_display.boolean = True

    def unpaid_premium_display(self, obj):
        return obj.unpaid_premium
    unpaid_premium_display.short_description = _('Unpaid Premium')

    def total_insured_assets_display(self, obj):
        return obj.total_insured_assets
    total_insured_assets_display.short_description = _('Insured Assets')

    def total_claims_display(self, obj):
        return obj.total_claims
    total_claims_display.short_description = _('Claims')


@admin.register(InsuredAsset)
class InsuredAssetAdmin(admin.ModelAdmin):
    """Insured Asset Admin."""

    list_display = [
        'policy_link', 'asset_link', 'insured_amount',
        'premium_amount', 'valuation_method'
    ]
    list_filter = ['valuation_method', 'created_at']
    search_fields = ['policy__policy_no', 'asset__asset_code', 'asset__asset_name']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'created_by',
        'updated_by', 'deleted_at', 'deleted_by', 'is_deleted'
    ]

    def policy_link(self, obj):
        if obj.policy:
            return format_html(
                '<a href="/admin/insurance/insurancepolicy/{}/change/">{}</a>',
                obj.policy.id,
                obj.policy.policy_no
            )
        return '-'
    policy_link.short_description = _('Policy')

    def asset_link(self, obj):
        if obj.asset:
            return format_html(
                '<a href="/admin/assets/asset/{}/change/">{}</a>',
                obj.asset.id,
                obj.asset.asset_name
            )
        return '-'
    asset_link.short_description = _('Asset')


@admin.register(PremiumPayment)
class PremiumPaymentAdmin(admin.ModelAdmin):
    """Premium Payment Admin."""

    list_display = [
        'payment_no', 'policy_link', 'due_date',
        'amount', 'paid_amount', 'outstanding_amount',
        'status', 'is_overdue'
    ]
    list_filter = ['status', 'due_date', 'paid_date']
    search_fields = ['payment_no', 'policy__policy_no', 'invoice_no']
    readonly_fields = [
        'outstanding_amount', 'is_overdue',
        'id', 'created_at', 'updated_at', 'created_by',
        'updated_by', 'deleted_at', 'deleted_by', 'is_deleted'
    ]
    date_hierarchy = 'due_date'

    def policy_link(self, obj):
        if obj.policy:
            return format_html(
                '<a href="/admin/insurance/insurancepolicy/{}/change/">{}</a>',
                obj.policy.id,
                obj.policy.policy_no
            )
        return '-'
    policy_link.short_description = _('Policy')

    def outstanding_amount(self, obj):
        return obj.outstanding_amount
    outstanding_amount.short_description = _('Outstanding')

    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.short_description = _('Is Overdue')
    is_overdue.boolean = True


@admin.register(ClaimRecord)
class ClaimRecordAdmin(admin.ModelAdmin):
    """Claim Record Admin."""

    list_display = [
        'claim_no', 'policy_link', 'asset_link',
        'incident_date', 'incident_type',
        'claimed_amount', 'approved_amount',
        'status', 'payout_ratio_display'
    ]
    list_filter = ['status', 'incident_type', 'incident_date']
    search_fields = ['claim_no', 'policy__policy_no', 'incident_description']
    readonly_fields = [
        'payout_ratio_display',
        'id', 'created_at', 'updated_at', 'created_by',
        'updated_by', 'deleted_at', 'deleted_by', 'is_deleted'
    ]
    date_hierarchy = 'incident_date'

    def policy_link(self, obj):
        if obj.policy:
            return format_html(
                '<a href="/admin/insurance/insurancepolicy/{}/change/">{}</a>',
                obj.policy.id,
                obj.policy.policy_no
            )
        return '-'
    policy_link.short_description = _('Policy')

    def asset_link(self, obj):
        if obj.asset:
            return format_html(
                '<a href="/admin/assets/asset/{}/change/">{}</a>',
                obj.asset.id,
                obj.asset.asset_name
            )
        return '-'
    asset_link.short_description = _('Asset')

    def payout_ratio_display(self, obj):
        return f"{obj.payout_ratio:.1f}%"
    payout_ratio_display.short_description = _('Payout Ratio')


@admin.register(PolicyRenewal)
class PolicyRenewalAdmin(admin.ModelAdmin):
    """Policy Renewal Admin."""

    list_display = [
        'renewal_no', 'original_policy_link', 'renewed_policy_link',
        'original_end_date', 'new_end_date',
        'original_premium', 'new_premium',
        'premium_change_display', 'premium_change_percent_display'
    ]
    list_filter = ['created_at', 'new_start_date']
    search_fields = ['renewal_no', 'original_policy__policy_no', 'renewed_policy__policy_no']
    readonly_fields = [
        'premium_change_display', 'premium_change_percent_display',
        'id', 'created_at', 'updated_at', 'created_by',
        'updated_by', 'deleted_at', 'deleted_by', 'is_deleted'
    ]
    date_hierarchy = 'created_at'

    def original_policy_link(self, obj):
        if obj.original_policy:
            return format_html(
                '<a href="/admin/insurance/insurancepolicy/{}/change/">{}</a>',
                obj.original_policy.id,
                obj.original_policy.policy_no
            )
        return '-'
    original_policy_link.short_description = _('Original Policy')

    def renewed_policy_link(self, obj):
        if obj.renewed_policy:
            return format_html(
                '<a href="/admin/insurance/insurancepolicy/{}/change/">{}</a>',
                obj.renewed_policy.id,
                obj.renewed_policy.policy_no
            )
        return '-'
    renewed_policy_link.short_description = _('Renewed Policy')

    def premium_change_display(self, obj):
        change = obj.premium_change
        color = 'green' if change >= 0 else 'red'
        return format_html(
            '<span style="color: {};">{:+.2f}</span>',
            color, change
        )
    premium_change_display.short_description = _('Premium Change')

    def premium_change_percent_display(self, obj):
        percent = obj.premium_change_percent
        color = 'green' if percent >= 0 else 'red'
        return format_html(
            '<span style="color: {};">{:+.1f}%</span>',
            color, percent
        )
    premium_change_percent_display.short_description = _('Change %')
