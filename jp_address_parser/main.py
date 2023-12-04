import os
from openai import OpenAI


def parse_address(address: str, client: OpenAI) -> dict:

    response = client.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {'role': 'user', 'content': 'Tell me about the Japanese history.'}
        ],
    )

    return response


def main() -> None:
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    address = '港区赤坂一丁目2の3'

    result = parse_address(address, client)
    print(result)


if __name__ == "__main__":
    main()
