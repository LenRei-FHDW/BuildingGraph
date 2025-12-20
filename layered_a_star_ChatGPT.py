import json
import time
from heapq import heappush, heappop
from typing import Optional, Tuple, List, Dict
import itertools

from BuildingGraph import BuildingGraph
from RoutingModel import RoutingModel
from custom_dataclasses import Node, Edge, Meta
from visualize import visualize_step


# --------------------------------------------------------
# Load and parse building JSON
# --------------------------------------------------------

def load_building(filepath="building.json") -> Tuple[BuildingGraph, RoutingModel]:
    """Load building data and return compiled graph with routing model."""
    with open(filepath, "r", encoding="utf8") as f:
        data = json.load(f)

    # Parse meta
    meta = Meta(
        building_name=data["meta"]["building_name"],
        unit=data["meta"]["unit"],
        format_version=data["meta"]["format_version"]
    )

    # Parse nodes
    nodes = {}
    for n in data["nodes"]:
        nodes[n["id"]] = Node(
            id=n["id"],
            type=n["type"],
            level=n["level"],
            pos=tuple(n["pos"]) if n.get("pos") else None,
            attrs=n.get("attrs", {}),
            name=n.get("name")
        )

    # Parse edges
    edges = []
    for e in data["edges"]:
        edges.append(Edge(
            a=e["a"],
            b=e["b"],
            weight=e["weight"],
            attrs=e.get("attrs", {})
        ))

    # Build and compile graph
    graph = BuildingGraph(meta, nodes, edges)
    graph.compile_for_routing()

    # Create routing model
    model = RoutingModel(
        graph,
        floor_transition_penalty=5.0,
        use_3d_heuristic=True
    )

    return graph, model


# --------------------------------------------------------
# Layered A* using RoutingModel
# --------------------------------------------------------

def layered_a_star(
        graph: BuildingGraph,
        model: RoutingModel,
        start_id: str,
        goal_id: str,
        visualize: bool = False
) -> Tuple[Optional[List[str]], Optional[float], float]:
    """A* search using RoutingModel for cost and heuristic calculations."""
    start_time = time.time()

    start_idx = graph.idx(start_id)
    goal_idx = graph.idx(goal_id)

    open_set = []
    heappush(open_set, (0.0, start_idx))

    closed_set = set()
    step = 0

    came_from = {}
    g_score = {i: float("inf") for i in range(len(graph.routing_nodes))}
    g_score[start_idx] = 0.0

    f_score = {i: float("inf") for i in range(len(graph.routing_nodes))}
    f_score[start_idx] = model.heuristic(start_idx, goal_idx)

    while open_set:
        _, current = heappop(open_set)

        if current == goal_idx:
            # Reconstruct path
            path_indices = [current]
            while current in came_from:
                current = came_from[current]
                path_indices.append(current)
            path_indices.reverse()

            # Convert to IDs
            path_ids = [graph.id(idx) for idx in path_indices]
            total_time = time.time() - start_time
            return path_ids, g_score[goal_idx], total_time

        # Explore neighbors using RoutingModel
        for edge in graph.neighbors(current):
            neighbor = edge.target
            tentative = g_score[current] + model.edge_cost(current, edge)

            if tentative < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative
                f_score[neighbor] = tentative + model.heuristic(neighbor, goal_idx)
                heappush(open_set, (f_score[neighbor], neighbor))

        if visualize:
            visualize_step(
            graph,
            open_set,
            closed_set,
            current,
            start_idx,
            goal_idx,
            step
        )

        closed_set.add(current)
        step += 1

    return None, None, time.time() - start_time


# --------------------------------------------------------
# Utilities
# --------------------------------------------------------

def format_path_verbose(path: List[str], graph: BuildingGraph) -> str:
    """Format path with node names."""
    result = []
    for nid in path:
        node = graph.raw_nodes[nid]
        name = node.name or nid
        result.append(f"{nid}({name})")
    return " -> ".join(result)


def benchmark_all_pairs(
        graph: BuildingGraph,
        model: RoutingModel,
        max_pairs: Optional[int] = None
) -> Optional[Dict]:
    """Benchmark pathfinding across all node pairs."""
    ids = list(graph.raw_nodes.keys())
    pairs = list(itertools.permutations(ids, 2))

    if max_pairs:
        pairs = pairs[:max_pairs]

    results = []
    for a, b in pairs:
        path, cost, dt = layered_a_star(graph, model, a, b)
        if path:
            results.append({
                'a': a,
                'b': b,
                'path': path,
                'cost': cost,
                'time': dt
            })

    if not results:
        print("No reachable node pairs found for benchmarking.")
        return None

    costs = [r['cost'] for r in results]
    times = [r['time'] for r in results]

    shortest = min(results, key=lambda x: x['cost'])
    longest = max(results, key=lambda x: x['cost'])

    avg_cost = sum(costs) / len(costs)
    avg_time = sum(times) / len(times)
    avg_hops = sum(len(r['path']) - 1 for r in results) / len(results)

    stats = {
        'count': len(results),
        'avg_cost': avg_cost,
        'avg_time': avg_time,
        'avg_hops': avg_hops,
        'shortest': shortest,
        'longest': longest
    }

    # Print summary
    print("\n--- Benchmark Summary ---")
    print(f"Pairs evaluated: {stats['count']}")
    print(f"Average cost: {stats['avg_cost']:.3f}")
    print(f"Average hops: {stats['avg_hops']:.2f}")
    print(f"Average search time: {stats['avg_time'] * 1000:.3f} ms")

    print("\nShortest path (by cost):")
    print(f" {shortest['a']} -> {shortest['b']}  cost={shortest['cost']:.3f} time={shortest['time'] * 1000:.3f} ms")
    print(format_path_verbose(shortest['path'], graph))

    print("\nLongest path (by cost):")
    print(f" {longest['a']} -> {longest['b']}  cost={longest['cost']:.3f} time={longest['time'] * 1000:.3f} ms")
    print(format_path_verbose(longest['path'], graph))

    return stats
