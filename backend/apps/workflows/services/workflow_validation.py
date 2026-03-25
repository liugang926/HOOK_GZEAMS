"""
Workflow Validation Service.

Validates workflow graph data structure and configuration.
Ensures workflows are properly configured before publishing.
"""
from typing import Dict, List, Tuple, Any
from django.utils.translation import gettext_lazy


class WorkflowValidationService:
    """
    Service for validating workflow definitions.

    Validates:
    - Graph structure (nodes, edges)
    - Required nodes (start, end)
    - Node ID uniqueness
    - Edge references
    - Node configuration
    - Approval node properties
    - Condition node branches
    """

    # Supported node types
    NODE_TYPES = ['start', 'end', 'approval', 'condition', 'cc', 'notify', 'parallel']

    # Valid approval types
    APPROVAL_TYPES = ['or', 'and', 'sequence']

    # Valid approver types
    APPROVER_TYPES = ['user', 'role', 'leader', 'dept_leader', 'continuous_leader', 'self_select']

    # Valid condition operators
    CONDITION_OPERATORS = [
        'eq', 'ne', 'gt', 'gte', 'lt', 'lte',
        'in', 'not_in', 'contains', 'not_contains',
        'is_empty', 'is_not_empty', 'between',
    ]

    # Valid permission levels
    PERMISSION_LEVELS = ['editable', 'read_only', 'hidden']

    # Valid condition group logic operators
    GROUP_LOGIC_VALUES = ['and', 'or']

    def __init__(self):
        """Initialize the validation service."""
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, graph_data: Dict) -> Tuple[bool, List[str], List[str]]:
        """
        Validate complete workflow graph data.

        Args:
            graph_data: The workflow graph data to validate

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        # Validate structure
        self._validate_structure(graph_data)

        if self.errors:
            return False, self.errors, self.warnings

        # Validate nodes
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])

        self._validate_nodes(nodes, edges)

        # Validate edges
        self._validate_edges(edges, nodes)

        # Validate connectivity
        self._validate_connectivity(nodes, edges)

        return len(self.errors) == 0, self.errors, self.warnings

    def validate_definition(self, graph_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate workflow definition (simplified interface).

        Args:
            graph_data: The workflow graph data to validate

        Returns:
            Tuple of (is_valid, errors)
        """
        is_valid, errors, warnings = self.validate(graph_data)
        return is_valid, errors

    def _validate_structure(self, graph_data: Dict) -> None:
        """Validate basic graph data structure."""
        if not isinstance(graph_data, dict):
            self.errors.append(str(gettext_lazy('Graph data must be a dictionary.')))
            return

        nodes = graph_data.get('nodes')
        edges = graph_data.get('edges')

        if nodes is None:
            self.errors.append(str(gettext_lazy('Graph data must contain "nodes" field.')))

        if edges is None:
            self.errors.append(str(gettext_lazy('Graph data must contain "edges" field.')))

    def _validate_nodes(self, nodes: List[Dict], edges: List[Dict] = None) -> None:
        """Validate all nodes in the workflow."""
        if not nodes:
            self.errors.append(str(gettext_lazy('Workflow must have at least one node.')))
            return

        node_ids = []

        for idx, node in enumerate(nodes):
            # Validate node structure
            if not isinstance(node, dict):
                self.errors.append(str(gettext_lazy(f'Node at index {idx} must be a dictionary.')))
                continue

            # Validate required fields
            if 'id' not in node:
                self.errors.append(str(gettext_lazy(f'Node at index {idx} is missing "id" field.')))

            if 'type' not in node:
                self.errors.append(str(gettext_lazy(f'Node {node.get("id", idx)} is missing "type" field.')))

            # Validate node type
            node_type = node.get('type')
            if node_type and node_type not in self.NODE_TYPES:
                self.errors.append(str(gettext_lazy(f'Node {node.get("id")} has invalid type: {node_type}')))

            # Validate node ID uniqueness
            node_id = node.get('id')
            if node_id:
                if node_id in node_ids:
                    self.errors.append(str(gettext_lazy(f'Duplicate node ID: {node_id}')))
                node_ids.append(node_id)

            # Type-specific validation
            if node_type == 'approval':
                self._validate_approval_node(node)
            elif node_type == 'condition':
                self._validate_condition_node(node, edges)
            elif node_type == 'start':
                self._validate_start_node(node)
            elif node_type == 'end':
                self._validate_end_node(node)

        # Validate required nodes exist
        node_types = {node.get('type') for node in nodes if 'type' in node}

        if 'start' not in node_types:
            self.errors.append(str(gettext_lazy('Workflow must have a start node.')))
        if 'end' not in node_types:
            self.errors.append(str(gettext_lazy('Workflow must have an end node.')))

        # Validate only one start node
        start_nodes = [n for n in nodes if n.get('type') == 'start']
        if len(start_nodes) > 1:
            self.errors.append(str(gettext_lazy('Workflow can have only one start node.')))

    def _validate_edges(self, edges: List[Dict], nodes: List[Dict]) -> None:
        """Validate all edges in the workflow."""
        if not edges:
            self.warnings.append(str(gettext_lazy('Workflow has no edges.')))
            return

        node_ids = {node.get('id') for node in nodes if 'id' in node}

        for idx, edge in enumerate(edges):
            # Validate edge structure
            if not isinstance(edge, dict):
                self.errors.append(str(gettext_lazy(f'Edge at index {idx} must be a dictionary.')))
                continue

            # Validate required fields
            if 'id' not in edge:
                self.errors.append(str(gettext_lazy(f'Edge at index {idx} is missing "id" field.')))

            if 'sourceNodeId' not in edge:
                self.errors.append(str(gettext_lazy(f'Edge {edge.get("id", idx)} is missing "sourceNodeId" field.')))

            if 'targetNodeId' not in edge:
                self.errors.append(str(gettext_lazy(f'Edge {edge.get("id", idx)} is missing "targetNodeId" field.')))

            # Validate references
            source = edge.get('sourceNodeId')
            target = edge.get('targetNodeId')

            if source and source not in node_ids:
                self.errors.append(str(gettext_lazy(f'Edge {edge.get("id")} references non-existent source node: {source}')))

            if target and target not in node_ids:
                self.errors.append(str(gettext_lazy(f'Edge {edge.get("id")} references non-existent target node: {target}')))

            # Validate no self-loops
            if source == target:
                self.errors.append(str(gettext_lazy(f'Edge {edge.get("id")} creates a self-loop (source == target).')))

            # Validate edge-level conditions if present
            edge_props = edge.get('properties', {})
            if edge_props and not edge_props.get('isDefault'):
                self._validate_edge_conditions(edge, edge_props)

    def _validate_edge_conditions(self, edge: Dict, properties: Dict) -> None:
        """Validate conditions on an edge, if present."""
        edge_id = edge.get('id', '?')

        # Validate conditionGroups on edge
        condition_groups = properties.get('conditionGroups')
        if condition_groups:
            self._validate_condition_groups(condition_groups, f'edge {edge_id}')
            return

        # Validate flat conditions on edge
        conditions = properties.get('conditions')
        if conditions:
            if not isinstance(conditions, list):
                self.errors.append(
                    str(gettext_lazy(f'Edge {edge_id}: conditions must be a list.'))
                )
            else:
                for cond_idx, condition in enumerate(conditions):
                    self._validate_single_condition(condition, cond_idx, f'edge {edge_id}')

    def _validate_connectivity(self, nodes: List[Dict], edges: List[Dict]) -> None:
        """Validate workflow connectivity (all nodes reachable, no isolated nodes)."""
        if not nodes or not edges:
            return

        node_ids = {node.get('id') for node in nodes if 'id' in node}
        start_nodes = [n for n in nodes if n.get('type') == 'start']

        if not start_nodes:
            return  # Already error in validate_nodes

        start_id = start_nodes[0].get('id')

        # Build adjacency list
        adj_list = {node_id: [] for node_id in node_ids}
        for edge in edges:
            source = edge.get('sourceNodeId')
            target = edge.get('targetNodeId')
            if source and target:
                if source in adj_list and target not in adj_list[source]:
                    adj_list[source].append(target)

        # BFS to find reachable nodes
        reachable = set()
        queue = [start_id]

        while queue:
            current = queue.pop(0)
            if current not in reachable:
                reachable.add(current)
                queue.extend(adj_list.get(current, []))

        # Check for isolated nodes
        isolated = node_ids - reachable
        if isolated:
            self.errors.append(str(gettext_lazy(f'Isolated nodes detected (not reachable from start): {list(isolated)}')))

    def _validate_approval_node(self, node: Dict) -> None:
        """Validate approval node configuration."""
        properties = node.get('properties', {})

        # Validate approveType
        approve_type = properties.get('approveType')
        if approve_type and approve_type not in self.APPROVAL_TYPES:
            self.errors.append(str(gettext_lazy(f'Approval node {node.get("id")} has invalid approveType: {approve_type}')))

        # Validate approvers
        approvers = properties.get('approvers', [])
        if not approvers:
            self.errors.append(str(gettext_lazy(f'Approval node {node.get("id")} has no approvers configured.')))
        else:
            for idx, approver in enumerate(approvers):
                if not isinstance(approver, dict):
                    self.errors.append(str(gettext_lazy(f'Approver {idx} in node {node.get("id")} must be a dictionary.')))
                    continue

                approver_type = approver.get('type')
                if not approver_type:
                    self.errors.append(str(gettext_lazy(f'Approver {idx} in node {node.get("id")} is missing "type" field.')))
                elif approver_type not in self.APPROVER_TYPES:
                    self.errors.append(str(gettext_lazy(f'Approver {idx} in node {node.get("id")} has invalid type: {approver_type}')))

        # Validate timeout
        timeout = properties.get('timeout')
        if timeout is not None:
            if not isinstance(timeout, int) or timeout <= 0:
                self.errors.append(str(gettext_lazy(f'Approval node {node.get("id")} has invalid timeout value.')))

    def _validate_condition_node(self, node: Dict, edges: List[Dict] = None) -> None:
        """
        Validate condition node configuration.

        Validates:
        - Node-level branches (must have at least 2)
        - Each branch's conditions or conditionGroups
        - Outgoing edge count (at least 2 when edges are available)
        """
        node_id = node.get('id')
        properties = node.get('properties', {})

        # Validate outgoing edges count (need at least 2 for branching)
        if edges:
            outgoing_edges = [
                e for e in edges if e.get('sourceNodeId') == node_id
            ]
            if len(outgoing_edges) < 2:
                self.warnings.append(
                    str(gettext_lazy(
                        f'Condition node {node_id} has fewer than 2 '
                        f'outgoing edges ({len(outgoing_edges)}).'
                    ))
                )

        branches = properties.get('branches', [])
        if not branches or len(branches) < 2:
            self.errors.append(str(gettext_lazy(f'Condition node {node_id} must have at least 2 branches.')))

        for idx, branch in enumerate(branches):
            if not isinstance(branch, dict):
                self.errors.append(str(gettext_lazy(f'Branch {idx} in node {node_id} must be a dictionary.')))
                continue

            # Check for conditionGroups (new schema)
            condition_groups = branch.get('conditionGroups')
            if condition_groups:
                self._validate_condition_groups(
                    condition_groups, f'branch {idx} of node {node_id}'
                )
                # Validate groupLogic
                group_logic = branch.get('groupLogic', 'and')
                if group_logic not in self.GROUP_LOGIC_VALUES:
                    self.errors.append(
                        str(gettext_lazy(
                            f'Branch {idx} in node {node_id} has '
                            f'invalid groupLogic: {group_logic}'
                        ))
                    )
                continue

            # Validate flat conditions (backward compatible)
            conditions = branch.get('conditions', [])
            if not conditions:
                self.errors.append(str(gettext_lazy(f'Branch {idx} in condition node {node_id} has no conditions.')))

            for cond_idx, condition in enumerate(conditions):
                self._validate_single_condition(
                    condition, cond_idx, f'branch {idx}'
                )

    def _validate_condition_groups(self, groups: Any, context: str) -> None:
        """
        Validate conditionGroups schema.

        Args:
            groups: List of group objects
            context: Human-readable context string for error messages
        """
        if not isinstance(groups, list):
            self.errors.append(
                str(gettext_lazy(f'{context}: conditionGroups must be a list.'))
            )
            return

        if len(groups) == 0:
            self.errors.append(
                str(gettext_lazy(
                    f'{context}: conditionGroups must contain at least one group.'
                ))
            )

        for group_idx, group in enumerate(groups):
            if not isinstance(group, dict):
                self.errors.append(
                    str(gettext_lazy(
                        f'{context}, group {group_idx}: must be an object.'
                    ))
                )
                continue

            logic = group.get('logic', 'and')
            if logic not in self.GROUP_LOGIC_VALUES:
                self.errors.append(
                    str(gettext_lazy(
                        f'{context}, group {group_idx}: '
                        f'invalid logic "{logic}".'
                    ))
                )

            conditions = group.get('conditions', [])
            if not isinstance(conditions, list):
                self.errors.append(
                    str(gettext_lazy(
                        f'{context}, group {group_idx}: '
                        f'conditions must be a list.'
                    ))
                )
            elif len(conditions) == 0:
                self.errors.append(
                    str(gettext_lazy(
                        f'{context}, group {group_idx}: '
                        f'must have at least one condition.'
                    ))
                )
            else:
                for cond_idx, condition in enumerate(conditions):
                    self._validate_single_condition(
                        condition, cond_idx,
                        f'{context}, group {group_idx}'
                    )

    def _validate_single_condition(self, condition: Any, cond_idx: int, context: str) -> None:
        """Validate a single condition object."""
        if not isinstance(condition, dict):
            self.errors.append(str(gettext_lazy(f'Condition {cond_idx} in {context} is invalid.')))
            return

        if 'field' not in condition:
            self.errors.append(str(gettext_lazy(f'Condition {cond_idx} in {context} is missing "field".')))

        if 'operator' not in condition:
            self.errors.append(str(gettext_lazy(f'Condition {cond_idx} in {context} is missing "operator".')))
        elif condition['operator'] not in self.CONDITION_OPERATORS:
            self.errors.append(str(gettext_lazy(f'Condition {cond_idx} has invalid operator: {condition["operator"]}')))

        operator = condition.get('operator')
        # is_empty / is_not_empty do not require a value
        if operator not in ('is_empty', 'is_not_empty'):
            if 'value' not in condition:
                self.errors.append(str(gettext_lazy(f'Condition {cond_idx} in {context} is missing "value".')))

    def _validate_start_node(self, node: Dict) -> None:
        """Validate start node (should have minimal configuration)."""
        # Start node typically has no properties
        pass

    def _validate_end_node(self, node: Dict) -> None:
        """Validate end node configuration."""
        properties = node.get('properties', {})

        # Validate end state if present
        end_state = properties.get('endState')
        valid_end_states = ['approved', 'rejected', 'cancelled', 'timeout']
        if end_state and end_state not in valid_end_states:
            self.warnings.append(str(gettext_lazy(f'End node {node.get("id")} has non-standard end state: {end_state}')))
