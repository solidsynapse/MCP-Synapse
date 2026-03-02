﻿# DECISIONS — Architectural & Process ADRs

## Format
- ID
- Date
- Decision
- Context
- Alternatives
- Consequences
- Evidence

---

## D-001 — SSOT lives in docs/*
- Date: 2026-02-14
- Decision: STATUS/PLAN/TASKS/DECISIONS under docs/ are the only source of truth.
- Context: Repo has limited docs (only pipeline-v1.md) and needs stabilization checkpoint.
- Alternatives: Keep decisions in chat / scattered notes.
- Consequences: Every change must update docs + include verifiable evidence refs.
- Evidence: docs tree + existence of docs/architecture/pipeline-v1.md

---

## D-002 — Gate-driven Build/QA/Deploy
- Date: 2026-02-14
- Decision: No stage (Build/QA/Deploy/Rollout) proceeds without explicit evidence capture.
- Context: Legacy path must remain stable while V1 is re-activated.
- Alternatives: Informal testing / ad-hoc toggling.
- Consequences: Slightly slower iteration, significantly lower risk.
- Evidence: STATUS.md checkpoint definition.

---

## D-003 — Pipeline V1 rollout is incremental (opt-in → 10% → 50% → 100%)
- Date: 2026-02-14
- Decision: V1 activation will be staged with explicit rollback triggers.
- Context: V1 is additive and must not break legacy.
- Alternatives: Big-bang switch.
- Consequences: Requires activation switch + metrics/log evidence before each expansion.
- Evidence: Requires proving activation mechanism first (see STATUS unknowns).

---

## D-006 — Legacy behavior is preserved until V1 gates pass
- Date: 2026-02-14
- Decision: No changes that alter legacy default behavior before M4 checkpoint.
- Context: MVP UX done; system stability is priority.
- Alternatives: Refactor legacy early.
- Consequences: V1 work must be opt-in and reversible.
- Evidence: pipeline-v1.md states backward compatibility intent.

---

## D-005 — Pipeline V1 activation must be an explicit call-site (no hidden toggle)
- Date: 2026-02-14
- Decision: Treat V1 activation as an explicit call-site change, not a config flag, unless future evidence shows a toggle exists.
- Context: execute_request_v1 is defined and call-site exists as of T0.8 (routing switch in MCPAgentServer._generate_text); config.json contains no related toggle keys.
- Alternatives: assume a hidden UI/config flag; auto-route to V1 by default.
- Consequences: next work is to locate the correct legacy integration point and implement opt-in gating there.
- Evidence: STATUS.md “Pipeline V1 Activation Status (T0.8)” runtime proof + file+line references in STATUS Evidence Index.

---

## D-007 — Stage 1 deterministic percent rollout (V1)

- Date: 2026-02-15
- Decision:
  1) Stage 0 override (force V1): `MCP_ROUTER_USE_V1` (existing).
  2) Stage 1 percent split control: `MCP_ROUTER_V1_PCT` as an integer in `[0,100]`.
  3) Precedence (routing decision order):
     - If `MCP_ROUTER_USE_V1` is set ⇒ force V1 (Stage 0 override).
     - Else if `MCP_ROUTER_V1_PCT` parses as a valid int in `[0,100]` ⇒ apply deterministic percent split.
     - Else ⇒ legacy default.
     - Invalid / non-integer / out-of-range `MCP_ROUTER_V1_PCT` behaves as “unset” (falls through to legacy default).
  4) Hash algorithm standard: **SHA-256 only** for Stage 1 split decisions.
  5) Split key (what is hashed): `split_key = agent_id + "\n" + prompt` (prompt-bazlı split bilinçli kabul).
  6) Deterministic bucket rule:
     - `digest = sha256(split_key).hexdigest()`
     - `bucket = int(digest[:8], 16) % 100`  (0–99)
     - Route to V1 iff `bucket < MCP_ROUTER_V1_PCT`
  7) Logging fields standard (Stage 1):
     - `routing` = `legacy` | `v1`
     - `pct` = int (0–100) or omitted if unset
     - `bucket` = int (0–99) or omitted if unset
     - `key_type` = `agent_id_prompt`
     - `key_hash_prefix` = `sha256(split_key)` hex digest prefix (first 8 chars)
     - `outcome` = `force_v1` | `pct_v1` | `pct_legacy` | `legacy_default`
- Context:
  - Stage 0 today is boolean env-var routing (legacy default preserved).
  - Stage 1 needs deterministic, reproducible split without external state (no DB/counter/cache).
  - SSOT does not show a stable request_id; agent_id and prompt are available at the routing decision point (see STATUS/ARCH logs).
- Alternatives:
  - Random sampling (non-deterministic; hard to test).
  - Global counters / DB-backed rollout (adds state + failure modes).
  - User/account-id based key (not evidenced in SSOT at routing point).
