import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


def _load_probe_module():
    root = Path(__file__).resolve().parents[1]
    path = root / "tools" / "lmstudio_probe.py"
    spec = importlib.util.spec_from_file_location("lmstudio_probe", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


class _FakeResp:
    def __init__(self, payload_bytes: bytes) -> None:
        self._b = payload_bytes

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._b


def test_lmstudio_probe_offline_model_discovery_and_output_deterministic(capsys):
    mod = _load_probe_module()
    base_url = "http://127.0.0.1:1234/v1"

    def _fake_urlopen(req, timeout=0):
        url = getattr(req, "full_url", "")
        method = req.get_method()
        if url.endswith("/models") and method == "GET":
            return _FakeResp(b'{"data":[{"id":"model-a"}]}')
        if url.endswith("/chat/completions") and method == "POST":
            return _FakeResp(b'{"choices":[{"message":{"content":"ok"}}]}')
        raise AssertionError(f"Unexpected request: {method} {url}")

    with patch("urllib.request.urlopen", side_effect=_fake_urlopen):
        rc1 = mod.main(["--base-url", base_url, "--prompt", "hi"])
        out1 = capsys.readouterr().out
        rc2 = mod.main(["--base-url", base_url, "--prompt", "hi"])
        out2 = capsys.readouterr().out

    assert rc1 == 0
    assert rc2 == 0
    assert out1 == out2
    assert "EXIT_CODE=0" in out1
    assert f"BASE_URL={base_url}" in out1
    assert "MODEL=model-a" in out1
    assert "\n---\n" in out1
    assert out1.rstrip().endswith("ok")
