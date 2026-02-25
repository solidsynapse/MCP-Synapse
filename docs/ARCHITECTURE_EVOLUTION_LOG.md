# MCP Router — Architecture Evolution Log (Legacy → Pipeline V1)

> Scope: This log records what changed, why it changed, and what evidence exists, from the point we started enforcing SSOT and routing gates through T0.8.

## SSOT Rules Adopted
- Source of truth: docs/STATUS.md, docs/PLAN.md, docs/TASKS.md, docs/DECISIONS.md
- Conversations are not authoritative; docs + reproducible command outputs are.
- New work proceeds only when the current gate is evidenced.

## Chat Organization Decision (Process)
- PROJECT – ARCHIVE (READ-ONLY): old chat, reference only; no new decisions.
- PROJECT – SUPERVISOR: active execution management (tasks + SSOT updates).
- PROJECT – VERIFIER: verification-only (checks evidence vs. SSOT).
- PROJECT – DEBUGGER: isolated deep dives / experiments (not SSOT).

## Timeline Summary (Stabilization)

### T0.5 — Build gate unblocked
- Packaging verified and produces dist\MCP Router.exe.
- Build uses venv Flet CLI entrypoint and PyInstaller.

### T0.6 — QA gate unblocked
- pytest present in venv and baseline test run passes.

### T0.7 — UI direct provider call removal (production path)
- UI direct VertexAIClient.generate_content exists only in Test action.
- Production MCP request path does not use UI direct provider call.

### T0.8 — V1 call-site + opt-in switch + path logging

Integration point:
- src/mcp_server/agent_server.py → MCPAgentServer._generate_text(prompt)

Routing switch:
- Env var MCP_ROUTER_USE_V1 controls routing
- Default: legacy
- Opt-in: V1 pipeline

Wiring:
- ServerManager injects agent_id and execute_request_v1 into MCPAgentServer

Logging evidence:
- routing=legacy agent_id=... prompt_len=...
- routing=v1 agent_id=... prompt_len=...

## Dependency stabilization

requirements.txt pinned to known-good set:

- flet==0.80.5
- pyperclip==1.11.0

requirements.txt normalized to UTF-8 without BOM.

Flet version evidence uses:
- flet.exe --version
- pip show flet

## Runtime routing proof

Same agent instance, same prompt:

routing=legacy → OUT1: LEGACY_OK  
routing=v1 → OUT2: V1_OK  

This proves routing switch and call-site integration are functional.

## Rollback safety

Unsetting MCP_ROUTER_USE_V1 immediately restores legacy routing.

Legacy provider call path remains intact.

## Current architecture summary

Execution boundary:
- MCPAgentServer._generate_text selects legacy or V1

Orchestration boundary:
- ServerManager owns lifecycle and provides execute_request_v1

Pipeline V1 components:
- ExecutionRequestV1
- PreflightGuardV1
- RouterV1
- ProviderAdapterV1
- ObserverV1

Status: Stabilized with opt-in V1 routing and verified runtime behavior.


## T1.5 — Stage 1 deterministic percent split IMPLEMENTED (D-007)

**What changed**
- Decision point remains single: src/mcp_server/agent_server.py::_generate_text().
- Stage 1 deterministic percent split implemented with precedence:
  MCP_ROUTER_USE_V1 > valid MCP_ROUTER_V1_PCT > legacy default.
- Deterministic bucket rule:
  split_key = agent_id + "\n" + prompt
  ucket = int(sha256(split_key)[:8], 16) % 100
  route to V1 iff ucket < pct.
- Logging schema (no prompt text): routing, pct, bucket, key_type, key_hash_prefix, outcome, agent_id, prompt_len.

**Evidence**
- Pytest PASS: $evRel\pytest_T1.5.txt
- Runtime proof (5 scenarios): $evRel\runtime_tmp_routing_test.txt

**SSOT flips**
- docs/STATUS.md: Stage 1 Activation Standard marked **Implemented** + evidence pointer.
- docs/TASKS.md: T1.5 marked [x] + evidence pointer.
(See $evRel\ssot_flip_snapshot.txt for the exact flipped lines.)
## T1.6 — Stage 1 canary execution (%10) proof PASS

- Objective: Prove Stage 1 percent split behavior at %10 and verify rollback to legacy without UI/server entrypoint.
- Evidence:
  - docs\evidence\T1.6_20260216-042251\verify_T1.6_runtime.txt
  - docs\evidence\T1.6_20260216-042251\runtime_tmp_routing_test_T1.6.txt

