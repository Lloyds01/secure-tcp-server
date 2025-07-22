"""This is a benchmarking script that compares different search algorithms."""
from configparser import ConfigParser
import csv
import itertools
import re
import timeit

import matplotlib.pyplot as plt


def update_config(reread: bool):
    """
    Update the configuration file with the provided 'reread' value.

    Args:
        reread (bool): Determines whether to reread the file on every query.
    """
    config = ConfigParser()
    config["DEFAULT"] = {
        "linuxpath": "test_file.txt",
        "reread_on_query": str(reread),
        "ssl_enabled": "False",
    }
    with open("config.ini", "w") as f:
        config.write(f)


def prepare_test_file(n_lines):
    """
    Generate a test file with the given number of lines.

    Args:
        n_lines (int): Number of lines to write to the test file.
    """
    with open("test_file.txt", "w") as f:
        f.writelines([f"line_{i}\n" for i in range(n_lines)])


def linear_search(query):
    """
    Perform a linear search by scanning the file line by line.

    Args:
        query (str): The query string to search for.

    Returns:
        bool: True if the query is found, False otherwise.
    """
    with open("test_file.txt") as f:
        for line in f:
            if query in line:
                return True
    return False


def regex_search(query):
    """
    Perform a regex-based search for the query in the file.

    Args:
        query (str): The query string to search for.

    Returns:
        bool: True if a match is found using regex, False otherwise.
    """
    pattern = re.compile(re.escape(query))
    with open("test_file.txt") as f:
        for line in f:
            if pattern.search(line):
                return True
    return False


def reverse_search(query):
    """
    Perform a reverse search by reading the file from the end.

    Args:
        query (str): The query string to search for.

    Returns:
        bool: True if the query is found, False otherwise.
    """
    with open("test_file.txt") as f:
        for line in reversed(list(f)):
            if query in line:
                return True
    return False


def split_search(query):
    """
    Search for the query by splitting each line on underscores.

    Args:
        query (str): The query string to search for.

    Returns:
        bool: True if the query is found in any of the split parts, False otherwise.
    """
    with open("test_file.txt") as f:
        for line in f:
            parts = line.strip().split("_")
            if query in parts:
                return True
    return False


cache = {}


def cached_search(query):
    """
    Perform a search using cached results for repeated queries.

    Args:
        query (str): The query string to search for.

    Returns:
        bool: True if the query is found, False otherwise.
    """
    if query in cache:
        return cache[query]
    with open("test_file.txt") as f:
        for line in f:
            if query in line:
                cache[query] = True
                return True
    cache[query] = False
    return False


def startswith_search(query):
    """
    Search for the query by checking if any line starts with it.

    Args:
        query (str): The query string to search for.

    Returns:
        bool: True if any line starts with the query, False otherwise.
    """
    with open("test_file.txt") as f:
        for line in f:
            if line.startswith(query):
                return True
    return False


def list_index_search(query):
    """
    Search for the query using list indexing of stripped lines.

    Args:
        query (str): The query string to search for.

    Returns:
        bool: True if the query is found, False otherwise.
    """
    with open("test_file.txt") as f:
        lines = [line.strip() for line in f]
        try:
            _ = lines.index(query)
            return True
        except ValueError:
            return False


def endswith_search(query):
    """
    Search for the query by checking if any line ends with it.

    Args:
        query (str): The query string to search for.

    Returns:
        bool: True if any line ends with the query, False otherwise.
    """
    with open("test_file.txt") as f:
        for line in f:
            if line.strip().endswith(query):
                return True
    return False


search_algorithms = {
    "Linear": linear_search,
    "Regex": regex_search,
    "Reverse": reverse_search,
    "Split": split_search,
    "Cached": cached_search,
    "Startswith": startswith_search,
    "ListIndex": list_index_search,
    "Endswith": endswith_search,
}


def run_single_benchmark(func, reread, n_lines):
    """
    Run a benchmark for a single search function.

    Args:
        func (Callable): The search function to benchmark.
        reread (bool): Whether to reread the file for each query.
        n_lines (int): Number of lines to generate in the test file.

    Returns:
        float: Average execution time in seconds.
    """
    update_config(reread)
    prepare_test_file(n_lines)
    return timeit.timeit(lambda: func("line_5000"), number=100) / 100


def run_all():
    """
    Run all search algorithm benchmarks on varying file sizes.

    Outputs:
        - speed_table.csv: Benchmark results per algorithm.
        - speed_report.pdf: Line graph comparing algorithms.
        - Console summary: Average times for each algorithm.
    """
    test_cases = [
        (10_000, "10K"),
        (100_000, "100K"),
        (250_000, "250K"),
        (1_000_000, "1M"),
    ]
    benchmark_results = {alg: {"True": [], "False": []} for alg in search_algorithms}
    average_times = {alg: {"True": 0, "False": 0} for alg in search_algorithms}
    labels = []

    with open("speed_table.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "Algorithm",
                "Reread",
                *[label for _, label in test_cases],
                "Average Time (ms)",
            ]
        )

        for n, label in test_cases:
            print(f"Running benchmarks for file with {label} lines...")
            labels.append(label)

            for alg_name, alg_func in search_algorithms.items():
                t_true = run_single_benchmark(alg_func, True, n)
                t_false = run_single_benchmark(alg_func, False, n)

                t_true_ms = t_true * 1000
                t_false_ms = t_false * 1000

                benchmark_results[alg_name]["True"].append(t_true_ms)
                benchmark_results[alg_name]["False"].append(t_false_ms)

                average_times[alg_name]["True"] = sum(
                    benchmark_results[alg_name]["True"]
                ) / len(benchmark_results[alg_name]["True"])
                average_times[alg_name]["False"] = sum(
                    benchmark_results[alg_name]["False"]
                ) / len(benchmark_results[alg_name]["False"])

                writer.writerow(
                    [
                        alg_name,
                        "True",
                        *benchmark_results[alg_name]["True"],
                        f"{average_times[alg_name]['True']:.4f}",
                    ]
                )
                writer.writerow(
                    [
                        alg_name,
                        "False",
                        *benchmark_results[alg_name]["False"],
                        f"{average_times[alg_name]['False']:.4f}",
                    ]
                )

    print("\n=== Average Execution Times (ms) ===")
    print(f"{'Algorithm':<12} | {'REREAD=True':<12} | {'REREAD=False':<12}")
    print("-" * 40)
    for alg in search_algorithms:
        true_time = f"{average_times[alg]['True']:>12.4f}"
        false_time = f"{average_times[alg]['False']:>12.4f}"
        print(f"{alg:<12} | {true_time} | {false_time}")

    plt.figure(figsize=(12, 6))
    marker_cycle = itertools.cycle(
        ["o", "s", "^", "D", "*", "x", "v", "+", "<", ">", "h"]
    )

    for i, (alg_name, results) in enumerate(benchmark_results.items()):
        marker = next(marker_cycle)
        plt.plot(
            labels,
            results["True"],
            label=f"{alg_name} (REREAD=True)",
            linestyle="--",
            marker=marker,
        )
        plt.plot(
            labels, results["False"], label=f"{alg_name} (REREAD=False)", marker=marker
        )

    plt.title("Benchmark: Query Time vs File Size for Search Algorithms")
    plt.xlabel("File Size")
    plt.ylabel("Average Query Time (ms)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig("speed_report.pdf")
    print("\n✅ Saved results to speed_table.csv and speed_report.pdf")


if __name__ == "__main__":
    run_all()
