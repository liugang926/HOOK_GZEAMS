"""
Condition Evaluator Service

Evaluates condition expressions in workflow nodes.
Supports various operators, OR/AND condition groups,
business data field resolution, and edge-level conditions.
"""
import logging

from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ConditionEvaluator:
    """
    Condition Evaluator Service.

    Evaluates condition expressions to determine workflow branching.
    Conditions are evaluated against workflow instance variables and,
    optionally, linked business document fields.

    Supported operators:
    - eq: Equal to
    - ne: Not equal to
    - gt: Greater than
    - gte: Greater than or equal to
    - lt: Less than
    - lte: Less than or equal to
    - in: In list
    - not_in: Not in list
    - contains: Contains string
    - not_contains: Does not contain string
    - is_empty: Is empty or null
    - is_not_empty: Is not empty and not null
    - between: Between two values (inclusive)

    Condition grouping:
    - Flat conditions list: AND logic (backward compatible)
    - conditionGroups with groupLogic: OR/AND between groups,
      each group has its own inner logic (AND/OR)
    """

    # Operator constants
    OP_EQ = 'eq'
    OP_NE = 'ne'
    OP_GT = 'gt'
    OP_GTE = 'gte'
    OP_LT = 'lt'
    OP_LTE = 'lte'
    OP_IN = 'in'
    OP_NOT_IN = 'not_in'
    OP_CONTAINS = 'contains'
    OP_NOT_CONTAINS = 'not_contains'
    OP_IS_EMPTY = 'is_empty'
    OP_IS_NOT_EMPTY = 'is_not_empty'
    OP_BETWEEN = 'between'

    OPERATORS = [
        OP_EQ, OP_NE, OP_GT, OP_GTE, OP_LT, OP_LTE,
        OP_IN, OP_NOT_IN, OP_CONTAINS, OP_NOT_CONTAINS,
        OP_IS_EMPTY, OP_IS_NOT_EMPTY, OP_BETWEEN,
    ]

    def __init__(self):
        """Initialize the condition evaluator."""
        # Per-evaluation cache for business object lookups
        self._business_object_cache = {}

    # === Public API ===

    def evaluate_conditions(self, conditions, instance):
        """
        Evaluate multiple conditions (AND logic).

        Args:
            conditions: List of condition objects
            instance: WorkflowInstance with variables

        Returns:
            bool: True if all conditions evaluate to True
        """
        if not conditions:
            return True  # No conditions means always true

        for condition in conditions:
            if not self.evaluate_condition(condition, instance):
                return False

        return True

    def evaluate_conditions_with_logic(self, conditions, instance, logic='and'):
        """
        Evaluate multiple conditions with specified logic operator.

        Args:
            conditions: List of condition objects
            instance: WorkflowInstance with variables
            logic: 'and' or 'or'

        Returns:
            bool: Result based on the logic operator
        """
        if not conditions:
            return True

        if logic == 'or':
            return any(
                self.evaluate_condition(c, instance) for c in conditions
            )
        else:
            # Default to AND
            return all(
                self.evaluate_condition(c, instance) for c in conditions
            )

    def evaluate_condition_groups(self, condition_groups, instance, group_logic='and'):
        """
        Evaluate condition groups with OR/AND logic between groups.

        Schema:
        {
            "conditionGroups": [
                {
                    "logic": "and",
                    "conditions": [
                        {"field": "amount", "operator": "gt", "value": 5000},
                        {"field": "category", "operator": "eq", "value": "IT"}
                    ]
                },
                {
                    "logic": "and",
                    "conditions": [
                        {"field": "priority", "operator": "eq", "value": "urgent"}
                    ]
                }
            ],
            "groupLogic": "or"
        }

        Args:
            condition_groups: List of group objects, each with 'logic' and 'conditions'
            instance: WorkflowInstance with variables
            group_logic: 'and' or 'or' — logic between groups

        Returns:
            bool: Result of evaluating all groups with given logic
        """
        if not condition_groups:
            return True

        results = []
        for group in condition_groups:
            inner_logic = group.get('logic', 'and')
            conditions = group.get('conditions', [])
            result = self.evaluate_conditions_with_logic(
                conditions, instance, inner_logic
            )
            results.append(result)

        if group_logic == 'or':
            return any(results)
        else:
            return all(results)

    def evaluate_condition(self, condition, instance):
        """
        Evaluate a single condition.

        Args:
            condition: Condition object with field, operator, value
            instance: WorkflowInstance with variables

        Returns:
            bool: Result of condition evaluation
        """
        field = condition.get('field')
        operator = condition.get('operator')
        expected_value = condition.get('value')

        if not field or not operator:
            return False

        # Get actual value from instance variables or business document
        actual_value = self._get_field_value(instance, field)

        # Evaluate based on operator
        try:
            if operator == self.OP_EQ:
                return self._eq(actual_value, expected_value)

            elif operator == self.OP_NE:
                return self._ne(actual_value, expected_value)

            elif operator == self.OP_GT:
                return self._gt(actual_value, expected_value)

            elif operator == self.OP_GTE:
                return self._gte(actual_value, expected_value)

            elif operator == self.OP_LT:
                return self._lt(actual_value, expected_value)

            elif operator == self.OP_LTE:
                return self._lte(actual_value, expected_value)

            elif operator == self.OP_IN:
                return self._in(actual_value, expected_value)

            elif operator == self.OP_NOT_IN:
                return self._not_in(actual_value, expected_value)

            elif operator == self.OP_CONTAINS:
                return self._contains(actual_value, expected_value)

            elif operator == self.OP_NOT_CONTAINS:
                return self._not_contains(actual_value, expected_value)

            elif operator == self.OP_IS_EMPTY:
                return self._is_empty(actual_value)

            elif operator == self.OP_IS_NOT_EMPTY:
                return self._is_not_empty(actual_value)

            elif operator == self.OP_BETWEEN:
                return self._between(actual_value, expected_value)

            else:
                return False

        except (TypeError, ValueError):
            return False

    def evaluate_branch(self, branch, instance):
        """
        Evaluate a branch with conditions (supports both flat and grouped).

        Checks for conditionGroups first (new schema), falls back to
        flat conditions list (backward compatible).

        Args:
            branch: Branch object with conditions or conditionGroups
            instance: WorkflowInstance with variables

        Returns:
            bool: True if branch conditions are met
        """
        # Check for condition groups first (new schema)
        condition_groups = branch.get('conditionGroups')
        if condition_groups:
            group_logic = branch.get('groupLogic', 'and')
            return self.evaluate_condition_groups(
                condition_groups, instance, group_logic
            )

        # Fall back to flat conditions (backward compatible AND logic)
        conditions = branch.get('conditions', [])
        return self.evaluate_conditions(conditions, instance)

    def evaluate_edge_conditions(self, edge, instance):
        """
        Evaluate conditions on an edge (LogicFlow edge properties).

        Args:
            edge: Edge dict with properties that may contain conditions
            instance: WorkflowInstance with variables

        Returns:
            bool: True if edge conditions are met
        """
        properties = edge.get('properties', {})
        if not properties:
            return False

        # Check for condition groups on edge
        condition_groups = properties.get('conditionGroups')
        if condition_groups:
            group_logic = properties.get('groupLogic', 'and')
            return self.evaluate_condition_groups(
                condition_groups, instance, group_logic
            )

        # Check for flat conditions on edge
        conditions = properties.get('conditions')
        if conditions:
            return self.evaluate_conditions(conditions, instance)

        return False

    def get_matching_branch(self, branches, instance):
        """
        Find the first matching branch.

        Args:
            branches: List of branch objects
            instance: WorkflowInstance with variables

        Returns:
            dict or None: The matching branch or None
        """
        for branch in branches:
            if self.evaluate_branch(branch, instance):
                return branch

        return None

    def clear_cache(self):
        """Clear the per-evaluation business object cache."""
        self._business_object_cache = {}

    # === Private Helper Methods ===

    def _get_field_value(self, instance, field):
        """
        Get field value from instance variables OR business document.

        Fields prefixed with 'business.' resolve from the linked
        business document. All other fields resolve from instance.variables.

        Supports dot notation for nested access within variables.
        """
        if not field:
            return None

        if field.startswith('business.'):
            return self._get_business_field_value(instance, field[9:])

        return self._get_variable_value(instance, field)

    def _get_variable_value(self, instance, field):
        """
        Get field value from instance variables.

        Supports dot notation for nested fields.
        """
        variables = instance.variables or {}

        # Support dot notation for nested access
        keys = field.split('.')
        value = variables

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value

    def _get_business_field_value(self, instance, field_name):
        """
        Get field value from the linked business document.

        Resolves the business model class via ObjectRegistry, fetches
        the business object by ID, and retrieves the field value.
        Results are cached per instance to avoid repeated lookups.

        Args:
            instance: WorkflowInstance with business_object_code and business_id
            field_name: Name of the field on the business document

        Returns:
            Field value or None if not resolvable
        """
        cache_key = (instance.business_object_code, str(instance.business_id))

        if cache_key not in self._business_object_cache:
            business_obj = self._resolve_business_object(instance)
            self._business_object_cache[cache_key] = business_obj

        business_obj = self._business_object_cache.get(cache_key)
        if business_obj is None:
            return None

        # Try direct attribute access first
        if hasattr(business_obj, field_name):
            return getattr(business_obj, field_name, None)

        # Try custom_fields JSONB store
        custom_fields = getattr(business_obj, 'custom_fields', None)
        if isinstance(custom_fields, dict):
            return custom_fields.get(field_name)

        return None

    def _resolve_business_object(self, instance):
        """
        Resolve and fetch the linked business document.

        Args:
            instance: WorkflowInstance

        Returns:
            Business model instance or None
        """
        try:
            from apps.system.services.object_registry import ObjectRegistry
            meta = ObjectRegistry.get_or_create_from_db(
                instance.business_object_code
            )
            if meta and meta.model_class:
                try:
                    return meta.model_class.all_objects.get(
                        pk=instance.business_id, is_deleted=False
                    )
                except meta.model_class.DoesNotExist:
                    return None
        except Exception:
            logger.debug(
                "Could not resolve business object for code=%s, id=%s",
                instance.business_object_code,
                instance.business_id,
            )
        return None

    # === Operator Implementations ===

    def _eq(self, actual, expected):
        """Equal to comparison."""
        # Handle string comparison with numeric values
        if isinstance(actual, str) and isinstance(expected, (int, float)):
            try:
                return float(actual) == float(expected)
            except ValueError:
                return str(actual) == str(expected)

        if isinstance(expected, str) and isinstance(actual, (int, float)):
            try:
                return float(actual) == float(expected)
            except ValueError:
                return str(actual) == str(expected)

        return actual == expected

    def _ne(self, actual, expected):
        """Not equal to comparison."""
        return not self._eq(actual, expected)

    def _gt(self, actual, expected):
        """Greater than comparison."""
        try:
            return float(actual) > float(expected)
        except (TypeError, ValueError):
            return False

    def _gte(self, actual, expected):
        """Greater than or equal to comparison."""
        try:
            return float(actual) >= float(expected)
        except (TypeError, ValueError):
            return False

    def _lt(self, actual, expected):
        """Less than comparison."""
        try:
            return float(actual) < float(expected)
        except (TypeError, ValueError):
            return False

    def _lte(self, actual, expected):
        """Less than or equal to comparison."""
        try:
            return float(actual) <= float(expected)
        except (TypeError, ValueError):
            return False

    def _in(self, actual, expected):
        """In list comparison."""
        if not isinstance(expected, list):
            expected = [expected]

        return actual in expected

    def _not_in(self, actual, expected):
        """Not in list comparison."""
        return not self._in(actual, expected)

    def _contains(self, actual, expected):
        """String contains comparison."""
        if actual is None:
            return False

        actual_str = str(actual)
        expected_str = str(expected)

        return expected_str in actual_str

    def _not_contains(self, actual, expected):
        """String does not contain comparison."""
        return not self._contains(actual, expected)

    def _is_empty(self, actual):
        """Is empty or null comparison."""
        if actual is None:
            return True

        if isinstance(actual, (str, list, dict)):
            return len(actual) == 0

        return False

    def _is_not_empty(self, actual):
        """Is not empty and not null comparison."""
        return not self._is_empty(actual)

    def _between(self, actual, expected):
        """
        Between two values (inclusive).

        Expected value should be a list or tuple with exactly 2 elements.
        """
        if not isinstance(expected, (list, tuple)) or len(expected) != 2:
            return False

        try:
            min_val, max_val = sorted([float(expected[0]), float(expected[1])])
            actual_val = float(actual)
            return min_val <= actual_val <= max_val
        except (TypeError, ValueError):
            return False

    # === Validation ===

    def validate_condition(self, condition):
        """
        Validate a condition configuration.

        Args:
            condition: Condition object to validate

        Returns:
            tuple: (is_valid: bool, errors: list)
        """
        errors = []

        if not isinstance(condition, dict):
            return False, ['Condition must be an object.']

        # Check required fields
        if 'field' not in condition:
            errors.append('Condition missing required field: field')

        if 'operator' not in condition:
            errors.append('Condition missing required field: operator')

        # Validate operator
        operator = condition.get('operator')
        if operator and operator not in self.OPERATORS:
            errors.append(f'Invalid operator: {operator}')

        # Validate value based on operator
        if operator in [self.OP_IN, self.OP_NOT_IN]:
            value = condition.get('value')
            if not isinstance(value, list):
                errors.append(f'Operator {operator} requires value to be a list.')

        elif operator == self.OP_BETWEEN:
            value = condition.get('value')
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                errors.append(f'Operator {operator} requires value to be an array with exactly 2 elements.')

        return len(errors) == 0, errors

    def validate_branch(self, branch):
        """
        Validate a branch configuration.

        Args:
            branch: Branch object to validate

        Returns:
            tuple: (is_valid: bool, errors: list)
        """
        errors = []

        if not isinstance(branch, dict):
            return False, ['Branch must be an object.']

        # Check required fields
        if 'id' not in branch:
            errors.append('Branch missing required field: id')

        if 'name' not in branch:
            errors.append('Branch missing required field: name')

        # Check for condition groups (new schema)
        condition_groups = branch.get('conditionGroups')
        if condition_groups:
            is_valid, group_errors = self.validate_condition_groups(
                condition_groups
            )
            errors.extend(group_errors)
        else:
            # Validate flat conditions (backward compatible)
            conditions = branch.get('conditions', [])
            if not isinstance(conditions, list):
                errors.append('Branch conditions must be a list.')
            else:
                for idx, condition in enumerate(conditions):
                    is_valid, condition_errors = self.validate_condition(condition)
                    if not is_valid:
                        for error in condition_errors:
                            errors.append(f'Condition {idx}: {error}')

        return len(errors) == 0, errors

    def validate_condition_groups(self, condition_groups):
        """
        Validate condition groups schema.

        Args:
            condition_groups: List of group objects

        Returns:
            tuple: (is_valid: bool, errors: list)
        """
        errors = []

        if not isinstance(condition_groups, list):
            return False, ['conditionGroups must be a list.']

        if len(condition_groups) == 0:
            errors.append('conditionGroups must contain at least one group.')

        for group_idx, group in enumerate(condition_groups):
            if not isinstance(group, dict):
                errors.append(f'Group {group_idx}: must be an object.')
                continue

            # Validate logic field
            logic = group.get('logic', 'and')
            if logic not in ('and', 'or'):
                errors.append(
                    f'Group {group_idx}: invalid logic "{logic}", '
                    f'must be "and" or "or".'
                )

            # Validate conditions within group
            conditions = group.get('conditions', [])
            if not isinstance(conditions, list):
                errors.append(
                    f'Group {group_idx}: conditions must be a list.'
                )
            elif len(conditions) == 0:
                errors.append(
                    f'Group {group_idx}: must have at least one condition.'
                )
            else:
                for cond_idx, cond in enumerate(conditions):
                    is_valid, cond_errors = self.validate_condition(cond)
                    if not is_valid:
                        for err in cond_errors:
                            errors.append(
                                f'Group {group_idx}, Condition {cond_idx}: {err}'
                            )

        return len(errors) == 0, errors
