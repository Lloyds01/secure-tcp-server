"""Benchmarking tests for various search algorithms."""
import configparser
import os
import timeit

import pytest

from benchmarks import (cache, cached_search, endswith_search, linear_search,
                        list_index_search, prepare_test_file, regex_search,
                        reverse_search, split_search, startswith_search,
                        update_config)

TEST_FILENAME = "test_file.txt"
CONFIG_FILENAME = "config.ini"


@pytest.fixture(autouse=True)
def cleanup():
    """Run before and after each test to clean up test files and cache."""
    if os.path.exists(TEST_FILENAME):
        os.remove(TEST_FILENAME)
    if os.path.exists(CONFIG_FILENAME):
        os.remove(CONFIG_FILENAME)
    cache.clear()


def test_prepare_test_file_creates_correct_lines():
    """Test that prepare_test_file creates the correct number of lines."""
    prepare_test_file(10)
    with open(TEST_FILENAME) as f:
        lines = f.readlines()
    assert len(lines) == 10
    assert lines[0].startswith("line_0")
    assert lines[-1].startswith("line_9")


def test_update_config_writes_file():
    """Test that update_config writes the config file correctly."""
    update_config(True)
    config = configparser.ConfigParser()
    config.read(CONFIG_FILENAME)
    assert config["DEFAULT"]["reread_on_query"] == "True"
    update_config(False)
    config.read(CONFIG_FILENAME)
    assert config["DEFAULT"]["reread_on_query"] == "False"


@pytest.mark.parametrize(
    "search_func",
    [
        linear_search,
        regex_search,
        reverse_search,
        split_search,
        cached_search,
        startswith_search,
        list_index_search,
        endswith_search,
    ],
)
def test_search_functions_return_true_and_false(search_func):
    """Test that search functions return True and False for known queries."""
    prepare_test_file(10000)  # Create the test file

    if search_func.__name__ == "split_search":
        query = "line"
    else:
        query = "line_5000"

    # Test a query that should exist
    assert search_func(query) is True

    # Test a query that should not exist
    assert search_func("not_in_file") is False


def test_cached_search_caches_results():
    """Test that cached_search caches results correctly."""
    prepare_test_file(10)
    cache.clear()
    assert "line_5" not in cache
    assert cached_search("line_5") is True
    assert "line_5" in cache
    assert cached_search("line_5") is True
    assert cached_search("not_exist") is False
    assert cache["not_exist"] is False


# Defines performance thresholds (in milliseconds)
PERFORMANCE_THRESHOLDS = {
    "linear_search": {
        10_000: 5.0,
        100_000: 50.0,
        250_000: 120.0,
        1_000_000: 500.0,
    },
    "regex_search": {
        10_000: 10.0,
        100_000: 100.0,
        250_000: 250.0,
        1_000_000: 1000.0,
    },
    "reverse_search": {
        10_000: 6.0,
        100_000: 60.0,
        250_000: 150.0,
        1_000_000: 600.0,
    },
    "split_search": {
        10_000: 15.0,
        100_000: 150.0,
        250_000: 400.0,
        1_000_000: 1500.0,
    },
    "cached_search": {
        10_000: 1.0,
        100_000: 1.0,
        250_000: 1.0,
        1_000_000: 1.0,
    },
    "startswith_search": {
        10_000: 5.0,
        100_000: 50.0,
        250_000: 120.0,
        1_000_000: 500.0,
    },
    "list_index_search": {
        10_000: 7.0,
        100_000: 70.0,
        250_000: 180.0,
        1_000_000: 750.0,
    },
    "endswith_search": {
        10_000: 5.0,
        100_000: 50.0,
        250_000: 120.0,
        1_000_000: 500.0,
    },
}

TIMEIT_NUMBER = 100

# Prepare parameter sets and corresponding IDs for pytest
_performance_test_cases = []
_performance_test_ids = []

for func_name in PERFORMANCE_THRESHOLDS:
    for n_lines in PERFORMANCE_THRESHOLDS[func_name]:
        _performance_test_cases.append((func_name, n_lines))
        _performance_test_ids.append(f"{func_name}_N{n_lines}")


@pytest.mark.parametrize(
    "search_func_key, n_lines",
    _performance_test_cases,
    ids=_performance_test_ids,
)
def test_search_function_performance(search_func_key, n_lines):
    """Test that search functions meet specified performance benchmarks.

    This test focuses on the 'reread_on_query=False' scenario,
    simulating a real-world query after initial setup/read.
    """
    search_func = globals()[search_func_key]
    max_time_ms = PERFORMANCE_THRESHOLDS[search_func_key][n_lines]

    update_config(False)
    prepare_test_file(n_lines)

    if search_func_key == "split_search":
        query_to_find = "line"
    else:
        query_to_find = f"line_{n_lines // 2}"

    if search_func_key == "cached_search":
        cache.clear()
        prime_query = "line_0"
        search_func(prime_query)

    execution_time_seconds = (
        timeit.timeit(lambda: search_func(query_to_find), number=TIMEIT_NUMBER)
        / TIMEIT_NUMBER
    )
    execution_time_ms = execution_time_seconds * 1000

    print(
        f"\n{search_func_key} (N={n_lines}): "
        f"Actual time = {execution_time_ms:.4f} ms, "
        f"Max allowed = {max_time_ms:.4f} ms"
    )

    assert execution_time_ms <= max_time_ms, (
        f"{search_func_key} for {n_lines} lines exceeded performance target: "
        f"{execution_time_ms:.4f} ms > {max_time_ms:.4f} ms"
    )
