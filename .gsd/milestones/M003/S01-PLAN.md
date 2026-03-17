# M003/S01 Implementation Plan

Status: READY

Decision gate: D-040 is recorded. S01 may proceed to implementation planning and execution.

## Objective

Implement the `v0.8.x` cost-transparency layer with litellm-backed cost normalization, explicit `cost_source` semantics, and graceful degradation when pricing data or the dependency is unavailable.

## Step 1 - litellm installation and wrapper entrypoint

Purpose:
Add the new runtime dependency in a controlled way and isolate it behind one local wrapper module.

Scope IN:
- `c:\mcp-router\requirements.txt`
- `c:\mcp-router\src\providers\cost_normalization.py` (new)
- provider import callsites that will use the wrapper:
  - `c:\mcp-router\src\providers\openai_client.py`
  - `c:\mcp-router\src\providers\azure_openai_client.py`
  - `c:\mcp-router\src\vertex\client.py`

Scope OUT:
- direct litellm imports scattered across multiple providers
- any UI file
- Bedrock/Hugging Face/Ollama runtime enablement work

Planned install/import shape:
- add `litellm` to `requirements.txt` with a pinned version during implementation
- inside the local wrapper, use `import litellm`
- provider code imports only the local wrapper, not litellm directly:
  - `from src.providers.cost_normalization import normalize_cost_with_litellm`

Acceptance criteria:
- `requirements.txt` includes a pinned `litellm` dependency
- exactly one local wrapper owns the runtime dependency boundary
- provider modules call the local wrapper instead of embedding litellm import logic themselves

## Step 2 - current cost-function inventory

Purpose:
Freeze the exact pre-migration cost logic before replacing it.

Scope IN:
- `c:\mcp-router\src\providers\openai_client.py`
- `c:\mcp-router\src\providers\azure_openai_client.py`
- `c:\mcp-router\src\vertex\client.py`

Scope OUT:
- unrelated provider contract files
- non-cost provider behavior

Current inventory:
- `src/providers/openai_client.py`
  - `_openai_unit_prices(...)`
  - `_estimate_cost(...)`
- `src/providers/azure_openai_client.py`
  - `_azure_unit_prices(...)`
  - `_estimate_cost(...)`
- `src/vertex/client.py`
  - `_calc_cost(...)`
  - token fallback already exists via `tiktoken` when usage metadata is missing

Acceptance criteria:
- plan and implementation reference the exact legacy cost functions above
- each legacy function has a clear replacement path or adapter outcome
- no provider is migrated without first documenting its current cost path

## Step 3 - provider migration to litellm delegates

Purpose:
Move provider cost logic from embedded arithmetic to wrapper-mediated normalization.

Scope IN:
- `c:\mcp-router\src\providers\openai_client.py`
- `c:\mcp-router\src\providers\azure_openai_client.py`
- `c:\mcp-router\src\vertex\client.py`
- optional explicit UNKNOWN pass-through alignment:
  - `c:\mcp-router\src\providers\huggingface_client.py`
  - `c:\mcp-router\src\providers\ollama_client.py`
  - `c:\mcp-router\src\providers\bedrock_client.py`

Scope OUT:
- adding new providers
- provider routing changes in `src/providers/factory.py`
- network/protocol behavior changes

Migration pattern:
- OpenAI: replace `_estimate_cost(...)` call with wrapper delegation
- Azure OpenAI: replace `_estimate_cost(...)` call with wrapper delegation
- Vertex: replace `_calc_cost(...)` call with wrapper delegation
- providers with no pricing data path return:
  - `cost_usd = None`
  - `cost_source = "UNKNOWN"`
- wrapper returns normalized payload fields:
  - `cost_usd`
  - `cost_source`

Fallback pattern:
- litellm has pricing data:
  - return computed value with `cost_source = "ESTIMATED"` unless provider exposes true billed cost in-response
- litellm has no pricing data:
  - return explicit `UNKNOWN`
- litellm import/runtime unavailable:
  - degrade gracefully through the local wrapper
  - preserve request success path
  - emit `cost_source = "UNKNOWN"` instead of fake zero

Acceptance criteria:
- OpenAI, Azure OpenAI, and Vertex no longer own duplicated arithmetic as the primary path
- fallback is explicit and never silently returns a misleading zero-cost success
- provider result payloads remain backward-compatible for callers that still expect `cost_usd`

