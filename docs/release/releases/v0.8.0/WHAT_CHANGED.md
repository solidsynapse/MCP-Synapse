# MCP Synapse v0.8.0 What Changed

## Added

- Anthropic provider client
- Groq provider client
- Gemini provider client
- OpenRouter provider client
- DeepSeek provider client
- xAI/Grok provider client
- REST adapter provider (`rest_api`)
- Budget Guard enforcement modes: `block`, `throttle`
- Settings update-check surface
- Bedrock `Early Access` badge in Connections

## Improved

- Provider endpoint normalization now keeps runtime SSE URLs separate from provider base URLs.
- Groq now uses the correct provider default base URL and OpenAI-compatible request path.
- Shutdown cleanup now force-stops worker runtimes so ports do not remain open after app exit.
- App startup now resets persisted connection runtime state to `stopped`.

## UI Surface Updates

- Connections now exposes the full M004 wave-2 provider set.
- Budget health alerts now reflect enforcement mode.
- Settings update checks use backend dispatch.

## Cost and Audit Behavior

- Existing local audit trail behavior remains in place.
- REST adapter usage rows record request status and latency while cost remains `UNKNOWN`.

## Release Position

`v0.8.0` is the provider-depth and domain-signal release that bridges AI-provider orchestration and generic REST-source integration.