- Consequences:
  - Prompt-bazlı split: aynı `agent_id` ile farklı prompt’lar farklı bucket’a düşebilir; bu bilinçli kabul.
  - Privacy: prompt text should not be logged; use `prompt_len` + `key_hash_prefix`.
  - Rollback: unset `MCP_ROUTER_USE_V1` and `MCP_ROUTER_V1_PCT` ⇒ legacy default.
- Evidence:
  - STATUS.md “Pipeline V1 Activation Status (T0.8)” shows Stage 0 env-var routing + `agent_id` + `prompt_len` in logs.
  - ARCHITECTURE_EVOLUTION_LOG.md records `_generate_text(prompt)` routing decision point and the `routing=... agent_id=... prompt_len=...` log shape.

---

## D-008 — Provider abstraction seam for Pipeline V1 (ProviderFactory + ProviderClient)

- Date: 2026-02-17
- Decision:
  - Introduce a provider-agnostic seam at ProviderAdapterV1:
    - `ProviderClient` protocol defines `provider_id`, `model_id`, and `generate_content(prompt, stream=...)`.
    - `ProviderFactory` creates a concrete ProviderClient by `provider_id`.
  - Provider selection lives in PreflightGuardV1 via agent config:
    - `provider_id = agent.provider_id || agent.provider || "vertex"` (default preserves existing Vertex flow).
    - `streaming = agent.streaming || agent.stream || False` (plumbed; no new routing policy).
  - Vertex integration becomes a concrete ProviderClient:
    - `VertexProviderClient` wraps existing `VertexAIClient` (no behavior change for Vertex).
- Context:
  - Phase 1.5 requires adding a second provider adapter without changing MCP wiring or UI request flows beyond config selection.
  - ProviderAdapterV1 previously constructed `VertexAIClient` directly, preventing a clean multi-provider extension.
- Alternatives:
  - Keep `VertexAIClient` construction inside ProviderAdapterV1 and add if/else branches per provider.
  - Move provider branching into MCP server wiring (high-risk zone) or UI routing (scope creep).
- Consequences:
  - Adding a new provider becomes: implement ProviderClient + register it (no MCP wiring edits).
  - Tests can inject a deterministic fake provider through the factory registry to prove feasibility offline.
- Evidence:
  - docs\evidence\T1.5_provider_abstraction_20260217-161800\

---

## D-009 — Pipeline V1 provider entrypoint is ProviderFactory only

- Date: 2026-02-17
- Decision:
  - Note (Phase 1.5, documentation only):
    - Legacy routing path is intentionally retained for rollback.
    - Phase 1.5 scope is limited to proving the ProviderFactory seam in Pipeline V1; no routing redesign.
  - Pipeline V1 provider seçimi ve client oluşturma tek giriş noktasıdır:
    - ProviderAdapterV1 → `ProviderFactory.create(provider_id, context)`
  - Pipeline V1 içinde doğrudan provider SDK/client inşası yapılmaz (örn. VertexAIClient ctor çağrısı yok).
- Context:
  - Phase 1.5 “provider-agnostic” iddiasını kilitlemek için seam’in bypass edilmemesi gerekir.
- Alternatives:
  - ProviderAdapterV1 içinde provider bazlı `if/elif` ile doğrudan client oluşturmak.
- Consequences:
  - Yeni provider eklemek: ProviderClient + ProviderFactory.register ile sınırlı kalır (MCP wiring/UI akışı değişmez).
- Evidence:
  - docs\evidence\T1.5_hardening_20260217-163300\

---

## D-010 — Azure OpenAI provider config + secret handling (file-path)

