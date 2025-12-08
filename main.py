import json
from BuildingGraph import BuildingGraph, Node, Edge, Meta


# ------------------------
# JSON → BuildingGraph Parser
# ------------------------
def parse_building_graph(data: dict) -> BuildingGraph:
    meta_raw = data["meta"]
    meta = Meta(
        building_name=meta_raw["building_name"],
        unit=meta_raw["unit"],
        format_version=meta_raw["format_version"]
    )

    raw_nodes = {}
    for n in data["nodes"]:
        node = Node(
            id=n["id"],
            type=n["type"],
            level=n["level"],
            pos=tuple(n["pos"]) if n["pos"] is not None else None,
            attrs=n["attrs"],
            name=n.get("name")
        )
        raw_nodes[node.id] = node

    raw_edges = []
    for e in data["edges"]:
        raw_edges.append(
            Edge(a=e["a"], b=e["b"], weight=e["weight"], attrs=e["attrs"])
        )

    return BuildingGraph(meta, raw_nodes, raw_edges)


# ------------------------
# MAIN
# ------------------------
if __name__ == "__main__":
    with open("test_building.json", "r") as f:
        data = json.load(f)

    graph = parse_building_graph(data)

    # Kompiliere für Routing
    graph.compile_for_routing()

    # ASCII visualisieren
    graph.visualize_ascii()