- Runtime proof summary (from verify_T1.6_runtime.txt):
  - CASE_count=7
  - routing_v1_count=2
  - routing_legacy_count=5
  - Required log fields observed on routing lines:
    routing, pct, bucket, key_type, key_hash_prefix, outcome, agent_id, prompt_len
  - Rollback proof: CASE=rollback_unset results in routing=legacy with pct=None / bucket=None (legacy_default)

## Stabilization Closeout — Stage 1 Ready (T1.4–T1.6)

**Scope locked:** Stage 1 deterministic percent split (D-007) tek decision point olarak `src/mcp_server/agent_server.py::_generate_text()` içinde.

### What changed
- Stage 1 deterministic percent split implemented (D-007):
  - Precedence: `MCP_ROUTER_USE_V1` > valid `MCP_ROUTER_V1_PCT` > legacy default
  - split_key: `agent_id + "\n" + prompt`
  - bucket: `int(sha256(split_key)[:8], 16) % 100`
  - route_to_v1: `bucket < pct`
- Logging schema (no prompt text):
  - `routing pct bucket key_type=agent_id_prompt key_hash_prefix outcome agent_id prompt_len`

### Evidence packages (authoritative)
- T1.4 SSOT patch + decision-point evidence:
  - `docs/evidence/T1.4_ssot_patch_20260216-004424/`
- T1.5 Implementation proof:
  - `docs/evidence/T1.5_20260216-031619/`
  - `pytest_T1.5.txt`, `runtime_tmp_routing_test.txt`, SSOT flip artifacts
- T1.6 Canary execution (%10) + rollback proof:
  - `docs/evidence/T1.6_20260216-042251/`
  - `runtime_tmp_routing_test_T1.6.txt`, `verify_T1.6_runtime.txt`

### Repro commands (fast)
- Tests:
  - `.\venv\Scripts\python.exe -m pytest -q .\tests\test_stage1_pct_split.py`
- Runtime proof (no server/UI):
  - `.\venv\Scripts\python.exe docs\evidence\T1.6_20260216-042251\tmp_routing_test_T1.6.py`

### Rollback (operational)
- Unset `MCP_ROUTER_USE_V1` and `MCP_ROUTER_V1_PCT` ⇒ legacy default path (log: `routing=legacy`, `outcome=legacy_default`).

## T2.2 Usage → Cost Map Discovery (Evidence Lock)

Scope:
- Map full usage logging surface (manager, pipeline_v1, UI test hook)
- Map token + cost production source (VertexAIClient)
- Confirm absence of budget/limit enforcement layer

Outcome:
- ObserverV1 confirmed as single structured V1 logging surface
- Legacy path still calls Vertex directly
- No enforcement logic exists in repository (verified via search)

Evidence:
docs\evidence\T2.2_usage_cost_map_20260216-103822\

## Phase 1.5 — Provider-agnostic abstraction seam (ProviderFactory + ProviderClient)

**Why**
- Enable adding a second provider adapter without changing MCP server wiring or UI request flow (beyond provider selection/config).
- Preserve Vertex behavior while making ProviderAdapterV1 provider-agnostic.

**What changed**
- New provider abstraction layer:
  - src/providers/base.py: ProviderClient protocol
  - src/providers/factory.py: ProviderFactory registry + vertex default
  - src/providers/vertex_client.py: VertexProviderClient wraps VertexAIClient
- Pipeline V1 now carries provider/model explicitly:
  - ExecutionContextV1 includes provider_id and streaming flag (plumbed)
  - PreflightGuardV1 reads provider_id from agent config, default "vertex"
  - ProviderAdapterV1 uses ProviderFactory instead of constructing VertexAIClient directly
- Deterministic feasibility proof:
  - tests register a FakeProviderClient in ProviderFactory without touching MCP wiring

**Evidence**
- docs\evidence\T1.5_provider_abstraction_20260217-161800\

## Phase 1.5 — Azure OpenAI provider adapter (ProviderFactory üzerinden)

**Why**
- İkinci gerçek provider’ı ProviderFactory seam üzerinden eklemek (UI/MCP wiring değişmeden).

**What changed**
- src/providers/azure_openai_client.py eklendi (non-streaming chat completions; stream=True => NotImplementedError).
- ProviderFactory içine `azure_openai` kaydı eklendi.
- Testler HTTP çağrısını mock’layarak success/error + usage logging’i doğruluyor.

**Evidence**
- docs\evidence\T1.5_azure_openai_20260217-170200\
