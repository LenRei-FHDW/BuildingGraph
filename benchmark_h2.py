import math
import statistics
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress
from benchmark_core import collect_benchmark_data


def run_h2(raw_results):
    node_counts, means_base, means_layer = [], [], []

    for b_data in raw_results.values():
        node_counts.append(b_data["n_nodes"])
        # Mittelwert der Expansionen (Index 0) pro Gebäude
        means_base.append(statistics.mean([res[0] for res in b_data["baseline"]]))
        means_layer.append(statistics.mean([res[0] for res in b_data["layered"]]))

    log_x, log_base, log_layer = np.log10(node_counts), np.log10(means_base), np.log10(means_layer)
    res_b, res_l = linregress(log_x, log_base), linregress(log_x, log_layer)

    plt.figure(figsize=(10, 7))
    plt.scatter(node_counts, means_base, color='blue', alpha=0.3)
    plt.scatter(node_counts, means_layer, color='green', alpha=0.3)

    x_range = np.linspace(min(node_counts), max(node_counts), 100)
    plt.plot(x_range, 10 ** res_b.intercept * x_range ** res_b.slope, "b-", label=f"A*: α={res_b.slope:.2f}")
    plt.plot(x_range, 10 ** res_l.intercept * x_range ** res_l.slope, "g-", label=f"Layered: α={res_l.slope:.2f}")

    plt.xscale("log");
    plt.yscale("log")
    plt.title("H2: Skalierungsverhalten $O(N^\\alpha)$")
    plt.legend();
    plt.show()
    print(f"A* Skalierung: O(N^{res_b.slope:.3f})\nLayered Skalierung: O(N^{res_l.slope:.3f})")


if __name__ == "__main__":
    data_dir = "generated_buildings"
    results = collect_benchmark_data(data_dir, pairs_per_building=20)
    run_h2(results)