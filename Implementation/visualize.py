from typing import List, Optional, Set, Tuple
import matplotlib.pyplot as plt

from BuildingGraph import BuildingGraph


def visualize_step(
    graph: BuildingGraph,
    open_set: List[Tuple[float, int]],
    closed_set: Set[int],
    current_idx: int,
    start_idx: int,
    goal_idx: int,
    step: int,
    path_indices: Optional[List[int]] = None,
    output_dir: str = "steps"
):
    # Gruppiere Nodes nach Level
    levels = sorted(set(n.level for n in graph.routing_nodes))
    fig, axes = plt.subplots(1, len(levels), figsize=(5 * len(levels), 5))

    if len(levels) == 1:
        axes = [axes]

    open_indices = {idx for _, idx in open_set}
    path_indices = set(path_indices or [])

    for ax, level in zip(axes, levels):
        ax.set_title(f"Level {level}")
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])

        # Draw edges (nur innerhalb eines Levels)
        for idx, node in enumerate(graph.routing_nodes):
            if node.level != level:
                continue
            for edge in graph.neighbors(idx):
                target = graph.routing_nodes[edge.target]
                if target.level != level:
                    continue

                x = [node.pos[0], target.pos[0]]
                y = [node.pos[1], target.pos[1]]
                ax.plot(x, y, color="lightgray", zorder=1)

        # Draw nodes
        for idx, node in enumerate(graph.routing_nodes):
            if node.level != level or node.pos is None:
                continue

            color = "white"
            size = 300

            if idx == start_idx:
                color = "blue"
            elif idx == goal_idx:
                color = "red"
            elif idx == current_idx:
                color = "orange"
            elif idx in path_indices:
                color = "green"
            elif idx in closed_set:
                color = "gray"
            elif idx in open_indices:
                color = "gold"
            elif graph.raw_nodes[graph.id(idx)].type in ("stair", "elevator"):
                color = "purple"

            ax.scatter(node.pos[0], node.pos[1], s=size, c=color, zorder=2)
            ax.text(
                node.pos[0],
                node.pos[1] + 0.15,
                graph.id(idx),
                ha="center",
                fontsize=7
            )

    plt.suptitle(f"Layered A* – Schritt {step}")
    plt.tight_layout()
    plt.savefig(f"step_{step:03d}.png")
    plt.close()
