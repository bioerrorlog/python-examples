import os
from openai import OpenAI


def parse_address(address: str, client: OpenAI) -> dict:
    system_prompt = """日本の住所を以下の項目に沿ってJSON形式で正確にパースし、JSONのみを出力すること:

# 項目
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
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        response_format={"type": "json_object"},
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': address},
        ],
    )

    return response.choices[0].message.content


def main() -> None:
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    address = '港区赤坂一丁目2の3'

    result = parse_address(address, client)
    print(result)


if __name__ == "__main__":
    main()
