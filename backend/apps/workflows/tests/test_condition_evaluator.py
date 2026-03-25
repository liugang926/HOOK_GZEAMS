"""
Tests for enhanced ConditionEvaluator service.

Covers: OR/AND condition groups, business data field resolution,
edge-level conditions, backward compatibility, and validation.
"""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.workflows.services.condition_evaluator import ConditionEvaluator


class _MockInstance:
    """Minimal mock of WorkflowInstance for evaluator tests."""

    def __init__(self, variables=None, business_object_code='test',
                 business_id='123', organization_id=None):
        self.variables = variables or {}
        self.business_object_code = business_object_code
        self.business_id = business_id
        self.organization_id = organization_id


# ---------------------------------------------------------------------------
# Backward-compatible flat-condition tests
# ---------------------------------------------------------------------------

class TestFlatConditions(TestCase):
    """Test that the original flat condition list (AND logic) still works."""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_empty_conditions_returns_true(self):
        """No conditions ⇒ always true."""
        instance = _MockInstance(variables={'x': 1})
        self.assertTrue(self.evaluator.evaluate_conditions([], instance))

    def test_and_all_true(self):
        """All conditions true ⇒ True."""
        instance = _MockInstance(variables={'amount': 15000, 'status': 'pending'})
        conditions = [
            {'field': 'amount', 'operator': 'gt', 'value': 10000},
            {'field': 'status', 'operator': 'eq', 'value': 'pending'},
        ]
        self.assertTrue(self.evaluator.evaluate_conditions(conditions, instance))

    def test_and_one_false(self):
        """One condition false ⇒ False."""
        instance = _MockInstance(variables={'amount': 5000, 'status': 'pending'})
        conditions = [
            {'field': 'amount', 'operator': 'gt', 'value': 10000},
            {'field': 'status', 'operator': 'eq', 'value': 'pending'},
        ]
        self.assertFalse(self.evaluator.evaluate_conditions(conditions, instance))

    def test_nested_field_access(self):
        """Dot-notation still works for nested variable access."""
        instance = _MockInstance(variables={'dept': {'id': 5}})
        cond = {'field': 'dept.id', 'operator': 'eq', 'value': 5}
        self.assertTrue(self.evaluator.evaluate_condition(cond, instance))


# ---------------------------------------------------------------------------
# OR / AND condition groups
# ---------------------------------------------------------------------------

class TestConditionGroups(TestCase):
    """Tests for evaluate_condition_groups and groupLogic."""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_or_group_any_match(self):
        """OR groupLogic: passes when any group matches."""
        instance = _MockInstance(variables={'priority': 'urgent', 'amount': 100})
        groups = [
            {
                'logic': 'and',
                'conditions': [
                    {'field': 'amount', 'operator': 'gt', 'value': 5000},
                    {'field': 'category', 'operator': 'eq', 'value': 'IT'},
                ],
            },
            {
                'logic': 'and',
                'conditions': [
                    {'field': 'priority', 'operator': 'eq', 'value': 'urgent'},
                ],
            },
        ]
        self.assertTrue(
            self.evaluator.evaluate_condition_groups(groups, instance, 'or')
        )

    def test_or_group_no_match(self):
        """OR groupLogic: fails when no group matches."""
        instance = _MockInstance(variables={'priority': 'low', 'amount': 100})
        groups = [
            {
                'logic': 'and',
                'conditions': [
                    {'field': 'amount', 'operator': 'gt', 'value': 5000},
                ],
            },
            {
                'logic': 'and',
                'conditions': [
                    {'field': 'priority', 'operator': 'eq', 'value': 'urgent'},
                ],
            },
        ]
        self.assertFalse(
            self.evaluator.evaluate_condition_groups(groups, instance, 'or')
        )

    def test_and_group_all_required(self):
        """AND groupLogic: requires all groups to match."""
        instance = _MockInstance(variables={'amount': 10000, 'priority': 'urgent'})
        groups = [
            {
                'logic': 'and',
                'conditions': [
                    {'field': 'amount', 'operator': 'gt', 'value': 5000},
                ],
            },
            {
                'logic': 'and',
                'conditions': [
                    {'field': 'priority', 'operator': 'eq', 'value': 'urgent'},
                ],
            },
        ]
        self.assertTrue(
            self.evaluator.evaluate_condition_groups(groups, instance, 'and')
        )

    def test_and_group_one_fails(self):
        """AND groupLogic: fails when one group fails."""
        instance = _MockInstance(variables={'amount': 10000, 'priority': 'low'})
        groups = [
            {
                'logic': 'and',
                'conditions': [
                    {'field': 'amount', 'operator': 'gt', 'value': 5000},
                ],
            },
            {
                'logic': 'and',
                'conditions': [
                    {'field': 'priority', 'operator': 'eq', 'value': 'urgent'},
                ],
            },
        ]
        self.assertFalse(
            self.evaluator.evaluate_condition_groups(groups, instance, 'and')
        )

    def test_inner_or_logic(self):
        """Inner group with logic 'or': any condition in group is enough."""
        instance = _MockInstance(variables={'status': 'approved'})
        groups = [
            {
                'logic': 'or',
                'conditions': [
                    {'field': 'status', 'operator': 'eq', 'value': 'approved'},
                    {'field': 'status', 'operator': 'eq', 'value': 'pending'},
                ],
            },
        ]
        self.assertTrue(
            self.evaluator.evaluate_condition_groups(groups, instance, 'and')
        )

    def test_empty_groups_returns_true(self):
        """Empty groups list ⇒ True."""
        instance = _MockInstance()
        self.assertTrue(
            self.evaluator.evaluate_condition_groups([], instance, 'and')
        )