## Step 4 - `cost_source` field and UsageDatabase persistence decision

Purpose:
Decide whether `ACTUAL / ESTIMATED / UNKNOWN` is derived at read time or persisted end-to-end.

Scope IN:
- `c:\mcp-router\src\data\usage_db.py`
- `c:\mcp-router\src\mcp_server\pipeline_v1.py`
- `c:\mcp-router\src\mcp_server\manager.py`
- tests that assert usage DB / export contract:
  - `c:\mcp-router\src\tests\test_d004_usage_db_contract.py`
  - `c:\mcp-router\src\tests\test_d004_g3_csv_export.py`
  - `c:\mcp-router\src\tests\test_d004_g2_error_type_and_test_traffic.py`

Scope OUT:
- analytics redesign beyond the current usage schema
- historical backfill or destructive DB migration

Schema decision:
- current schema stores `cost_usd` only
- this is not sufficient to distinguish `ACTUAL` vs `ESTIMATED` after persistence
- therefore S01 should treat a nullable `cost_source TEXT` column as required if the UI/CSV must show authoritative source labels across restarts and exports

Acceptance criteria:
- one explicit decision is implemented:
  - either persist `cost_source` in the `usage` table
  - or document why S01 intentionally keeps it derived-only
- if persisted, `UsageDatabase._ensure_storage()` adds the column safely without breaking existing DBs
- `manager.py` and `pipeline_v1.py` pass `cost_source` through when logging usage rows

## Step 5 - UI cost badge surface

Purpose:
Expose `ACTUAL / ESTIMATED / UNKNOWN` clearly on the current Svelte surface without broad UI churn.

Scope IN:
- primary file:
  - `c:\mcp-router\ui-tauri\src\routes\usage\history\+page.svelte`
- optional parity follow-up only if S01 still fits cleanly:
  - `c:\mcp-router\ui-tauri\src\routes\usage\summary\+page.svelte`
- styling tokens if a new badge variant is required:
  - `c:\mcp-router\ui-tauri\src\app.css`

Scope OUT:
- legacy Flet UI files under `src/ui/`
- broad page redesign
- non-usage pages

Why this surface:
- `usage/history/+page.svelte` already contains the current "Pricing status" logic and CSV export column
- this is the narrowest place to introduce an explicit cost badge without expanding scope

Acceptance criteria:
- Usage History shows `ACTUAL / ESTIMATED / UNKNOWN` from the real payload, not the current inferred-only heuristic
- CSV export stays aligned with the same source label
- Summary page is touched only if needed for narrow parity, not by default

## Step 6 - test strategy

Purpose:
Prove the dependency boundary, fallback behavior, and provider-specific migration without needing broad live-network coverage.

Scope IN:
- new unit/integration tests under:
  - `c:\mcp-router\src\tests\test_m003_s01_cost_normalization.py` (new)
- existing contract surfaces to extend:
  - `c:\mcp-router\src\tests\test_d004_usage_db_contract.py`
  - `c:\mcp-router\src\tests\test_d004_g3_csv_export.py`
  - `c:\mcp-router\src\tests\test_phase2.py`
  - provider-specific offline tests where relevant

Scope OUT:
- Bedrock unblock live testing
- full packaged-app smoke
- unrelated UI snapshot work

Required test lanes:
- litellm unavailable scenario:
  - wrapper import failure
  - request succeeds
  - `cost_source = "UNKNOWN"`
- no-pricing-data scenario:
  - provider/model not present in litellm
  - no silent zero-cost success label
- persisted-source scenario:
  - DB round-trip preserves `cost_source` if schema is upgraded
- per-provider smoke:
  - OpenAI
  - Azure OpenAI
  - Vertex
- UI/CSV parity:
  - Usage History label and exported "Pricing status" stay aligned

Acceptance criteria:
- tests cover both dependency absence and missing-pricing data
- at least one smoke/assertion path exists for each migrated provider
- UI/CSV assertions fail if `cost_source` regresses back to heuristic-only labeling

## Recommended execution order

1. Step 1 - add dependency and local wrapper boundary
2. Step 2 - freeze the legacy inventory
3. Step 4 - settle persistence model for `cost_source`
4. Step 3 - migrate provider delegates
5. Step 5 - update Usage History badge surface
6. Step 6 - finalize tests and fallback proof
