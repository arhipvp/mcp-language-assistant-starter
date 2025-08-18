import json
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
def test_create_generation_task_json_no_image():
    client = make_client()
    url = f"{client.BASE_URL}/api/v1/networks/model"
    responses.add(responses.POST, url, json={"ok": True}, status=200)
    client.create_generation_task("model", "prompt", False)
    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert call.request.headers["Content-Type"] == "application/json"
    body = json.loads(call.request.body)
    assert body["prompt"] == "prompt"
    assert "image_url" not in body and "image_b64" not in body


@responses.activate
def test_create_generation_task_image_url():
    client = make_client()
    url = f"{client.BASE_URL}/api/v1/networks/model"
    responses.add(responses.POST, url, json={"ok": True}, status=200)
    img_url = "http://img"
    client.create_generation_task("model", "prompt", False, ref_image_url=img_url)
    call = responses.calls[0]
    body = json.loads(call.request.body)
    assert body["image_url"] == img_url
    assert call.request.headers["Content-Type"] == "application/json"


@responses.activate
def test_create_generation_task_image_b64():
    client = make_client()
    url = f"{client.BASE_URL}/api/v1/networks/model"
    responses.add(responses.POST, url, json={"ok": True}, status=200)
    b64 = "YWJj"  # 'abc'
    client.create_generation_task("model", "prompt", False, ref_image_b64=b64)
    call = responses.calls[0]
    body = json.loads(call.request.body)
    assert body["image_b64"] == b64
    assert call.request.headers["Content-Type"] == "application/json"


@responses.activate
def test_create_generation_task_image_file(tmp_path):
    client = make_client()
    url = f"{client.BASE_URL}/api/v1/networks/model"
    responses.add(responses.POST, url, json={"ok": True}, status=200)
    img_path = tmp_path / "img.png"
    img_path.write_bytes(b"123")
    client.create_generation_task("model", "prompt", False, ref_image_path=str(img_path))
    call = responses.calls[0]
    assert call.request.headers["Content-Type"].startswith("multipart/form-data")
    body = call.request.body
    assert b'name="image"' in body
    assert b'filename="img.png"' in body


@responses.activate
def test_create_generation_task_image_conflict():
    client = make_client()
    with pytest.raises(ValueError):
        client.create_generation_task(
            "model", "prompt", False, ref_image_url="http://img", ref_image_b64="abc"
        )
    assert len(responses.calls) == 0


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
