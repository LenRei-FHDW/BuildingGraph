import json
import time
import math
from heapq import heappush, heappop

# --------------------------------------------------------
# Load building JSON
# --------------------------------------------------------

def load_building(filepath="building.json"):
    with open(filepath, "r", encoding="utf8") as f:
        data = json.load(f)
    return data


# --------------------------------------------------------
# Build adjacency + node lookup from JSON
# --------------------------------------------------------

def build_graph(building_data):
    nodes = {n["id"]: n for n in building_data["nodes"]}
    graph = {n["id"]: [] for n in building_data["nodes"]}

    for e in building_data["edges"]:
        a, b, w = e["a"], e["b"], e["weight"]
        # bidirectional edges:
        graph[a].append((b, w, e.get("attrs", {})))
        graph[b].append((a, w, e.get("attrs", {})))

    return graph, nodes


# --------------------------------------------------------
# Heuristic for Layered A*
# weighted heuristic:
#   horizontal distance + floor penalty based on levels
# --------------------------------------------------------

def layered_heuristic(node_a, node_b):
    (x1, y1, z1) = node_a["pos"]
    (x2, y2, z2) = node_b["pos"]

    # Simple planar distance
    planar = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

    # floor penalty
    floor_penalty = abs(node_a["level"] - node_b["level"]) * 5.0  

    return planar + floor_penalty


# --------------------------------------------------------
# Layered A*
# --------------------------------------------------------

def layered_a_star(graph, nodes, start_id, goal_id):
    start_time = time.time()

    open_set = []
    heappush(open_set, (0, start_id))

    came_from = {}
    g_score = {n: float("inf") for n in graph}
    g_score[start_id] = 0

    f_score = {n: float("inf") for n in graph}
    f_score[start_id] = layered_heuristic(nodes[start_id], nodes[goal_id])

    while open_set:
        _, current = heappop(open_set)

        if current == goal_id:
            # reconstruct path
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()

            total_time = time.time() - start_time
            return path, g_score[goal_id], total_time

        # explore neighbors
        for neighbor, cost, attrs in graph[current]:
            tentative = g_score[current] + cost

            # Optional decision logic:
            # Example: Give elevator small priority
            if attrs.get("elevator_move"):
                tentative -= 1

            if tentative < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative
                f_score[neighbor] = tentative + layered_heuristic(nodes[neighbor], nodes[goal_id])
                heappush(open_set, (f_score[neighbor], neighbor))

    return None, None, time.time() - start_time


# --------------------------------------------------------
# Utilities for formatting and benchmarking
# --------------------------------------------------------

def format_path_verbose(path, nodes):
    return " -> ".join(f"{nid}({nodes[nid].get('name', nid)})" for nid in path)


def benchmark_all_pairs(graph, nodes, max_pairs=None):
    import itertools

    ids = list(graph.keys())
    pairs = list(itertools.permutations(ids, 2))
    if max_pairs:
        pairs = pairs[:max_pairs]

    results = []
    for a, b in pairs:
        path, cost, dt = layered_a_star(graph, nodes, a, b)
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

    # Print concise benchmark summary
    print("\n--- Benchmark Summary ---")
    print(f"Pairs evaluated: {stats['count']}")
    print(f"Average cost: {stats['avg_cost']:.3f}")
    print(f"Average hops: {stats['avg_hops']:.2f}")
    print(f"Average search time: {stats['avg_time']*1000:.3f} ms")

    print("\nShortest path (by cost):")
    print(f" {shortest['a']} -> {shortest['b']}  cost={shortest['cost']:.3f} time={shortest['time']*1000:.3f} ms")
    print(format_path_verbose(shortest['path'], nodes))

    print("\nLongest path (by cost):")
    print(f" {longest['a']} -> {longest['b']}  cost={longest['cost']:.3f} time={longest['time']*1000:.3f} ms")
    print(format_path_verbose(longest['path'], nodes))

    return stats


# --------------------------------------------------------
# Main execution example
# --------------------------------------------------------

if __name__ == "__main__":
    building = load_building("building.json")
    graph, nodes = build_graph(building)

    # Example: Search path from entrance to Seminar room on F1
    START = "entrance_F0"
    GOAL = "OFFICE_F1"

    path, cost, dt = layered_a_star(graph, nodes, START, GOAL)

    if path:
        print("\nShortest path found:")
        for step in path:
            print(" →", step)
        print("\nTotal cost:", cost)
    else:
        print("No path found.")

    print(f"\nSearch time: {dt*1000:.2f} ms\n")

    # Run benchmarks across all pairs (may take longer on large graphs)
    _ = benchmark_all_pairs(graph, nodes)
