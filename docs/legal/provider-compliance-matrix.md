# Provider Compliance Matrix

This matrix summarizes the current provider surface for MCP Synapse in the `v0.6.x` Early Access lane and the current `M003` planning context.

| Provider | Status | Region | Credential type | Cost data | Notes |
| --- | --- | --- | --- | --- | --- |
| Vertex AI | Active | User-selected Vertex location | Service account JSON path | `ESTIMATED` or `UNKNOWN` | Current runtime path is active. Cost normalization uses the local cost layer; missing pricing stays explicit instead of silently becoming zero. |
| OpenAI | Active | Provider-managed region | API key file | `ESTIMATED` or `UNKNOWN` | Active on the first-release surface. Cost data is normalized locally and may remain `UNKNOWN` if pricing data cannot be resolved. |
| Azure OpenAI | Active | Azure resource region | API key file plus endpoint and deployment name | `ESTIMATED` or `UNKNOWN` | Active on the first-release surface. Uses deployment-based configuration rather than raw model-name-only setup. |
| HuggingFace | Active | Provider-managed region | Access token file | `UNKNOWN` | Active on the first-release surface, but cost data is not currently normalized into a known price in the current runtime path. |
| Ollama | Active | Local machine | Local runtime endpoint; no cloud credential required | `UNKNOWN` | Active on the first-release surface for local runtime use. Cost data is not currently priced by the runtime path. |
| Bedrock | Blocked / Deferred | User-supplied AWS region | Credentials path, manual AWS key pair, or Bedrock bearer token | `UNKNOWN` / not runtime-proven | Blocked because the current client support and the available AWS quota do not line up. Current blocker: model-support mismatch plus quota gap. |

## Cost-source meaning

The current product surface uses explicit pricing state:

- `ACTUAL` means the provider supplied real cost data to the runtime
- `ESTIMATED` means the product calculated a best-effort local estimate
- `UNKNOWN` means pricing could not be resolved and is not silently treated as zero

## Compliance boundary

Provider support in this matrix does not replace provider-side compliance review. You remain responsible for provider terms, regional rules, account governance, and credential handling under your own environment.