- Date: 2026-02-17
- Decision:
  - Provider id: `azure_openai`
  - Agent config alanları (data/config.json agent entry):
    - `azure_endpoint` (örn: https://{resource}.openai.azure.com)
    - `azure_api_version` (örn: 2024-02-15-preview)
    - Deployment adı:
      - Varsayılan: `model_id` deployment olarak kullanılır
      - Override: `deployment_name` (veya `azure_deployment`)
  - Secret (API key) saklama:
    - Raw key config’te tutulmaz.
    - CredentialManager ile (mevcut semantik: agent_id) alınan değer bir dosya yoludur.
    - Dosya içeriği UTF-8 okunur ve `strip()` ile API key elde edilir; boşsa hata.
    - (Phase 1.5 constraint) Azure provisioning:
      - UI credential save is NOT used for Azure (CredentialManager.save_credential currently validates GCP JSON).
      - CredentialManager.get_credential(agent_id) MUST return an absolute file path.
      - The Azure provider reads the file as UTF-8, applies strip(); empty => hard error.
      - No silent fallback on missing/invalid path.
  - Streaming:
    - `stream=True` geldiğinde açık `NotImplementedError` (sessiz davranış değişimi yok).
- Context:
  - Phase 1.5 kapsamında ikinci gerçek provider eklenmesi isteniyor; UI/MCP wiring değiştirilmeden ProviderFactory seam üzerinden eklenmeli.
- Alternatives:
  - API key’i config’e koymak (yasak).
  - Unknown provider_id için sessiz fallback yapmak (yasak).
- Consequences:
  - Azure OpenAI eklemesi sadece yeni ProviderClient + ProviderFactory kaydı ile sınırlı kalır.
- Evidence:
  - docs\evidence\T1.5_azure_openai_20260217-170200\

---

## D-011 — ProviderClient canonical output + annotation boundary (Phase 1.5)

- Date: 2026-02-18
- Decision:
  - ProviderClient.generate_content() canonical output:
    - Required:
      - text: str (empty allowed)
    - Optional:
      - tokens_input: int | None
      - tokens_output: int | None
      - cost_usd: float | None
  - Provider-reserved keys: text, tokens_input, tokens_output, cost_usd
  - Pipeline/Adapter-reserved keys: latency_ms, status, error_type, request_id, provider, model_id
  - Pipeline/Adapter may only add its reserved keys; it MUST NOT overwrite provider-reserved keys.
  - In-place mutation is allowed subject to the overwrite rule above.
  - Scope note: This decision formalizes existing behavior only; no new enforcement layer is introduced in Phase 1.5.

---

## D-012 — Streaming determinism gate (Phase 1.5)

- Date: 2026-02-18
- Decision:
  - If stream=True is requested, a provider MUST either implement streaming or raise NotImplementedError.
  - Silently ignoring the stream parameter is forbidden (Vertex included).

---

## D-013 — No silent swallow (Phase 1.5 scoped)

- Date: 2026-02-18
- Decision:
  - Phase 1.5 scope is limited to fixing ONLY the already-identified swallow instances:
    - src/ui/main_window.py refresh loop: bare except/pass
    - src/data/credentials.py delete_credential: except Exception/pass
  - No repo-wide sweep is performed in Phase 1.5 (global swallow cleanup is Phase 2).
  - If a best-effort swallow is ever required, it must be narrowly scoped (specific exception), documented, and visible (e.g., log/explicit outcome). Otherwise the error must surface.


---

## D-014 — AWS Bedrock provider (Phase 2 start authorization, non-streaming)

- Date: 2026-02-18
- Decision:
  - Provider id: edrock
  - Scope (Phase 2):
    - Add Bedrock as provider #3 via ProviderFactory seam only (no core routing/pipeline branching by provider).
    - Non-streaming only: if stream=True => raise NotImplementedError (per D-012).
    - No hidden retry/backoff. No silent fallback. Errors must surface explicitly.
    - Output contract MUST follow D-011 (text required; tokens/cost optional; pipeline reserved keys must not overwrite provider keys).
  - Credentials:
    - No CredentialManager redesign.
    - Provisioning may be UI-external if UI/save_credential validation blocks Bedrock-shaped credential files.
    - CredentialManager.get_credential(agent_id) continues to return an absolute file path.
  - Dependencies:
    - No new dependency may be added without an explicit SSOT decision amendment (this decision does NOT approve adding boto3/botocore yet).
- Evidence:
  - docs/evidence/T2_bedrock_acceptance_20260218-043014/

---

## D-015 — Bedrock real network calls (dependency approval + explicit gate)

- Date: 2026-02-18
- Decision:
  - This amends D-014 to allow real Bedrock network calls post-MVP, behind an explicit opt-in gate.
  - Approved dependencies (Bedrock only):
    - oto3
    - otocore
  - Constraints (unchanged):
    - No hidden retry/backoff, no silent fallback, errors surface explicitly.
    - Streaming remains disabled: if stream=True => raise NotImplementedError (D-012).
    - Output contract follows D-011 (provider keys not overwritten by pipeline keys).
  - Gate:
    - Real network calls MUST be opt-in (default remains non-network / NotImplementedError).
    - Gate mechanism will be config-driven (agent config) or environment-driven, but MUST be explicit and documented.
- Evidence:
  - docs/evidence/T2C_bedrock_realcall_gate_20260218_050723/

---

## D-016 — Hugging Face provider authorization (Inference API over HTTP, deterministic, non-streaming)

- Date: 2026-02-18
- Decision:
  - Provider id: `huggingface`
  - Mode choice (default):
    - Default mode is the Hugging Face Inference API over HTTP, implemented with dependency-free stdlib HTTP only.
    - Optional override: `hf_endpoint` may be provided to target a self-hosted / internal Hugging Face-compatible endpoint base URL.
  - Determinism / error policy:
    - No hidden retry/backoff.
    - No silent fallback (e.g., do not switch providers/endpoints/models implicitly).
    - Non-success responses and request/parse errors must surface explicitly as errors.
  - Streaming:
    - Streaming remains unsupported. If `stream=True` is requested, raise `NotImplementedError` (per D-012).
  - Output contract (D-011):
    - Provider returns D-011 canonical keys (`text` required; `tokens_input/tokens_output/cost_usd` optional).
    - Provider MUST NOT return or overwrite pipeline/adapter-reserved keys; annotation boundary is respected.
  - Secrets (token via existing mechanism):
    - Token material is not stored in agent config.
    - `credentials_path` is stored in the OS keyring by the existing CredentialManager and resolves to an absolute file path.
    - The provider reads the file as UTF-8, applies `strip()`, and uses the result as the bearer token; empty is a hard error.
    - If UI credential save is blocked by existing validation, provisioning is UI-external; no CredentialManager redesign is introduced for this provider.
- Context:
  - Bedrock has been authorized as a real provider; Hugging Face is the next real provider to add via the ProviderFactory seam, without adding dependencies.
  - Hugging Face supports both the public Inference API base URL and self-hosted endpoints; SSOT must lock a single default mode and deterministic behavior.
- Alternatives:
  - Add a Hugging Face SDK dependency (rejected; dependency-free HTTP is the default).
  - Implement retries/backoff or fallback to preserve “best effort” behavior (rejected; determinism requirement).
  - Implement streaming (deferred; not in Phase 1.5/2 scope per D-012).
  - Store the token directly in config or redesign credential storage (rejected; existing file-path mechanism remains).
- Consequences:
  - Hugging Face can be implemented as a ProviderClient with predictable behavior and no new dependencies.
  - Operators must provision a token file externally when UI save is blocked; missing/empty credentials fail fast.
- Evidence:
  - docs/evidence/T2F_hf_start_auth_20260218-054605/

---

## D-004 — Usage DB → KPI Contract (Phase 2)
- Date: 2026-02-17
- Decision: Define a single, normative contract for how the UI Usage tab derives KPIs and table rows from the local Usage DB.
- Context: KPI logic and filters must be deterministic and consistent across KPI panel, table, and CSV export. Prior references exist outside SSOT; this decision locks the contract inside SSOT.
- Alternatives: Leave KPI semantics scattered across plans/evidence; derive ad-hoc in UI.
- Consequences: UI and DB querying MUST follow this contract; any change requires updating this decision + evidence.
- Evidence: docs\evidence\T3.1_20260217-095736\ (db_schema_*.txt, db_rows_sample.txt, grep proofs)

### Scope
- This contract defines how the UI Usage tab derives KPIs and table rows from the local Usage DB.
- Applies to production UI path; debug/test traffic inclusion is explicitly defined below.

### Canonical fields (source of truth)
- provider, model_id, request_id (identifiers)
- status (canonical), error_type (canonical, nullable)
- latency_ms (integer milliseconds)
- tokens_input, tokens_output (integers, may be null if unavailable)
- cost_usd (float, may be null if unavailable)
- timestamp (UTC timestamp)
- agent_name (string)

### Status mapping (canonical)
- success: request completed successfully
- error: request completed with an error (includes provider errors, validation errors, etc.)
- cancelled: user-initiated cancel (if present in DB; otherwise map to error with error_type="cancelled")
- unknown: only if DB row lacks sufficient information; must be counted separately (not success)

### Success / Failure definitions
- success_count = rows where status == "success"
- failure_count = rows where status in {"error","cancelled"} (exclude "unknown" unless explicitly chosen)
- success_rate = success_count / (success_count + failure_count)   (0/0 => 0)

### Latency KPI
- avg_latency_ms computed over rows where latency_ms is not null and status in {"success","error","cancelled"} (exclude unknown)
- p95_latency_ms (if implemented) uses same inclusion rules

### Cost & tokens KPIs
- total_cost_usd = sum(cost_usd) over included rows where cost_usd is not null
- tokens_in_total = sum(tokens_input) where not null
- tokens_out_total = sum(tokens_output) where not null

### Error type canonicalization
- error_type MUST be one of:
  - provider_error
  - auth_error
  - rate_limit
  - timeout
  - network_error
  - validation_error
  - cancelled
  - unknown_error
- If raw provider error is available, it must be mapped deterministically to the above set.

### Filter semantics (single contract for KPI + table)
- agent_name filter:
  - if set: include only rows where agent_name exactly matches
  - if empty/all: include all agent_name values
- date range filter:
  - inclusive start, exclusive end (UTC)
  - presets (Last 1h/24h/7d/30d/All) must map deterministically to UTC boundaries
- KPI panel and table MUST use identical filter predicates.

### Test/debug traffic inclusion
- Production UI MUST exclude debug/test traffic unless explicitly toggled.
- A deterministic rule must exist:
  - either a DB column flag (e.g., is_test) OR a reserved agent_name prefix (e.g., "_test_")
  - if no marker exists, then ALL traffic is treated as production and included.

### CSV export determinism
- Export uses the same filtered dataset as table.
- Stable column order: provider, model_id, request_id, status, error_type, latency_ms, tokens_input, tokens_output, cost_usd, timestamp, agent_name
- Stable row order: ORDER BY datetime(timestamp) ASC, request_id ASC, id ASC
- Values must be serialized deterministically (UTC ISO8601, '.' decimal separator)

## D-018 — Pytest is required for verification evidence (dev/test only)
- Date: 2026-02-19
- Decision: The project test runner is pytest. Verification/evidence bundles MUST include `python -m pytest -q` output.
- Context: Repo ships `pytest.ini` and tests import pytest; gates require deterministic test proof.
- Alternatives: unittest-only; ad-hoc manual testing.
- Consequences:
  - Pytest is a dev/test requirement (not a production dependency).
  - Installing pytest locally for verification is allowed without changing production requirements.
- Evidence: pytest.ini in repo; tests importing pytest.


## D-019 — Phase 2 Pivot: Core Productization (locked scope)


### Core-first principle (MVP track)
- Until MVP is shipped, progress MUST be proven via headless evidence only:
  - pytest
  - mcp_sse_probe (initialize/tools/list/tools/call raw dumps)
  - smoke_tests.ps1 (MVP.1)
  - evidence pack (commands_ran + grep_proofs + pytest + exit_code + changed_files + rollback + before/after snapshots as applicable)
- UI is a thin shell and may only be built as the final MVP step:
  - UI must not contain provider calls or core logic; it only configures + dispatches and renders status/usage.
  - Any UI code changes remain out of scope for Phase 2 per D-019.
- Phase 2 scope is locked to: Deterministic Core Engine + MCP protocol compliance + Headless MVP verification.
- UI (including Flet) is OUT OF SCOPE for Phase 2:
  - UI code changes are forbidden in Phase 2.
  - UI may be used only for observation/screenshot evidence capture.

### Phase 2 DONE gates (normative)
1) MCP Tool Discovery Contract (BLOCKER)
   - MUST support JSON-RPC methods: `initialize`, `tools/list`, `tools/call`.
   - `initialize` response MUST include `capabilities.tools`.
   - `tools/list` MUST return at least 1 tool (non-empty list).
   - Responses MUST be deterministic for the same input:
     - response shape + status MUST be stable (except timestamp/request_id fields).

