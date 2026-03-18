# M004 Roadmap

Milestone: `v0.9.x`
Status: COMPLETE

## S01 - Provider Wave 2

- Status: COMPLETE

- Risk: HIGH
- Depends: none
- Scope:
  - Anthropic
  - Groq
  - Gemini
  - OpenRouter
  - DeepSeek
  - xAI/Grok
- Notes:
  - DeepSeek and xAI/Grok should prefer the thinnest OpenAI-compatible adapter path that preserves the existing core boundary.
  - OpenRouter is treated as a single adapter surface with broad downstream model coverage.
- Demo criteria:
  - each provider can be created from the Connections surface,
  - preflight produces an explicit result,
  - runtime smoke writes a usage row,
  - cost normalization remains explicit through the current `cost_source` path.
- Acceptance gate:
  - all listed providers have a documented adapter path,
  - each provider either passes a minimal runtime gate or is explicitly marked blocked with evidence,
  - no provider logic leaks into the UI layer.

## S02 - Bedrock Early Access UI badge

- Status: COMPLETE

- Risk: LOW
- Depends: S01
- Scope:
  - add Bedrock to the UI surface as Early Access,
  - make runtime-proof limitations explicit,
  - avoid presenting Bedrock as generally supported.
- Demo criteria:
  - Bedrock is visible in the product surface with an `Early Access` label,
  - user-facing text makes the runtime-test gap explicit,
  - provider configuration can be inspected without implying production readiness.
- Acceptance gate:
  - Bedrock remains clearly documented as unproven at runtime,
  - no public surface claims full support,
  - R018 remains consistent unless external blockers are truly resolved.

## S03 - Budget Enforcement Toggle (D-031)

- Status: COMPLETE

- Risk: MEDIUM
- Depends: S01
- Scope:
  - move Budget Guard from monitor-only to actionable modes,
  - introduce explicit block and throttle behavior,
  - keep user-visible controls and behavior deterministic.
- Demo criteria:
  - user can switch between monitor-only, block, and throttle modes,
  - enforcement behavior is observable in the product surface,
  - protected actions do not silently bypass the configured policy.
- Acceptance gate:
  - D-031 dedicated package requirements are implemented and verified,
  - enforcement is explicit and reversible,
  - no hidden retry, fallback, or silent override behavior is introduced.

## S04 - Auto-update + Sigstore (D-038)

- Status: COMPLETE

- Risk: MEDIUM
- Depends: S03
- Scope:
  - add an Updates section under Settings,
  - expose a check-for-update flow that points to GitHub releases,
  - integrate Sigstore-backed artifact integrity guidance per D-038,
  - keep installation user-confirmed rather than silent.
- Demo criteria:
  - user can open Settings and check for updates,
  - the product links to the correct GitHub release surface,
  - integrity guidance is visible and consistent with D-038.
- Acceptance gate:
  - no silent install path is introduced,
  - SHA256 + Sigstore guidance is aligned with release policy,
  - update UX remains explicit and user-controlled.

## S05 - REST Adapter

- Status: COMPLETE

- Risk: MEDIUM
- Depends: S01
- Scope:
  - add a `REST Sources` category to the Connections provider picker,
  - support endpoint URL, auth type, HTTP method, and response field mapping,
  - keep the REST adapter inside the Connections surface rather than a new primary menu.
- Strategic posture:
  - `Any API. Any model. One gateway. Full audit trail.`
- Demo criteria:
  - user can configure a REST source from Connections,
  - request/response mapping produces a usable result path,
  - usage telemetry records request count, latency, and status through the same local audit surface.
- Acceptance gate:
  - REST adapter snapshot works without breaking the thin-shell/core boundary,
  - auth and mapping stay local-only and deterministic,
  - scope remains snapshot-level and does not drift into WebSocket or streaming behavior.
