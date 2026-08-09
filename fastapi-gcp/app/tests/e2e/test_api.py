"""End-to-end assertions over the responses recorded by exe_api_calls/main.py.

These tests do no network I/O: run `uv run tests/e2e/exe_api_calls/main.py`
first, then `pytest tests/e2e`. Without a results file the tests skip.
"""

import pytest
from conftest import case_names


@pytest.mark.parametrize("name", case_names("echo"))
def test_echo_returns_request_text(case, name):
    echo = case(name)
    assert echo["path"] == "/echo"
    assert echo["status_code"] == 200
    assert echo["json"] == {"text": echo["body"]["text"]}