2) Headless MVP harness
   - MUST be able to prove (without UI): bridge list/start/stop/test; usage list/export/clear; MCP probe (initialize + tools/list + tools/call).
   - No new harness surface may be invented without an explicit SSOT decision.

### SSOT-core for Phase 2 enforcement
- Binding SSOT files for Phase 2 gating: docs/DECISIONS.md, docs/STATUS.md, docs/TASKS.md.
- docs/PLAN.md is HISTORICAL ONLY (non-binding reference).
- docs/ARCHITECTURE_EVOLUTION_LOG.md is excluded from SSOT-core enforcement due to drift risk.



## D-020 — Phase 2 MCP Tool Discovery evidence generation contract

- MCP Tool Discovery (initialize + tools/list + tools/call) cannot be marked DONE unless the repo contains a committed, headless probe that produces raw JSON-RPC request/response dumps for:
  - initialize
  - tools/list
  - tools/call
- The canonical command MUST be documented (exact command line) and MUST write files under:
  docs/evidence/<ID_timestamp>/mcp_probe/
- Until such a probe exists and evidence is produced, the MCP Tool Discovery gate remains BLOCKER.
- Rollback discipline MUST NOT assume git; when git is unavailable, SSOT edits MUST be backed up by copying the pre-edit file into the evidence root.


