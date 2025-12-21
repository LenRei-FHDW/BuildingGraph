from __future__ import annotations
import argparse, json, math, random
from pathlib import Path
from typing import Dict, Any, List, Tuple

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def clamp(x, lo, hi): return max(lo, min(hi, x))
def euclid(a, b): return math.dist(a, b)

def sizes_geometric(n, lo, hi):
    r = (hi / lo) ** (1 / (n - 1))
    return [int(lo * r ** i) for i in range(n)]

# --------------------------------------------------
# GraphBuilder
# --------------------------------------------------

class GraphBuilder:
    def __init__(self, name, b_class):
        self.meta = {
            "building_name": name,
            "group": b_class,
            "unit": "meters",
            "format_version": 1
        }
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []

    def add_node(self, nid, ntype, level, pos, attrs=None):
        self.nodes[nid] = {
            "id": nid,
            "name": nid,
            "type": ntype,
            "level": level,
            "pos": list(pos),
            "attrs": attrs or {}
        }

    def add_edge(self, a, b, weight=None, attrs=None):
        if a not in self.nodes or b not in self.nodes: return
        pa, pb = self.nodes[a]["pos"], self.nodes[b]["pos"]
        w = weight if weight is not None else euclid(pa, pb)
        self.edges.append({
            "a": a, "b": b,
            "weight": round(w, 3),
            "attrs": attrs or {}
        })

    def as_json(self):
        return {"meta": self.meta, "nodes": list(self.nodes.values()), "edges": self.edges}

# --------------------------------------------------
# Class-Specific Generators
# --------------------------------------------------

