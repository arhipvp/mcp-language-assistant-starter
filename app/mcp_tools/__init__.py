from typing import Any
from .text import generate_sentence
from .llm_text import chat

llm_text: Any | None = None
__all__ = ["generate_sentence"]
__all__ = ["chat"]
