import statistics
import matplotlib.pyplot as plt
from scipy.stats import linregress
from benchmark_core import collect_benchmark_data

def run_h3(raw_results):
    floors_map = {}
    for b_data in raw_results.values():
        f = b_data["n_floors"]
        floors_map.setdefault(f, {"baseline": [], "layered": []})
        floors_map[f]["baseline"].extend([res[0] for res in b_data["baseline"]])
        floors_map[f]["layered"].extend([res[0] for res in b_data["layered"]])

    xs = sorted(floors_map.keys())
    mean_base = [statistics.mean(floors_map[f]["baseline"]) for f in xs]
    mean_layer = [statistics.mean(floors_map[f]["layered"]) for f in xs]

    slope_b, _, rb, _, _ = linregress(xs, mean_base)
    slope_l, _, rl, _, _ = linregress(xs, mean_layer)

    plt.figure(figsize=(9, 6))
    plt.plot(xs, mean_base, "bo-", label=f"A* (Steigung={slope_b:.1f})")
    plt.plot(xs, mean_layer, "gs-", label=f"Layered A* (Steigung={slope_l:.1f})")
    plt.xlabel("Anzahl Etagen"); plt.ylabel("Expansionen (Ø)")
    plt.legend(); plt.grid(True); plt.show()

if __name__ == "__main__":
    data_dir = "generated_buildings"
    results = collect_benchmark_data(data_dir, pairs_per_building=20)
    run_h3(results)