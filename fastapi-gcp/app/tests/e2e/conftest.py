"""Loads the result files recorded by exe_api_calls/main.py.

The e2e tests never call the service themselves; they only verify the files that
the collection script wrote, always taking the most recent run under
exe_api_calls/results/.
"""

import json
from pathlib import Path
from typing import Callable

import pytest


EXE_DIR = Path(__file__).parent / "exe_api_calls"
DATA_DIR = EXE_DIR / "data"
RESULTS_DIR = EXE_DIR / "results"


def case_names(endpoint: str) -> list[str]:
    """Return an endpoint's case names, taken from its test data files.

    Parametrising over the data directory rather than the results keeps the test
    list stable whether or not a run has been collected yet.
    """
    return sorted(path.stem for path in (DATA_DIR / endpoint).glob("*.json"))


@pytest.fixture(scope="session")
def run_dir() -> Path:
    """Return the newest run directory, or skip when nothing has been collected.

    Run directories are named after their JST start time, so the newest one is
    also the last in sorted order.
    """
    runs = sorted(path for path in RESULTS_DIR.glob("*") if path.is_dir())
    if not runs:
        pytest.skip(
            f"no runs found under {RESULTS_DIR}; "
            "run `uv run tests/e2e/exe_api_calls/main.py` first"
        )
    return runs[-1]


@pytest.fixture(scope="session")
def case(run_dir: Path) -> Callable[[str, str], dict]:
    """Return a lookup for one recorded case by endpoint and case name.

    The three files the case was recorded as are returned under the keys
    "request", "response" and "meta".
    """

    def _case(endpoint: str, name: str) -> dict:
        case_dir = run_dir / endpoint / name
        recorded = {}
        for part in ("request", "response", "meta"):
            path = case_dir / f"{part}.json"
            if not path.exists():
                pytest.fail(
                    f"{path} not found; "
                    "collect the results again to include this case"
                )
            recorded[part] = json.loads(path.read_text())
        return recorded

    return _case
