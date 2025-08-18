import time
import requests
import responses
import pytest

from app.net.genapi_client import (
    GenAPIClient,
    GenAPIUnauthorized,
    GenAPIPaymentRequired,
    GenAPINotFound,
    GenAPIServiceUnavailable,
)


def make_client():
    return GenAPIClient(token="TOKEN", timeout=1, retries=3)


@responses.activate
def test_get_task_status_processing_to_success(monkeypatch):
    client = make_client()
    request_id = "abc"
    url = f"{client.BASE_URL}/api/v1/requests/{request_id}"

    responses.add(responses.GET, url, json={"status": "processing"}, status=200)
    responses.add(responses.GET, url, json={"status": "success", "result": {"img": "data"}}, status=200)

    monkeypatch.setattr(time, "sleep", lambda _: None)

    result = client.get_task_status(request_id)
    assert result["status"] == "success"
    assert len(responses.calls) == 2


@responses.activate
def test_create_generation_task_401():
    client = make_client()
    url = f"{client.BASE_URL}/api/v1/networks/model"
    responses.add(responses.POST, url, json={"detail": "unauthorized"}, status=401)
    with pytest.raises(GenAPIUnauthorized):
        client.create_generation_task("model", "prompt", False)


@responses.activate
def test_create_generation_task_402():
    client = make_client()
    url = f"{client.BASE_URL}/api/v1/networks/model"
    responses.add(responses.POST, url, json={"detail": "payment"}, status=402)
    with pytest.raises(GenAPIPaymentRequired):
        client.create_generation_task("model", "prompt", False)


@responses.activate
def test_get_task_status_404():
    client = make_client()
    request_id = "missing"
    url = f"{client.BASE_URL}/api/v1/requests/{request_id}"
    responses.add(responses.GET, url, json={"detail": "not found"}, status=404)
    with pytest.raises(GenAPINotFound):
        client.get_task_status(request_id)


@responses.activate
def test_get_task_status_503():
    client = make_client()
    request_id = "svc"
    url = f"{client.BASE_URL}/api/v1/requests/{request_id}"
    responses.add(responses.GET, url, json={"detail": "busy"}, status=503)
    with pytest.raises(GenAPIServiceUnavailable):
        client.get_task_status(request_id)


@responses.activate
def test_get_task_status_timeouts(monkeypatch):
    client = make_client()
    request_id = "slow"
    url = f"{client.BASE_URL}/api/v1/requests/{request_id}"

    responses.add(responses.GET, url, body=requests.exceptions.Timeout())
    responses.add(responses.GET, url, body=requests.exceptions.Timeout())
    responses.add(responses.GET, url, json={"status": "success"}, status=200)

    monkeypatch.setattr(time, "sleep", lambda _: None)

    result = client.get_task_status(request_id)
    assert result["status"] == "success"
    assert len(responses.calls) == 3
