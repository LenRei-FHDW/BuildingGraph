from typing import Dict, List

from custom_dataclasses import Meta, Node, RoutingNode, RoutingEdge, Edge


class BuildingGraph:
    def __init__(self, meta: Meta,
                 nodes: Dict[str, Node],
                 edges: List[Edge]):
        self.meta = meta
        self.raw_nodes = nodes
        self.raw_edges = edges

        # Filled after compile_for_routing()
        self.routing_nodes: List[RoutingNode] = []
        self.routing_edges: List[List[RoutingEdge]] = []
        self.node_index: Dict[str, int] = {}
        self.level_index: Dict[int, List[int]] = {}

        self.compiled = False

    def compile_for_routing(self):
        # stable ordering
        all_ids = list(self.raw_nodes.keys())
        self.node_index = {nid: i for i, nid in enumerate(all_ids)}

        # Compile nodes
        self.routing_nodes = []
        self.level_index = {}
        for nid in all_ids:
            n = self.raw_nodes[nid]
            idx = self.node_index[nid]
            rn = RoutingNode(id=n.id, level=n.level, pos=n.pos)
            self.routing_nodes.append(rn)

            self.level_index.setdefault(n.level, []).append(idx)

        # adjacency
        n = len(self.routing_nodes)
        self.routing_edges = [[] for _ in range(n)]

        # Compile edges
        for e in self.raw_edges:
            ai = self.node_index[e.a]
            bi = self.node_index[e.b]

            flags = {
                "is_floor_transition": bool(e.attrs.get("floor_transition", False)),
                "is_stairs": bool(e.attrs.get("stairs", False)),
                "is_elevator": bool(
                    e.attrs.get("elevator_enter", False)
                    or e.attrs.get("elevator_exit", False)
                    or e.attrs.get("elevator_move", False)
                ),
                "accessible": bool(e.attrs.get("accessible", True)),
            }

            ra = RoutingEdge(
                target=bi, weight=e.weight, **flags
            )
            rb = RoutingEdge(
                target=ai, weight=e.weight, **flags
            )

            self.routing_edges[ai].append(ra)
            self.routing_edges[bi].append(rb)

        self.compiled = True

    # ----------------- Helpers -----------------

    def idx(self, node_id: str) -> int:
        return self.node_index[node_id]

    def id(self, idx: int) -> str:
        return self.routing_nodes[idx].id

    def neighbors(self, idx: int) -> List[RoutingEdge]:
        return self.routing_edges[idx]

    # ----------------- Layer-specific helpers -----------------

    def nodes_on_level(self, level: int) -> List[int]:
        return self.level_index.get(level, [])

    def vertical_edges_from(self, idx: int) -> List[RoutingEdge]:
        lvl = self.routing_nodes[idx].level
        return [
            e for e in self.routing_edges[idx]
            if self.routing_nodes[e.target].level != lvl
        ]

    def intralevel_edges_from(self, idx: int) -> List[RoutingEdge]:
        lvl = self.routing_nodes[idx].level
        return [
            e for e in self.routing_edges[idx]
            if self.routing_nodes[e.target].level == lvl
        ]

    def visualize_ascii(self):
        print("=== ASCII Building Graph View ===")
        print(f"Building: {self.meta.building_name}")
        print(f"Nodes: {len(self.routing_nodes)}")
        print(f"Edges: {sum(len(lst) for lst in self.routing_edges) // 2}")
        print("----------------------------------")

        for idx, node in enumerate(self.routing_nodes):
            print(f"[{idx}] {node.id} (level={node.level}, pos={node.pos})")
            for e in self.routing_edges[idx]:
                target_name = self.routing_nodes[e.target].id
                print(f"     -> {target_name} (w={e.weight})")
        print("----------------------------------")