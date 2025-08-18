import logging
import re

import pytest

from app.tool_logging import log_tool


class FakeServer:
    def __init__(self):
        self.tools: dict[str, callable] = {}

    def tool(self, name: str):
        def decorator(func):
            self.tools[name] = func
            return func
        return decorator


def test_log_tool_success(caplog):
    server = FakeServer()

    @log_tool(server, "sample")
    def sample(x, token):
        return x * 2

    assert "sample" in server.tools

    with caplog.at_level(logging.DEBUG, logger="mcp.tools"):
        result = sample(3, token="secret")

    assert result == 6
    messages = [r.message for r in caplog.records]
    assert any("sample ok" in m for m in messages)
    assert any(re.search(r"sample args=.*\*\*\*", m) for m in messages)
    assert not any("secret" in m for m in messages)


def test_log_tool_error(caplog):
    server = FakeServer()

    @log_tool(server, "boom")
    def boom(token):
        raise ValueError("boom")

    assert "boom" in server.tools

    with pytest.raises(ValueError):
        with caplog.at_level(logging.DEBUG, logger="mcp.tools"):
            boom(token="topsecret")

    messages = [r.message for r in caplog.records]
    assert any("boom err" in m for m in messages)
    assert any("ValueError" in m or "boom" in m for m in messages)
    assert not any("topsecret" in m for m in messages)
