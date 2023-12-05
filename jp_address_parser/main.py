import os
import json
from openai import OpenAI


def parse_address(address: str, client: OpenAI) -> dict:
    system_prompt = """日本の住所を以下の項目に沿ってJSON形式で正確にパースし、JSONのみを出力すること:

# 項目
- original_data
- 都道府県
- 郡名
- 市区町村
- 町域
- 丁目
- 番地
- 号
- 建物名・部屋番号

# 規則
- 都道府県が省略されている場合は適切に補うこと
- ハイフンを残さないこと
- 固有名詞に含まれない漢数字は半角数字に置換すること
- ない場合は空欄にすること
- `original_data`には、パース前の元住所を入れること
"""

    shot1_user = '港区赤坂1-2-3'
    shot1_assistant = str({"original_data": "港区赤坂1-2-3", "都道府県": "東京都", "郡名": "", "市区町村": "港区", "町域": "赤坂", "丁目": "1", "番地": "2", "号": "3", "建物名・部屋番号": ""})

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        response_format={"type": "json_object"},
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': shot1_user},
            {'role': 'assistant', 'content': shot1_assistant},
            {'role': 'user', 'content': address},
        ],
    )

    content = response.choices[0].message.content
    return json.loads(content)


def main() -> None:
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    address = '港区赤坂一丁目2の3'

    result = parse_address(address, client)
    print(result)


if __name__ == "__main__":
    main()
