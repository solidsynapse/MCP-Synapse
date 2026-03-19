# MCP Synapse v0.8.0 Release Notes

## Summary

`v0.8.0` expands MCP Synapse beyond the original provider set and turns the desktop runtime into a broader local-first gateway surface for both AI providers and arbitrary REST APIs.

Positioning:

`Any API. Any model. One gateway. Full audit trail.`

## Highlights

### Provider Wave 2

- Added Anthropic, Groq, Gemini, OpenRouter, DeepSeek, and xAI/Grok to the provider surface.
- Groq was runtime-tested directly during the milestone.
- Endpoint contamination fixes now prevent the local SSE bridge URL from being reused as a provider base URL.

### REST Adapter

- Added `Custom REST API` as a new connection type.
- The REST adapter supports endpoint URL, auth mode, HTTP method, and response-field mapping.
- This is the first domain-agnostic snapshot source in the product surface.

### Budget Enforcement

- Budget Guards now support `monitor`, `block`, and `throttle` modes.
- Enforcement is explicit and user-configured.
- No hidden retry, fallback, or silent override behavior was introduced.

### Auto-update

- Settings now includes `Check for Updates`.
- Update checks run through backend dispatch instead of direct frontend HTTP calls.
- Update flow remains user-controlled; there is no silent install path.

### Bedrock Early Access

- Bedrock now appears in the Connections surface with an `Early Access` badge.
- The product explicitly states that Bedrock has not been runtime-tested by the development team.

### Runtime Stability Fixes

- Fixed zombie port cleanup on shutdown.
- Fixed persisted startup state so saved connections no longer auto-start when the app opens.
- Fixed provider endpoint/base URL contamination from the local SSE bridge runtime URL.

## Notes

- SHA256 hashes will be added to `SHA256SUMS.txt` after the release build is finalized.
- Sigstore remains the planned artifact integrity direction per `D-038`.
