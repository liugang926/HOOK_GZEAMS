"""
Serializers for Approval Delegate model.
"""
from rest_framework import serializers
from apps.common.serializers.base import (
    BaseModelSerializer,
    BaseModelWithAuditSerializer,
    BaseListSerializer
)
from apps.mobile.models import ApprovalDelegate


class ApprovalDelegateSerializer(BaseModelSerializer):
    """Serializer for ApprovalDelegate."""

    delegate_type_display = serializers.CharField(source='get_delegate_type_display', read_only=True)
    delegate_scope_display = serializers.CharField(source='get_delegate_scope_display', read_only=True)
    delegator_name = serializers.CharField(source='delegator.username', read_only=True)
    delegate_name = serializers.CharField(source='delegate.username', read_only=True)
    revoked_by_name = serializers.CharField(source='revoked_by.username', read_only=True, allow_null=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = ApprovalDelegate
        fields = BaseModelSerializer.Meta.fields + [
            'delegator',
            'delegator_name',
            'delegate',
            'delegate_name',
            'delegate_type',
            'delegate_type_display',
            'delegate_scope',
            'delegate_scope_display',
            'start_time',
            'end_time',
            'scope_config',
            'reason',
            'is_active',
            'is_revoked',
            'revoked_at',
            'revoked_by',
            'revoked_by_name',
            'approved_count',
            'is_valid',
        ]


class ApprovalDelegateListSerializer(BaseListSerializer):
    """Optimized serializer for approval delegate list views."""

    delegate_type_display = serializers.CharField(source='get_delegate_type_display', read_only=True)
    delegate_scope_display = serializers.CharField(source='get_delegate_scope_display', read_only=True)
    delegator_name = serializers.CharField(source='delegator.username', read_only=True)
    delegate_name = serializers.CharField(source='delegate.username', read_only=True)

    class Meta(BaseListSerializer.Meta):
        model = ApprovalDelegate
        fields = BaseListSerializer.Meta.fields + [
            'delegator',
            'delegator_name',
            'delegate',
            'delegate_name',
            'delegate_type',
            'delegate_type_display',
            'delegate_scope',
            'start_time',
            'end_time',
            'is_active',
            'is_revoked',
            'approved_count',
        ]


class ApprovalDelegateDetailSerializer(BaseModelWithAuditSerializer):
    """Detailed serializer for ApprovalDelegate."""

    delegate_type_display = serializers.CharField(source='get_delegate_type_display', read_only=True)
    delegate_scope_display = serializers.CharField(source='get_delegate_scope_display', read_only=True)
    delegator_name = serializers.CharField(source='delegator.username', read_only=True)
    delegator_email = serializers.CharField(source='delegator.email', read_only=True)
    delegate_name = serializers.CharField(source='delegate.username', read_only=True)
    delegate_email = serializers.CharField(source='delegate.email', read_only=True)
    revoked_by_name = serializers.CharField(source='revoked_by.username', read_only=True, allow_null=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = ApprovalDelegate
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'delegator',
            'delegator_name',
            'delegator_email',
            'delegate',
            'delegate_name',
            'delegate_email',
            'delegate_type',
            'delegate_type_display',
            'delegate_scope',
            'delegate_scope_display',
            'start_time',
            'end_time',
            'scope_config',
            'reason',
            'is_active',
            'is_revoked',
            'revoked_at',
            'revoked_by',
            'revoked_by_name',
            'approved_count',
            'is_valid',
        ]
