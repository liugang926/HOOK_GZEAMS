"""
Business Rule serializers for API endpoints.
"""
from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from apps.system.models import BusinessRule, RuleExecution


class BusinessRuleSerializer(BaseModelSerializer):
    """Serializer for BusinessRule model."""
    
    business_object_code = serializers.CharField(
        source='business_object.code',
        read_only=True
    )
    
    class Meta(BaseModelSerializer.Meta):
        model = BusinessRule
        fields = BaseModelSerializer.Meta.fields + [
            'business_object',
            'business_object_code',
            'rule_code',
            'rule_name',
            'description',
            'rule_type',
            'priority',
            'is_active',
            'condition',
            'action',
            'target_field',
            'trigger_events',
            'error_message',
            'error_message_en',
        ]
        read_only_fields = ['business_object_code']


class BusinessRuleCreateSerializer(BaseModelSerializer):
    """Serializer for creating BusinessRule."""
    
    business_object_code = serializers.CharField(write_only=True)
    
    class Meta(BaseModelSerializer.Meta):
        model = BusinessRule
        fields = BaseModelSerializer.Meta.fields + [
            'business_object_code',
            'rule_code',
            'rule_name',
            'description',
            'rule_type',
            'priority',
            'is_active',
            'condition',
            'action',
            'target_field',
            'trigger_events',
            'error_message',
            'error_message_en',
        ]
    
    def create(self, validated_data):
        bo_code = validated_data.pop('business_object_code', None)
        if bo_code:
            from apps.system.models import BusinessObject
            try:
                validated_data['business_object'] = BusinessObject.objects.get(
                    code=bo_code, is_deleted=False
                )
            except BusinessObject.DoesNotExist:
                raise serializers.ValidationError(
                    {'business_object_code': f'BusinessObject with code "{bo_code}" not found.'}
                )
        return super().create(validated_data)


class RuleExecutionSerializer(BaseModelSerializer):
    """Serializer for RuleExecution logs."""
    
    rule_code = serializers.CharField(source='rule.rule_code', read_only=True)
    rule_name = serializers.CharField(source='rule.rule_name', read_only=True)
    
    class Meta(BaseModelSerializer.Meta):
        model = RuleExecution
        fields = BaseModelSerializer.Meta.fields + [
            'rule',
            'rule_code',
            'rule_name',
            'target_record_id',
            'target_record_type',
            'trigger_event',
            'input_data',
            'condition_result',
            'action_executed',
            'execution_result',
            'executed_at',
            'execution_time_ms',
            'has_error',
            'error_message',
        ]
        read_only_fields = fields


class RuleEvaluationRequestSerializer(serializers.Serializer):
    """Request serializer for rule evaluation."""
    
    record = serializers.JSONField(
        help_text='Record data to evaluate rules against'
    )
    event = serializers.ChoiceField(
        choices=['create', 'update', 'submit', 'approve'],
        default='update',
        help_text='Event type for rule evaluation'
    )


class RuleEvaluationResponseSerializer(serializers.Serializer):
    """Response serializer for rule evaluation."""
    
    visibility = serializers.DictField(
        child=serializers.BooleanField(),
        help_text='Field visibility map'
    )
    validation = serializers.DictField(
        help_text='Validation result with is_valid and errors'
    )
    computed = serializers.DictField(
        help_text='Computed field values'
    )
    linkage = serializers.DictField(
        help_text='Linkage updates'
    )
