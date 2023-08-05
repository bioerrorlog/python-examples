import os
import openai

openai.api_key = os.environ["OPENAI_API_KEY"]


def main() -> None:
    messages = [
        {"role": "user", "content": "Please explain about TDD (Test Driven Development)"},
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        # request_timeout=20,
    )
    content = response.choices[0].message.content
    print(content)


if __name__ == "__main__":
    main()
