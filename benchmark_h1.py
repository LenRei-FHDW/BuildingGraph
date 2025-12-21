import statistics
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon
import math
from benchmark_core import collect_benchmark_data


def run_h1(raw_results):
    bins, all_base_exp, all_layer_exp = {}, [], []

    for b_data in raw_results.values():
        n_nodes = b_data["n_nodes"]
        bin_center = 10 ** round(math.log10(n_nodes), 1) if n_nodes > 0 else 0
        bins.setdefault(bin_center, {"baseline": [], "layered": []})

        # Extraktion der Expansionen (Index 0)
        base_exp = [res[0] for res in b_data["baseline"]]
        layer_exp = [res[0] for res in b_data["layered"]]

        bins[bin_center]["baseline"].extend(base_exp)
        bins[bin_center]["layered"].extend(layer_exp)
        all_base_exp.extend(base_exp)
        all_layer_exp.extend(layer_exp)

    xs = sorted(bins.keys())
    mean_base = [statistics.mean(bins[x]["baseline"]) for x in xs]
    mean_layer = [statistics.mean(bins[x]["layered"]) for x in xs]

    # --- Plotting ---
    plt.figure(figsize=(10, 6))
    plt.plot(xs, mean_base, "bo-", label="A* (klassisch)", linewidth=1.5, markersize=5)
    plt.plot(xs, mean_layer, "gs-", label="Layered A*", linewidth=1.5, markersize=5)

    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Anzahl Knoten |V| (log)")
    plt.ylabel("Expandierte Knoten (log)")
    plt.title("H1: Reduktion des Suchraums durch Layer-Modell", fontsize=12, fontweight='bold')
    plt.legend(shadow=True)
    plt.grid(True, which="both", linestyle="--", alpha=0.6)

    # Bild speichern
    output_file = "h1_reduction_plot.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Grafik wurde als '{output_file}' gespeichert.")

    plt.show()

    # --- Statistik ---
    stat, p = wilcoxon(all_base_exp, all_layer_exp)
    ratios = [b / l if l > 0 else 1.0 for b, l in zip(all_base_exp, all_layer_exp)]

    print("\n" + "=" * 30)
    print("=== H1 ERGEBNIS ===")
    print(f"Ø Verbesserung: Faktor {statistics.mean(ratios):.2f}")
    print(f"p-Wert: {p:.2e}")
    if p < 0.05:
        print("Status: Statistisch signifikant")
    print("=" * 30)


if __name__ == "__main__":
    data_dir = "generated_buildings"
    results = collect_benchmark_data(data_dir, pairs_per_building=20)
    run_h1(results)