from dotenv import load_dotenv
import os
import sys
import base64

import openai

load_dotenv()

API_URL = "https://openrouter.ai/api/v1"
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

if not API_KEY:
    print("WARN: NVIDIA_API_KEY is not set")

SYSTEM_PROMPT = """
You are analyzing a short-form social video frame.
In ONE pass, determine whether the frame contains any embedded or referenced media
(e.g., music players, video players, app cards, screenshots).

If yes, extract:
- media type (music, video, article, app)
- platform (spotify, youtube, apple_music, etc.)
- title
- creator/artist/channel
- confidence (0–1)

If no, return JSON object with has_embedded_media=false.

Respond ONLY as valid JSON matching this schema:
{
  "has_embedded_media": boolean,
  "media": {
    "type": string | null,
    "platform": string | null,
    "title": string | null,
    "creator": string | null,
    "confidence": number | null
  },
  "intent": string | null
}
"""


def load_image_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def chat_with_image(
    client: openai.OpenAI, image_base64: str, model_name: str = "moonshotai/kimi-k2.5"
):
    messages = [
        {
            "role": "system",
            "content": [
                {"type": "text", "text": SYSTEM_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64, {image_base64}"},
                },
            ],
        }
    ]

    response = client.chat.completions.create(
        model=model_name, messages=messages, stream=False, max_tokens=8192
    )
    print(f"{response.choices[0].message.content}")

    # Also support instant mode if pass {"thinking" = {"type":"disabled"}}
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        stream=False,
        max_tokens=4096,
        extra_body={"thinking": {"type": "disabled"}},  # this is for official API
        # extra_body= {'chat_template_kwargs': {"thinking": False}}  # this is for vLLM/SGLang
    )
    print("===== Below is response in Instant Mode ======")
    print(f"response: {response.choices[0].message.content}")

    return response.choices[0].message.content


def main():
    if len(sys.argv) < 2:
        print("path to image missing")
        exit(1)
    path = sys.argv[1]

    client = openai.OpenAI(base_url=API_URL, api_key=API_KEY)

    image_base64 = load_image_base64(path)

    chat_with_image(client, image_base64)


if __name__ == "__main__":
    main()
