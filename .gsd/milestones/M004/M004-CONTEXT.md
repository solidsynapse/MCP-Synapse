---
depends_on: [M003]
---

# M004: v0.9.x provider wave 2 + release productization - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

## Project Description

M004 is the `v0.9.x` milestone for MCP Synapse. It expands the provider surface beyond the first wave, introduces the next release-productization package, formalizes Bedrock as an explicit Early Access lane, adds actionable budget enforcement, and brings the first REST adapter snapshot into the product surface.

## Why This Milestone

The working SSOT now places `v0.9.x` after the completed `v0.8.x` capability-depth milestone. This milestone exists to turn the product from a well-instrumented local MCP router into a broader integration gateway with stronger release trust, a wider provider lane, and the first strategic signal of the domain-agnostic expansion.

## User-Visible Outcome

### When this milestone is complete, the user can:

- connect a broader provider wave through the same local gateway surface
- see Bedrock represented honestly as an Early Access lane when runtime proof is still incomplete
- configure actionable budget enforcement instead of monitor-only behavior
- check for updates and verify release integrity without silent installation behavior
- add non-LLM REST sources from the Connections surface under the same audit and telemetry model

### Entry point / environment

- Entry point: provider adapters, provider picker/config surface, budget-guard controls, Settings update surface, release-integrity flow, and Connections-based REST source onboarding
- Environment: local dev, packaged runtime, release-integrity artifacts, and product-facing configuration surfaces
- Live dependencies involved: provider contracts/runtime adapters, budget policy layer, Settings/Updates UI, release channel metadata, REST request/response mapping path

## Completion Class

- Contract complete means: the `v0.9.x` scope is explicitly mapped into slices and remains consistent with D-037, D-038, D-040, and the new REST-adapter positioning decision.
- Integration complete means: provider wave 2, Bedrock Early Access truth, budget enforcement, update/integrity surfaces, and the REST adapter snapshot all agree with the active SSOT and shipped UI/core boundaries.
- Operational complete means: M004 can execute slice-by-slice without reopening M003 closure or violating the thin-shell, BYOK, or no-silent-fallback rules.

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- S01 closes the confirmed provider wave 2 set: Anthropic, Groq, Gemini, OpenRouter, DeepSeek, and xAI/Grok
- S02 adds Bedrock to the UI as an explicit Early Access lane with clear runtime-proof limitations
- S03 upgrades Budget Guard from monitor-only to actionable enforcement through the D-031 package
- S04 exposes update checking and Sigstore-backed release integrity without silent install behavior
- S05 ships the REST adapter snapshot inside the Connections surface with a strategic, product-level positioning

## Risks and Unknowns

- Provider wave 2 can sprawl if OpenAI-compatible adapters are not kept thin and contract-driven.
- Bedrock can create product-surface confusion unless the Early Access boundary remains explicit everywhere.
- Budget enforcement is behaviorally sensitive and must avoid hidden or surprising routing side effects.
- Auto-update and integrity work can drift into signed-installer expectations that remain out of scope for this lane.
- REST adapter scope can sprawl toward streaming or domain-specific adapters before the snapshot boundary is stabilized.

## Existing Codebase / Prior Art

- `.gsd/DECISIONS.md` - active architectural decisions and updated `v0.9.x` milestone policy
- `.gsd/REQUIREMENTS.md` - active/deferred requirement contract inherited from prior milestones
- `.gsd/milestones/M003/M003-CONTEXT.md` - prior milestone closure and handoff context
- `docs/PRODUCT_ROADMAP.md` - archive/reference roadmap for M004 framing only
- `src/providers/anthropic_contract_pr4.py` - existing Anthropic contract stub
- `src/providers/groq_contract_pr5.py` - existing Groq contract stub

## Relevant Requirements

- R018 - Bedrock unblock lane
- R022 - Release integrity and distribution policy is established
- R023 - BYOK + local-only boundary is preserved and verified

## Slices

- S01 - provider wave 2
- S02 - Bedrock Early Access
- S03 - budget enforcement toggle
- S04 - auto-update + Sigstore
- S05 - REST adapter (strategic priority)

## Confirmed Scope Notes

- S01 provider set: Anthropic, Groq, Gemini, OpenRouter, DeepSeek, xAI/Grok
- DeepSeek and xAI/Grok are expected to enter via OpenAI-compatible API patterns
- OpenRouter is treated as a single adapter with broad model-surface reach
- Bedrock remains explicitly unproven at runtime entering this milestone and must be labeled as Early Access
- REST adapter belongs inside the Connections product surface, not as a separate primary menu
- REST adapter positioning: `Any API. Any model. One gateway. Full audit trail.`

## Technical Constraints

- D-024 must remain intact: thin-shell UI, no provider/network logic in the UI layer
- D-029 must remain intact: no hidden retry/backoff/fallback and no unauthorized core/UI behavior
- D-033 must remain intact: BYOK + local-only boundary remains binding
- D-037 must remain intact: `v0.9.x` now includes provider wave 2, budget enforcement, auto-update, and REST adapter snapshot
- D-038 must remain intact: Sigstore/integrity is allowed, silent install is not
- D-040 remains binding for cost normalization across any newly added provider adapters

## Open Questions

- none yet beyond the expected slice-planning breakdown for M004 execution
