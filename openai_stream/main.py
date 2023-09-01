import os
import openai

openai.api_key = os.environ["OPENAI_API_KEY"]


def main() -> None:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=[
            {'role': 'user', 'content': 'Tell me about the Japanese history'}
        ],
        stream=True
    )

    collected_chunks = []
    collected_messages = []
    for chunk in response:
        collected_chunks.append(chunk)
        chunk_message = chunk['choices'][0]['delta']
        collected_messages.append(chunk_message)
        print(f"Message received: {chunk_message}")

    full_reply_content = ''.join([m.get('content', '') for m in collected_messages])
    print(f"Full conversation received: {full_reply_content}")


if __name__ == "__main__":
    main()
