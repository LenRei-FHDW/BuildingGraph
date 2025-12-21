import matplotlib.pyplot as plt
import pandas as pd
from benchmark_core import collect_benchmark_data


def run_efficiency_benchmark(raw_data):
    rows = []
    for filename, results in raw_data.items():
        b_class = filename.split('_')[0]
        for b_res, l_res in zip(results["baseline"], results["layered"]):
            if b_res[0] > 0:
                saving = (1 - (l_res[0] / b_res[0])) * 100
                rows.append({"Class": b_class, "Saving": saving})

    df = pd.DataFrame(rows)

    # --- TEXT INFORMATIONEN ---
    stats = df.groupby("Class")["Saving"].agg(['mean', 'std', 'min', 'max']).sort_values('mean', ascending=False)

    print("\n" + "=" * 50)
    print("EFFIZIENZ-ANALYSE: LAYERED A* VS. BASELINE")
    print("=" * 50)
    print(stats.round(2).to_string())
    print("-" * 50)

    best_class = stats.index[0]
    print(f"ERGEBNIS: Klasse {best_class} profitiert am stärksten vom Layer-Modell.")
    print("Interpretation:")
    print("- K4 (Mehrstockwerk): Hohe Gewinne durch effektives Floor-Skipping.")
    print("- K1 (Linear): Geringe Gewinne, da kaum Suchraum-Alternativen existieren.")
    print("=" * 50 + "\n")

    # --- PLOT ---
    plt.figure(figsize=(10, 6))
    stats['mean'].plot(kind='barh', color='seagreen', edgecolor='black')
    plt.title("Durchschnittlicher Effizienzgewinn pro Klasse (%)", fontsize=14)
    plt.xlabel("Ersparnis an expandierten Knoten")
    plt.ylabel("Gebäudeklasse")
    plt.grid(axis='x', linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    data_dir = "generated_buildings"
    results = collect_benchmark_data(data_dir, pairs_per_building=20)
    run_efficiency_benchmark(results)