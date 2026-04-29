"""Small heterogeneous graph implementation for meta-path reasoning."""

from __future__ import annotations

from collections import defaultdict, deque

from .models import Entity, NodeType, Relation


class HeterogeneousGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, Entity] = {}
        self.edges: dict[str, list[Relation]] = defaultdict(list)
        self.reverse_edges: dict[str, list[Relation]] = defaultdict(list)

    @classmethod
    def from_parts(cls, entities: list[Entity], relations: list[Relation]) -> "HeterogeneousGraph":
        graph = cls()
        for entity in entities:
            graph.add_node(entity)
        for relation in relations:
            graph.add_edge(relation)
        return graph

    def add_node(self, entity: Entity) -> None:
        self.nodes[entity.key] = entity

    def add_edge(self, relation: Relation) -> None:
        self.add_node(relation.source)
        self.add_node(relation.target)
        self.edges[relation.source.key].append(relation)
        self.reverse_edges[relation.target.key].append(relation)

    def companies(self) -> list[Entity]:
        return [entity for entity in self.nodes.values() if entity.type == NodeType.COMPANY]

    def find_company(self, preferred_name: str | None = None) -> Entity | None:
        companies = self.companies()
        if preferred_name:
            for company in companies:
                if preferred_name in company.name or company.name in preferred_name:
                    return company
        return companies[-1] if companies else None

    def metapath_paths(self, start: Entity, node_types: list[NodeType], max_paths: int = 12) -> list[list[Relation]]:
        """Return relation paths whose node type sequence matches node_types.

        node_types includes the start node type. Example:
        [Company, Product, Company].
        """

        if not node_types or start.type != node_types[0]:
            return []

        paths: list[list[Relation]] = []

        def walk(current: Entity, depth: int, path: list[Relation]) -> None:
            if len(paths) >= max_paths:
                return
            if depth == len(node_types) - 1:
                paths.append(path.copy())
                return

            next_type = node_types[depth + 1]
            for edge in self.edges.get(current.key, []):
                if edge.target.type == next_type:
                    path.append(edge)
                    walk(edge.target, depth + 1, path)
                    path.pop()

            for edge in self.reverse_edges.get(current.key, []):
                if edge.source.type == next_type:
                    reversed_relation = Relation(edge.target, edge.relation, edge.source, edge.evidence, edge.weight * 0.8)
                    path.append(reversed_relation)
                    walk(edge.source, depth + 1, path)
                    path.pop()

        walk(start, 0, [])
        return paths

    def cascade_paths(self, start: Entity, max_depth: int = 4, max_paths: int = 6) -> list[list[Relation]]:
        paths: list[list[Relation]] = []
        queue: deque[tuple[Entity, list[Relation], set[str]]] = deque([(start, [], {start.key})])

        while queue and len(paths) < max_paths:
            current, path, seen = queue.popleft()
            if len(path) >= 3:
                paths.append(path)
                continue
            if len(path) >= max_depth:
                continue

            for edge in self.edges.get(current.key, []):
                if edge.target.key in seen:
                    continue
                queue.append((edge.target, path + [edge], seen | {edge.target.key}))

            for edge in self.reverse_edges.get(current.key, []):
                if edge.source.key in seen:
                    continue
                reversed_relation = Relation(edge.target, edge.relation, edge.source, edge.evidence, edge.weight * 0.8)
                queue.append((edge.source, path + [reversed_relation], seen | {edge.source.key}))

        return paths

