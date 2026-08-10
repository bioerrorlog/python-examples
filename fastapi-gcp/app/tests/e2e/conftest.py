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
RESULTS_DIR = EXE_DIR / "results"

# The newest run, resolved at import time because the test list is built from it
# during collection, before any fixture runs. Result directories are named after
# their UTC start time, so the newest one is also the last in sorted order.
_result_dirs = sorted(path for path in RESULTS_DIR.glob("*") if path.is_dir())
LATEST_RESULT_DIR = _result_dirs[-1] if _result_dirs else None


def case_names(endpoint: str) -> list[str]:
    """Return an endpoint's case names as recorded by the newest run.

    The tests describe what the last collection actually produced, so a case
    that was not recorded is not silently reported as passing, and a case added
    to data/ only appears once it has been collected.
    """
    if LATEST_RESULT_DIR is None:
        return []
    return sorted(
        path.name for path in (LATEST_RESULT_DIR / endpoint).glob("*") if path.is_dir()
    )


@pytest.fixture(scope="session")
def latest_result_dir() -> Path:
    """Return the newest run's directory, or skip when nothing has been collected."""
    if LATEST_RESULT_DIR is None:
        pytest.skip(
            f"no runs found under {RESULTS_DIR}; "
            "run `uv run tests/e2e/exe_api_calls/main.py` first"
        )
    return LATEST_RESULT_DIR


@pytest.fixture(scope="session")
def case(latest_result_dir: Path) -> Callable[[str, str], dict]:
    """Return a lookup for one recorded case by endpoint and case name.

    The three files the case was recorded as are returned under the keys
    "request", "response" and "meta".
    """

    def _case(endpoint: str, name: str) -> dict:
        case_dir = latest_result_dir / endpoint / name
        recorded = {}
        for part in ("request", "response", "meta"):
            path = case_dir / f"{part}.json"
            if not path.exists():
                pytest.fail(
                    f"{path} not found; "
                    "this case was only partly recorded, so collect it again"
                )
            recorded[part] = json.loads(path.read_text())
        return recorded

    return _case
