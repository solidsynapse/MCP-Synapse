from __future__ import annotations

import json
import os
import importlib
from typing import Any


class BedrockProviderClient:
    provider_id = "bedrock"

    def __init__(
        self,
        *,
        agent: dict[str, Any],
        model_id: str,
        credentials_path: str,
    ) -> None:
        self.model_id = str(model_id)
        self._agent = dict(agent)
        self._credentials_path = str(credentials_path)

    def generate_content(self, prompt: str, *, stream: bool = False) -> dict[str, Any]:
        if stream:
            raise NotImplementedError("bedrock streaming not implemented")

        if not bool(self._agent.get("bedrock_enable_network") or False):
            raise NotImplementedError(
                "bedrock network gate is disabled; set agent config bedrock_enable_network: true to enable real calls"
            )

        try:
            boto3 = importlib.import_module("boto3")
            importlib.import_module("botocore")
        except Exception:
            raise NotImplementedError(
                "bedrock provider requires boto3/botocore (approved in D-015) but they are not installed in this environment"
            )

        region = str(self._agent.get("aws_region") or "").strip()
        if not region:
            raise ValueError("Missing agent config: aws_region")

        req = self._build_invoke_request(model_id=self.model_id, prompt=str(prompt))

        old_env = os.environ.get("AWS_SHARED_CREDENTIALS_FILE")
        try:
            os.environ["AWS_SHARED_CREDENTIALS_FILE"] = self._credentials_path
            session = boto3.session.Session(region_name=region)
            client = session.client("bedrock-runtime", region_name=region)
            resp = client.invoke_model(
                modelId=self.model_id,
                contentType=req["content_type"],
                accept=req["accept"],
                body=req["body"],
            )
        finally:
            if old_env is None:
                os.environ.pop("AWS_SHARED_CREDENTIALS_FILE", None)
            else:
                os.environ["AWS_SHARED_CREDENTIALS_FILE"] = old_env

        text = self._extract_text(model_id=self.model_id, response=resp)
        return {
            "text": text,
            "tokens_input": None,
            "tokens_output": None,
            "cost_usd": None,
        }

    def _build_invoke_request(self, *, model_id: str, prompt: str) -> dict[str, Any]:
        model_id = str(model_id)
        if model_id.startswith("amazon.titan-text"):
            payload = {
                "inputText": str(prompt),
                "textGenerationConfig": {
                    "maxTokenCount": 512,
                    "temperature": 0,
                    "topP": 1,
                },
            }
            return {
                "content_type": "application/json",
                "accept": "application/json",
                "body": json.dumps(payload).encode("utf-8"),
            }

        if model_id.startswith("anthropic.claude-3"):
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 512,
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": str(prompt)}]}
                ],
            }
            return {
                "content_type": "application/json",
                "accept": "application/json",
                "body": json.dumps(payload).encode("utf-8"),
            }

        raise NotImplementedError(
            f"bedrock model_id not supported for real calls: {model_id}; supported: amazon.titan-text*, anthropic.claude-3*"
        )

    def _extract_text(self, *, model_id: str, response: dict[str, Any]) -> str:
        body = (response or {}).get("body")
        if not hasattr(body, "read"):
            raise ValueError("bedrock response missing readable body")
        raw = body.read()
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise ValueError(f"bedrock response is not valid JSON: {exc}")

        model_id = str(model_id)
        if model_id.startswith("amazon.titan-text"):
            results = parsed.get("results") or []
            first = results[0] if results else {}
            return str((first or {}).get("outputText") or "")

        if model_id.startswith("anthropic.claude-3"):
            content = parsed.get("content") or []
            first = content[0] if content else {}
            return str((first or {}).get("text") or "")

        raise NotImplementedError(
            f"bedrock model_id not supported for response parsing: {model_id}"
        )