# ---------------------------------------------------------------------------
# evaluate_branch backward compatibility with conditionGroups
# ---------------------------------------------------------------------------

class TestBranchEvaluation(TestCase):
    """Tests for evaluate_branch supporting both schemas."""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_flat_conditions_branch(self):
        """Branch with flat conditions (old schema) still works."""
        instance = _MockInstance(variables={'amount': 6000})
        branch = {
            'id': 'b1',
            'name': 'High Amount',
            'conditions': [
                {'field': 'amount', 'operator': 'gt', 'value': 5000},
            ],
        }
        self.assertTrue(self.evaluator.evaluate_branch(branch, instance))

    def test_condition_groups_branch(self):
        """Branch with conditionGroups (new schema) evaluates correctly."""
        instance = _MockInstance(variables={'amount': 100, 'priority': 'urgent'})
        branch = {
            'id': 'b2',
            'name': 'Priority Or High Amount',
            'conditionGroups': [
                {
                    'logic': 'and',
                    'conditions': [
                        {'field': 'amount', 'operator': 'gt', 'value': 5000},
                    ],
                },
                {
                    'logic': 'and',
                    'conditions': [
                        {'field': 'priority', 'operator': 'eq', 'value': 'urgent'},
                    ],
                },
            ],
            'groupLogic': 'or',
        }
        self.assertTrue(self.evaluator.evaluate_branch(branch, instance))

    def test_condition_groups_has_priority(self):
        """conditionGroups is checked before flat conditions."""
        instance = _MockInstance(variables={'a': 1})
        branch = {
            'id': 'b3',
            'name': 'Override Test',
            'conditions': [
                # This would be True
                {'field': 'a', 'operator': 'eq', 'value': 1},
            ],
            'conditionGroups': [
                {
                    'logic': 'and',
                    'conditions': [
                        # This is False — conditionGroups wins
                        {'field': 'a', 'operator': 'eq', 'value': 999},
                    ],
                },
            ],
            'groupLogic': 'and',
        }
        # conditionGroups takes priority → should be False
        self.assertFalse(self.evaluator.evaluate_branch(branch, instance))


# ---------------------------------------------------------------------------
# Edge-level condition evaluation
# ---------------------------------------------------------------------------

