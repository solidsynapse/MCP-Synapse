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
    credentials_path: str
    project_id: str = ""
    location: str = ""
    price_per_1m_input: float = 0.0
    price_per_1m_output: float = 0.0
    streaming: bool = False


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Headless OpenAI probe (non-streaming).")
    p.add_argument("--base-url", default="", help="OpenAI base URL (default https://api.openai.com/v1).")
    p.add_argument("--model", required=True, help="Model id (e.g. gpt-4o-mini).")
    p.add_argument("--prompt", required=True, help="Prompt text.")
    p.add_argument("--credentials-path", required=True, help="Path to a file containing the OpenAI API key.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    base_url = str(args.base_url or "").strip()
    model_id = str(args.model or "").strip()
    prompt = str(args.prompt or "")
    cred_path = str(args.credentials_path or "").strip()
    if not cred_path:
        sys.stderr.write("Missing required --credentials-path\n")
        return 2

    agent = {}
    if base_url:
        agent["openai_base_url"] = base_url

    context = _Context(
        agent=agent,
        provider_id="openai",
        model_id=model_id,
        credentials_path=cred_path,
        streaming=False,
    )
    try:
        client = ProviderFactory.create(context.provider_id, context)
        result = client.generate_content(prompt, stream=False)
    except Exception as exc:
        sys.stderr.write(str(exc).strip() + "\n")
        return 1

    sys.stdout.write(str(result.get("text") or ""))
    if not str(result.get("text") or "").endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
