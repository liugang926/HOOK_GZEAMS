"""
Business Rule ViewSet for managing business rules via API.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import BaseResponse
from apps.system.models import BusinessRule, RuleExecution
from apps.system.serializers import (
    BusinessRuleSerializer,
    BusinessRuleCreateSerializer,
    RuleExecutionSerializer,
    RuleEvaluationRequestSerializer,
)
from apps.system.services.rule_engine import RuleEngine


class BusinessRuleFilter(filters.FilterSet):
    """Filter for business rules."""
    
    business_object = filters.CharFilter(field_name='business_object__code')
    rule_type = filters.CharFilter()
    is_active = filters.BooleanFilter()
    
    class Meta:
        model = BusinessRule
        fields = ['business_object', 'rule_type', 'is_active']


class BusinessRuleViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for managing business rules.
    
    Provides CRUD operations for business rules and
    rule evaluation endpoints.
    """
    
    queryset = BusinessRule.objects.select_related('business_object').all()
    serializer_class = BusinessRuleSerializer
    filterset_class = BusinessRuleFilter
    search_fields = ['rule_code', 'rule_name', 'description']
    ordering_fields = ['priority', 'rule_type', 'created_at']
    ordering = ['-priority', 'rule_type']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BusinessRuleCreateSerializer
        return BusinessRuleSerializer
    
    @action(detail=False, methods=['get'], url_path='by-object/(?P<object_code>[^/.]+)')
    def by_object(self, request, object_code=None):
        """
        Get all rules for a specific business object.
        
        GET /api/system/rules/by-object/{object_code}/
        """
        rules = self.get_queryset().filter(
            business_object__code=object_code,
            is_active=True
        )
        serializer = self.get_serializer(rules, many=True)
        return BaseResponse.success(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='evaluate/(?P<object_code>[^/.]+)')
    def evaluate(self, request, object_code=None):
        """
        Evaluate all rules for a business object against provided data.
        
        POST /api/system/rules/evaluate/{object_code}/
        Body: {"record": {...}, "event": "update"}
        """
        serializer = RuleEvaluationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        record = serializer.validated_data['record']
        event = serializer.validated_data['event']
        
        try:
            engine = RuleEngine(object_code)
            result = engine.evaluate_all(record, event)
            return BaseResponse.success(result)
        except Exception as e:
            return BaseResponse.error(str(e))
    
    @action(detail=False, methods=['post'], url_path='validate/(?P<object_code>[^/.]+)')
    def validate_only(self, request, object_code=None):
        """
        Run only validation rules.
        
        POST /api/system/rules/validate/{object_code}/
        """
        record = request.data.get('record', {})
        event = request.data.get('event', 'update')
        
        try:
            engine = RuleEngine(object_code)
            is_valid, errors = engine.validate_record(record, event)
            return BaseResponse.success({
                'is_valid': is_valid,
                'errors': [e.to_dict() for e in errors]
            })
        except Exception as e:
            return BaseResponse.error(str(e))
    
    @action(detail=False, methods=['post'], url_path='visibility/(?P<object_code>[^/.]+)')
    def visibility(self, request, object_code=None):
        """
        Get field visibility rules result.
        
        POST /api/system/rules/visibility/{object_code}/
        """
        record = request.data.get('record', {})
        
        try:
            engine = RuleEngine(object_code)
            visibility_map = engine.get_visibility_rules(record)
            return BaseResponse.success(visibility_map)
        except Exception as e:
            return BaseResponse.error(str(e))


class RuleExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing rule execution logs (read-only).
    """
    
    queryset = RuleExecution.objects.select_related('rule').all()
    serializer_class = RuleExecutionSerializer
    filterset_fields = ['rule', 'target_record_id', 'trigger_event', 'has_error']
    ordering = ['-executed_at']
    
    @action(detail=False, methods=['get'], url_path='by-record/(?P<record_id>[^/.]+)')
    def by_record(self, request, record_id=None):
        """Get all rule executions for a specific record."""
        executions = self.get_queryset().filter(target_record_id=record_id)[:50]
        serializer = self.get_serializer(executions, many=True)
        return BaseResponse.success(serializer.data)
