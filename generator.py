# generator.py
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple

# ==================================================
# Helpers
# ==================================================

def clamp(x: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, x))

def euclid(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
    return math.dist(a, b)

def sizes_geometric(n: int, lo: int, hi: int) -> List[int]:
    r = (hi / lo) ** (1 / (n - 1))
    return [int(lo * r ** i) for i in range(n)]

def distribute_counts(total: int, buckets: int) -> List[int]:
    """Verteilt 'total' möglichst gleichmäßig auf 'buckets' (Summe exakt total)."""
    base = total // buckets
    rem = total % buckets
    return [base + (1 if i < rem else 0) for i in range(buckets)]

# ==================================================
# GraphBuilder
# ==================================================

class GraphBuilder:
    def __init__(self, name: str, b_class: str):
        self.meta = {
            "building_name": name,
            "group": b_class,
            "unit": "meters",
            "format_version": 1
        }
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []

    def add_node(self, nid: str, ntype: str, level: int, pos: Tuple[float, float, float], attrs=None):
        self.nodes[nid] = {
            "id": nid,
            "name": nid,
            "type": ntype,
            "level": level,
            "pos": [float(pos[0]), float(pos[1]), float(pos[2])],
            "attrs": attrs or {}
        }

    def add_edge(self, a: str, b: str, weight: float | None = None, attrs=None):
        if a not in self.nodes or b not in self.nodes:
            return
        pa = tuple(self.nodes[a]["pos"])
        pb = tuple(self.nodes[b]["pos"])
        w = float(weight) if weight is not None else euclid(pa, pb)
        self.edges.append({
            "a": a,
            "b": b,
            "weight": round(w, 3),
            "attrs": attrs or {}
        })

    def as_json(self) -> Dict[str, Any]:
        return {"meta": self.meta, "nodes": list(self.nodes.values()), "edges": self.edges}

# ==================================================
# Global cost model knobs (match your Layered heuristic assumptions)
# ==================================================

# Damit Layered-Heuristik "passt": pro Etagenwechsel MUSS es eine spürbare Mindestkostenstruktur geben.
# Du verwendest im RoutingModel floor_transition_penalty=10.0 und in der Heuristik fixed_entry_cost≈5.0
# => Mindestkosten pro Etage ~15.0. Wir sorgen hier dafür, dass vertikale Kanten NICHT günstiger sind.
FLOOR_TRANSITION_PENALTY = 10.0
FIXED_ENTRY_COST = 5.0
MIN_FLOOR_STEP_COST = FLOOR_TRANSITION_PENALTY + FIXED_ENTRY_COST  # ~15.0

# ==================================================
# Elevators (kept, but made consistent with Layered model)
# ==================================================

def add_elevators(
    gb: GraphBuilder,
    floors: int,
    floor_nodes: Dict[int, List[str]],
    rnd: random.Random,
):
    """
    Aufzüge bleiben drin. Wichtig: Vertikale Fahrten dürfen NICHT günstiger sein als MIN_FLOOR_STEP_COST,
    sonst überschätzt die Layered-Heuristik systematisch und verliert Suchqualität/Expansion.
    """
    n_shafts = rnd.randint(1, max(1, floors // 3))
    for s in range(n_shafts):
        shaft_id = f"E{s}"
        served = sorted(rnd.sample(range(floors), rnd.randint(2, floors)))
        prev_cabin = None

        for f in served:
            z = f * 3.0
            cabin = f"elev_{shaft_id}_F{f}"
            door = f"door_{shaft_id}_F{f}"

            gb.add_node(
                cabin, "elevator_cabin", f,
                (rnd.uniform(-10, -5), rnd.uniform(-10, -5), z),
                {"shaft": shaft_id}
            )
            gb.add_node(
                door, "elevator_door", f,
                (rnd.uniform(-4, -2), rnd.uniform(-4, -2), z),
                {"shaft": shaft_id}
            )

            # Verbindung zum Stockwerk (lokale Tür)
            if floor_nodes.get(f):
                gb.add_edge(rnd.choice(floor_nodes[f]), door, weight=None, attrs={"action": "walk_to_elevator"})
            # Einstieg (Fixkosten)
            gb.add_edge(door, cabin, weight=FIXED_ENTRY_COST, attrs={"action": "enter_elevator"})

            # Vertikale Fahrt (Wartezeit + Fahrtzeit), aber niemals zu billig
            if prev_cabin:
                dist = abs(gb.nodes[prev_cabin]["level"] - f)
                # konservativ: mindestens MIN_FLOOR_STEP_COST pro Etage, plus etwas Fahrtzeit
                move_cost = dist * (MIN_FLOOR_STEP_COST + 2.5)
                gb.add_edge(prev_cabin, cabin, weight=move_cost, attrs={"elevator_move": True})
            prev_cabin = cabin

# ==================================================
# Connectivity helpers
# ==================================================

def connect_floors_with_stairs_chain(
    gb: GraphBuilder,
    floors: int,
    floor_nodes: Dict[int, List[str]],
    rnd: random.Random,
):
    """
    Fügt eine explizite Treppen-Kette ein, sodass jedes Gebäude garantiert
    über alle Etagen verbunden ist. Kosten >= MIN_FLOOR_STEP_COST.
    """
    for f in range(floors - 1):
        if not floor_nodes.get(f) or not floor_nodes.get(f + 1):
            continue
        a = rnd.choice(floor_nodes[f])
        b = rnd.choice(floor_nodes[f + 1])
        gb.add_edge(a, b, weight=MIN_FLOOR_STEP_COST, attrs={"stairs": True})

def ensure_within_floor_backbone(
    gb: GraphBuilder,
    floor_nodes: Dict[int, List[str]],
    rnd: random.Random,
):
    """
    Sorgt dafür, dass pro Etage ein (leichter) Backbone existiert,
    damit die Heuristik sinnvoll greifen kann und der Graph nicht in Inseln zerfällt.
    """
    for f, ids in floor_nodes.items():
        if len(ids) < 2:
            continue
        # Verbinde die Etage als einfache Kette (billig, euklidisch)
        # (wir nehmen eine zufällige Reihenfolge, um nicht immer gleiche Strukturen zu erzeugen)
        perm = ids[:]
        rnd.shuffle(perm)
        for i in range(1, len(perm)):
            gb.add_edge(perm[i - 1], perm[i], weight=None, attrs={"backbone": True})

# ==================================================
# Class-Specific Generators
# ==================================================

def gen_building(target_nodes: int, seed: int, b_class: str) -> Dict[str, Any]:
    rnd = random.Random(seed)
    gb = GraphBuilder(f"B_{b_class}_{target_nodes}_{seed}", b_class)
    floor_nodes: Dict[int, List[str]] = {}

    # --------------------------------------------------
    # K1: Linear (Worst Case für A*) - 2 Etagen, lange Ketten, ein teurer Wechsel
    # --------------------------------------------------
    if b_class == "K1":
        floors = 2
        counts = distribute_counts(target_nodes, floors)
        for f in range(floors):
            floor_nodes[f] = []
            for i in range(counts[f]):
                nid = f"n_f{f}_{i}"
                gb.add_node(nid, "path", f, (i * 3.0, f * 10.0, f * 3.0))
                floor_nodes[f].append(nid)
                if i > 0:
                    gb.add_edge(f"n_f{f}_{i-1}", nid, weight=None)
        # ein kontrollierter Wechsel zwischen Etagen (nicht zu billig)
        gb.add_edge(floor_nodes[0][-1], floor_nodes[1][0], weight=MIN_FLOOR_STEP_COST, attrs={"stairs": True})

    # --------------------------------------------------
    # K2: Stark geclustert (Best Case) - jetzt explizit multi-floor + klare Vertikal-Connectoren
    # --------------------------------------------------
    elif b_class == "K2":
        # Mehr Etagen als vorher, damit Layered wirken kann
        floors = clamp(target_nodes // 200, 3, 8)
        floor_counts = distribute_counts(target_nodes, floors)

        # Pro Etage mehrere Cluster (lokal dicht), zwischen Clustern weite Brücken
        nodes_per_cluster = 20
        for f in range(floors):
            floor_nodes[f] = []
            n_on_floor = floor_counts[f]
            n_clusters = max(1, n_on_floor // nodes_per_cluster)
            # exakte Verteilung innerhalb der Etage
            cluster_sizes = distribute_counts(n_on_floor, n_clusters)

            prev_cluster_rep = None
            for c, c_size in enumerate(cluster_sizes):
                cx, cy = rnd.uniform(0, 200), rnd.uniform(0, 200)
                cluster_ids = []
                for i in range(c_size):
                    nid = f"f{f}_c{c}_n{i}"
                    gb.add_node(
                        nid, "room", f,
                        (cx + rnd.uniform(-2, 2), cy + rnd.uniform(-2, 2), f * 3.0)
                    )
                    # dichte lokale Verbindungen
                    if cluster_ids:
                        gb.add_edge(rnd.choice(cluster_ids), nid, weight=None)
                    cluster_ids.append(nid)
                    floor_nodes[f].append(nid)

                # weite Brücken zwischen Clustern auf derselben Etage (dominant horizontal)
                rep = cluster_ids[0]
                if prev_cluster_rep:
                    gb.add_edge(prev_cluster_rep, rep, weight=50.0, attrs={"bridge": True})
                prev_cluster_rep = rep

        # Vertikale Verbindungen: klar als "stairs" mit Mindestkosten (damit Layered-H passt)
        connect_floors_with_stairs_chain(gb, floors, floor_nodes, rnd)

    # --------------------------------------------------
    # K3: Realistisch (Indoor) - Korridore + Räume, Treppen zwischen Etagen (nicht zu billig)
    # --------------------------------------------------
    elif b_class == "K3":
        floors = clamp(target_nodes // 150, 2, 6)
        per_floor = distribute_counts(target_nodes, floors)

        for f in range(floors):
            floor_nodes[f] = []
            n_on_floor = per_floor[f]

            # Wir bauen pro Etage einen Korridor-Backbone und hängen Räume dran.
            # Verhältnis: ca. 1/2 corridor, 1/2 rooms (aufgerundet).
            n_corr = max(1, n_on_floor // 2)
            n_rooms = n_on_floor - n_corr

            corridor_ids = []
            for i in range(n_corr):
                cid = f"corr_f{f}_{i}"
                gb.add_node(cid, "corridor", f, (i * 4.0, 0.0, f * 3.0))
                corridor_ids.append(cid)
                floor_nodes[f].append(cid)
                if i > 0:
                    gb.add_edge(corridor_ids[i - 1], cid, weight=None, attrs={"corridor": True})

            for i in range(n_rooms):
                # hänge Raum an zufälligen Korridor
                anchor = rnd.choice(corridor_ids)
                rid = f"room_f{f}_{i}"
                # seitlich vom Korridor
                ax = gb.nodes[anchor]["pos"][0]
                gb.add_node(rid, "room", f, (ax, rnd.choice([-3.0, 3.0]), f * 3.0))
                gb.add_edge(anchor, rid, weight=None, attrs={"door": True})
                floor_nodes[f].append(rid)

        connect_floors_with_stairs_chain(gb, floors, floor_nodes, rnd)

    # --------------------------------------------------
    # K4: Mehrstockwerk (Vertikaler Fokus) - FIX: vertikale Kanten NICHT euklidisch billig
    # --------------------------------------------------
    elif b_class == "K4":
        floors = clamp(target_nodes // 40, 5, 40)
        per_floor = distribute_counts(target_nodes, floors)

        for f in range(floors):
            floor_nodes[f] = []
            for i in range(per_floor[f]):
                nid = f"n_f{f}_{i}"
                gb.add_node(nid, "node", f, (rnd.uniform(0, 10), rnd.uniform(0, 10), f * 3.0))
                floor_nodes[f].append(nid)

        # innerhalb Etage Backbone
        ensure_within_floor_backbone(gb, floor_nodes, rnd)

        # vertikal: explizit Treppe mit Mindestkosten (statt Default-Euklidisch)
        connect_floors_with_stairs_chain(gb, floors, floor_nodes, rnd)

    # --------------------------------------------------
    # K5: Chaotisch/Random - FIX: nicht zu viele Quer-Kanten; dennoch verbunden + vertikal nicht billig
    # --------------------------------------------------
    else:
        floors = 5
        per_floor = distribute_counts(target_nodes, floors)

        all_nodes: List[str] = []
        for f in range(floors):
            floor_nodes[f] = []
            for i in range(per_floor[f]):
                nid = f"rand_f{f}_{i}"
                gb.add_node(nid, "node", f, (rnd.uniform(0, 150), rnd.uniform(0, 150), f * 3.0))
                floor_nodes[f].append(nid)
                all_nodes.append(nid)

        # innerhalb Etage: ein bisschen Struktur
        ensure_within_floor_backbone(gb, floor_nodes, rnd)

        # random cross edges: reduziert, damit Heuristik nicht komplett entwertet wird
        # (zu viele Cross-Edges machen jedes h "rauschig" und killen Layered-Vorteile)
        for _ in range(max(1, target_nodes // 6)):
            a = rnd.choice(all_nodes)
            b = rnd.choice(all_nodes)
            if a != b and rnd.random() < 0.5:
                gb.add_edge(a, b, weight=50.0, attrs={"random_bridge": True})

        connect_floors_with_stairs_chain(gb, floors, floor_nodes, rnd)

    # --------------------------------------------------
    # Aufzüge überall hinzufügen (aber kostenkonsistent)
    # --------------------------------------------------
    add_elevators(gb, floors, floor_nodes, rnd)

    return gb.as_json()

# ==================================================
# Main Loop
# ==================================================

def main():
    classes = ["K1", "K2", "K3", "K4", "K5"]
    n_sizes = 20
    n_instances = 3

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="generated_buildings")
    ap.add_argument("--nmin", type=int, default=300)
    ap.add_argument("--nmax", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=None, help="Optional: global seed for reproducibility")
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    sizes = sizes_geometric(n_sizes, args.nmin, args.nmax)
    total_count = 0

    for b_class in classes:
        for s_idx, n in enumerate(sizes, 1):
            for inst in range(n_instances):
                seed = random.randint(0, 10**9)
                data = gen_building(n, seed, b_class)

                # Dateiname: K{1..5}_S{01..20}_I{0..2}
                fname = f"{b_class}_s{s_idx:02d}_i{inst}"
                data["meta"]["building_name"] = fname

                with (out / f"{fname}.json").open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

                total_count += 1

    print(f"Done! 5 Klassen × {n_sizes} Größen × {n_instances} Instanzen = {total_count} Gebäude.")
    print(f"Speicherort: {out.resolve()}")
    print(f"Vertikale Mindestkosten (stairs) = {MIN_FLOOR_STEP_COST:.1f}")
    print(f"Elevator move: dist * ({MIN_FLOOR_STEP_COST:.1f} + 2.5)")

if __name__ == "__main__":
    main()
