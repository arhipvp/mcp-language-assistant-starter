import time

import pytest
import requests

from app.net.http import NetworkError, request_json


class DummyResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code
        self.text = str(data)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

    def json(self):
        return self._data


def test_request_json_success(monkeypatch):
    def fake_request(method, url, json=None, headers=None, timeout=None):
        return DummyResponse({"ok": True})

    monkeypatch.setattr(requests, "request", fake_request)
    assert request_json("GET", "http://example.com") == {"ok": True}


def test_request_json_retry(monkeypatch):
    calls = {"count": 0}

    def fake_request(method, url, json=None, headers=None, timeout=None):
        if calls["count"] == 0:
            calls["count"] += 1
            raise requests.RequestException("boom")
        return DummyResponse({"ok": True})

    monkeypatch.setattr(requests, "request", fake_request)
    monkeypatch.setattr(time, "sleep", lambda s: None)

    assert request_json("GET", "http://example.com") == {"ok": True}


def test_request_json_fail(monkeypatch):
    def fake_request(method, url, json=None, headers=None, timeout=None):
        raise requests.RequestException("boom")

    monkeypatch.setattr(requests, "request", fake_request)
    monkeypatch.setattr(time, "sleep", lambda s: None)

    with pytest.raises(NetworkError) as exc:
        request_json("GET", "http://example.com", retries=3)

    assert exc.value.code == "network"
