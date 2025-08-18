"""HTML sanitation utilities."""
from __future__ import annotations

from html.parser import HTMLParser
import html
import re


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag.lower() == "br":
            self._parts.append(" ")

    def handle_startendtag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag.lower() == "br":
            self._parts.append(" ")

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        self._parts.append(data)

    def handle_entityref(self, name: str) -> None:  # type: ignore[override]
        self._parts.append(html.unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:  # type: ignore[override]
        self._parts.append(html.unescape(f"&#{name};"))

    def get_data(self) -> str:
        return "".join(self._parts)


def strip_html(text: str) -> str:
    """Return ``text`` without HTML tags.

    All tags are removed, consecutive whitespace is collapsed into a single
    space, and ``<br>`` tags are treated as spaces.
    """

    parser = _HTMLStripper()
    parser.feed(text)
    parser.close()
    result = parser.get_data()
    result = html.unescape(result)
    result = re.sub(r"\s+", " ", result)
    return result.strip()


__all__ = ["strip_html"]
