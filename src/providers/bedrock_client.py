from __future__ import annotations

import json
import os
import importlib
import re
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

    @staticmethod
    def _is_local_bridge_endpoint(value: str) -> bool:
        raw = str(value or "").strip()
        return bool(re.match(r"^https?://(?:127\.0\.0\.1|localhost):\d+/sse/?$", raw, re.IGNORECASE))

    def generate_content(self, prompt: str, *, stream: bool = False) -> dict[str, Any]:
        if stream:
            raise NotImplementedError("bedrock streaming not implemented")

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
        endpoint_raw = str(self._agent.get("endpoint") or "").strip()
        endpoint_override = endpoint_raw or None
        # Guard against bridge endpoint leakage into provider override.
        if endpoint_override and self._is_local_bridge_endpoint(endpoint_override):
            endpoint_override = None
        credential_source = str(self._agent.get("credential_source") or "file").strip().lower()
        if credential_source not in ("file", "manual", "api_key"):
            credential_source = "file"

        client_kwargs: dict[str, Any] = {"region_name": region}
        if endpoint_override:
            client_kwargs["endpoint_url"] = endpoint_override

        if credential_source == "manual":
            access_key_id = str(self._agent.get("aws_access_key_id") or "").strip()
            secret_access_key = str(self._agent.get("aws_secret_access_key") or "").strip()
            session_token = str(self._agent.get("aws_session_token") or "").strip()
            if not access_key_id or not secret_access_key:
                raise ValueError(
                    "bedrock manual credentials require aws_access_key_id and aws_secret_access_key"
                )
            session = boto3.session.Session(
                region_name=region,
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                aws_session_token=session_token or None,
            )
            client = session.client("bedrock-runtime", **client_kwargs)
            resp = client.invoke_model(
                modelId=self.model_id,
                contentType=req["content_type"],
                accept=req["accept"],
                body=req["body"],
            )
        elif credential_source == "api_key":
            bedrock_api_key = str(self._agent.get("bedrock_api_key") or "").strip()
            if not bedrock_api_key:
                raise ValueError("Missing bedrock_api_key for bedrock api_key credential source")
            old_bearer = os.environ.get("AWS_BEARER_TOKEN_BEDROCK")
            old_shared = os.environ.get("AWS_SHARED_CREDENTIALS_FILE")
            try:
                os.environ["AWS_BEARER_TOKEN_BEDROCK"] = bedrock_api_key
                # Avoid accidental precedence from stale shared-credentials env.
                os.environ.pop("AWS_SHARED_CREDENTIALS_FILE", None)
                session = boto3.session.Session(region_name=region)
                client = session.client("bedrock-runtime", **client_kwargs)
                resp = client.invoke_model(
                    modelId=self.model_id,
                    contentType=req["content_type"],
                    accept=req["accept"],
                    body=req["body"],
                )
            finally:
                if old_bearer is None:
                    os.environ.pop("AWS_BEARER_TOKEN_BEDROCK", None)
                else:
                    os.environ["AWS_BEARER_TOKEN_BEDROCK"] = old_bearer
                if old_shared is None:
                    os.environ.pop("AWS_SHARED_CREDENTIALS_FILE", None)
                else:
                    os.environ["AWS_SHARED_CREDENTIALS_FILE"] = old_shared
        else:
            if not self._credentials_path:
                raise ValueError("Missing credentials_path for bedrock file credential source")
            old_env = os.environ.get("AWS_SHARED_CREDENTIALS_FILE")
            try:
                os.environ["AWS_SHARED_CREDENTIALS_FILE"] = self._credentials_path
                session = boto3.session.Session(region_name=region)
                client = session.client("bedrock-runtime", **client_kwargs)
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

