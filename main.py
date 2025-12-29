from layered_a_star_ChatGPT import benchmark_all_pairs, layered_a_star, load_building
import os

if __name__ == '__main__':
    print(os.getcwd())
    graph, model = load_building("test_building.json")

    # Example search
    START = "entrance_L0"
    GOAL = "room_L2_1"

    path, cost, dt = layered_a_star(graph, model, START, GOAL, visualize=True)

    if path:
        print("\nShortest path found:")
        for step in path:
            print(" →", step)
        print(f"\nTotal cost: {cost:.3f}")
    else:
        print("No path found.")

    print(f"Search time: {dt * 1000:.2f} ms\n")

    # Run benchmarks
    _ = benchmark_all_pairs(graph, model)