## D-021 — Post-Phase-2 cleanup policy (docs-only; no implementation in Phase 2)

- Code deletion / UI refactor / dead-code cleanup is OUT OF SCOPE for Phase 2.
- Cleanup work may start only after Phase 2 DONE gates are satisfied and must be tracked as its own task(s) with evidence roots.
- Legacy path must remain available until an explicit SSOT decision retires it (no silent removal).


## D-022 — Legacy path retirement policy (docs-only)

- “Legacy path” is the direct provider call path used when routing=v1 is not selected or V1 prerequisites are missing.
- Legacy path MUST remain available until:
  - a dedicated retirement decision explicitly declares it retired, and
  - Phase-3+ evidence proves: v1 path covers all required headless MVP operations without legacy fallback.
- No silent retirement:
  - removal or disabling of legacy behavior MUST be accompanied by SSOT updates (DECISIONS + TASKS + STATUS) and an evidence root.
- Prereq-missing behavior:
  - Any “v1 prereq missing → legacy” behavior MUST be explicit, logged, and deterministic.
  - Removing this behavior requires a separate SSOT decision and tests proving stable behavior for missing-prereq cases.
- UI boundary (policy reminder):
  - UI production path MUST NOT directly call providers; any provider invocation must be via the headless core/bridge surface.
  - Enforcing this boundary is Post-Phase-2 work and must be tracked as its own task(s) with evidence roots.

## D-023 — Master plans are reference-only (non-SSOT)

- Master plan documents (e.g., MASTERPLAN_V2) are reference/vision only and are NOT SSOT.
- Binding SSOT files: docs/DECISIONS.md, docs/STATUS.md, docs/TASKS.md.
- Any change to runtime stack, dependency set, UI framework, or phase ordering requires an explicit SSOT decision + a tracked task with evidence roots.

## D-024 — Phase 3 scope + exit criteria + gates (UI thin shell)

- Date: 2026-02-21
- Decision: Phase 3 is a UI thin-shell phase. Core remains deterministic and provider-agnostic.

