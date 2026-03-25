"""
Rule Engine Service - evaluates and executes business rules.

This module provides the core rule engine that:
- Evaluates JSON Logic conditions
- Executes rule actions
- Manages rule priorities and execution order
- Logs rule executions for auditing
"""
import time
from typing import Dict, List, Any, Optional, Tuple
from django.db import transaction
from django.utils import timezone

try:
    from json_logic import jsonLogic
except ImportError:
    # Fallback to simpler evaluation if json-logic not installed
    jsonLogic = None


class RuleEngineError(Exception):
    """Exception raised by the rule engine."""
    pass


class ValidationError:
    """Represents a validation error from a rule."""
    
    def __init__(self, field: str, message: str, rule_code: str = None):
        self.field = field
        self.message = message
        self.rule_code = rule_code
    
    def to_dict(self) -> dict:
        return {
            'field': self.field,
            'message': self.message,
            'rule_code': self.rule_code
        }


class RuleEngine:
    """
    JSON Logic-based business rule engine.
    
    Supports rule types:
    - validation: Field and cross-field validation
    - visibility: Conditional field display
    - computed: Derived field values
    - linkage: Field change propagation
    - trigger: Event-driven actions
    """
    
    def __init__(self, business_object_code: str):
        """
        Initialize the rule engine for a business object.
        
        Args:
            business_object_code: Code of the business object
        """
        self.bo_code = business_object_code
        self._rules_cache = None
        self._log_executions = True
    
    @property
    def rules(self) -> List:
        """Lazy load and cache rules for this business object."""
        if self._rules_cache is None:
            from apps.system.models import BusinessRule
            self._rules_cache = list(
                BusinessRule.objects.filter(
                    business_object__code=self.bo_code,
                    is_active=True,
                    is_deleted=False
                ).select_related('business_object').order_by('-priority')
            )
        return self._rules_cache
    
    def get_rules_by_type(self, rule_type: str) -> List:
        """Get rules of a specific type."""
        return [r for r in self.rules if r.rule_type == rule_type]
    
    def evaluate_condition(self, condition: dict, context: dict) -> bool:
        """
        Evaluate a JSON Logic condition.
        
        Args:
            condition: JSON Logic condition object
            context: Data context for variable resolution
            
        Returns:
            Boolean result of condition evaluation
        """
        if not condition:
            return True
            
        if jsonLogic:
            try:
                result = jsonLogic(condition, context)
                return bool(result)
            except Exception as e:
                raise RuleEngineError(f"Condition evaluation failed: {str(e)}")
        else:
            # Simple fallback for basic conditions
            return self._simple_eval(condition, context)
    
    def _simple_eval(self, condition: dict, context: dict) -> bool:
        """Simple condition evaluator as fallback."""
        if not isinstance(condition, dict):
            return bool(condition)
        
        # Handle basic operators
        for op, args in condition.items():
            if op == '==':
                left = self._resolve_value(args[0], context)
                right = self._resolve_value(args[1], context)
                return left == right
            elif op == '!=':
                left = self._resolve_value(args[0], context)
                right = self._resolve_value(args[1], context)
                return left != right
            elif op == '>':
                left = self._resolve_value(args[0], context)
                right = self._resolve_value(args[1], context)
                return left > right
            elif op == '<':
                left = self._resolve_value(args[0], context)
                right = self._resolve_value(args[1], context)
                return left < right
            elif op == 'and':
                return all(self._simple_eval(arg, context) for arg in args)
            elif op == 'or':
                return any(self._simple_eval(arg, context) for arg in args)
            elif op == '!':
                return not self._simple_eval(args, context)
            elif op == 'var':
                value = self._get_var(args, context)
                return bool(value)
        
        return True
    
    def _resolve_value(self, value: Any, context: dict) -> Any:
        """Resolve a value that may be a var reference."""
        if isinstance(value, dict) and 'var' in value:
            return self._get_var(value['var'], context)
        return value
    
    def _get_var(self, path: str, context: dict) -> Any:
        """Get a variable value from context using dot notation."""
        parts = path.split('.') if isinstance(path, str) else [path]
        result = context
        for part in parts:
            if isinstance(result, dict):
                result = result.get(part)
            else:
                return None
        return result
    
    def validate_record(
        self, 
        record: dict, 
        event: str = 'update'
    ) -> Tuple[bool, List[ValidationError]]:
        """
        Execute all validation rules on a record.
        
        Args:
            record: Record data to validate
            event: Trigger event (create, update, submit)
            
        Returns:
            Tuple of (is_valid, list of ValidationError)
        """
        errors = []
        validation_rules = self.get_rules_by_type('validation')
        
        for rule in validation_rules:
            # Check if rule applies to this event
            if rule.trigger_events and event not in rule.trigger_events:
                continue
            
            start_time = time.time()
            try:
                condition_result = self.evaluate_condition(rule.condition, record)
                
                # For validation rules, condition=True means validation FAILED
                if condition_result:
                    error = ValidationError(
                        field=rule.target_field or '_form',
                        message=rule.error_message or rule.action.get('error_message', '验证失败'),
                        rule_code=rule.rule_code
                    )
                    errors.append(error)
                
                if self._log_executions:
                    self._log_execution(
                        rule=rule,
                        record_id=record.get('id'),
                        event=event,
                        input_data=record,
                        condition_result=condition_result,
                        action_executed=condition_result,
                        result={'error': error.to_dict()} if condition_result else {},
                        execution_time=int((time.time() - start_time) * 1000)
                    )
                    
            except Exception as e:
                errors.append(ValidationError(
                    field='_form',
                    message=f'规则执行错误: {str(e)}',
                    rule_code=rule.rule_code
                ))
        
        return len(errors) == 0, errors
    
    def get_visibility_rules(self, record: dict) -> Dict[str, bool]:
        """
        Evaluate visibility rules and return field visibility map.
        
        Args:
            record: Current record data
            
        Returns:
            Dict mapping field codes to visibility boolean
        """
        visibility_map = {}
        visibility_rules = self.get_rules_by_type('visibility')
        
        for rule in visibility_rules:
            try:
                condition_result = self.evaluate_condition(rule.condition, record)
                
                # Get affected fields from action
                action = rule.action
                fields = action.get('fields', [])
                visible = action.get('visible', True)
                
                # Apply visibility based on condition result
                for field in fields:
                    if condition_result:
                        visibility_map[field] = visible
                    else:
                        visibility_map[field] = not visible
                        
            except Exception:
                # On error, default to visible
                pass
        
        return visibility_map
    
    def compute_fields(self, record: dict) -> Dict[str, Any]:
        """
        Execute computed field rules and return computed values.
        
        Args:
            record: Current record data
            
        Returns:
            Dict of computed field values
        """
        computed_values = {}
        computed_rules = self.get_rules_by_type('computed')
        
        for rule in computed_rules:
            try:
                # Check condition (if any)
                if rule.condition and not self.evaluate_condition(rule.condition, record):
                    continue
                
                action = rule.action
                target_field = action.get('target_field') or rule.target_field
                formula = action.get('formula', '')
                
                if target_field and formula:
                    # Simple formula evaluation using existing formula engine
                    from apps.system.services.dynamic_data_service import DynamicDataService
                    import re
                    
                    expression = formula
                    for field_code, value in record.items():
                        expression = re.sub(
                            rf'\{{{field_code}\}}',
                            str(value) if value is not None else '0',
                            expression
                        )
                    
                    try:
                        from simpleeval import simple_eval
                        result = simple_eval(expression)
                        computed_values[target_field] = result
                    except Exception:
                        computed_values[target_field] = 0
                        
            except Exception:
                pass
        
        return computed_values
    
    def execute_linkage(self, record: dict, changed_field: str) -> Dict[str, Any]:
        """
        Execute linkage rules for a changed field.
        
        Args:
            record: Current record data
            changed_field: Field code that changed
            
        Returns:
            Dict of field updates to apply
        """
        updates = {}
        linkage_rules = self.get_rules_by_type('linkage')
        
        for rule in linkage_rules:
            # Check if this rule is triggered by the changed field
            trigger_events = rule.trigger_events or []
            field_trigger = f'field_change:{changed_field}'
            
            if trigger_events and field_trigger not in trigger_events:
                if 'field_change' not in trigger_events:
                    continue
            
            try:
                # Check condition
                if rule.condition and not self.evaluate_condition(rule.condition, record):
                    continue
                
                action = rule.action
                target_field = action.get('target_field')
                source_field = action.get('source_field')
                value = action.get('value')
                
                if target_field:
                    if source_field:
                        # Copy from source field
                        updates[target_field] = self._get_var(source_field, record)
                    elif value is not None:
                        # Set fixed value
                        updates[target_field] = value
                        
            except Exception:
                pass
        
        return updates
    
    def evaluate_all(self, record: dict, event: str = 'update') -> dict:
        """
        Evaluate all rule types and return combined result.
        
        Args:
            record: Record data
            event: Trigger event
            
        Returns:
            Dict with visibility, validation, computed, and linkage results
        """
        is_valid, validation_errors = self.validate_record(record, event)
        
        return {
            'visibility': self.get_visibility_rules(record),
            'validation': {
                'is_valid': is_valid,
                'errors': [e.to_dict() for e in validation_errors]
            },
            'computed': self.compute_fields(record),
            'linkage': {}  # Linkage requires specific field change context
        }
    
    def _log_execution(
        self,
        rule,
        record_id: Optional[str],
        event: str,
        input_data: dict,
        condition_result: bool,
        action_executed: bool,
        result: dict,
        execution_time: int,
        error: str = ''
    ):
        """Log rule execution for auditing."""
        try:
            from apps.system.models import RuleExecution
            
            RuleExecution.objects.create(
                rule=rule,
                target_record_id=record_id or '00000000-0000-0000-0000-000000000000',
                target_record_type=self.bo_code,
                trigger_event=event,
                input_data=input_data,
                condition_result=condition_result,
                action_executed=action_executed,
                execution_result=result,
                execution_time_ms=execution_time,
                has_error=bool(error),
                error_message=error
            )
        except Exception:
            # Don't let logging errors affect rule execution
            pass
    
    def invalidate_cache(self):
        """Clear the rules cache."""
        self._rules_cache = None
