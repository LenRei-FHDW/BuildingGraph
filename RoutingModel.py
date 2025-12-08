import math

from BuildingGraph import BuildingGraph
from custom_dataclasses import RoutingEdge


class RoutingModel:
    def __init__(self, graph: BuildingGraph,
                 floor_transition_penalty: float = 0.0,
                 use_3d_heuristic: bool = True):
        if not graph.compiled:
            raise RuntimeError("Graph must be compiled first.")
        self.g = graph
        self.floor_transition_penalty = floor_transition_penalty
        self.use_3d_heuristic = use_3d_heuristic

        self.min_floor_transition_cost = (
            self._estimate_min_floor_transition_cost()
        )

    def _estimate_min_floor_transition_cost(self):
        best = None
        for fr_idx, edges in enumerate(self.g.routing_edges):
            fr_lvl = self.g.routing_nodes[fr_idx].level
            for e in edges:
                to_lvl = self.g.routing_nodes[e.target].level
                if fr_lvl != to_lvl:
                    best = e.weight if best is None else min(best, e.weight)
        return best or 0.0

    # -------- cost function -------

    def edge_cost(self, fr_idx: int, edge: RoutingEdge) -> float:
        """Basiskosten: weight + optional floor penalty."""
        fr_lvl = self.g.routing_nodes[fr_idx].level
        to_lvl = self.g.routing_nodes[edge.target].level

        base = edge.weight
        if fr_lvl != to_lvl:
            base += self.floor_transition_penalty
        return base

    # -------- heuristic -------

    def heuristic(self, idx: int, goal_idx: int) -> float:
        """Layered heuristic."""
        a = self.g.routing_nodes[idx]
        b = self.g.routing_nodes[goal_idx]

        # 3D or 2D distance
        if a.pos and b.pos:
            if self.use_3d_heuristic:
                d = math.dist(a.pos, b.pos)
            else:
                d = math.hypot(a.pos[0] - b.pos[0], a.pos[1] - b.pos[1])
        else:
            d = 0.0

        # layer penalty
        level_diff = abs(a.level - b.level)
        return d + level_diff * self.min_floor_transition_cost