### Scope (allowed)
- UI may only:
  - write/read configuration and selections
  - dispatch requests to the headless/core surface
  - render status + usage views (read-only; export/clear actions must call core services, not providers)

### Scope (forbidden)
- UI production path MUST NOT call provider clients directly.
- Core (router/manager/pipeline) MUST NOT gain provider-specific branching.

### Gates (Phase 3)
- No streaming unless explicitly approved by SSOT decision.
- No new runtime dependencies unless explicitly approved by SSOT decision.
- No silent fallback, hidden retry, or backoff in core.
- Evidence standard remains: docs/evidence/<ID_timestamp>/ with commands_ran.txt + anchor_proofs.txt (+ pytest artifacts when applicable).

### Exit criteria (Phase 3 DONE)
- UI “thin shell boundary” is proven via evidence:
  - grep_proofs show provider client calls are absent from UI production path
  - dispatch chain points to headless/core execution surfaces
- All Phase 3 tasks in TASKS/STATUS have evidence roots and are marked DONE with anchor proof (+ pytest when applicable).

## D-025 — Budget Guard is monitor-only in Phase 3 (no enforcement)
- Date: 2026-02-21
- Decision: Budget Guard in Phase 3 is **monitor-only**. It reports usage/cost/tokens and can emit warnings, but MUST NOT block, throttle, or alter request execution.
- Rationale:
  - Minimizes maintenance burden and avoids false-positive “hard stops”.
  - Preserves determinism: no hidden behavior changes in core.
  - Enforcement requires careful UX/override/rollback and will be reconsidered in a later phase via a dedicated SSOT decision + evidence.
- Constraints:
  - No new runtime dependencies.
  - No streaming changes.
  - UI remains thin shell; any “warning display” is render-only; no provider calls.
- Exit proof (when implemented):
  - Headless evidence shows thresholds are computed deterministically from stored usage rows.
  - No code path blocks execution based on budget (grep proof + tests).
## D-026 — Provider ToS gate + BYOK/local-only compliance baseline (Phase 3+)
- Date: 2026-02-21
- Decision:
  - The router is **BYOK + local-only** by default:
    - Users supply their own provider credentials.
    - No key pooling, no key relay as-a-service, no shared accounts.
    - Router runs locally; “SaaS proxy mode” is out of scope unless a future SSOT decision explicitly authorizes it.
  - Provider integrations with unclear/strict ToS (e.g., Google AI Studio / Gemini API) remain **contract-only** until written clarification/approval is captured under docs/evidence.
  - The product must include a **User Terms/Use Acknowledgement** layer (documentation + UI acknowledgement when UI exists):
    - User confirms they are authorized to use the provided API key and will comply with provider ToS.
    - User acknowledges the router does not provide or share API access and is not a proxy service.
- Constraints:
  - No new runtime dependencies without SSOT decision.
  - No streaming unless SSOT-approved.
  - Determinism preserved: no silent fallback/retry/backoff.
- Evidence (for any provider marked “enabled”):
  - docs/evidence/<ID_timestamp>/ contains:
    - ssot_core.sha256.txt
    - contract summary + ToS gate statement
    - (if ToS ambiguous) written clarification/approval artifact reference (email/pdf/screenshot)
## D-028 — Product naming: MCP Synapse (formerly MCP Router)
- Date: 2026-02-22
- Decision: The product name is **MCP Synapse**.
- Former/legacy name: **MCP Router** (may appear in repo paths, historical evidence, and legacy filenames).
- SSOT wording rule:
  - Use “MCP Synapse” as the primary name in SSOT and user-facing docs.
  - If needed for clarity, use “MCP Synapse (formerly MCP Router)” on first mention only.

### P3 Implementation Allowed (gate)
- P3 implementation may proceed without requiring “Phase 3 sealed” (P4 transition gate).
- Constraints:
  - No new P3.* IDs may be introduced in SSOT.
  - Existing P3 items may be implemented; details may be added only as sub-bullets under existing IDs (no new IDs).
  - No scope expansion: no new feature/phase start outside existing SSOT P3 items.
  - Evidence standard remains mandatory: docs\evidence\<id_timestamp>\ (+ required evidence files).
  - P3.PR3.I1 remains BLOCKED without BYOK key; no provider/network calls are permitted while blocked.
- P4 transition still requires “Phase 3 sealed”.

## D-029 — Phase 4 UI Prep Architecture Lock (Thin Shell)

- Date: 2026-02-22
- Decision: UI rewrite preparation is Phase 4 work (P4 UI PREP), not Phase 3.
- Rationale: Phase 3 stabilizes core + provider contract layer + regression guardrails; UI work is surface/presentation refactor.

