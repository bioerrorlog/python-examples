import os
from openai import OpenAI
import pytest
from main import parse_address


@pytest.fixture
def openai_client():
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


@pytest.mark.parametrize("address, expected", [
    ('港区赤坂一丁目2の3', {
        "original_data": "港区赤坂一丁目2の3",
        "都道府県": "東京都",
        "郡名": "",
        "市区町村": "港区",
        "町域": "赤坂",
        "丁目": "1",
        "番地": "2",
        "号": "3",
        "建物名・部屋番号": ""
    }),
    ('港区赤坂1-2-3', {
        "original_data": "港区赤坂1-2-3",
        "都道府県": "東京都",
        "郡名": "",
        "市区町村": "港区",
        "町域": "赤坂",
        "丁目": "1",
        "番地": "2",
        "号": "3",
        "建物名・部屋番号": ""
    }),
    ('浦安市舞浜2-1-1', {
        "original_data": "浦安市舞浜2-1-1",
        "都道府県": "千葉県",
        "郡名": "",
        "市区町村": "浦安市",
        "町域": "舞浜",
        "丁目": "2",
        "番地": "1",
        "号": "1",
        "建物名・部屋番号": ""
    }),
])
def test_parse_address(address, expected, openai_client):
    result = parse_address(address, openai_client)
    assert result == expected
