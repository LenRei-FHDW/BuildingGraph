import json
import random
import time
from pathlib import Path
from heapq import heappush, heappop
from typing import Dict, List, Tuple, Callable, Optional

from BuildingGraph import BuildingGraph
from RoutingModel import RoutingModel
from custom_dataclasses import Node, Edge, Meta


# --------------------------------------------------------
# Generischer A* Core (basiert auf deinem ChatGPT-Snippet)
# --------------------------------------------------------

def run_astar(
        graph: BuildingGraph,
        model: RoutingModel,
        start_idx: int,
        goal_idx: int,
        heuristic_fn: Callable[[int, int], float]
) -> Tuple[int, float]:
    """
    Führt A* aus und gibt (Anzahl expandierter Knoten, Pfadkosten) zurück.
    """
    open_set = []
    heappush(open_set, (0.0, start_idx))

    g_score = {start_idx: 0.0}
    closed_set = set()
    expanded_count = 0

    while open_set:
        _, current = heappop(open_set)
        if current in closed_set: continue

        expanded_count += 1
        closed_set.add(current)

        if current == goal_idx:
            # Hier geben wir nun beides zurück: Effizienz und Qualität
            return expanded_count, g_score[goal_idx]

        for edge in graph.neighbors(current):
            neighbor = edge.target
            tentative_g = g_score[current] + model.edge_cost(current, edge)

            if tentative_g < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic_fn(neighbor, goal_idx)
                heappush(open_set, (f_score, neighbor))

    return expanded_count, float('inf')


# --------------------------------------------------------
# Heuristik-Definitionen
# --------------------------------------------------------

def get_baseline_heuristic(graph: BuildingGraph):
    """Gibt eine reine 3D-Distanz Funktion zurück (Baseline)."""

    def h(idx, goal_idx):
        a = graph.routing_nodes[idx]
        b = graph.routing_nodes[goal_idx]
        if a.pos and b.pos:
            return math.dist(a.pos, b.pos)
        return 0.0

    return h


# --------------------------------------------------------
# Hilfsfunktionen
# --------------------------------------------------------

def load_building(filepath: str) -> Tuple[BuildingGraph, RoutingModel]:
    with open(filepath, "r", encoding="utf8") as f:
        data = json.load(f)

    meta = Meta(**data["meta"])
    nodes = {n["id"]: Node(id=n["id"], type=n["type"], level=n["level"],
                           pos=tuple(n["pos"]) if n.get("pos") else None,
                           attrs=n.get("attrs", {}), name=n.get("name"))
             for n in data["nodes"]}
    edges = [Edge(a=e["a"], b=e["b"], weight=e["weight"], attrs=e.get("attrs", {}))
             for e in data["edges"]]

    graph = BuildingGraph(meta, nodes, edges)
    graph.compile_for_routing()

    # Standard-Konfiguration für Benchmarks
    model = RoutingModel(graph, floor_transition_penalty=10.0)
    return graph, model


import math  # Für math.dist in der Baseline


def collect_benchmark_data(
        buildings_dir: str,
        pairs_per_building: int = 20,
        force_different_floors: float = 0.8
) -> Dict[str, Dict]:
    """
    Erhebt Daten pro Gebäude.
    Rückgabe: { "dateiname": { "n_nodes": int, "n_floors": int, "baseline": [], "layered": [] } }
    """
    results = {}
    path = Path(buildings_dir)

    for file in path.glob("*.json"):
        graph, model = load_building(str(file))
        node_ids = list(graph.raw_nodes.keys())

        # Metadaten extrahieren
        n_nodes = len(node_ids)
        n_floors = len(graph.level_index)  # Anzahl Etagen aus dem BuildingGraph

        results[file.name] = {
            "n_nodes": n_nodes,
            "n_floors": n_floors,
            "baseline": [],
            "layered": []
        }

        # Sampling-Vorbereitung
        nodes_by_lvl = {}
        for nid in node_ids:
            lvl = graph.raw_nodes[nid].level
            nodes_by_lvl.setdefault(lvl, []).append(nid)
        levels = list(nodes_by_lvl.keys())

        # Heuristiken (Layered Heuristik aus dem Modell nutzen)
        h_baseline = get_baseline_heuristic(graph)
        h_layered = model.heuristic

        for _ in range(pairs_per_building):
            if len(levels) > 1 and random.random() < force_different_floors:
                l1, l2 = random.sample(levels, 2)
                s_id, g_id = random.choice(nodes_by_lvl[l1]), random.choice(nodes_by_lvl[l2])
            else:
                s_id, g_id = random.sample(node_ids, 2)

            si, gi = graph.idx(s_id), graph.idx(g_id)

            # Messungen durchführen
            results[file.name]["baseline"].append(run_astar(graph, model, si, gi, h_baseline))
            results[file.name]["layered"].append(run_astar(graph, model, si, gi, h_layered))

    return results