### P4 UI PREP Scope Freeze (Consolidated)
- Cross-reference: D-024 “UI thin shell” rule applies. UI may only configure + dispatch + render.
- Allowed UI responsibilities:
  - Collect user inputs and selections for request execution.
  - Dispatch execution to the headless/core surface via the single-entrypoint rule.
  - Entrypoint (exact symbol) = ServerManager imported from src.mcp_server.manager
    - UI proof must match one of:
      - from src.mcp_server.manager import ServerManager
      - src.mcp_server.manager
      - mcp_server.manager
  - Render results, statuses, errors, and usage views returned from core.
  - Maintain ephemeral view state only (loading flags, selection state, expanded/collapsed, etc.).
  - Trigger agent lifecycle and configuration operations only via core services.
- Forbidden UI responsibilities (explicit prohibition list):
  - Provider calls:
    - UI MUST NOT import or call ProviderFactory, ProviderClient, or any provider client modules.
    - UI production path MUST NOT call providers directly.
  - Network/protocol logic:
    - UI MUST NOT implement provider/network protocols or call network libraries for provider execution.
  - Config/credential I/O:
    - UI MUST NOT read/write config files directly.
    - UI MUST NOT read/write credentials, secrets, key material, or keyring storage directly.
  - Streaming:
    - No streaming (SSE/websocket/token streaming) in UI or core unless SSOT explicitly approves.
  - Retry/backoff/fallback:
    - No hidden retry/backoff.
    - No silent fallback to alternate providers/models/paths.
- Single-entrypoint dispatch boundary (thin-shell dispatch rule):
  - UI MUST call exactly one core/headless entrypoint for execution:
    - `src.mcp_server.manager.ServerManager.execute_request_v1(agent_id, prompt)`
  - UI MUST NOT call provider clients or provider factories as part of execution.
- Determinism rules:
  - UI MUST NOT introduce timestamps, randomness, or environment-dependent mutation into request content.
  - Failure behavior MUST be explicit: no silent fallback, and errors must be surfaced (or clearly reported) to the user.
  - Any retry/backoff behavior is forbidden unless explicitly SSOT-approved and explicitly visible (never hidden).

### P4 UI PREP scope (allowed)
1) UI remains a thin shell (inherits D-024 constraints):
   - UI may only configure + dispatch + render.
   - UI production path MUST NOT call provider clients directly.
2) UI → core dispatch boundary:
   - UI MUST call exactly one core/headless entrypoint for execution (e.g., ServerManager / headless API surface).
   - UI MUST NOT import or call ProviderClient/ProviderFactory/any provider client modules.
3) Config I/O:
   - UI MUST NOT read/write config files directly.
   - UI MUST read/write configuration only via core services (stable API surface).
4) State rule:
   - Persistent truth (agent config, usage, status) MUST live in core/DB.
   - UI may hold only ephemeral view state (loading flags, selection state, expanded/collapsed, etc.).
5) UI pattern constraint:
   - UI event handlers MUST remain thin; business logic must not accumulate in view handlers.
   - A ViewModel/Controller-like layer is REQUIRED for UI logic organization (MVVM-like is acceptable; exact framework choice is non-normative).

### P4 UI PREP scope (forbidden)
- No visual redesign/UX expansion beyond minimal functional UI required to prove the architecture boundary.
- No streaming.
- No new runtime dependencies.
- No hidden retry/backoff/fallback anywhere in core or UI.
- No provider-layer changes.

### P4 UI PREP implementation gate (deterministic)
P4 UI PREP is ALLOWED when:
- Phase 3 core/provider-contract baseline is stable enough to proceed (pytest green + no-new-P3-ID drift gates remain enforced), AND
- P3.PR3.I1 may remain BLOCKED (BYOK required); this blocks only online OpenAI feasibility, not UI work, AND
- P3.LG1 is post-technical documentation closeout (not a blocker for UI prep).

### Evidence (required for P4 UI PREP work)
- Evidence root: docs/evidence/<id_timestamp>/
- Required: commands_ran.txt, changed_files.txt, rollback.txt, pytest.txt, pytest_exit_code.txt, anchor_proofs.txt
- Thin-shell enforcement proof: grep_proofs demonstrate UI has zero provider-client callsites on production path.

### Headless Proof Plan (Minimal; boundary gates)
- Gate A (UI provider/network references): `src/ui/**` provider or network references count MUST be 0 (grep-based).
- Gate B (dispatch anchor): anchor proof that UI dispatch reaches the single core/headless entrypoint:
  - UI dispatch call site anchors (file+line) AND
  - core/headless entrypoint anchor (file+line) at `ServerManager.execute_request_v1`.


### Addendum — UI Implementation Stack Lock (Normative)
- **UI implementation stack is locked to:** **Tauri + Svelte (or SvelteKit) + shadcn/ui**.
- **No stack changes** (framework/runtime/UI kit) are permitted **without an explicit SSOT decision update** under this same D-029 section.
- This lock applies to the **UI production path** only and **does not alter** core/headless/provider-agnostic constraints.
- UI must remain a **thin shell**: no provider client imports/calls, no network/protocol logic, no credential/config I/O, no streaming, no hidden retries/backoff.

