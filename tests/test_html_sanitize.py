import pytest

from app.utils.html_sanitize import strip_html


@pytest.mark.parametrize(
    "html, expected",
    [
        ("plain text", "plain text"),
        ("<b>bold</b> text", "bold text"),
        ("hello<br>world", "hello world"),
        ("<p> spaced   \n text </p>", "spaced text"),
        ("before <img src='x.png' alt='img'> after", "before after"),
        ("<img src='x.png'>only", "only"),
    ],
)
def test_strip_html(html, expected):
    assert strip_html(html) == expected
