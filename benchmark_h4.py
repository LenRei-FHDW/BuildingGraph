import statistics
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon
import numpy as np
import math
from benchmark_core import collect_benchmark_data


def run_h4(raw_results):
    exp_ratios = []  # Verhältnis Expansionen: Layered / Baseline
    cost_diffs = []  # Prozentuale Kostendifferenz
    n_nodes_list = []  # Anzahl der Knoten (für die neue x-Achse)

    for b_data in raw_results.values():
        n_nodes = b_data["n_nodes"]

        # Unpacking der Messergebnisse
        for (b_exp, b_cost), (l_exp, l_cost) in zip(b_data["baseline"], b_data["layered"]):
            if b_exp > 0 and b_cost > 0 and l_cost != float("inf"):
                exp_ratios.append(l_exp / b_exp)
                cost_diffs.append(((l_cost - b_cost) / b_cost) * 100)
                n_nodes_list.append(n_nodes)

    # --------------------------------------------------------
    # PLOT 1: EFFIZIENZ (Boxplot) - Unverändert
    # --------------------------------------------------------
    plt.figure(figsize=(10, 5))
    plt.boxplot(exp_ratios, vert=False, patch_artist=True,
                boxprops=dict(facecolor="skyblue", alpha=0.6))
    plt.axvline(1.0, color='red', linestyle='--', label='Baseline-Niveau (1.0)')

    plt.title("H4: Effizienzgewinn (Knotenexpansionen)")
    plt.xlabel("Verhältnis Layered/Baseline (Werte < 1.0 sind effizienter)")
    plt.yticks([])
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig("h4_efficiency.png", dpi=300)
    plt.show()

    # --------------------------------------------------------
    # PLOT 2: PFADQUALITÄT (Scatter Plot) - X-ACHSE GEÄNDERT
    # --------------------------------------------------------
    plt.figure(figsize=(10, 6))

    # Scatter Plot mit Knotenzahl auf der X-Achse
    plt.scatter(n_nodes_list, cost_diffs, alpha=0.4, color='purple', edgecolors='none', s=25)

    plt.axhline(0, color='black', linestyle='-', linewidth=1.5, label="Optimal (0% Abweichung)")

    # Logarithmische Skalierung für Knotenzahl (da oft von 300 bis 12000)
    plt.xscale("log")

    plt.title("H4: Analyse der Pfadqualität vs. Gebäudegröße", fontsize=12, fontweight='bold')
    plt.xlabel("Anzahl Knoten im Gebäude |V| (log-Skala)")
    plt.ylabel("Zusatzkosten in % (0% = Optimal)")

    # Intelligente Grid-Einteilung
    plt.grid(True, which="both", linestyle=":", alpha=0.5)
    plt.legend()

    # Annotation
    plt.text(min(n_nodes_list), max(cost_diffs) * 0.9, " Punkte auf der 0%-Linie = Globales Optimum gefunden",
             fontsize=9, color='green', fontweight='bold', bbox=dict(facecolor='white', alpha=0.8))

    plt.tight_layout()
    plt.savefig("h4_optimality_vs_size.png", dpi=300)
    plt.show()
    print("Grafik gespeichert: h4_optimality_vs_size.png")

    # --------------------------------------------------------
    # STATISTIK-AUSGABE
    # --------------------------------------------------------
    avg_gain = (1 - statistics.mean(exp_ratios)) * 100
    avg_opt_loss = statistics.mean(cost_diffs)

    print("\n" + "=" * 40)
    print(f"{'H4 STATISTIK':^40}")
    print("=" * 40)
    print(f"Ø Suchraum-Reduktion:         {avg_gain:.2f}%")
    print(f"Ø Abweichung (Optimality Gap): {avg_opt_loss:.4f}%")

    # Wilcoxon-Test (Prüfung ob Abweichung signifikant von 0 verschieden ist)
    if any(d != 0 for d in cost_diffs):
        stat, p = wilcoxon(cost_diffs)
        print(f"Wilcoxon p-Wert (Kosten):      {p:.3e}")
    else:
        print("Alle Pfade sind zu 100% optimal.")
    print("=" * 40)


if __name__ == "__main__":
    # Stelle sicher, dass der Pfad korrekt ist
    data_dir = "stress_test_set"
    results = collect_benchmark_data(data_dir, pairs_per_building=20)
    run_h4(results)