### Addendum — Navigation Layout (Normative)
- Primary navigation is LEFT SIDEBAR ONLY (no right-side panel/drawer).
- Sidebar supports collapsed icon-rail and expanded label mode.
- Nested rollouts: at most one level deep.
- Documentation (if added later) is a sidebar item that opens a full-page view with search.
- Thin-shell rule remains: all actions dispatch via the single approved Tauri command boundary.

### Addendum — Sidebar IA & Theme Defaults (Normative)
- Theme: default DARK mode (light mode may be added later).
- Sidebar IA (initial, top section): Bridges, Usage, Resilience, Automation/Policies.
- Settings is bottom-pinned in the sidebar (separate bottom section).
- No right-side panel/drawer; left sidebar is the only primary navigation.
- Nested rollouts: at most one level deep.

### Addendum — UI Hard-ban Scan Scope (Normative)
- Hard-ban provider token scans MUST be source-only.
- Exclude build artifacts: node_modules/, target/, src-tauri/target/.
- Exclude binary extensions (.lib, .rlib, .dll, .exe, .pdb, etc.).
- Scan only source/text extensions (e.g., .svelte .ts .js .css .json .rs .toml .md).

### Addendum — Navigation IA v2 (Normative)
- This addendum supersedes prior UI IA addenda under D-029 where conflicts exist.
- Default landing route: Dashboard.
- Sidebar navigation (labels + routes):
  - Dashboard: /dashboard
  - Connections (formerly Bridges): /connections
  - Usage (group): Summary (/usage/summary, default when clicking Usage), History (/usage/history)
  - Policies (group): Persona Lite (/policies/persona), Optimizations (/policies/optimizations)
  - Resilience (group): Budget Guards (/resilience/budget), Interceptors (/resilience/interceptors)
  - Reliability is reserved (not implemented yet).
  - Settings is bottom-pinned: /settings
- Top bar: left shows current page title; right has Help dropdown: Docs, Feedback, About (links or placeholders).
- Footer: Solid Synapse © 2026 + last refresh timestamp (placeholder if not available).
- No right-side navigation panel/drawer. A right column inside a page grid is allowed (it is not a drawer).
- Visual style guidance (non-functional): dark theme; glass/neumorphic accents; hover emphasis; high contrast; system font stack (SF Pro on macOS, Segoe UI on Windows, fallback sans-serif).
- No new UI dependencies are introduced solely for charts/graphics; use placeholders or pure SVG only until SSOT explicitly allows otherwise.

### Addendum — Dashboard Design Language Reference:
- The canonical UI primitive definitions are located in: ui-tauri/src/app.css under: "/* ===== UI Primitives (Dashboard Design Language) ===== */"
- Usage and constraints are documented in docs/UI_STYLE_GUIDE.md.
- New UI pages MUST reuse these primitives and tokens.
- No alternative styling system is allowed.

## D-030 — P5 Remaining Pages Wiring Order Lock

- Date: 2026-02-27
- Decision: After Connections completion (P5.8/P5.9/P5.10), remaining page wiring must proceed in strict page-scoped packages and fixed order.
- Scope: Usage, Policies, Resilience, Settings, Dashboard (non-Connections surfaces).

### Normative rules
- Execution order is fixed:
  1) Usage/Summary
  2) Usage/History
  3) Policies/Persona Lite
  4) Policies/Optimizations
  5) Resilience/Budget Guards
  6) Resilience/Interceptors
  7) Dashboard
  8) Settings
- One package = one page (or one leaf route group) only; no cross-page feature expansion.
- Functional wiring precedes UI polish. Layout/visual refactors are forbidden unless required for functional success/error rendering.
- Thin-shell and single-entrypoint rules from D-024 and D-029 remain mandatory for every package.
- Existing Connections behavior is locked; no opportunistic refactor during non-Connections wiring packages.

### Evidence gate
- Each package must produce docs\evidence\<id_timestamp>\ with: commands_ran.txt, changed_files.txt, rollback.txt, anchor_proofs.txt, ssot_core.sha256.before.txt, ssot_core.sha256.after.txt.
- If UI is touched: ui_static_check.txt is mandatory.
- Provider/network callsite guard (UI production path) must remain zero and be evidenced via grep_proofs.txt.

## D-031 — Budget Enforcement Toggle Deferred; Monitor-Only Lock Continues

- Date: 2026-03-01
- Decision:
  - Budget Guard MUST remain monitor-only for current phase packages.
  - Optional enforcement toggle (block/throttle at threshold) is explicitly deferred.
  - Enforcement toggle is allowed only after a dedicated future package + SSOT FLIP decision + deterministic evidence.
- Constraints:
  - Current runtime behavior MUST NOT block, throttle, or alter request execution from budget thresholds.
  - Dashboard/alerts may render budget warning/critical status only (render-only semantics).
- Next-gate order (normative):
  1) Interceptors runtime effect proof
  2) Optimizations runtime effect proof (context caching + request dedup)
  3) Usage/Connections residual wiring behavior fixes
  4) Settings functional validation
  5) Tooltip/helper evaluation (post-functional gate)
  6) Final copy/meta fixes + UI polish + app icon
