from benchmark_core import collect_benchmark_data
from benchmark_h1 import run_h1
from benchmark_h2 import run_h2
from benchmark_h3 import run_h3
from benchmark_h4 import run_h4
from benchmark_h5 import run_efficiency_benchmark
from benchmark_h6 import run_scalability_benchmark


def main():
    data_dir="generated_buildings"
    raw_results = collect_benchmark_data(data_dir, pairs_per_building=20)
    run_h1(raw_results)
    run_h2(raw_results)
    run_h3(raw_results)
    run_h4(raw_results)
    run_scalability_benchmark(raw_results)
    run_efficiency_benchmark(raw_results)

if __name__ == "__main__":
    main()