def add_elevators(gb: GraphBuilder, floors: int, floor_nodes: Dict[int, List[str]], rnd: random.Random):
    """Fügt nicht-euklidische Aufzugskosten hinzu (identisch für alle Klassen)."""
    n_shafts = rnd.randint(1, max(1, floors // 3))
    for s in range(n_shafts):
        shaft_id = f"E{s}"
        served = sorted(rnd.sample(range(floors), rnd.randint(2, floors)))
        prev_cabin = None
        for f in served:
            z = f * 3.0
            cabin, door = f"elev_{shaft_id}_F{f}", f"door_{shaft_id}_F{f}"
            gb.add_node(cabin, "elevator_cabin", f, (rnd.uniform(-10, -5), rnd.uniform(-10, -5), z), {"shaft": shaft_id})
            gb.add_node(door, "elevator_door", f, (rnd.uniform(-4, -2), rnd.uniform(-4, -2), z))
            
            # Verbindung zum Stockwerk
            if floor_nodes[f]:
                gb.add_edge(rnd.choice(floor_nodes[f]), door)
            gb.add_edge(door, cabin, weight=5.0, attrs={"action": "enter_elevator"})

            if prev_cabin:
                dist = abs(gb.nodes[prev_cabin]["level"] - f)
                # Nicht-euklidische Kosten: Wartezeit (10s) + Fahrtzeit
                gb.add_edge(prev_cabin, cabin, weight=10.0 + dist * 2.5, attrs={"elevator_move": True})
            prev_cabin = cabin

def gen_building(target_nodes: int, seed: int, b_class: str) -> Dict[str, Any]:
    rnd = random.Random(seed)
    gb = GraphBuilder(f"B_{b_class}_{target_nodes}_{seed}", b_class)
    floor_nodes: Dict[int, List[str]] = {}

    # --- K1: Linear (Worst Case für A*) ---
    if b_class == "K1":
        floors = 2
        for f in range(floors):
            floor_nodes[f] = []
            n_per_floor = target_nodes // floors
            for i in range(n_per_floor):
                nid = f"n_f{f}_{i}"
                gb.add_node(nid, "path", f, (i * 3.0, f * 10, f * 3.0))
                floor_nodes[f].append(nid)
                if i > 0: gb.add_edge(f"n_f{f}_{i-1}", nid)
        gb.add_edge(floor_nodes[0][-1], floor_nodes[1][0], weight=10.0)

    # --- K2: Geclustert (Best Case) ---
    elif b_class == "K2":
        floors = 3
        nodes_per_cluster = 20
        n_clusters = target_nodes // nodes_per_cluster
        all_ids = []
        for c in range(n_clusters):
            f = rnd.randint(0, floors-1)
            cx, cy = rnd.uniform(0, 100), rnd.uniform(0, 100)
            cluster_nodes = []
            for i in range(nodes_per_cluster):
                nid = f"c{c}_n{i}"
                gb.add_node(nid, "room", f, (cx + rnd.uniform(-2, 2), cy + rnd.uniform(-2, 2), f * 3.0))
                if cluster_nodes: gb.add_edge(rnd.choice(cluster_nodes), nid)
                cluster_nodes.append(nid)
            if all_ids: gb.add_edge(rnd.choice(all_ids), cluster_nodes[0], weight=50.0) # Weite Brücken
            all_ids.extend(cluster_nodes)
            floor_nodes.setdefault(f, []).extend(cluster_nodes)

    # --- K3: Realistisch (Original-Logik) ---
    elif b_class == "K3":
        floors = clamp(target_nodes // 100, 2, 5)
        for f in range(floors):
            floor_nodes[f] = []
            prev_corr = None
            for i in range(target_nodes // floors // 2):
                cid = f"corr_f{f}_{i}"
                gb.add_node(cid, "corridor", f, (i * 4, 0, f * 3))
                floor_nodes[f].append(cid)
                if prev_corr: gb.add_edge(prev_corr, cid)
                # Raum links/rechts
                rid = f"room_f{f}_{i}"
                gb.add_node(rid, "room", f, (i * 4, rnd.choice([-3, 3]), f * 3))
                gb.add_edge(cid, rid)
                prev_corr = cid
        for f in range(floors - 1):
            gb.add_edge(rnd.choice(floor_nodes[f]), rnd.choice(floor_nodes[f+1]), attrs={"stairs": True})

    # --- K4: Mehrstockwerk (Vertikaler Fokus) ---
    elif b_class == "K4":
        floors = clamp(target_nodes // 20, 5, 40)
        for f in range(floors):
            floor_nodes[f] = []
            for i in range(target_nodes // floors):
                nid = f"n_f{f}_{i}"
                gb.add_node(nid, "node", f, (rnd.uniform(0, 10), rnd.uniform(0, 10), f * 3.0))
                floor_nodes[f].append(nid)
                if i > 0: gb.add_edge(f"n_f{f}_{i-1}", nid)
        for f in range(floors - 1):
            gb.add_edge(rnd.choice(floor_nodes[f]), rnd.choice(floor_nodes[f+1]))

    # --- K5: Chaotisch (Random) ---
    else:
        floors = 5
        all_nodes = []
        for i in range(target_nodes):
            f = rnd.randint(0, floors-1)
            nid = f"rand_{i}"
            gb.add_node(nid, "node", f, (rnd.uniform(0, 100), rnd.uniform(0, 100), f * 3.0))
            floor_nodes.setdefault(f, []).append(nid)
            if all_nodes and rnd.random() > 0.3:
                gb.add_edge(rnd.choice(all_nodes), nid)
            all_nodes.append(nid)

    # Überall Aufzüge hinzufügen
    add_elevators(gb, floors, floor_nodes, rnd)
    return gb.as_json()

# --------------------------------------------------
# Main Loop
# --------------------------------------------------

def main():
    classes = ["K1", "K2", "K3", "K4", "K5"]
    n_sizes = 20
    n_instances = 3
    
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="generated_buildings")
    ap.add_argument("--nmin", type=int, default=300)
    ap.add_argument("--nmax", type=int, default=10000)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    
    sizes = sizes_geometric(n_sizes, args.nmin, args.nmax)
    total_count = 0

    for c_idx, b_class in enumerate(classes, 1):
        for s_idx, n in enumerate(sizes, 1):
            for inst in range(n_instances):
                seed = random.randint(0, 10**9)
                data = gen_building(n, seed, b_class)
                
                # Dateiname: K{1..5}_S{01..20}_I{0..2}
                fname = f"{b_class}_s{s_idx:02d}_i{inst}"
                data["meta"]["building_name"] = fname
                
                with (out / f"{fname}.json").open("w") as f:
                    json.dump(data, f, indent=2)
                total_count += 1

    print(f"Done! 5 Klassen × 20 Größen × 3 Instanzen = {total_count} Gebäude.")
    print(f"Speicherort: {out.resolve()}")

if __name__ == "__main__":
    main()