"""Loads the results recorded by exe_api_calls/main.py.

The e2e tests never call the service themselves; they only verify the file that
the collection script wrote.
"""

import json
from pathlib import Path
from typing import Callable

import pytest


RESULTS_PATH = Path(__file__).with_name("results.json")
DATA_DIR = Path(__file__).parent / "exe_api_calls" / "data"


def case_names(endpoint: str) -> list[str]:
    """Return the recorded case names for an endpoint, taken from its data files.

    Parametrising over the data directory rather than the results file keeps the
    test list stable whether or not results have been collected yet.
    """
    return sorted(f"{endpoint}/{path.stem}" for path in (DATA_DIR / endpoint).glob("*.json"))


@pytest.fixture(scope="session")
def results() -> dict:
    """Return the whole recorded run, or skip when nothing has been collected."""
    if not RESULTS_PATH.exists():
        pytest.skip(
            f"{RESULTS_PATH} not found; "
            "run `uv run tests/e2e/exe_api_calls/main.py` first"
        )
    return json.loads(RESULTS_PATH.read_text())


@pytest.fixture(scope="session")
def case(results: dict) -> Callable[[str], dict]:
    """Return a lookup for a single recorded request/response by case name."""

    def _case(name: str) -> dict:
        if name not in results["cases"]:
            pytest.fail(
                f"case {name!r} missing from {RESULTS_PATH}; "
                "collect the results again to include it"
            )
        return results["cases"][name]

    return _case
