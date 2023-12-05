import os
import pytest
from openai import OpenAI

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
])
def test_parse_address_in_easy_cases(address, expected, openai_client):
    result = parse_address(address, openai_client)
    assert result == expected


@pytest.mark.parametrize("address, expected", [
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
    ('浦安市舞浜2-11', {
        "original_data": "浦安市舞浜2-11",
        "都道府県": "千葉県",
        "郡名": "",
        "市区町村": "浦安市",
        "町域": "舞浜",
        "丁目": "",
        "番地": "2",
        "号": "11",
        "建物名・部屋番号": ""
    }),
    ('浦静岡県下田市2-4-26', {
        "original_data": "浦静岡県下田市2-4-26",
        "都道府県": "静岡県",
        "郡名": "",
        "市区町村": "下田市",
        "町域": "",
        "丁目": "2",
        "番地": "4",
        "号": "26",
        "建物名・部屋番号": ""
    }),
    ('春日部市大字八丁目３５３番地１', {
        "original_data": "春日部市大字八丁目３５３番地１",
        "都道府県": "埼玉県",
        "郡名": "",
        "市区町村": "春日部市",
        "町域": "大字八丁目",
        "丁目": "",
        "番地": "353",
        "号": "1",
        "建物名・部屋番号": ""
    }),
    ('奈良県御所市1番地の3', {
        "original_data": "奈良県御所市1番地の3",
        "都道府県": "奈良県",
        "郡名": "",
        "市区町村": "御所市",
        "町域": "",
        "丁目": "",
        "番地": "1",
        "号": "3",
        "建物名・部屋番号": ""
    }),
])
def test_parse_address_in_difficult_cases(address, expected, openai_client):
    result = parse_address(address, openai_client)
    assert result == expected
