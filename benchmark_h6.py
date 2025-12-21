import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import math
import statistics
from benchmark_core import collect_benchmark_data


def run_scalability_benchmark(raw_data):
    # Struktur: { class_name: { bin_center: [list_of_expansions] } }
    class_bins = {}

    for filename, results in raw_data.items():
        b_class = filename.split('_')[0]
        n_nodes = results["n_nodes"]

        # Logarithmisches Binning (gruppiert Gebäude ähnlicher Größe)
        bin_center = 10 ** round(math.log10(n_nodes), 1) if n_nodes > 0 else 0

        class_bins.setdefault(b_class, {})
        class_bins[b_class].setdefault(bin_center, [])

        # Wir betrachten hier den Layered A*
        expansions = [res[0] for res in results["layered"]]
        class_bins[b_class][bin_center].extend(expansions)

    plt.figure(figsize=(10, 6))

    # Farben und Marker für die Klassen
    styles = {
        "K1": ("ro-", "Linear (Worst)"),
        "K2": ("gs-", "Geclustert (Best)"),
        "K3": ("bo-", "Realistisch"),
        "K4": ("mv-", "Mehrstockwerk"),
        "K5": ("yD-", "Chaotisch")
    }

    print("\n" + "=" * 60)
    print(f"{'Klasse':<15} | {'Ø Search Factor':<15} | {'Skalierung'}")
    print("-" * 60)

    for b_class, bins in sorted(class_bins.items()):
        xs = sorted(bins.keys())
        ys = [statistics.mean(bins[x]) for x in xs]

        style, label = styles.get(b_class, ("k+-", b_class))
        plt.plot(xs, ys, style, label=label, markersize=6, linewidth=1.5, alpha=0.8)

        # Text-Statistik berechnen
        avg_factor = statistics.mean([y / x for x, y in zip(xs, ys)]) * 100
        print(f"{label:<15} | {avg_factor:>12.2f}% | {'Linear' if avg_factor < 50 else 'Suboptimal'}")

    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Anzahl Knoten im Graph |V| (log)")
    plt.ylabel("Expandierte Knoten (log)")
    plt.title("Skalierbarkeit: Suchaufwand nach Gebäudeklasse", fontsize=14, fontweight='bold')
    plt.legend(loc="upper left", frameon=True, shadow=True)
    plt.grid(True, which="both", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig("scalability_clean.png", dpi=300)
    print("=" * 60)
    print("Grafik 'scalability_clean.png' wurde erstellt.")
    plt.show()

if __name__ == "__main__":
    data_dir = "generated_buildings"
    results = collect_benchmark_data(data_dir, pairs_per_building=20)
    run_scalability_benchmark(results)