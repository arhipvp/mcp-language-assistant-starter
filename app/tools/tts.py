
"""TTS interface (stub). Plug in your preferred engine (Edge-TTS, Coqui, Piper)."""
from typing import Optional

def speak_to_file(text: str, out_path: str, voice: Optional[str] = None) -> str:
    # TODO: implement using your TTS backend
    with open(out_path, "wb") as f:
        f.write(b"TODO: generate audio here")
    return out_path
