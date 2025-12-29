import os
import math
import statistics
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.animation import FuncAnimation, FFMpegWriter
from scipy.stats import wilcoxon


def run_h4(raw_results):
    """
    H4 – Effizienz vs. Optimalität
    Robuste Version mit garantiert gültigem MP4-Export
    """

    # =========================
    # 1. Daten sammeln
    # =========================
    exp_ratios = []
    cost_diffs = []
    n_nodes_list = []
    building_ids = []

    for building_id, b_data in raw_results.items():
        n_nodes = b_data["n_nodes"]

        for (b_exp, b_cost), (l_exp, l_cost) in zip(
            b_data["baseline"], b_data["layered"]
        ):
            if (
                b_exp > 0
                and b_cost > 0
                and l_cost > 0
                and l_cost != float("inf")
            ):
                exp_ratios.append(l_exp / b_exp)
                cost_diffs.append((l_cost - b_cost) / b_cost * 100)
                n_nodes_list.append(n_nodes)
                building_ids.append(building_id)

    if not exp_ratios:
        raise RuntimeError("H4: Keine gültigen Messpunkte gefunden.")

    # =========================
    # 2. Boxplot – Effizienz
    # =========================
    plt.figure(figsize=(10, 4.5))
    plt.boxplot(
        exp_ratios,
        vert=False,
        patch_artist=True,
        boxprops=dict(facecolor="skyblue", alpha=0.7),
        medianprops=dict(color="black", linewidth=2),
    )

    plt.axvline(1.0, color="red", linestyle="--", label="Baseline (1.0)")
    plt.xlabel("Layered / Baseline ( < 1 = effizienter )")
    plt.title("H4 – Reduktion der Knotenexpansionen")
    plt.yticks([])
    plt.grid(axis="x", linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig("h4_efficiency.png", dpi=300)
    plt.close()

    # =========================
    # 3. Vorbereitung Animation
    # =========================
    order = np.argsort(n_nodes_list)

    x = np.array(n_nodes_list)[order]
    y = np.array(cost_diffs)[order]
    ratios = np.array(exp_ratios)[order]
    labels = np.array(building_ids)[order]

    # defensive Grenzen
    xmin = max(1, x.min() * 0.8)
    xmax = x.max() * 1.2
    ymin = min(-5, y.min() - 2)
    ymax = max(5, y.max() + 5)

    fig, ax = plt.subplots(figsize=(10, 6))

    scatter = ax.scatter([], [], s=28, alpha=0.45)

    ax.set_xscale("log")
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    ax.axhline(0, color="black", linewidth=1.4, label="Globales Optimum (0%)")

    ax.set_title(
        "H4 – Pfadoptimalität in Abhängigkeit von der Gebäudegröße",
        fontsize=12,
        fontweight="bold",
    )
    ax.set_xlabel("Anzahl Knoten |V| (log)")
    ax.set_ylabel("Kostenabweichung in %")
    ax.grid(True, which="both", linestyle=":", alpha=0.5)
    ax.legend()

    info_text = ax.text(
        xmin,
        ymax * 0.92,
        "Punkte auf der 0%-Linie = optimaler Pfad",
        fontsize=9,
        color="green",
        bbox=dict(facecolor="white", alpha=0.85),
    )

    id_texts = []

    # =========================
    # 4. Init & Animate
    # =========================
    def init():
        scatter.set_offsets(np.empty((0, 2)))
        return (scatter,)

    def animate(frame):
        pts = np.column_stack((x[: frame + 1], y[: frame + 1]))
        scatter.set_offsets(pts)

        # alte Labels entfernen
        for t in id_texts:
            t.remove()
        id_texts.clear()

        # auffällige Gebäude markieren
        for i in range(frame + 1):
            if ratios[i] > 2.0:
                txt = ax.text(
                    x[i],
                    y[i] + 1.0,
                    labels[i],
                    fontsize=7,
                    color="red",
                    ha="center",
                    va="bottom",
                    fontweight="bold",
                )
                id_texts.append(txt)

        return (scatter,)

    anim = FuncAnimation(
        fig,
        animate,
        init_func=init,
        frames=len(x),
        interval=35,
        blit=False,
        repeat=True,
    )

    # =========================
    # 5. Sicherer MP4-Export
    # =========================
    writer = FFMpegWriter(
        fps=25,
        codec="libx264",
        bitrate=2000,
        extra_args=[
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart"
        ],
    )

    out_file = "h4_optimality_vs_size.mp4"
    anim.save(out_file, writer=writer)
    plt.close()

    print(f"Animation gespeichert: {out_file}")
    print(f"Dateigröße: {os.path.getsize(out_file) / 1024:.1f} KB")

    # =========================
    # 6. Statistik
    # =========================
    avg_gain = (1 - statistics.mean(exp_ratios)) * 100
    avg_opt_loss = statistics.mean(cost_diffs)

    print("\n" + "=" * 46)
    print(f"{'H4 – STATISTIK':^46}")
    print("=" * 46)
    print(f"Ø Suchraumreduktion:        {avg_gain:8.2f} %")
    print(f"Ø Optimalitätsabweichung:  {avg_opt_loss:8.4f} %")

    if any(abs(d) > 1e-9 for d in cost_diffs):
        stat, p = wilcoxon(cost_diffs)
        print(f"Wilcoxon-Test (Kosten):    p = {p:.3e}")
    else:
        print("Alle Pfade sind optimal (0%).")

    print("=" * 46)
