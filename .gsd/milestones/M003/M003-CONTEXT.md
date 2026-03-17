---
depends_on: [M002]
---

# M003: v0.8.x capability depth + provider wave 1 - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

## Project Description

M003 is the `v0.8.x` milestone for MCP Synapse. It deepens product trust and provider completeness after the `v0.7.x` release-hardening milestone. The milestone focuses on cost transparency, the Bedrock blocked/deferred lane check, performance and security baseline closure, the documentation/compliance pack, and capability/IDE compatibility follow-through.

## Why This Milestone

The working SSOT now places `v0.8.x` after release hardening and before broader provider wave 2 or pro-surface work. This milestone exists to make the current product surface more trustworthy, close deferred baseline items that are now promoted into active scope, and prepare the codebase for the next expansion lane without violating the existing architectural boundaries.

## User-Visible Outcome

### When this milestone is complete, the user can:

- understand cost behavior and pricing trust on the current provider surface more clearly
- see the current blocked/deferred Bedrock status represented honestly and consistently
- rely on updated performance, security, documentation, and MCP capability/IDE compatibility baselines

### Entry point / environment

- Entry point: current provider/runtime surface, UI capability declarations, documentation surface, and verification outputs
- Environment: local dev / packaged runtime truth / product-facing documentation and compatibility surfaces
- Live dependencies involved: current active providers, usage/cost reporting path, MCP config generation path

## Completion Class

- Contract complete means: the `v0.8.x` scope is explicitly mapped into slices and protected by the active architectural constraints.
- Integration complete means: cost transparency, blocked-lane handling, baseline closure, documentation, and MCP capability/IDE compatibility all agree with the updated SSOT.
- Operational complete means: M003 can proceed slice-by-slice without reopening `v0.7.x` closure or inventing unauthorized scope.

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- S01 defines and closes the cost transparency direction with a new ADR before any litellm-backed implementation begins
- S02 keeps Bedrock truth explicit as a blocked/deferred lane unless the external blocker is actually resolved
- S03 closes the active performance and security baseline follow-up set
- S04 closes the promoted documentation and compliance pack work
- S05 closes MCP capability types and IDE compatibility matrix follow-through for the current product surface

## Risks and Unknowns

- Cost transparency work can drift into dependency or behavior changes before the ADR is written.
- Bedrock may remain externally blocked for the entire milestone, requiring strict scope discipline.
- Performance, security, and documentation work can sprawl if slice boundaries are not kept narrow.

## Existing Codebase / Prior Art

- `.gsd/DECISIONS.md` - active architectural and milestone policy decisions
- `.gsd/REQUIREMENTS.md` - active and deferred requirement set for M003
- `.gsd/milestones/M002/M002-ROADMAP.md` - prior milestone closure and handoff context
- `docs/PRODUCT_ROADMAP.md` - archive/reference roadmap aligned to the current `.gsd/` working truth

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions. Any litellm move requires a new ADR before implementation starts.

## Relevant Requirements

- R014 - Post-RC performance smoke
- R015 - Full English documentation pack
- R018 - Bedrock unblock lane

## Slices

- S01 - cost transparency + litellm
- S02 - Bedrock deferred/blocked lane check
- S03 - performance + security baseline closure
- S04 - documentation + compliance pack
- S05 - MCP capability types + IDE compatibility matrix

## Technical Constraints

- D-024 must remain intact: thin-shell UI, no provider logic in UI
- D-029 must remain intact: no hidden retry/backoff/fallback and no unauthorized scope expansion
- D-033 must remain intact: BYOK + local-only boundary remains binding
- litellm requires a new ADR and must be written before S01 implementation starts

## Open Questions

- none yet beyond the required litellm ADR gate before S01 execution
