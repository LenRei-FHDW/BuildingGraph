import statistics
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter
from benchmark_core import collect_benchmark_data


def run_h2(raw_results):
    node_counts, means_base, means_layer = [], [], []

    for b_data in raw_results.values():
        node_counts.append(b_data["n_nodes"])
        means_base.append(statistics.mean([res[0] for res in b_data["baseline"]]))
        means_layer.append(statistics.mean([res[0] for res in b_data["layered"]]))

    log_x, log_base, log_layer = np.log10(node_counts), np.log10(means_base), np.log10(means_layer)
    res_b, res_l = linregress(log_x, log_base), linregress(log_x, log_layer)

    # Animation erstellen
    fig, ax = plt.subplots(figsize=(10, 7))

    # Sortieren für flüssigere Animation
    sorted_indices = np.argsort(node_counts)
    node_counts_sorted = [node_counts[i] for i in sorted_indices]
    means_base_sorted = [means_base[i] for i in sorted_indices]
    means_layer_sorted = [means_layer[i] for i in sorted_indices]

    # Für die Regressionslinien
    x_range = np.linspace(min(node_counts), max(node_counts), 100)
    y_base_line = 10 ** res_b.intercept * x_range ** res_b.slope
    y_layer_line = 10 ** res_l.intercept * x_range ** res_l.slope

    scatter_base = ax.scatter([], [], color='blue', alpha=0.3, s=50)
    scatter_layer = ax.scatter([], [], color='green', alpha=0.3, s=50)
    line_base, = ax.plot([], [], "b-", linewidth=2, label=f"A*: α={res_b.slope:.2f}")
    line_layer, = ax.plot([], [], "g-", linewidth=2, label=f"Layered: α={res_l.slope:.2f}")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(min(node_counts) * 0.8, max(node_counts) * 1.2)
    ax.set_ylim(min(means_base + means_layer) * 0.5, max(means_base + means_layer) * 1.5)
    ax.set_title("H2: Skalierungsverhalten $O(N^\\alpha)$", fontsize=14, fontweight='bold')
    ax.set_xlabel("Anzahl Knoten |V|", fontsize=12)
    ax.set_ylabel("Expandierte Knoten", fontsize=12)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    total_points = len(node_counts_sorted)
    frames_for_points = total_points
    frames_for_lines = 30
    total_frames = frames_for_points + frames_for_lines

    def animate(frame):
        if frame < frames_for_points:
            # Punkte erscheinen nacheinander
            idx = frame + 1
            scatter_base.set_offsets(np.c_[node_counts_sorted[:idx], means_base_sorted[:idx]])
            scatter_layer.set_offsets(np.c_[node_counts_sorted[:idx], means_layer_sorted[:idx]])
        else:
            # Linien werden gezeichnet
            progress = (frame - frames_for_points) / frames_for_lines
            line_idx = int(progress * len(x_range))
            line_base.set_data(x_range[:line_idx], y_base_line[:line_idx])
            line_layer.set_data(x_range[:line_idx], y_layer_line[:line_idx])

        return scatter_base, scatter_layer, line_base, line_layer

    anim = FuncAnimation(fig, animate, frames=total_frames, interval=50, blit=True, repeat=True)

    # Als MP4 speichern
    writer = FFMpegWriter(fps=20, bitrate=1800)
    anim.save("h2_scaling_benchmark.mp4", writer=writer)
    plt.close()

    print(f"Animation gespeichert: h2_scaling_benchmark.mp4")
    print(f"A* Skalierung: O(N^{res_b.slope:.3f})")
    print(f"Layered Skalierung: O(N^{res_l.slope:.3f})")