class TestEdgeConditions(TestCase):
    """Tests for evaluate_edge_conditions."""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_edge_flat_conditions(self):
        """Edge with flat conditions evaluates correctly."""
        instance = _MockInstance(variables={'amount': 10000})
        edge = {
            'id': 'e1',
            'sourceNodeId': 'cond_1',
            'targetNodeId': 'approval_1',
            'properties': {
                'conditions': [
                    {'field': 'amount', 'operator': 'gt', 'value': 5000},
                ],
            },
        }
        self.assertTrue(
            self.evaluator.evaluate_edge_conditions(edge, instance)
        )

    def test_edge_condition_groups(self):
        """Edge with conditionGroups evaluates correctly."""
        instance = _MockInstance(variables={'priority': 'urgent'})
        edge = {
            'id': 'e2',
            'sourceNodeId': 'cond_1',
            'targetNodeId': 'approval_2',
            'properties': {
                'conditionGroups': [
                    {
                        'logic': 'and',
                        'conditions': [
                            {'field': 'priority', 'operator': 'eq', 'value': 'urgent'},
                        ],
                    },
                ],
                'groupLogic': 'and',
            },
        }
        self.assertTrue(
            self.evaluator.evaluate_edge_conditions(edge, instance)
        )

    def test_edge_no_conditions(self):
        """Edge without conditions returns False."""
        instance = _MockInstance(variables={'x': 1})
        edge = {
            'id': 'e3',
            'sourceNodeId': 'a',
            'targetNodeId': 'b',
            'properties': {},
        }
        self.assertFalse(
            self.evaluator.evaluate_edge_conditions(edge, instance)
        )

    def test_edge_no_properties(self):
        """Edge without properties returns False."""
        instance = _MockInstance()
        edge = {'id': 'e4', 'sourceNodeId': 'a', 'targetNodeId': 'b'}
        self.assertFalse(
            self.evaluator.evaluate_edge_conditions(edge, instance)
        )


# ---------------------------------------------------------------------------
# Business data field resolution
# ---------------------------------------------------------------------------

class TestBusinessFieldResolution(TestCase):
    """Tests for fields prefixed with 'business.'."""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_variable_field_no_prefix(self):
        """Unprefixed field resolves from instance.variables."""
        instance = _MockInstance(variables={'amount': 5000})
        cond = {'field': 'amount', 'operator': 'eq', 'value': 5000}
        self.assertTrue(self.evaluator.evaluate_condition(cond, instance))

    @patch(
        'apps.workflows.services.condition_evaluator'
        '.ConditionEvaluator._resolve_business_object'
    )
    def test_business_field_prefix(self, mock_resolve):
        """'business.amount' resolves from business document."""
        business_obj = MagicMock()
        business_obj.amount = 20000
        mock_resolve.return_value = business_obj

        instance = _MockInstance(variables={})
        cond = {'field': 'business.amount', 'operator': 'gt', 'value': 10000}
        result = self.evaluator.evaluate_condition(cond, instance)
        self.assertTrue(result)

    @patch(
        'apps.workflows.services.condition_evaluator'
        '.ConditionEvaluator._resolve_business_object'
    )
    def test_business_custom_field(self, mock_resolve):
        """'business.x' falls back to custom_fields when no attribute."""
        business_obj = MagicMock(spec=[])
        business_obj.custom_fields = {'colour': 'red'}
        mock_resolve.return_value = business_obj

        instance = _MockInstance(variables={})
        cond = {'field': 'business.colour', 'operator': 'eq', 'value': 'red'}
        result = self.evaluator.evaluate_condition(cond, instance)
        self.assertTrue(result)

    @patch(
        'apps.workflows.services.condition_evaluator'
        '.ConditionEvaluator._resolve_business_object'
    )
    def test_business_field_model_not_found(self, mock_resolve):
        """Gracefully returns None when business model cannot be resolved."""
        mock_resolve.return_value = None

        instance = _MockInstance(variables={})
        cond = {'field': 'business.amount', 'operator': 'eq', 'value': 100}
        result = self.evaluator.evaluate_condition(cond, instance)
        self.assertFalse(result)

    @patch(
        'apps.workflows.services.condition_evaluator'
        '.ConditionEvaluator._resolve_business_object'
    )
    def test_business_object_cached(self, mock_resolve):
        """Business object is cached per evaluation session."""
        business_obj = MagicMock()
        business_obj.amount = 100
        business_obj.status = 'active'
        mock_resolve.return_value = business_obj

        instance = _MockInstance(variables={})
        self.evaluator.evaluate_condition(
            {'field': 'business.amount', 'operator': 'eq', 'value': 100},
            instance,
        )
        self.evaluator.evaluate_condition(
            {'field': 'business.status', 'operator': 'eq', 'value': 'active'},
            instance,
        )
        # Should only resolve once due to caching
        mock_resolve.assert_called_once()

    def test_cache_cleared(self):
        """clear_cache empties the lookup cache."""
        self.evaluator._business_object_cache[('x', '1')] = 'cached'
        self.evaluator.clear_cache()
        self.assertEqual(self.evaluator._business_object_cache, {})


