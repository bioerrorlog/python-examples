import os
from openai import OpenAI
import base64
import mimetypes


def image_to_base64(image_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(image_path)

    if not mime_type or not mime_type.startswith('image'):
        raise ValueError("The file type is not recognized as an image")

    with open(image_path, 'rb') as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    return f"data:{mime_type};base64,{encoded_string}"


def main() -> None:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    base64_string = image_to_base64("data/test.jpg")

    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe the attached image"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": base64_string,
                            "detail": "low"
                        }
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
