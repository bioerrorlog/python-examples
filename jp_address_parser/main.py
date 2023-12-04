import os
import time
import openai

openai.api_key = os.environ["OPENAI_API_KEY"]


def main() -> None:
    start_time = time.time()

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=[
            {'role': 'user', 'content': 'Tell me about the Japanese history.'}
        ],
        stream=True,
        request_timeout=3,
    )

    collected_chunks = []
    collected_messages = []
    for chunk in response:
        chunk_time = time.time() - start_time

        collected_chunks.append(chunk)
        chunk_message = chunk['choices'][0]['delta'].get('content', '')
        collected_messages.append(chunk_message)
        print(f"Message received {chunk_time:.2f} seconds after request: {chunk_message}")

    full_reply_content = ''.join(collected_messages)
    print(f"Full conversation received: {full_reply_content}")


if __name__ == "__main__":
    main()
