import base64
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_IMAGE_MODEL = os.getenv("OPENROUTER_IMAGE_MODEL", "")
IMAGES_URL = "https://openrouter.ai/api/v1/images"


def generate_image_file(sentence_de: str) -> str:
    """Сгенерировать иллюстрацию и сохранить как PNG."""
    if not OPENROUTER_IMAGE_MODEL:
        return ""
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    payload = {"model": OPENROUTER_IMAGE_MODEL, "prompt": sentence_de}
    for attempt in range(3):
        try:
            resp = requests.post(IMAGES_URL, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()["data"][0]["b64_json"]
            img_bytes = base64.b64decode(data)
            os.makedirs("media", exist_ok=True)
            filename = os.path.join("media", f"img_{abs(hash(sentence_de))}.png")
            with open(filename, "wb") as f:
                f.write(img_bytes)
            return filename
        except Exception:
            if attempt == 2:
                return ""
            time.sleep(2**attempt)
    return ""
