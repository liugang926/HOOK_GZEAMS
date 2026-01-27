"""
Tests for workflow validation service.

Tests for WorkflowValidationService including graph structure validation,
node validation, edge validation, and connectivity validation.
"""
from django.test import TestCase

from apps.workflows.services.workflow_validation import WorkflowValidationService


class WorkflowValidationServiceTest(TestCase):
    """Test cases for WorkflowValidationService."""

    def setUp(self):
        """Set up test validator."""
        self.validator = WorkflowValidationService()

        self.valid_graph_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
                {
                    'id': 'node_2',
                    'type': 'approval',
                    'x': 300,
                    'y': 100,
                    'text': 'Approve',
                    'properties': {
                        'approveType': 'or',
                        'approvers': [
                            {'type': 'user', 'id': 'user_1'},
                            {'type': 'role', 'id': 'role_1'}
                        ]
                    }
                },
                {'id': 'node_3', 'type': 'end', 'x': 500, 'y': 100, 'text': 'End'},
            ],
            'edges': [
                {'id': 'edge_1', 'sourceNodeId': 'node_1', 'targetNodeId': 'node_2', 'type': 'polyline'},
                {'id': 'edge_2', 'sourceNodeId': 'node_2', 'targetNodeId': 'node_3', 'type': 'polyline'},
            ]
        }

    def test_valid_workflow_passes_validation(self):
        """Test that a valid workflow passes validation."""
        is_valid, errors, warnings = self.validator.validate(self.valid_graph_data)

        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(warnings), 0)

    def test_validate_definition_simplified_interface(self):
        """Test the simplified validate_definition interface."""
        is_valid, errors = self.validator.validate_definition(self.valid_graph_data)

        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_missing_graph_data_nodes_field(self):
        """Test validation fails when nodes field is missing."""
        invalid_data = {'edges': []}

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('nodes' in e for e in errors))

    def test_missing_graph_data_edges_field(self):
        """Test validation fails when edges field is missing."""
        invalid_data = {'nodes': []}

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('edges' in e for e in errors))

    def test_invalid_graph_data_type(self):
        """Test validation fails when graph_data is not a dict."""
        is_valid, errors, warnings = self.validator.validate("not a dict")

        self.assertFalse(is_valid)
        self.assertTrue(any('dictionary' in e for e in errors))

    def test_missing_start_node(self):
        """Test validation fails when start node is missing."""
        invalid_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'end', 'x': 100, 'y': 100, 'text': 'End'},
            ],
            'edges': []
        }

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('start' in e.lower() for e in errors))

    def test_missing_end_node(self):
        """Test validation fails when end node is missing."""
        invalid_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
            ],
            'edges': []
        }

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('end' in e.lower() for e in errors))

    def test_multiple_start_nodes_fails(self):
        """Test validation fails with multiple start nodes."""
        invalid_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start 1'},
                {'id': 'node_2', 'type': 'start', 'x': 300, 'y': 100, 'text': 'Start 2'},
                {'id': 'node_3', 'type': 'end', 'x': 500, 'y': 100, 'text': 'End'},
            ],
            'edges': []
        }

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('only one' in e.lower() or 'start node' in e.lower() for e in errors))

    def test_duplicate_node_ids_fails(self):
        """Test validation fails with duplicate node IDs."""
        invalid_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
                {'id': 'node_1', 'type': 'end', 'x': 300, 'y': 100, 'text': 'End'},
            ],
            'edges': []
        }

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('duplicate' in e.lower() or 'node_1' in e for e in errors))

    def test_invalid_node_type(self):
        """Test validation fails with invalid node type."""
        invalid_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
                {'id': 'node_2', 'type': 'invalid_type', 'x': 300, 'y': 100, 'text': 'Invalid'},
                {'id': 'node_3', 'type': 'end', 'x': 500, 'y': 100, 'text': 'End'},
            ],
            'edges': [
                {'id': 'edge_1', 'sourceNodeId': 'node_1', 'targetNodeId': 'node_2'},
                {'id': 'edge_2', 'sourceNodeId': 'node_2', 'targetNodeId': 'node_3'},
            ]
        }

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('invalid_type' in e or 'invalid type' in e.lower() for e in errors))

    def test_edge_references_non_existent_source_node(self):
        """Test validation fails when edge references non-existent source."""
        invalid_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
                {'id': 'node_2', 'type': 'end', 'x': 300, 'y': 100, 'text': 'End'},
            ],
            'edges': [
                {'id': 'edge_1', 'sourceNodeId': 'non_existent', 'targetNodeId': 'node_1'},
            ]
        }

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('non_existent' in e or 'source' in e.lower() for e in errors))

    def test_edge_references_non_existent_target_node(self):
        """Test validation fails when edge references non-existent target."""
        invalid_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
                {'id': 'node_2', 'type': 'end', 'x': 300, 'y': 100, 'text': 'End'},
            ],
            'edges': [
                {'id': 'edge_1', 'sourceNodeId': 'node_1', 'targetNodeId': 'non_existent'},
            ]
        }

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('non_existent' in e or 'target' in e.lower() for e in errors))

    def test_self_loop_edge_fails(self):
        """Test validation fails when edge creates self-loop."""
        invalid_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
            ],
            'edges': [
                {'id': 'edge_1', 'sourceNodeId': 'node_1', 'targetNodeId': 'node_1'},
            ]
        }

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('self-loop' in e or 'self loop' in e.lower() for e in errors))

    def test_isolated_node_detected(self):
        """Test validation detects isolated nodes."""
        invalid_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
                {'id': 'node_2', 'type': 'approval', 'x': 300, 'y': 100, 'text': 'Isolated'},
                {'id': 'node_3', 'type': 'end', 'x': 500, 'y': 100, 'text': 'End'},
            ],
            'edges': [
                {'id': 'edge_1', 'sourceNodeId': 'node_1', 'targetNodeId': 'node_3'},
            ]
        }

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('isolated' in e.lower() or 'node_2' in e for e in errors))

    def test_approval_node_missing_approvers(self):
        """Test validation fails when approval node has no approvers."""
        invalid_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
                {
                    'id': 'node_2',
                    'type': 'approval',
                    'x': 300,
                    'y': 100,
                    'text': 'Approve',
                    'properties': {'approveType': 'or', 'approvers': []}
                },
                {'id': 'node_3', 'type': 'end', 'x': 500, 'y': 100, 'text': 'End'},
            ],
            'edges': [
                {'id': 'edge_1', 'sourceNodeId': 'node_1', 'targetNodeId': 'node_2'},
                {'id': 'edge_2', 'sourceNodeId': 'node_2', 'targetNodeId': 'node_3'},
            ]
        }

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('approvers' in e.lower() or 'node_2' in e for e in errors))

    def test_approval_node_invalid_approve_type(self):
        """Test validation fails with invalid approve type."""
        invalid_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
                {
                    'id': 'node_2',
                    'type': 'approval',
                    'x': 300,
                    'y': 100,
                    'text': 'Approve',
                    'properties': {
                        'approveType': 'invalid_type',
                        'approvers': [{'type': 'user', 'id': 'user_1'}]
                    }
                },
                {'id': 'node_3', 'type': 'end', 'x': 500, 'y': 100, 'text': 'End'},
            ],
            'edges': [
                {'id': 'edge_1', 'sourceNodeId': 'node_1', 'targetNodeId': 'node_2'},
                {'id': 'edge_2', 'sourceNodeId': 'node_2', 'targetNodeId': 'node_3'},
            ]
        }

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('invalid_approve_type' in e or 'approveType' in e for e in errors))

    def test_approval_node_invalid_approver_type(self):
        """Test validation fails with invalid approver type."""
        invalid_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
                {
                    'id': 'node_2',
                    'type': 'approval',
                    'x': 300,
                    'y': 100,
                    'text': 'Approve',
                    'properties': {
                        'approveType': 'or',
                        'approvers': [{'type': 'invalid_type', 'id': 'id_1'}]
                    }
                },
                {'id': 'node_3', 'type': 'end', 'x': 500, 'y': 100, 'text': 'End'},
            ],
            'edges': [
                {'id': 'edge_1', 'sourceNodeId': 'node_1', 'targetNodeId': 'node_2'},
                {'id': 'edge_2', 'sourceNodeId': 'node_2', 'targetNodeId': 'node_3'},
            ]
        }

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('invalid_type' in e or 'approver' in e.lower() for e in errors))

    def test_condition_node_missing_branches(self):
        """Test validation fails when condition node has insufficient branches."""
        invalid_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
                {
                    'id': 'node_2',
                    'type': 'condition',
                    'x': 300,
                    'y': 100,
                    'text': 'Condition',
                    'properties': {'branches': []}
                },
                {'id': 'node_3', 'type': 'end', 'x': 500, 'y': 100, 'text': 'End'},
            ],
            'edges': [
                {'id': 'edge_1', 'sourceNodeId': 'node_1', 'targetNodeId': 'node_2'},
                {'id': 'edge_2', 'sourceNodeId': 'node_2', 'targetNodeId': 'node_3'},
            ]
        }

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('branch' in e.lower() or 'node_2' in e for e in errors))

    def test_condition_node_branch_no_conditions(self):
        """Test validation fails when branch has no conditions."""
        invalid_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
                {
                    'id': 'node_2',
                    'type': 'condition',
                    'x': 300,
                    'y': 100,
                    'text': 'Condition',
                    'properties': {
                        'branches': [
                            {'name': 'Branch 1', 'conditions': []}
                        ]
                    }
                },
                {'id': 'node_3', 'type': 'end', 'x': 500, 'y': 100, 'text': 'End'},
            ],
            'edges': [
                {'id': 'edge_1', 'sourceNodeId': 'node_1', 'targetNodeId': 'node_2'},
                {'id': 'edge_2', 'sourceNodeId': 'node_2', 'targetNodeId': 'node_3'},
            ]
        }

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('condition' in e.lower() for e in errors))

    def test_condition_node_invalid_operator(self):
        """Test validation fails with invalid condition operator."""
        invalid_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
                {
                    'id': 'node_2',
                    'type': 'condition',
                    'x': 300,
                    'y': 100,
                    'text': 'Condition',
                    'properties': {
                        'branches': [
                            {
                                'name': 'Branch 1',
                                'conditions': [
                                    {'field': 'status', 'operator': 'invalid_op', 'value': 'active'}
                                ]
                            },
                            {
                                'name': 'Branch 2',
                                'conditions': [
                                    {'field': 'status', 'operator': 'eq', 'value': 'inactive'}
                                ]
                            }
                        ]
                    }
                },
                {'id': 'node_3', 'type': 'end', 'x': 500, 'y': 100, 'text': 'End'},
            ],
            'edges': [
                {'id': 'edge_1', 'sourceNodeId': 'node_1', 'targetNodeId': 'node_2'},
                {'id': 'edge_2', 'sourceNodeId': 'node_2', 'targetNodeId': 'node_3'},
            ]
        }

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('invalid_op' in e or 'operator' in e.lower() for e in errors))

    def test_condition_node_missing_condition_field(self):
        """Test validation fails when condition is missing field."""
        invalid_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
                {
                    'id': 'node_2',
                    'type': 'condition',
                    'x': 300,
                    'y': 100,
                    'text': 'Condition',
                    'properties': {
                        'branches': [
                            {
                                'name': 'Branch 1',
                                'conditions': [
                                    {'operator': 'eq', 'value': 'active'}
                                ]
                            },
                            {
                                'name': 'Branch 2',
                                'conditions': [
                                    {'field': 'status', 'operator': 'eq', 'value': 'inactive'}
                                ]
                            }
                        ]
                    }
                },
                {'id': 'node_3', 'type': 'end', 'x': 500, 'y': 100, 'text': 'End'},
            ],
            'edges': [
                {'id': 'edge_1', 'sourceNodeId': 'node_1', 'targetNodeId': 'node_2'},
                {'id': 'edge_2', 'sourceNodeId': 'node_2', 'targetNodeId': 'node_3'},
            ]
        }

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('field' in e.lower() for e in errors))

    def test_condition_node_missing_condition_value(self):
        """Test validation fails when condition is missing value."""
        invalid_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
                {
                    'id': 'node_2',
                    'type': 'condition',
                    'x': 300,
                    'y': 100,
                    'text': 'Condition',
                    'properties': {
                        'branches': [
                            {
                                'name': 'Branch 1',
                                'conditions': [
                                    {'field': 'status', 'operator': 'eq'}
                                ]
                            },
                            {
                                'name': 'Branch 2',
                                'conditions': [
                                    {'field': 'status', 'operator': 'eq', 'value': 'inactive'}
                                ]
                            }
                        ]
                    }
                },
                {'id': 'node_3', 'type': 'end', 'x': 500, 'y': 100, 'text': 'End'},
            ],
            'edges': [
                {'id': 'edge_1', 'sourceNodeId': 'node_1', 'targetNodeId': 'node_2'},
                {'id': 'edge_2', 'sourceNodeId': 'node_2', 'targetNodeId': 'node_3'},
            ]
        }

        is_valid, errors, warnings = self.validator.validate(invalid_data)

        self.assertFalse(is_valid)
        self.assertTrue(any('value' in e.lower() for e in errors))

    def test_valid_condition_node_passes(self):
        """Test valid condition node passes validation."""
        valid_data = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
                {
                    'id': 'node_2',
                    'type': 'condition',
                    'x': 300,
                    'y': 100,
                    'text': 'Condition',
                    'properties': {
                        'branches': [
                            {
                                'name': 'Branch 1',
                                'conditions': [
                                    {'field': 'status', 'operator': 'eq', 'value': 'active'}
                                ]
                            },
                            {
                                'name': 'Branch 2',
                                'conditions': [
                                    {'field': 'status', 'operator': 'eq', 'value': 'inactive'}
                                ]
                            }
                        ]
                    }
                },
                {'id': 'node_3', 'type': 'end', 'x': 500, 'y': 100, 'text': 'End'},
            ],
            'edges': [
                {'id': 'edge_1', 'sourceNodeId': 'node_1', 'targetNodeId': 'node_2'},
                {'id': 'edge_2', 'sourceNodeId': 'node_2', 'targetNodeId': 'node_3'},
            ]
        }

        is_valid, errors, warnings = self.validator.validate(valid_data)

        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_end_node_non_standard_state_produces_warning(self):
        """Test non-standard end state produces warning."""
        data_with_warning = {
            'nodes': [
                {'id': 'node_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
                {
                    'id': 'node_2',
                    'type': 'end',
                    'x': 300,
                    'y': 100,
                    'text': 'End',
                    'properties': {'endState': 'custom_state'}
                },
            ],
            'edges': [
                {'id': 'edge_1', 'sourceNodeId': 'node_1', 'targetNodeId': 'node_2'},
            ]
        }

        is_valid, errors, warnings = self.validator.validate(data_with_warning)

        # Should still be valid but with a warning
        self.assertTrue(is_valid)
        self.assertTrue(any('custom_state' in w for w in warnings))


class WorkflowValidationServiceConstantsTest(TestCase):
    """Test validation service constants."""

    def test_node_types_constant(self):
        """Test NODE_TYPES constant includes all expected types."""
        from apps.workflows.services.workflow_validation import WorkflowValidationService

        expected_types = ['start', 'end', 'approval', 'condition', 'cc', 'notify', 'parallel']
        for expected in expected_types:
            self.assertIn(expected, WorkflowValidationService.NODE_TYPES)

    def test_approval_types_constant(self):
        """Test APPROVAL_TYPES constant."""
        from apps.workflows.services.workflow_validation import WorkflowValidationService

        expected_types = ['or', 'and', 'sequence']
        self.assertEqual(WorkflowValidationService.APPROVAL_TYPES, expected_types)

    def test_approver_types_constant(self):
        """Test APPROVER_TYPES constant."""
        from apps.workflows.services.workflow_validation import WorkflowValidationService

        expected_types = ['user', 'role', 'leader', 'dept_leader', 'continuous_leader', 'self_select']
        self.assertEqual(WorkflowValidationService.APPROVER_TYPES, expected_types)

    def test_condition_operators_constant(self):
        """Test CONDITION_OPERATORS constant."""
        from apps.workflows.services.workflow_validation import WorkflowValidationService

        expected_operators = ['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'in', 'not_in', 'contains', 'not_contains']
        self.assertEqual(WorkflowValidationService.CONDITION_OPERATORS, expected_operators)
