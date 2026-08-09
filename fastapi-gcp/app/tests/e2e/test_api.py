"""End-to-end assertions over the responses recorded by exe_api_calls/main.py.

These tests do no network I/O: run `uv run tests/e2e/exe_api_calls/main.py`
first, then `pytest tests/e2e`. Without a collected run the tests skip.
"""

import pytest
from conftest import case_names


@pytest.mark.parametrize("name", case_names("echo"))
def test_echo_returns_request_text(case, name):
    echo = case("echo", name)
    assert echo["meta"]["status_code"] == 200
    assert echo["response"] == {"text": echo["request"]["text"]}


@pytest.mark.parametrize("name", case_names("slow-hello"))
def test_slow_hello_greets_request_text(case, name):
    slow_hello = case("slow-hello", name)
    assert slow_hello["meta"]["status_code"] == 200
    assert slow_hello["response"] == {"message": f"Hello, {slow_hello['request']['text']}"}
