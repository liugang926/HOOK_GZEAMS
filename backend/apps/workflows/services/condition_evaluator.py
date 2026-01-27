"""
Condition Evaluator Service

Evaluates condition expressions in workflow nodes.
Supports various operators and field types for branching logic.
"""
from django.core.exceptions import ValidationError


class ConditionEvaluator:
    """
    Condition Evaluator Service.

    Evaluates condition expressions to determine workflow branching.
    Conditions are evaluated against workflow instance variables.

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
        pass

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

        # Get actual value from instance variables
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
        Evaluate a branch with multiple conditions.

        Args:
            branch: Branch object with name and conditions
            instance: WorkflowInstance with variables

        Returns:
            bool: True if all branch conditions are met
        """
        conditions = branch.get('conditions', [])
        return self.evaluate_conditions(conditions, instance)

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

    # === Private Helper Methods ===

    def _get_field_value(self, instance, field):
        """
        Get field value from instance variables.

        Supports dot notation for nested fields.
        """
        if not field:
            return None

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

        # Validate conditions
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
