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
        """
        Optimierte Layered-Heuristik.
        Kombiniert 3D-Tightness mit logischen Transitions-Kosten.
        """
        a = self.g.routing_nodes[idx]
        b = self.g.routing_nodes[goal_idx]

        # 1. Physikalische Basis (3D-Distanz)
        # Sie ist die absolut kleinste Distanz im Raum und immer zulässig.
        h_dist = math.dist(a.pos, b.pos)

        level_diff = abs(a.level - b.level)
        if level_diff == 0:
            return h_dist

        # 2. Einpreisung der logischen Zusatzkosten (Penalties)
        # Da jede Kante zwischen Etagen die 'floor_transition_penalty' kostet,
        # muss dieser Wert zwingend in die Heuristik einfließen.
        logical_penalty = self.floor_transition_penalty

        # 3. Einpreisung der nicht-euklidischen Fixkosten (Wartezeit/Antritt)
        # Treppen und Aufzüge im Generator haben Fixkosten (ca. 5.0 - 6.0).
        # Indem wir einen konservativen Fixwert addieren, 'weiß' der A*,
        # dass ein Wechsel niemals 'umsonst' ist.
        fixed_entry_cost = 5.0

        # Aggressive, aber zulässige Schranke:
        # Wir addieren die Kosten pro Etagen-Differenz.
        return h_dist + (level_diff * (logical_penalty + fixed_entry_cost))

    def heuristic_3d_only(self, idx: int, goal_idx: int) -> float:
        """Reine 3D-Luftlinie ohne Layer-Logik für die Baseline."""
        a = self.g.routing_nodes[idx]
        b = self.g.routing_nodes[goal_idx]
        return math.dist(a.pos, b.pos) if (a.pos and b.pos) else 0.0
