from __future__ import annotations

import io
import json
from urllib.error import HTTPError

from tools import headless_dispatch_v1


class _FakeHttpResponse:
    def __init__(self, payload: object) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeHttpResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def test_m004_s04_system_check_update_returns_tag_name(monkeypatch) -> None:
    def _fake_urlopen(request, timeout=0):
        headers = {str(key).lower(): str(value) for key, value in request.header_items()}
        assert request.full_url == "https://api.github.com/repos/solidsynapse/MCP-Synapse/releases?per_page=1"
        assert timeout == 10
        assert headers["accept"] == "application/vnd.github+json"
        assert headers["x-github-api-version"] == "2022-11-28"
        return _FakeHttpResponse(
            [
                {
                    "tag_name": "v0.7.1",
                    "html_url": "https://github.com/solidsynapse/MCP-Synapse/releases/tag/v0.7.1",
                }
            ]
        )

    monkeypatch.setattr(headless_dispatch_v1.urllib_request, "urlopen", _fake_urlopen)

    result = headless_dispatch_v1._dispatch(
        agent_id="settings",
        prompt=json.dumps({"op": "system.check_update"}),
    )

    assert result["ok"] is True
    payload = json.loads(result["text"])
    assert payload == {
        "tag_name": "v0.7.1",
        "html_url": "https://github.com/solidsynapse/MCP-Synapse/releases/tag/v0.7.1",
    }


def test_m004_s04_system_check_update_requires_release_entry(monkeypatch) -> None:
    def _fake_urlopen(request, timeout=0):
        return _FakeHttpResponse([])

    monkeypatch.setattr(headless_dispatch_v1.urllib_request, "urlopen", _fake_urlopen)

    result = headless_dispatch_v1._dispatch(
        agent_id="settings",
        prompt=json.dumps({"op": "system.check_update"}),
    )

    assert result["ok"] is False
    assert result["error"] == {
        "code": "update_check_failed",
        "message": "GitHub API response did not include a release entry.",
    }


def test_m004_s04_system_check_update_surfaces_http_error(monkeypatch) -> None:
    def _fake_urlopen(request, timeout=0):
        raise HTTPError(
            url=request.full_url,
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=io.BytesIO(json.dumps({"message": "Not Found"}).encode("utf-8")),
        )

    monkeypatch.setattr(headless_dispatch_v1.urllib_request, "urlopen", _fake_urlopen)

    result = headless_dispatch_v1._dispatch(
        agent_id="settings",
        prompt=json.dumps({"op": "system.check_update"}),
    )

    assert result["ok"] is False
    assert result["error"] == {
        "code": "update_check_failed",
        "message": "GitHub API returned 404: Not Found",
    }