# ---------------------------------------------------------------------------
# Validation — condition groups
# ---------------------------------------------------------------------------

class TestConditionGroupValidation(TestCase):
    """Tests for validate_condition_groups."""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_valid_groups(self):
        """Valid conditionGroups passes validation."""
        groups = [
            {
                'logic': 'and',
                'conditions': [
                    {'field': 'a', 'operator': 'eq', 'value': 1},
                ],
            },
        ]
        is_valid, errors = self.evaluator.validate_condition_groups(groups)
        self.assertTrue(is_valid, errors)

    def test_not_a_list(self):
        """conditionGroups that is not a list fails."""
        is_valid, errors = self.evaluator.validate_condition_groups('bad')
        self.assertFalse(is_valid)
        self.assertIn('conditionGroups must be a list.', errors[0])

    def test_empty_groups(self):
        """Empty conditionGroups produces error."""
        is_valid, errors = self.evaluator.validate_condition_groups([])
        self.assertFalse(is_valid)

    def test_invalid_logic(self):
        """Invalid group logic ('xor') produces error."""
        groups = [
            {
                'logic': 'xor',
                'conditions': [
                    {'field': 'a', 'operator': 'eq', 'value': 1},
                ],
            },
        ]
        is_valid, errors = self.evaluator.validate_condition_groups(groups)
        self.assertFalse(is_valid)

    def test_group_missing_conditions(self):
        """Group with no conditions produces error."""
        groups = [{'logic': 'and', 'conditions': []}]
        is_valid, errors = self.evaluator.validate_condition_groups(groups)
        self.assertFalse(is_valid)

    def test_invalid_condition_in_group(self):
        """Condition with invalid operator inside a group is caught."""
        groups = [
            {
                'logic': 'and',
                'conditions': [
                    {'field': 'a', 'operator': 'NOPE', 'value': 1},
                ],
            },
        ]
        is_valid, errors = self.evaluator.validate_condition_groups(groups)
        self.assertFalse(is_valid)


# ---------------------------------------------------------------------------
# Validation — branch (backward compatible + new schema)
# ---------------------------------------------------------------------------

class TestBranchValidation(TestCase):
    """Tests for validate_branch supporting both schemas."""

    def setUp(self):
        self.evaluator = ConditionEvaluator()

    def test_flat_valid_branch(self):
        """Valid flat-conditions branch passes."""
        branch = {
            'id': 'b1',
            'name': 'Branch 1',
            'conditions': [
                {'field': 'a', 'operator': 'eq', 'value': 1},
            ],
        }
        is_valid, errors = self.evaluator.validate_branch(branch)
        self.assertTrue(is_valid, errors)

    def test_groups_valid_branch(self):
        """Valid conditionGroups branch passes."""
        branch = {
            'id': 'b1',
            'name': 'Branch 1',
            'conditionGroups': [
                {
                    'logic': 'and',
                    'conditions': [
                        {'field': 'x', 'operator': 'gt', 'value': 0},
                    ],
                },
            ],
        }
        is_valid, errors = self.evaluator.validate_branch(branch)
        self.assertTrue(is_valid, errors)


# ---------------------------------------------------------------------------
# Import sanity checks
# ---------------------------------------------------------------------------

class TestConditionEvaluatorImports(TestCase):
    """Verify the module can be imported cleanly."""

    def test_import_class(self):
        from apps.workflows.services.condition_evaluator import ConditionEvaluator
        self.assertIsNotNone(ConditionEvaluator)

    def test_operators_list(self):
        evaluator = ConditionEvaluator()
        self.assertEqual(len(evaluator.OPERATORS), 13)
