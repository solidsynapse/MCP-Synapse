from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.providers.factory import ProviderFactory


@dataclass(frozen=True)
class _Context:
    agent: dict
    provider_id: str
    model_id: str
    project_id: str = ""
    location: str = ""
    credentials_path: str = ""
    price_per_1m_input: float = 0.0
    price_per_1m_output: float = 0.0
    streaming: bool = False


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Headless Ollama probe (non-streaming).")
    p.add_argument("--base-url", default="", help="Ollama base URL (default http://127.0.0.1:11434).")
    p.add_argument("--model", default="", help="Model id (e.g. llama3.2).")
    p.add_argument("--prompt", required=True, help="Prompt text.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    base_url = str(args.base_url or "").strip()
    model_id = str(args.model or "").strip()
    if not model_id:
        sys.stderr.write("Missing required --model\n")
        return 2

    agent = {}
    if base_url:
        agent["ollama_base_url"] = base_url

    context = _Context(agent=agent, provider_id="ollama", model_id=model_id, streaming=False)
    client = ProviderFactory.create(context.provider_id, context)
    try:
        result = client.generate_content(str(args.prompt), stream=False)
    except Exception as exc:
        sys.stderr.write(str(exc).strip() + "\n")
        return 1

    sys.stdout.write(str(result.get("text") or ""))
    if not str(result.get("text") or "").endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
