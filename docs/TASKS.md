<!-- Naming: MCP Synapse (formerly MCP Router) -->
﻿﻿﻿﻿﻿# TASKS - Stabilization + Pipeline V1

## Conventions
- Each task must include:
  - Evidence required (command/file+line)
  - Done evidence (paste output or line refs)
  - Owner: Builder / Verifier

## P0 - Must for Stabilization Checkpoint
- [x] T0.1 Create SSOT docs (STATUS/PLAN/TASKS/DECISIONS)
  - Evidence required: `tree docs /F`
  - Done evidence: [to fill]
  - Owner: Builder -> Verifier

- [x] T0.2 Identify V1 activation mechanism (toggle/entrypoint/callsite)
  - Evidence required:
    - src grep with line numbers for: execute_request_v1, pipeline_v1 usage, enable/opt-in/rollout keys
    - data/config.json relevant keys (masked values ok)
  - Done evidence: [to fill]
  - Owner: Builder -> Verifier

- [x] T0.3 Capture "V1 used to work, now doesn't" repro + logs
 (evidence: docs\evidence\T0.3_20260215-113316\pytest_env_check.txt + docs\evidence\T0.3_20260215-113316\repro_pytest.txt ; result: pytest=9.0.2 in repo venv, 5 passed; claim not reproduced)
  - Evidence required: exact repro steps + log excerpt (file or console) + timestamp
  - Done evidence: [to fill]
  - Owner: Builder -> Verifier

## P1 - Hardening / Process
- [ ] T1.1 Initialize git repo (optional but recommended for gates)
  - Evidence required: `git init` + `git status`
  - Done evidence: [to fill]
  - Owner: Builder -> Verifier

- [x] T1.2 Define Build command
 (evidence: docs\evidence\T1.2_20260215-114500\build_pack.txt + docs\evidence\T1.2_20260215-114500\dist_exe_stat.txt + docs\evidence\T1.2_20260215-114500\dist_exe_sha256.txt)
  - Evidence required: `python build.py --help` (or working build cmd output)
  - Done evidence: [to fill]
  - Owner: Builder -> Verifier

- [x] T1.3 Define QA command + baseline test set
 (evidence: docs\evidence\T0.3_20260215-113316\pytest_env_check.txt + docs\evidence\T0.3_20260215-113316\repro_pytest.txt ; QA command now in docs/PLAN.md)
- [x] T1.5 Implement Stage 1 deterministic percent split mechanism (D-007) (evidence: docs\evidence\T1.5_20260216-031619\pytest_T1.5.txt + docs\evidence\T1.5_20260216-031619\runtime_tmp_routing_test.txt)
- [x] T1.6 Canary execution (%10) runtime proof + rollback (evidence: docs\evidence\T1.6_20260216-042251\verify_T1.6_runtime.txt + docs\evidence\T1.6_20260216-042251\runtime_tmp_routing_test_T1.6.txt)
  - Evidence required: test runner version + one run output
  - Done evidence: [to fill]
  - Owner: Builder -> Verifier

- [x] T1.7 Provider-agnostic ProviderAdapterV1 seam (factory + client protocol)
  - Acceptance criteria:
    - ProviderAdapterV1 does not construct VertexAIClient directly.
    - Provider selection by provider_id supports "vertex" (default) and a test-injected "fake".
    - Usage rows include provider, model_id, status, latency_ms, request_id (success/error).
    - Observer failures do not break success/error propagation.
  - Evidence: docs\evidence\T1.5_provider_abstraction_20260217-161800\
  - Owner: Builder -> Verifier

- [x] T1.8 Phase 1.5 hardening (config uyumluluğu + factory invariantleri + unit testler)
  - Acceptance criteria:
    - Config uyumluluğu: agent["provider_id"] || agent["provider"] || default "vertex"; agent["streaming"] || agent["stream"] || default False.
    - ProviderFactory: "vertex" default kayıtlı; unknown provider_id => açık ValueError (silent fallback yok).
    - ProviderAdapterV1: ProviderFactory kullanır; pipeline_v1 içinde doğrudan VertexAIClient(...) yok.
  - Evidence: docs\evidence\T1.5_hardening_20260217-163300\
  - Owner: Builder -> Verifier

- [x] T1.9 Azure OpenAI provider adapter (ProviderFactory seam; no UI/MCP wiring changes)
  - Acceptance criteria:
    - ProviderClient: provider_id="azure_openai" ile HTTPS chat completions çalışır (non-streaming).
    - stream=True => açık NotImplementedError (silent fallback yok).
    - API key config’te tutulmaz; keyring’den gelen dosya yolundan okunur (strip).
    - Başarı/hatada Usage DB row yazılır: provider/model_id/status/latency_ms/request_id (+ error_type).
    - Bilinmeyen provider_id => ValueError (mevcut davranış korunur).
  - Evidence: docs\evidence\T1.5_azure_openai_20260217-170200\
  - Owner: Builder -> Verifier

- [x] T1.10 Azure OpenAI UI config surface (provider seçimi + alanlar; secret yok)
  - Acceptance criteria:
    - UI “Add/Edit Bridge” formunda provider: vertex (default) + azure_openai.
    - azure_openai seçilince azure_endpoint + azure_api_version zorunlu; deployment_name opsiyonel.
    - Azure alanları provider vertex iken gizli; config’te mevcut değerler korunur.
    - Config (data/config.json) restart sonrası aynı değerleri yükler; secret/key içeriği config’e yazılmaz.
    - pytest -q PASS.
  - Evidence: docs\evidence\T1.5_azure_ui_config_20260217-184200\
  - Owner: Builder -> Verifier

## P2 - Docs/Encoding hygiene
  - Evidence required: show a line with "opt-in" rendered correctly via a command that specifies encoding
  - Done evidence: [to fill]
  - Owner: Builder -> Verifier

- [ ] Queued — T2.D Hugging Face acceptance gate (evidence: docs\evidence\T2D_hf_acceptance_20260218-051818\)

- [x] T0.4 Integrate Pipeline V1 activation (create an explicit call-site)
  - Historical: execute_request_v1 had no call-sites before T0.8; resolved by T0.8 integration in _generate_text (see Done Evidence - T0.8).
  - Evidence: src/mcp_server/manager.py:173 definition; repo search shows no calls.
  - Evidence required (next): identify the correct integration point in legacy flow (file+line) and add an opt-in switch.
  - Done evidence: file+line for call-site + log output showing V1 path executed.
  - Owner: Builder -> Verifier


### P0 - Blockers identified from Step-5 (detailed)

- [x] T0.5 Build gate unblocked (flet dependency)
  - Evidence required:
    - requirements.txt (or equivalent) shows flet dependency OR documented alternative (file+line).
    - Command: `.\venv\Scripts\python.exe build.py --help` succeeds OR build.py entrypoint documented with proof.
  - Done evidence:
    - Paste command output (success) or definitive documented blocker with error output.
  - Owner: Builder -> Verifier

- [x] T0.6 QA gate unblocked (pytest dependency)
  - Evidence required:
    - pytest installed in venv (command output).
    - Command: `.\venv\Scripts\python.exe -m pytest --version` succeeds.
    - One deterministic test run command output captured (even a minimal subset).
  - Done evidence:
    - Paste version output + one test run output.
  - Owner: Builder -> Verifier

- [x] T0.7 Remove UI direct provider call for production path
  - Evidence required:
    - File+line: UI routes request through ServerManager for production path.
    - File+line: direct `VertexAIClient(...).generate_content(...)` not used on production request path (can remain in debug/test path if documented).
  - Done evidence:
    - File+line diff + runtime log showing ServerManager path executed.
  - Owner: Builder -> Verifier

- [x] T0.8 Add V1 call-site + opt-in switch + path logging
  - Evidence required:
    - file+line: chosen legacy integration point (where legacy calls provider today).
    - file+line: new explicit call-site for `execute_request_v1`.
    - file+line: opt-in selection mechanism (env var OR request flag OR other) implemented and documented.
    - log output: same prompt executed with legacy and with V1 (shows which path ran).
    - legacy path remains available (file+line).
  - Done evidence:
    - Paste file+line refs + pasted logs.
  - Owner: Builder -> Verifier


### Done Evidence - T0.6 (QA gate unblocked)
- pytest installed: .\venv\Scripts\python.exe -m pytest --version -> pytest 9.0.2
- deterministic run: .\venv\Scripts\python.exe -m pytest -q tests\test_pipeline_v1.py -vv -> 5 passed in 4.09s

### Done Evidence - T0.5 (Build gate unblocked)
- requirements.txt: flet==0.80.5 (evidence: requirements.txt line match)
- initial failure: .\venv\Scripts\python.exe -m flet ... failed because flet.__main__ is missing:
  - find_spec('flet.__main__') -> None
- flet CLI verified:
  - .\venv\Scripts\flet.exe --help shows commands including pack
- fix: build.py switched to Flet CLI entrypoint:
  - uses .\venv\Scripts\flet.exe pack src\main.py ...
- additional dependency: PyInstaller installed (6.19.0) to enable flet pack
- verification: .\venv\Scripts\python.exe build.py --help executes packaging and completes:
  - output: Build complete; results in C:\mcp-router\dist
  - produced artifact: dist\MCP Router.exe (legacy filename)
### Done Evidence - T0.7 (UI production path does not call provider directly)
- Direct provider call is only in the Test button flow:
  - UI button binding: src/ui/main_window.py:702-705 (""Test"", on_click=handle_test)
  - Direct call site: src/ui/main_window.py:574-585 (VertexAIClient + generate_content)
- UI folder scan: no other VertexAIClient/generate_content occurrences outside src/ui/main_window.py
- UI uses ServerManager for agent lifecycle/config operations:
  - server_mgr init: src/ui/main_window.py:167
  - start/stop: src/ui/main_window.py:544-547
  - create_agent: src/ui/main_window.py:883-889
  
  
  
  ### Done Evidence - T0.8 (V1 call-site + opt-in switch + path logging)
- Legacy integration point (where legacy calls provider today):
  - MCP tool dispatch calls _generate_text: src/mcp_server/agent_server.py:73-76
  - Legacy path uses VertexAIClient.generate_content: src/mcp_server/agent_server.py:94-104
- V1 call-site + routing selection is implemented inside MCPAgentServer._generate_text:
  - opt-in switch: env var MCP_ROUTER_USE_V1 parsed: src/mcp_server/agent_server.py:79
  - v1 branch: calls self._execute_request_v1(agent_id, prompt) + logs routing=v1: src/mcp_server/agent_server.py:82-85
  - legacy branch retained + logs routing=legacy: src/mcp_server/agent_server.py:94-95
- Wiring (ServerManager → MCPAgentServer) to supply agent_id + execute_request_v1:
  - create_agent instantiation passes agent_id + execute_request_v1: src/mcp_server/manager.py:52-58
  - start_agent instantiation passes agent_id + execute_request_v1: src/mcp_server/manager.py:78-84
- Verification (offline, deterministic; legacy is monkeypatched to avoid real Vertex calls):
  - command:
    - .\venv\Scripts\python.exe -c @" ... (see Step output) "@
  - output (proof of both paths on same prompt):
    - INFO:src.mcp_server.agent_server:routing=legacy agent_id=A prompt_len=4
    - OUT1: LEGACY_OK
    - INFO:src.mcp_server.agent_server:routing=v1 agent_id=A prompt_len=4
    - OUT2: V1_OK




- Agent start + same prompt executed (legacy vs v1) with routing logs captured:
  - Script: tmp_routing_test.py (runs via venv python)
  - Start evidence:
    - INFO:src.mcp_server.manager:Starting agent id=f80e81c2-cb67-4d71-9baf-c74e851ff830
    - INFO:src.mcp_server.agent_server:Starting MCPAgentServer 't' on port 5009
    - INFO:src.mcp_server.agent_server:MCPAgentServer 't' started on port 5009
  - Legacy path evidence (env unset):
    - INFO:src.mcp_server.agent_server:routing=legacy agent_id=f80e81c2-cb67-4d71-9baf-c74e851ff830 prompt_len=4
    - OUT1: LEGACY_OK
  - V1 path evidence (env MCP_ROUTER_USE_V1=1):
    - INFO:src.mcp_server.agent_server:routing=v1 agent_id=f80e81c2-cb67-4d71-9baf-c74e851ff830 prompt_len=4
    - OUT2: V1_OK
  - Stop evidence:
    - INFO:src.mcp_server.manager:Stopping agent id=f80e81c2-cb67-4d71-9baf-c74e851ff830
    - INFO:src.mcp_server.agent_server:MCPAgentServer 't' stopped



- [x] T2.2 Usage → Cost Map Discovery (evidence-only)

- [x] T2.3 Pytest scope fix (exclude docs/evidence from collection)
  - Scope: Ensure QA does not collect tests under docs/evidence; pin collection to src/tests + tests.
  - Change: add pytest.ini (ASCII/no-BOM) with testpaths + python_files.
  - Evidence: docs\evidence\T_QA_PYTEST_SCOPE_20260217-003016\
  - Status: CLOSED (QA collection fixed)
  - Owner: Builder → Verifier


  - Goal: Keep MCP Router provider-agnostic; act as a universal bridge/router for providers that do not offer native IDE MCP.
  - Scope (for this task): define requirements + acceptance criteria only (no implementation).
  - Evidence required: SSOT requirements block + provider adapter interface sketch + rollout/rollback notes (docs-only).
  - Requirements:
    - Must not hardcode any provider/vendor in core routing logic (provider-agnostic by default).
    - Must keep “universal bridge/router” goal explicit (not tied to any single cloud).
    - Must define a stable provider adapter contract (inputs/outputs/errors) as docs-only.
    - Must define how providers are selected (config/env) without assuming any provider-specific flags.
    - Must define how legacy vs V1 routing decisions are logged (no secrets; no prompt text).
    - Must define usage logging surfaces to map (manager, pipeline_v1, UI test hook) as a discovery checklist.
    - Must define token/cost production sources as “provider-reported metrics” (no enforcement requirements).
    - Must define what constitutes “no enforcement layer exists” as a repo search requirement (docs-only).
    - Must define minimum SSOT evidence artifacts expected for discovery tasks (file+line + saved outputs).
    - Must define compatibility constraints: legacy default remains available; opt-in only unless SSOT says otherwise.
    - Must define a rollback note format (what to unset/disable; expected log lines).
    - Must keep scope limited to docs changes (no code changes proposed).
  - Acceptance Criteria:
    - TASKS.md contains a complete T2.4 requirements block (≤12 items) and acceptance block (≤8 items).
    - Requirements contain no provider-specific assumptions or new architecture mandates.
    - Requirements do not propose enforcement/limits/budget logic; discovery-only wording is used.
    - Rollout / Rollback notes exist and are actionable (docs-only).
    - Evidence folder exists with a linenum dump of the modified TASKS lines.
    - Evidence folder includes a file list of written evidence artifacts.
  - Rollout / Rollback notes:
    - Rollout is SSOT-gated; follow incremental rollout principle (opt-in → 10% → 50% → 100%) when implemented.
    - Do not change defaults: keep legacy routing as default unless SSOT explicitly flips it.
    - Rollout control uses existing SSOT activation knobs (env/config) only; no provider-specific toggles.
    - Rollback is “disable routing opt-in” and confirm logs show legacy routing (no prompt/secrets in logs).
    - If provider-specific behavior is needed, document it under provider adapter docs, not core routing requirements.
    - This is a docs-only task; rollback can be achieved by reverting TASKS.md edits.
  - Owner: Supervisor → Builder → Verifier

## P3 - Usage (Operational Metrics)
- [x] T3.1 Usage: operational metrics + filtering + KPI correctness (DB as single source)
  - Evidence: docs\evidence\T3.1_20260217-095736\
  - Owner: Builder

- [x] Phase 2 / D-004 verification
  - Status: **DONE**
  - Evidence pointers: docs\evidence\D004_verify_20260219-050337\ (pytest.txt, pytest_exit_code.txt, grep_proofs.txt, commands_ran.txt, changed_files.txt, rollback.txt)

---

## Done — Phase 1.5 Flip SSOT

- Date: 2026-02-18
- Evidence: docs/evidence/T1.5_flip_ssot_20260218-000100/
- Completed:
  - D-010 amended (Azure provisioning constraint; UI-external)
  - D-011 added (ProviderClient canonical output + annotation boundary)
  - D-012 added (Streaming determinism gate; Vertex stream=True raises)
  - D-013 added (No silent swallow — scoped)
  - Code fixes:
    - Vertex provider: stream=True => NotImplementedError
    - UI refresh_loop: removed silent swallow (visible error)
    - CredentialManager.delete_credential: removed silent pass (visible warning)
  - Tests: pytest -q PASS

## Done — MVP.1 Release gate (Vertex + Azure)

- Evidence root: docs/evidence/MVP_release_gate_20260218_050710/
- Acceptance (normative):
  - Production UI path must not call providers; UI must only configure and dispatch.
  - Core must remain deterministic: no hidden branching, no silent fallback, no retries/backoff in core.
  - Core must remain provider-agnostic; provider-specific branching must live in provider adapter/factory.
  - Network calls (if any) must be explicit opt-in and user-visible; failures must surface explicitly.
- Evidence (required to mark Done):
  - checklist.md (finalized and checked)
  - evidence_plan.md
  - rollback_plan.md
  - smoke_tests.ps1 run output captured (no interactive steps)
  - pytest -q output captured


- Date: 2026-02-20
- Smoke tests: PASS (evidence: docs\evidence\MVP1_smoke_tests_20260220-064633\smoke_tests.out.txt + smoke_tests_exit_code.txt)
- MCP probe: PASS (evidence: docs\evidence\MVP1_smoke_run_20260220-064637\mcp_probe\initialize.* + tools_list.* + tools_call.* + probe.out.txt + probe.err.txt)
## Done — T2.A Bedrock acceptance gate (docs-only)

- Date: 2026-02-18
- Evidence root: docs/evidence/T2_bedrock_acceptance_20260218-043014/
- Acceptance (normative):
  - No provider calls in UI production path; UI must only configure and dispatch.
  - Core routing must remain provider-agnostic; provider-specific branching must live in provider adapter/factory.
  - Any real network calls for Bedrock must be explicit opt-in (no silent fallback, no hidden retries).
  - Failures must be explicit and user-visible (no swallow, no “best effort” behavior).
- Evidence (required):
  - acceptance_criteria.md
  - config_fields.md
  - credential_provisioning.md
  - grep_baseline.txt
  - rollback_plan.md

## Done — T2.C Bedrock real call gate (post-MVP) (superseded by T2.E)

- Evidence: docs/evidence/T2C_bedrock_realcall_gate_20260218_050723/
- Superseded by T2.E (explicit opt-in) — Evidence root: docs/evidence/T2E_bedrock_realcall_20260218_053156/


## Done — T2.E Bedrock real-call gate (post-MVP, explicit opt-in)

- Date: 2026-02-18
- Evidence: docs/evidence/T2E_bedrock_realcall_20260218_053156/
- Completed:
  - D-015 aligned: boto3/botocore approved; real calls are behind explicit gate (bedrock_enable_network).
  - Non-streaming determinism preserved: stream=True => NotImplementedError.
  - No silent fallback; tests + rollback captured in evidence pack.

## Done — T2.F Hugging Face start authorization (docs-only)

- Evidence root: docs/evidence/T2F_hf_start_auth_20260218-054605/

## Done — T2.G Hugging Face provider (Inference API over HTTP, non-streaming)

- Date: 2026-02-18
- Evidence: docs/evidence/T2G_hf_provider_20260218-055322/
- Completed:
  - ProviderClient implemented via stdlib HTTP only (no new deps).
  - Determinism preserved: no retry/backoff, no silent fallback, errors surface explicitly.
  - Streaming disabled: stream=True => NotImplementedError (per D-012).
  - Token via credentials_path file (UTF-8, strip(); empty => hard error) (per D-016).
  - ProviderFactory registration exists: provider_id=huggingface.

## Done — T2.H Hugging Face real-call gate (explicit opt-in)

- Date: 2026-02-18
- Evidence: docs/evidence/docs\evidence\T2H_hf_realcall_gate_20260218-060300/
- Completed:
  - D-017 aligned: real calls are behind explicit gate (hf_enable_network: true).
  - Determinism preserved: no retry/backoff, no silent fallback, explicit errors.
  - Streaming remains disabled: stream=True => NotImplementedError (D-012).




## Done — T0.3.P0 UI crash + destructive action correctness

- Date: 2026-02-18
- Evidence: docs/evidence/T0.3_triage_20260218-080141/
- Completed:
  - Fixed Test button crash (Flet ElevatedButton label API; no AttributeError).
  - Fixed Help link warning (no un-awaited launch_url coroutine).
  - Fixed Clear History Cancel (non-destructive; Cancel emphasized).
## Done — T0.3.P1 Bridges list ordering (new bridge appears at top)

- Evidence: docs/evidence/T0.3P1_ui_triage_20260218-082900/
- Scope:
  - Fix ordering in config storage layer (no UI hack/sort).
  - Evidence must show agents.insert(0, agent) (or equivalent) in ConfigManager.add_agent.
  - pytest PASS.

## Done — T0.3.P2 ProbeAgent stale status reconcile (UI refresh port probe)

- Date: 2026-02-18
- Evidence: docs/evidence/T0.3.P2_20260218-085543/
- Completed:
  - UI refresh reconciles status=running via local port probe (127.0.0.1:port).
  - If port closed: status corrected to stopped (config + in-memory UI).
  - No silent swallow (prints deterministic note on edge cases).

## Done — T2.X MCP Tool Discovery probe + raw dump (headless)

- Evidence root: docs/evidence/T2X_mcp_tool_discovery_probe_20260220-044918/

- Goal: Produce raw JSON-RPC request/response dumps for initialize, 	ools/list, 	ools/call against the running local MCP server.
- Constraints:
  - Headless only (no UI).
  - No new “harness surface” beyond committed repo command/script.
- Evidence (required):
  - docs/evidence/<ID_timestamp>/mcp_probe/initialize.request.json
  - docs/evidence/<ID_timestamp>/mcp_probe/initialize.response.json
  - docs/evidence/<ID_timestamp>/mcp_probe/tools_list.request.json
  - docs/evidence/<ID_timestamp>/mcp_probe/tools_list.response.json
  - docs/evidence/<ID_timestamp>/mcp_probe/tools_call.request.json
  - docs/evidence/<ID_timestamp>/mcp_probe/tools_call.response.json
  - commands_ran.txt
  - pytest.txt + pytest_exit_code.txt (if applicable)


## Done — T2.Y Remove or justify duplicate tree `src/mcp_server/1`

- Problem: src/mcp_server/1/agent_server.py is a divergent duplicate of src/mcp_server/agent_server.py (determinism/maintenance risk).
- Requirement: repo MUST contain a single canonical implementation; duplicates MUST be removed or explicitly justified by SSOT decision.
- Evidence:
  - fc/diff proof showing divergence
  - import proof that runtime uses canonical file
  - changed_files.txt + rollback.txt

  - Evidence root: docs\evidence\T2Y_remove_dup_tree_20260220-054120


## Done — T3.A Post-Phase-2 cleanup inventory (no deletions yet)
- Evidence root: docs\evidence\T3A_cleanup_inventory_20260220-054743\cleanup_inventory\
- Inventory findings (summary; docs-only):
  - UI entrypoint: src\main.py (flet)
  - Headless entrypoints: src\tests\test_phase1.py, src\tests\test_phase2.py, src\tests\mcp_sse_probe.py
  - UI-shared utilities used by tests: src\ui\usage_*.py (do NOT delete in cleanup batch without explicit plan)
  - Duplicate filename hotspots: manager.py (2), __init__.py (8), generated .pyc files present
- Candidate delete list (docs-only; no deletions yet):
  - __pycache__ / *.pyc (generated artifacts) — delete only in a bounded deletion batch with pytest PASS evidence
  - Investigate duplicate manager.py (confirm role/scope before any deletion)

- Goal: Produce an evidence-backed inventory of:
  - dead/unused files, duplicate modules, unused entrypoints
  - UI-only code that must remain untouched until UI phase
  - legacy vs v1 paths and their current usage
- Constraints:
  - NO code deletion in this task (inventory only).
  - No new dependencies.
- Evidence (required):
  - docs/evidence/<ID_timestamp>/cleanup_inventory/
    - tree.txt
    - grep_entrypoints.txt
    - import_map.txt (runtime import proofs)
    - candidate_delete_list.txt (docs-only list; no deletions)
  - commands_ran.txt + changed_files.txt + rollback.txt

## Done — T3.B Safe code deletion batch-1 (bounded; evidence-gated)
- Batch-1 delete scope (bounded; generated artifacts only):
  - Delete: src\**\__pycache__\
  - Delete: src\**\*.pyc
  - Do NOT delete any .py sources in this batch.
- Verification:
  - pytest -q PASS after deletion
  - evidence root contains: dir_listing_before.txt, dir_listing_after.txt, pytest.txt, pytest_exit_code.txt

- Goal: Delete only items explicitly listed in T3.A candidate_delete_list.txt and re-validated as unused.
- Constraints:
  - Bounded scope: delete list must be small and reviewed via evidence.
  - Must NOT touch UI refactor (UI out of scope unless explicitly opened later).
- Evidence (required):
  - fc/diff proofs (removed files)
  - pytest PASS
  - changed_files.txt + rollback.txt
  - docs/evidence/<ID_timestamp>/cleanup_delete_batch1/

## Done — T3.C Legacy path retirement decision gate (docs-only)
- Evidence root: docs\evidence\G_D022_add_legacy_retirement_policy_20260220-055132\

- Goal: Define explicit SSOT decision for retiring any legacy path (no silent removal).
- Constraints:
  - Decision only; implementation happens in a separate task after approval.
- Evidence (required):
  - docs/DECISIONS.md update (new D-0xx)
- Evidence root: docs\evidence\T3B_delete_generated_artifacts_20260220-054924\
  - rationale + compatibility notes
  - evidence root with commands_ran.txt + rollback.txt






## Phase 3 — UI Shell/Rewrite (Historical carry-over; pre-pivot)

- Policy reminder: Phase 2 forbids UI code changes (see D-019).
- Items below are historical carry-over; do NOT reopen UI work under Phase 2.

> NOTE: This completed item is historical carry-over; it does NOT authorize UI work inside Phase 2 (D-019).

## Done — T0.3.P3 UI smoke/layout stabilization

- Date: 2026-02-20
- Evidence: docs/evidence/T0.3.P3_ui_smoke_20260220-065459/
- Scope:
  - Modal sizing: “Keyboard Shortcuts” + “Test Result” dialogs (no oversize).
  - Usage top bar alignment: filters left, actions right; stable layout.
  - KPI cards padding/alignment improvements (no redesign).
  - Help menu: Landing page / Wiki / Report issue (await-safe open).
- Non-goals:
  - No provider/routing changes, no new dependencies, no refactors.
- Acceptance / Evidence required:
  - grep_proofs.txt + triage_notes.md + screenshots (or manual capture steps) + pytest PASS.
- Completed:
  - Constrained modal sizing for “Keyboard Shortcuts” and “Test Result”.
  - Stabilized Usage top bar alignment (filters left, actions right; button sizing).
  - Improved KPI card padding/alignment (consistent spacing, no edge-touch).
  - Replaced single Help link with 3-option Help menu (await-safe URL open; no warning).

## Post-Phase-2 backlog (non-binding; not Phase-2 gates)
- NOTE: Phase 2 is DONE. Items below are backlog and must not be treated as Phase-2 remaining work.

- [x] T2.1 Normalize docs encoding display issues (UTF-8 handling)
  - Evidence: docs\evidence\T2.1_docs_encoding_20260220-233021\ (utf8_proof.txt + TASKS before/after + hashes)

### T2.1 — Docs encoding hygiene (UTF-8 proof; docs-only)

- Goal:
  - Ensure SSOT docs render UTF-8 characters deterministically and that evidence commands always specify encoding.
- Non-goals:
  - No content rewrite; no refactors; no new dependencies.
- Required proof (minimum):
  - A command that uses Get-Content -Encoding UTF8 and shows an 'opt-in' line rendered correctly.
- Policy (going forward):
  - SSOT/evidence reads MUST use -Encoding UTF8 for docs/*.md.

- [x] T2.4 Universal bridge / multi-provider routing core (backlog)
  - Evidence: docs/evidence/T_FEAT_FEAS_20260220_120000/ (feature_matrix.md + ssot_extracts.txt + src_map.txt)

### T2.4 — Universal bridge / multi-provider routing core (docs-only definition)

- Goal:
  - Define a provider-agnostic core routing contract that can bridge non-native MCP providers to IDEs without changing UI.
- Non-goals (for this task):
  - No implementation.
  - No new dependencies.
  - No streaming enablement.
  - No provider-specific branching added to core.
- Requirements (normative; ≤12):
  1) Core (router/manager/pipeline) MUST remain provider-agnostic.
  2) Provider-specific behavior MUST live behind adapter/factory seams.
  3) Determinism MUST be preserved: no hidden retry/backoff, no silent fallback.
  4) UI production path MUST NOT call providers; UI is configure+dispatch+render only.
  5) Network calls MUST be explicit opt-in per provider (gated), with user-visible failure modes.
  6) Method/contract compliance MUST be provable headless-first (pytest/probe/smoke evidence packs).
  7) Legacy path MUST remain until an explicit SSOT retirement decision (D-022).
  8) No new harness surface may be invented without explicit SSOT decision.
- Acceptance criteria (≤8):
  1) TASKS.md contains this complete T2.4 definition block.
  2) Definition contains no provider-locked architecture mandates (keeps options open).
  3) Evidence pack is created with before/after snapshots + rollback + hashes.
- Evidence required:
  - docs/evidence/<ID_timestamp>/ (commands_ran.txt, changed_files.txt, rollback.txt, TASKS.before.md, TASKS.after.md, TASKS.sha256.txt)


### P3.TS1 — UI thin shell compliance (D-024)
- Goal: Remove provider client imports/calls from UI production path; UI dispatches to headless/core only.
- Evidence: docs\evidence\G_P3_thinshell_boundary_probe_20260221-003424\
- Proofs:
  - grep_proofs_ui_provider_refs.after.count.txt => MATCHES=0
  - dispatch_chain_proof.after.txt => UI -> ServerManager (file+line)
- Notes: Keep Phase 3 gated by D-024 (no streaming, no new deps, no provider calls in UI).
### P3.BE1 — Backend health proof (pytest + D-024 safe)
- Goal: Prove backend/core stability via pytest (green) while preserving D-024 thin shell (no provider calls in UI).
- Evidence:
  - docs\evidence\G_P3_backend_health_20260221-014056\  (initial run: failed, recorded)
  - docs\evidence\G_P3_backend_health_fix_importerror_20260221-014205\  (fix: pytest_exit_code.after.txt => 0)
  - docs\evidence\G_P3_thinshell_boundary_probe_20260221-003424\  (post-fix grep_proofs_ui_provider_refs.postfix.count.txt => MATCHES=0)
- Exit:
  - pytest_exit_code.after.txt == 0
  - D-024 grep count remains MATCHES=0
### P3.BE2 — Backend regression guardrails (pre-UI rewrite)
- Goal: Lock backend determinism + provider-agnostic core before UI rewrite starts.
- Scope:
  - Keep D-024 gates: no streaming, no new deps, no silent fallback/retry/backoff in core.
  - Core (router/manager/pipeline) stays provider-agnostic (no provider-specific branching).
- Proof (evidence pack required):
  - pytest_exit_code == 0 (full test suite or agreed subset)
  - targeted grep proofs:
    - core has no provider-specific branching additions
    - UI production path keeps provider-client refs at MATCHES=0
- Evidence: docs\evidence\G_P3_backend_regression_guardrails_<timestamp>\

### P3.BE3 — Backend health proof: single-command reproducible runner
- Goal: Make backend proof sustainable: one command produces a complete deterministic evidence pack (headless-only).
- Constraints: no new runtime deps; PS 5.1 compatible; deterministic; no provider/network calls; no streaming; no silent retry/backoff.
- Deliverable:
  - A repo script runnable as a single command that:
    - runs pytest headlessly
    - runs core-only forbidden-string checks (provider-specific strings must not be in core)
    - writes a complete evidence folder under `docs/evidence/<ID_timestamp>/` containing:
      - commands_ran.txt
      - changed_files.txt
      - rollback.txt
      - pytest.txt
      - pytest_exit_code.txt
      - anchor_proofs.txt
      - grep_proofs.txt
  - Runner behavior:
    - Deterministic PASS/FAIL for the same repo state.
    - Fail-fast on any step failure (no hidden retry/fallback/backoff).
    - Evidence folder is always written (even on FAIL), and contains the required files.
- Evidence: docs\evidence\G_P3_backend_health_runner_<timestamp>\
### P3.BE2A — Core provider-agnostic compliance: remove provider-specific tool routing from core
- Problem: src\mcp_server\agent_server.py contains provider-specific tool name/branching ("call_google_vertex_ai", "[VERTEX AI GATEWAY]").
- Goal: Core must be provider-agnostic (no provider-specific branching in core). Tool naming/routing must not hardcode a provider.
- Constraints: no new runtime deps; no streaming; keep determinism (no hidden retry/backoff).
- Evidence (current violation): docs\evidence\G_P3_core_provider_specific_violation_20260221-024237\
- Exit proof:
  - targeted grep in src\mcp_server\agent_server.py shows no "call_google_vertex_ai" / "[VERTEX AI GATEWAY]"
  - pytest -q exit code 0
### P3.BE4 — Headless backend smoke (pre-UI rewrite)
- Goal: Prove headless backend can start, respond to MCP probe, and write/read usage DB without UI involvement.
- Constraints: no streaming; no new deps; deterministic; UI must not call providers.
- Related evidence: docs\evidence\G_P3_backend_health_runner_20260221-034734\
- Evidence pack:
  - commands_ran.txt
  - changed_files.txt
  - rollback.txt
  - ssot_core.sha256.txt
  - smoke_run.txt (start server + probe)
  - pytest_exit_code.txt == 0 (or documented smoke-only subset)
- Evidence: docs\evidence\G_P3_headless_backend_smoke_<timestamp>\
### P3.F1 — Copy Config UX (contract-first; headless proof)
- Goal: Lock the “copy config” contract and prove it headlessly (no UI dependency).
- Contract (normative):
  - Input:
    - `agent`: dict from existing config store (no new config keys)
  - Required fields:
    - `agent["name"]`: non-empty string after `strip()`
    - `agent["port"]`: int-like value
  - Output:
    - A deterministic MCP client config snippet for connecting to the local agent server:
      - `{"mcpServers": { <agent_name>: { "url": "http://localhost:<port>/sse" }}}`
    - Exported JSON text MUST be UTF-8 encoded and stable across runs for the same input:
      - stable key order (`sort_keys=True`)
      - stable indentation (`indent=2`)
  - Safety:
    - Output MUST NOT include secrets or credential paths.
    - Output MUST NOT include provider configuration fields (project_id/location/model_id/keys/etc).
  - Determinism:
    - For identical `agent` content, exported JSON text is byte-for-byte identical.
    - No timestamps, randomness, environment-dependent behavior, or implicit normalization (other than `agent["name"].strip()`).
  - Error behavior:
    - Missing/empty `name` or missing `port` raises `ValueError` (no silent fallback).
  - Prohibited behavior:
    - MUST NOT call providers or attempt network access.
    - MUST NOT stream.
- Evidence pack (when implemented):
  - commands_ran.txt
  - changed_files.txt
  - rollback.txt
  - pytest.txt
  - pytest_exit_code.txt
  - anchor_proofs.txt
- Evidence: docs\evidence\G_P3_copy_config_contract_<timestamp>\

### P3.F2 — CSV Export (headless) implement + evidence (align D-### CSV determinism)
- Goal: Implement CSV export via core services (headless) consistent with DECISIONS “CSV export determinism”.
- Constraints: no new deps; deterministic column order; export uses same filtered dataset as table.
- Evidence pack:
  - commands_ran.txt
  - pytest_exit_code.txt == 0
  - export.csv (sample export)
  - ssot_core.sha256.txt
- Evidence: docs\evidence\G_P3_csv_export_headless_<timestamp>\
- Contract details (normative):
  - Input: agent_id (or bridge_id) selected from config store.
  - Output: a deterministic MCP server config snippet (text) with:
    - stable key order
    - UTF-8 encoding
    - NO secrets (only credential file paths or keyring refs as already defined by SSOT)
  - Proof:
    - headless command produces copy_config.out.txt
    - repeat run produces identical output (byte-equal) for same input
### P3.F3 — Budget Guard (monitor-only) contract + headless report
- Decision ref: D-025 (monitor-only; no enforcement).
- Goal: Deterministically compute per-agent daily totals (cost_usd, tokens_in/out if present) and emit a warning report when thresholds are exceeded.
- Contract (normative):
  - Inputs:
    - agent_id (required)
    - window: day (UTC or local — must be specified and consistent)
    - thresholds: max_cost_usd (optional), max_tokens_in (optional), max_tokens_out (optional)
  - Outputs:
    - report JSON/text with totals + threshold status (OK/WARN), no blocking behavior
  - Data source: local Usage DB rows (D-004 contract fields).
- Constraints:
  - No new runtime deps
  - No streaming
  - MUST NOT block/alter execution (monitor-only)
- Evidence pack (when implemented):
  - commands_ran.txt
  - pytest_exit_code.txt == 0
  - budget_report.out.txt (sample)
  - ssot_core.sha256.txt
  - grep proof: no code path raises/blocks on budget thresholds
- Evidence: docs\evidence\G_P3_budget_guard_monitor_<timestamp>\
- Window definition: day = UTC day (00:00:00Z..23:59:59Z) based on D-004 timestamp (UTC).
### P3.PR1 — Google AI Studio provider (contract-first; docs-only)
- Goal: Define a deterministic, provider-agnostic integration contract for Google AI Studio as a ProviderClient via ProviderFactory seam.
- Constraints:
  - No new runtime deps without explicit SSOT decision.
  - No streaming (unless SSOT-approved).
  - No silent fallback/retry/backoff.
  - Core remains provider-agnostic; no provider-specific branching in core.
- Contract (normative):
  - provider_id: google_ai_studio
  - Secret handling: MUST follow existing CredentialManager semantics (no secrets in config; file-path or keyring ref only).
  - Output: MUST follow D-011 canonical output keys (text required; tokens/cost optional; pipeline keys not overwritten).
  - Network: default mode must be explicit opt-in if real calls are introduced.
- Evidence (when implemented):
  - pytest_exit_code == 0
  - headless MCP probe PASS (initialize/tools/list/tools/call) for this provider
  - determinism grep proof (no hidden retry/backoff/fallback)
- Evidence: docs\evidence\G_P3_aistudio_contract_<timestamp>\
- Policy update (normative):
  - Google AI Studio is **deferred to post-MVP**.
  - Implementation is **BLOCKED** until written ToS clarification/approval is captured in docs/evidence (per D-026).
### P3.PR2 — Ollama provider (contract-first; docs-only)
- Goal: Define Ollama provider contract surface (offline-first) via ProviderFactory seam (provider-agnostic core).
- Constraints:
  - No new runtime deps.
  - No streaming unless SSOT-approved (default non-streaming).
  - No silent fallback/retry/backoff.
- Contract (normative):
  - provider_id: ollama
  - Request shape (normative):
    - Target endpoint (future online mode): `POST <base_url>/v1/chat/completions`
    - Body keys (minimum):
      - `model`: `model_id` (string)
      - `messages`: `[{ "role": "user", "content": <prompt> }]`
      - `temperature`: `0` (determinism baseline)
    - Encoding: UTF-8 JSON.
  - Output (normative; provider-agnostic):
    - MUST follow D-011 canonical output keys:
      - `text` required (string)
      - `tokens_input`, `tokens_output`, `cost_usd` optional
  - Offline test mode (normative for Phase 3):
    - MUST provide an offline-only fake/stub path that produces deterministic outputs for fixed inputs.
    - MUST NOT make any network calls in tests (network guard required).
    - No streaming.
  - Error behavior (normative):
    - In online mode (future): fail-fast on unreachable; surface explicit error; no retries.
    - In offline mode: errors are deterministic and explicit (ValueError/RuntimeError); no retries.
- Evidence (when implemented):
  - pytest_exit_code == 0
  - offline contract tests PASS (network guard; determinism)
- Evidence: docs\evidence\G_P3_ollama_contract_<timestamp>\
### P3.PR2 — Ollama feasibility smoke (headless; non-streaming; no deps)
- Goal: Prove we can talk to a local Ollama HTTP endpoint deterministically (non-streaming) via ProviderFactory seam.
- Constraints:
  - No new runtime deps.
  - No streaming (use non-streaming endpoint/mode only).
  - No silent fallback/retry/backoff.
  - BYOK/local-only baseline applies (D-026).
- Contract (minimal):
  - provider_id: ollama
  - base_url is operator-provided (default: http://127.0.0.1:11434)
  - model_id is operator-provided (no hardcoded model list)
  - Fail-fast if Ollama not reachable; error surfaces explicitly.
- Evidence pack (PASS requirements):
  - commands_ran.txt
  - pytest_exit_code.txt == 0
  - ollama_probe.out.txt (response contains text)
  - grep proof: no streaming usage
  - ssot_core.sha256.txt
- Evidence: docs\evidence\G_P3_ollama_feasibility_<timestamp>\
- I1a: Ollama unreachable behavior (fail-fast; deterministic)
- Goal: When Ollama is not running/reachable, the probe must fail fast with an explicit error and no retries.
- Evidence: docs\evidence\G_P3_ollama_feasibility_20260221-063541\ (EXIT_CODE=1 + WinError 10061)
- Result: PASS when evidence shows explicit connection-refused error and no streaming.

- I1b: Ollama reachable smoke (requires local Ollama running)
- Goal: When Ollama is running locally, probe returns text (non-streaming).
- Preconditions: port 11434 LISTENING and /api/tags reachable.
- Evidence: docs\evidence\G_P3_ollama_reachable_<timestamp>\
- Result: TBD
### P3.LG1 — Final legal documentation pack (post-technical; docs-only)
- Goal: Produce a strict legal/compliance documentation bundle before release, aligned with D-026 baseline.
- Scope (docs-only):
  - Terms of Use / User Acknowledgement (BYOK + local-only; no pooling; no SaaS proxy)
  - Provider compliance matrix (per provider: allowed usage, blocked usage, ToS gate status, written approvals if required)
  - Disclaimer & limitation of liability draft (jurisdiction-neutral wording; reviewed externally)
  - Privacy note (local-first; no prompt/response payload storage; what is logged)
- Constraints:
  - Must not contradict SSOT decisions (D-026, D-025, D-024, D-004).
  - Any “provider enabled” status must reference evidence roots and ToS gate artifacts.
- Evidence:
  - docs\evidence\G_P3_legal_pack_<timestamp>\ (draft files + review checklist)
### P3.PR3 — OpenAI provider (contract-first; docs-only; BYOK/local-only)
- Decision ref: D-026 (BYOK + local-only; no pooling; no SaaS proxy).
- Constraints: no new runtime deps; no streaming unless SSOT-approved; no silent fallback/retry/backoff.
- Contract (normative):
  - provider_id: openai
  - Auth: user-supplied credential only (file-path/keyring ref); secrets never stored in config.
  - Request shape (normative):
    - Target endpoint (future online mode): `POST <base_url>/v1/chat/completions`
    - Body keys (minimum):
      - `model`: `model_id` (string)
      - `messages`: `[{ "role": "user", "content": <prompt> }]`
      - `temperature`: `0` (determinism baseline)
    - Encoding: UTF-8 JSON.
  - Output (normative; provider-agnostic):
    - MUST follow D-011 canonical output keys:
      - `text` required (string)
      - `tokens_input`, `tokens_output`, `cost_usd` optional
  - Offline test mode (normative for Phase 3):
    - MUST provide an offline-only fake/stub path that produces deterministic outputs for fixed inputs.
    - MUST NOT make any network calls in tests (network guard required).
    - No streaming.
  - Network: explicit enable flag if real calls introduced; fail-fast otherwise.
- Evidence (when implemented): pytest PASS + offline contract tests PASS (network guard; determinism).
- Evidence: docs\evidence\G_P3_openai_contract_<timestamp>\

### P3.PR4 — Anthropic provider (contract-first; docs-only; BYOK/local-only)
- Decision ref: D-026 (BYOK + local-only; no pooling; no SaaS proxy).
- Constraints: no new runtime deps; no streaming unless SSOT-approved; no silent fallback/retry/backoff.
- Contract (normative):
  - provider_id: anthropic
  - Auth: user-supplied credential only (file-path/keyring ref); secrets never stored in config.
  - Request shape (normative):
    - Target endpoint (future online mode): `POST <base_url>/v1/messages`
    - Body keys (minimum):
      - `model`: `model_id` (string)
      - `max_tokens`: int (determinism baseline; caller-provided)
      - `messages`: `[{ "role": "user", "content": <prompt> }]`
      - `temperature`: `0` (determinism baseline)
    - Encoding: UTF-8 JSON.
  - Output (normative; provider-agnostic):
    - MUST follow D-011 canonical output keys:
      - `text` required (string)
      - `tokens_input`, `tokens_output`, `cost_usd` optional
  - Offline test mode (normative for Phase 3):
    - MUST provide an offline-only fake/stub path that produces deterministic outputs for fixed inputs.
    - MUST NOT make any network calls in tests (network guard required).
    - No streaming.
  - Network: explicit enable flag if real calls introduced; fail-fast otherwise.
- Evidence (when implemented): pytest PASS + offline contract tests PASS (network guard; determinism).
- Evidence: docs\evidence\G_P3_anthropic_contract_<timestamp>\

### P3.PR5 — Groq provider (contract-first; docs-only; BYOK/local-only)
- Decision ref: D-026 (BYOK + local-only; no pooling; no SaaS proxy).
- Constraints: no new runtime deps; no streaming unless SSOT-approved; no silent fallback/retry/backoff.
- Contract (normative):
  - provider_id: groq
  - Auth: user-supplied credential only (file-path/keyring ref); secrets never stored in config.
  - Request shape (normative):
    - Target endpoint (future online mode): `POST <base_url>/v1/chat/completions`
    - Body keys (minimum):
      - `model`: `model_id` (string)
      - `messages`: `[{ "role": "user", "content": <prompt> }]`
      - `temperature`: `0` (determinism baseline)
    - Encoding: UTF-8 JSON.
  - Output (normative; provider-agnostic):
    - MUST follow D-011 canonical output keys:
      - `text` required (string)
      - `tokens_input`, `tokens_output`, `cost_usd` optional
  - Offline test mode (normative for Phase 3):
    - MUST provide an offline-only fake/stub path that produces deterministic outputs for fixed inputs.
    - MUST NOT make any network calls in tests (network guard required).
    - No streaming.
  - Network: explicit enable flag if real calls introduced; fail-fast otherwise.
- Evidence (when implemented): pytest PASS + offline contract tests PASS (network guard; determinism).
- Evidence: docs\evidence\G_P3_groq_contract_<timestamp>\
### P3.PR3.I1 — OpenAI feasibility smoke (headless; non-streaming; no deps)
- Decision ref: D-026 (BYOK + local-only; no pooling; no SaaS proxy).
- Goal: Prove we can call OpenAI over HTTPS deterministically (non-streaming) via ProviderFactory seam.
- Constraints:
  - No new runtime deps.
  - No streaming.
  - No silent fallback/retry/backoff.
- Contract (minimal):
  - provider_id: openai
  - base_url optional (default official)
  - model_id operator-provided (no hardcoded model list)
  - Auth via CredentialManager file-path/keyring ref (no plaintext in config).
  - Fail-fast if unreachable/unauthorized; error surfaces explicitly.
- Evidence pack (PASS requirements):
  - commands_ran.txt
  - pytest_exit_code.txt == 0
  - openai_probe.out.txt (response contains text)
  - grep proof: no streaming usage
  - ssot_core.sha256.txt
- Evidence: docs\evidence\G_P3_openai_feasibility_<timestamp>\
### P3.PR3 — Offline fake-provider proof (no network; high-confidence core test)
- Decision ref: D-008 (tests can inject a deterministic fake provider via ProviderFactory registry).
- Goal: Prove the ProviderFactory seam + Pipeline V1 core wiring behaves correctly without any network calls or API keys.
- Scope:
  - Implement a deterministic FakeOpenAIProviderClient (or generic FakeProviderClient) used ONLY in tests/tools.
  - Register/unregister in ProviderFactory within the test to avoid global pollution.
  - Exercise the same execution surface used by headless flows (V1 execution path), asserting:
    - canonical output keys (D-011) preserved
    - pipeline reserved keys added correctly (status/error_type/latency_ms/provider/model_id/request_id)
    - determinism: same inputs => byte-identical outputs (or hash-identical normalized output)
    - no retries/backoff/streaming paths touched
- Constraints:
  - No new runtime deps.
  - No streaming.
  - No network traffic (prove via grep or by design: fake provider does not import urllib/requests).
- Evidence pack (PASS requirements):
  - pytest_exit_code.txt == 0 (must include the new offline test)
  - grep proof: test fake provider has no network imports/usages
  - ssot_core.sha256.txt
- Evidence: docs\evidence\G_P3_openai_offline_fake_provider_<timestamp>\
### P3.PR4 — Offline fake-provider proof (Anthropic) (no network; high-confidence core test)
- Decision ref: D-008 (tests can inject a deterministic fake provider via ProviderFactory registry).
- Goal: Same as PR3.I0, but using provider_id anthropic_fake to prove provider-agnostic seam behavior.
- Scope/Constraints/Evidence: identical to PR3 offline fake-provider I0 (no deps, no streaming, no network, determinism hash).
- Evidence: docs\evidence\G_P3_anthropic_offline_fake_provider_<timestamp>\

### P3.PR5 — Offline fake-provider proof (Groq) (no network; high-confidence core test)
- Decision ref: D-008 (tests can inject a deterministic fake provider via ProviderFactory registry).
- Goal: Same as PR3.I0, but using provider_id groq_fake to prove provider-agnostic seam behavior.
- Scope/Constraints/Evidence: identical to PR3 offline fake-provider I0 (no deps, no streaming, no network, determinism hash).
- Evidence: docs\evidence\G_P3_groq_offline_fake_provider_<timestamp>\
### P3.PR7 — LM Studio provider (contract-first; docs-only; local-only)
- Decision ref: D-026 (BYOK + local-only; no pooling; no SaaS proxy).
- Goal: Add LM Studio as a local provider alternative (OpenAI-compatible endpoints).
- Contract (normative):
  - provider_id: lmstudio
  - base_url default: http://127.0.0.1:1234/v1 (operator override allowed)
  - Non-streaming only unless SSOT approves streaming.
  - Auth: no key required by default for local server; if provided, treat as user-supplied (never store plaintext in config).
  - Local-only default: MUST bind to localhost; serving on LAN is opt-in and must be explicitly acknowledged (security).
  - Request shape (normative; OpenAI-compatible):
    - Target endpoint (future online mode): `POST <base_url>/chat/completions`
    - Body keys (minimum):
      - `model`: `model_id` (string)
      - `messages`: `[{ "role": "user", "content": <prompt> }]`
      - `temperature`: `0` (determinism baseline)
    - Encoding: UTF-8 JSON.
  - Output contract: MUST follow D-011 canonical output keys.
  - Offline test mode (normative for Phase 3):
    - MUST provide an offline-only fake/stub path that produces deterministic outputs for fixed inputs.
    - MUST NOT make any network calls in tests (network guard required).
    - No streaming.
- ToS gate: record LM Studio App Terms reference; any ambiguity => contract-only until clarified.
- Evidence (when implemented):
  - headless probe PASS (models + chat/completions)
  - no streaming grep proof
  - pytest PASS
- Evidence: docs\evidence\G_P3_lmstudio_contract_<timestamp>\
### P3.PR7 — LM Studio reachable smoke (headless; non-streaming; no deps)
- Goal: Prove LM Studio local server (OpenAI-compatible) is reachable and returns text deterministically (non-streaming).
- Constraints: no new deps; no streaming; no retry/backoff/fallback; localhost-only default (D-026).
- Contract (minimal):
  - provider_id: lmstudio
  - base_url default: http://127.0.0.1:1234/v1 (override allowed)
  - model_id operator-provided (discover via /v1/models)
- Evidence pack (PASS):
  - lmstudio_probe.out.txt (EXIT_CODE=0 + text)
  - grep_no_streaming.proof.txt (STREAM_KEY_MATCHES=0; SSE_MATCHES=0)
  - pytest_exit_code.txt == 0
  - ssot_core.sha256.txt
- Evidence: docs\evidence\G_P3_lmstudio_feasibility_<timestamp>\

## Phase 3 Roadmap (Next)
> This section is normative for planning only (SSOT-core). Do not treat MASTERPLAN as binding.

1) I1: LM Studio reachable smoke (headless; non-streaming; no deps)
2) P3.P1/P3.P2/P3.P3 — Premium contract-first (docs-only) + headless proof runners later
3) P3.PR3.I1 — OpenAI online feasibility (requires BYOK key; otherwise stays blocked)
4) UI rewrite prep → UI (thin shell; last major step before release)
   - P4.1 docs contract updated
     - Evidence required: docs\evidence\P4_1_verify_<timestamp>\commands_ran.txt + changed_files.txt + rollback.txt + anchor_proofs.txt + grep_proofs.txt + ssot_core.sha256.txt
5) Documentation closeout:
   - P3.LG1 — Final legal documentation pack (docs-only)
   - User Guide (how to install, configure bridges, troubleshoot, privacy/compliance notes)
### P3.P1 — Interceptor (JSON syntax repair) (contract-first; docs-only)
- Goal: Define a deterministic “repair layer” contract for malformed tool/function payloads, without changing core determinism.
- Constraints: no streaming; no new deps unless SSOT-approved; must be deterministic; must not modify provider output keys (D-011 boundary).
- Output: repair report must be explicit (what changed, why) and never silent.
- Evidence (when implemented): headless test vectors + pytest PASS + determinism proof.
- Evidence: docs\evidence\G_P3_interceptor_contract_<timestamp>\

### P3.P2 — Persona Lite (system prompt injection) (contract-first; docs-only)
- Goal: Define deterministic rule injection contract that does not corrupt IDE context; opt-in per agent.
- Constraints: no silent injection; must be visible/configurable; no streaming; no new deps unless SSOT-approved.
- Contract (normative):
  - Inputs:
    - `agent`: existing agent config dict (no new config keys introduced by this feature)
    - `prompt`: user prompt string (unchanged source-of-truth)
  - Persona source:
    - Persona text is read from `agent["persona"]` when present and a non-empty string after `strip()`.
    - If `agent["persona"]` is missing or empty/whitespace, behavior is a strict no-op.
    - If `agent["persona"]` is present but not a string, raise `ValueError("invalid_persona")`.
  - Output (internal request assembly, prior to provider call):
    - `messages`: list of `{role, content}` dicts.
      - No persona: `[{ "role": "user", "content": prompt }]`
      - With persona: `[{ "role": "system", "content": persona }, { "role": "user", "content": prompt }]`
    - `provider_prompt`: rendered string used for current provider clients (which accept a single `prompt: str`).
      - No persona: `provider_prompt == prompt`
      - With persona: `provider_prompt == persona + "\\n\\n" + prompt`
  - Injection precedence:
    - Persona MUST be injected as the first message (`role="system"`).
    - The user prompt MUST remain the final message (`role="user"`).
    - No other messages are introduced by Persona Lite.
  - Determinism:
    - Given identical `agent` content and identical `prompt`, `messages` and `provider_prompt` are byte-for-byte identical across runs.
    - No timestamps, randomness, environment-dependent behavior, or implicit normalization.
  - Error behavior:
    - Invalid persona type: raise `ValueError("invalid_persona")`.
    - Persona absent/empty: strict no-op; do not log, mutate, or annotate provider outputs.
- Evidence (when implemented): offline tests showing stable injected prompt shape + pytest PASS.
- Evidence: docs\evidence\G_P3_persona_lite_contract_<timestamp>\

### P3.P3 — Context caching (contract-first; docs-only)
- Goal: Define provider-agnostic caching contract (capability-detected; never assumed).
- Constraints: no provider-specific branching in core; no streaming; no hidden fallback.
- Contract (normative):
  - Scope:
    - Cache applies ONLY to internal request preparation artifacts produced before provider invocation (e.g., assembled `messages` list and `provider_prompt` string).
    - Cache does NOT store provider responses and does NOT skip provider invocation.
  - Inputs:
    - `agent`: existing agent config dict
    - `prompt`: user prompt string
  - Cache enablement (no new config keys):
    - Cache is enabled ONLY when Persona Lite is configured under the existing agent structure:
      - `agent["persona"]` exists and is a non-empty string after `strip()`.
    - Otherwise cache is disabled and behavior is a strict no-op relative to current behavior.
  - Cache key:
    - Key MUST be derived deterministically from:
      - `agent_id` (from `agent["id"]` when present; otherwise empty string)
      - `persona_clean` (the `strip()`ped persona string)
      - `prompt` (exact string)
    - Key derivation MUST be order-stable and collision-resistant for common inputs (e.g., length-prefixed or unambiguous delimiter).
  - Cache value:
    - Cached value is the assembled request artifacts:
      - `messages`: list of `{role, content}` dicts
      - `provider_prompt`: rendered string passed to current provider clients
  - Eviction/limits:
    - In-memory process-local cache with a fixed max entry limit (LRU eviction).
    - Eviction MUST be deterministic given identical call sequences.
  - Output:
    - Returned assembled artifacts MUST be identical on cache hit vs cache miss for the same inputs.
  - Determinism:
    - For identical `agent` content and identical `prompt`, outputs MUST be byte-for-byte identical.
    - Cache may affect performance but MUST NOT affect content.
  - Error behavior:
    - If persona is present but invalid type, propagate `ValueError("invalid_persona")` (from Persona Lite contract).
    - Cache internal errors (unexpected exceptions) MUST fall back to a deterministic cache-disabled path (no partial state exposure).
- Evidence (when implemented): contract tests with fake providers; metrics show cost/token deltas without storing payload.
- Evidence: docs\evidence\G_P3_context_caching_contract_<timestamp>\

  - P4.2 UI thin-shell guard gates (deterministic):
    - Keep a repo-level grep gate: src/ui/** provider/network references MUST remain 0 (exclude .pyc + __pycache__).
    - Keep a dispatch anchor gate: UI must reference the single core/headless entrypoint (e.g., ServerManager).
    - Evidence required: docs\evidence\P4_2_<timestamp>\ with commands_ran.txt, changed_files.txt, rollback.txt, grep_proofs.txt, anchor_proofs.txt, ssot_core.sha256.txt (+ pytest.txt only if run).

  - P4 UI PREP exit criteria satisfied: P4.1/P4.2/P4.3 PASS
    - Evidence: docs\evidence\P4_1_verify_20260222-120400
    - Evidence: docs\evidence\P4_2_guard_run_20260222-121431
    - Evidence: docs\evidence\P4_3_strict_guard_run_refined_20260222-122356

### P4 UI milestones (evidence-indexed) — DONE
- P4_UI_IMPL_1 FULL PASS (evidence: docs\evidence\P4_UI_IMPL_1_full_verify_20260222-232005)
- P4_UI_IMPL_2 PASS (evidence: docs\evidence\P4_UI_IMPL_2_reconcile_20260223-010254)
- P4_UI_IMPL_3 PASS (evidence: docs\evidence\P4_UI_IMPL_3_verify_sourcesonly_20260223-040024)
- P4_UI_IMPL_4 PASS (evidence: docs\evidence\P4_UI_IMPL_4_verify_20260223-042533)
- P4_UI_IMPL_5 PASS (evidence: docs\evidence\P4_UI_IMPL_5_verify_20260223-050723)
- P4_UI_IMPL_6 PASS (evidence: docs\evidence\P4_UI_IMPL_6_verify_20260223-054458)
- P4_UI_IA_V2 applied PASS (evidence: docs\evidence\P4_UI_IA_V2_verify_20260223-093211)
- P4_UI_WIRE_1 PASS (evidence: docs\evidence\P4_UI_WIRE_1_verify_20260223-204650)
- P4_UI_WIRE_2 PASS (evidence: docs\evidence\P4_UI_WIRE_2_verify_20260223-210228)
- UI smoke run PASS (routes 9/9) (evidence: docs\evidence\P4_UI_smoke_run_20260223-213051)


## P5 — Wiring (packaged, stoppable)

Goal: Move from UI-only stubs to deterministic thin-shell wiring where UI = form state + dispatch + render, and mapping/validation/persistence lives in core.

Hard constraints (inherit SSOT D-024/D-029):
- UI production path MUST NOT call provider clients directly.
- No provider/network/protocol logic in UI.
- Core remains provider-agnostic; no provider-specific branching in core.
- No new runtime dependencies; no streaming.

Packages (each is independently committable + verifiable):

- P5.3 UI session state (UI-only)
  - Make toggles/presets/session state stable across in-app navigation (in-memory only).
  - Evidence: `npm run check` exit 0 + UI network/provider scan 0 hits.

- P5.4 Persisted config (core)
  - “New Connection → Create” dispatches to core.
  - Core writes config to the approved store via core surface (no UI file writes).
  - UI only collects fields and renders results/errors.

- P5.5 Preflight validation (core)
  - Validate required fields + basic path existence without any provider calls.
  - UI renders structured errors from core.

- P5.6 Copy Config canonicalization (core)
  - UI “Copy Config” obtains canonical JSON from core (removes UI hardcode).
  - Evidence: docs\evidence\P5_6_COPY_CONFIG_VERIFY_20260226-024338 (core deterministic canonical output) + docs\evidence\P5_6_COPY_UI_ENABLE_20260227-070630 (row Copy enabled; Start/Stop/Delete gates unchanged; ui check PASS).

- P5.7 Test (dry-run)
  - Bind existing dry_run dispatch to persisted config; still zero provider/network calls.
  - Evidence: deterministic dry_run result returned through single-entrypoint.

- P5.8 Connections lifecycle wiring (core)
  - Enable Connections Start/Stop/Delete through the single core/headless dispatch boundary.
  - UI remains thin-shell: collect + dispatch + render only; no provider/network/protocol logic in UI.
  - Core must expose deterministic ops: connections.start, connections.stop, connections.delete with explicit error payloads.
  - No hidden retry/backoff/fallback; no streaming; no new runtime dependencies.
  - Evidence (PASS, package slices): docs\evidence\P5_8A_DELETE_WIRING_20260227-073626 (connections.delete core+dispatcher+UI confirm flow) + docs\evidence\P5_8B_START_STOP_WIRING_20260227-074309
(connections.start/stop wiring + UI start/stop enable + ui check PASS + grep guard PASS) + docs\evidence\P5_8C_DELETE_ROW_UNGATE_20260227-075607 (UI row Delete ungated; delete dispatch unchanged; busy-safe +
explicit banner preserved; ui check PASS).

- P5.9 Connections runtime orchestration (core)
  - Start/Stop must control real connection runtime lifecycle (not status-only).
  - Start must provision/activate runtime for a persisted connection and expose reachable SSE endpoint.
  - Stop must terminate/deactivate runtime and release endpoint.
  - Keep thin-shell rule: UI only dispatches + renders; no provider/network/protocol logic in UI.
  - No hidden retry/backoff/fallback; deterministic error payloads required.
  - Evidence (PASS): docs\evidence\P5_9_TASK_PACKAGE_ADD_20260227-091534 (task package add) + docs\evidence\P5_9A_RETRY_CORE_ONLY_V2_20260227-092552 (core-only runtime start/stop with SSE reachable-after-start and unreachable-after-stop; UI unchanged) + docs\evidence\INCIDENT_START_TEST_SPLIT_FIX_V1_20260227-100837 (dry_run project_id payload fix) + docs\evidence\P5_9A_DRYRUN_PROJECTID_REGRESSION_TEST_20260227-101255 (regression test PASS) + docs\evidence\P5_9_REAL_SURFACE_SMOKE_V1_20260227-101926 (real-surface smoke PASS) + docs\evidence\FULL_OWNERSHIP_STOP_WIN87_FIX_20260227-120009 (Windows stop WinError 87 fix) + docs\evidence\ENCODING_CHARMAP_FIX_20260227-123051 (runtime charmap encoding fix) + docs\evidence\DRYRUN_BANNER_COMPACT_V1_20260227-123854 (dry-run banner compact) + docs\evidence\P5_9_RUNTIME_ENCODING_CLOSURE_AUDIT_20260227-124419 (closure audit PASS).

- Acceptance criteria:
  - For a started connection, `connections.list` returns runtime-reflective status and endpoint metadata.
  - SSE probe to reported endpoint succeeds after Start and fails after Stop (evidence-based).
  - `connections.start/stop` return explicit success/error codes/messages for: missing id, not found, start failed, stop failed.
  - Existing P5.8 behavior remains intact for Delete/Copy/Test UX and guards.

- Evidence required:
  - docs\evidence\P5_9_<timestamp>\
  - commands_ran.txt, changed_files.txt, rollback.txt, anchor_proofs.txt, ssot_core.sha256.before.txt, ssot_core.sha256.after.txt
  - runtime_probe.txt (start->SSE reachable, stop->SSE unreachable)
  - list_before_after.json, start_stop_outputs.json
  - ui_static_check.txt (if UI touched in later execution package)

- Acceptance criteria:
  - Row actions Start/Stop/Delete dispatch through single-entrypoint path and return explicit success/error.
  - Start/Stop/Delete UI actions are busy-safe (no double-dispatch) and render explicit error messages.
  - Existing P5.6 Copy and P5.7 Test behavior remains unchanged.
  - UI provider/network callsite guard remains 0 hits on production path.

- Evidence required:
  - docs\evidence\P5_8_<timestamp>\
  - commands_ran.txt, changed_files.txt, rollback.txt, anchor_proofs.txt, ssot_core.sha256.before.txt, ssot_core.sha256.after.txt
  - grep_proofs.txt (UI provider/network references = 0)
  - ui_static_check.txt (npm run check)
  - test/smoke outputs (if run) + exit codes

- P5.10 IDE tool response contract hardening (core)
  - Ensure successful MCP tool calls return deterministic content payload (not health-only text).
  - Ensure failure payloads expose explicit error code/message and remain UTF-8 safe on Windows runtime paths.
  - Preserve thin-shell + single-entrypoint: UI dispatch/render only; no provider/network/protocol logic in UI.
  - No hidden retry/backoff/fallback; deterministic failures only.
  - Evidence (PASS): docs\evidence\P5_10_TASK_PACKAGE_ADD_20260227-195403 (task package add) + docs\evidence\P5_10A_MCP_CONTENT_ERROR_CONTRACT_20260227-195727 (MCP success/error contract hardening + regression tests + raw shape proofs) + docs\evidence\P5_10A_CLOSURE_AUDIT_20260227-203253 (closure audit PASS).

- Acceptance criteria:
  - A successful tool call returns non-empty MCP `content` with at least one `type: "text"` item.
  - Raw response evidence shows MCP `content/text` shape for at least one Vertex-backed connection.
  - Failure-path evidence shows explicit `error.code` + `error.message` (no generic unknown/charmap crash).
  - Existing P5.8/P5.9 Start/Stop/Delete/Copy/Test behavior remains unchanged.

- Evidence required:
  - docs\evidence\P5_10_<timestamp>\
  - commands_ran.txt, changed_files.txt, rollback.txt, anchor_proofs.txt, ssot_core.sha256.before.txt, ssot_core.sha256.after.txt
  - tool_call_success_raw.json, tool_call_error_raw.json
  - mcp_content_shape_proof.txt
  - ui_static_check.txt (only if UI is touched in later execution slices)

- P5.11 Remaining pages wiring rollout (page-scoped, no-polish-first)
  - Goal: Complete functional wiring for non-Connections pages in deterministic, page-by-page packages.
  - Connections page is baseline-complete; do not refactor/re-scope Connections while executing P5.11 packages.
  - UI polish/layout changes are out of scope unless strictly required to render functional success/error state.
  - Preserve thin-shell + single-entrypoint constraints from D-024/D-029 for all packages.

- Execution order (normative):
  - P5.11A Usage / Summary wiring
  - P5.11B Usage / History wiring
  - P5.11C Policies / Persona Lite wiring
  - P5.11D Policies / Optimizations wiring
  - P5.11E Resilience / Budget Guards wiring
  - P5.11F Resilience / Interceptors wiring
  - P5.11G Dashboard read-model wiring
  - P5.11H Settings wiring

- Evidence (PASS slices):
  - P5.11A Usage / Summary wiring: docs\evidence\P5_11A_USAGE_SUMMARY_WIRING_20260227-205310
  - P5.11B Usage / History wiring: docs\evidence\P5_11B_USAGE_HISTORY_WIRING_20260227-210405
  - P5.11C Policies / Persona Lite wiring: docs\evidence\P5_11C_POLICIES_PERSONA_WIRING_20260227-211026
  - P5.11D Policies / Optimizations wiring: docs\evidence\P5_11D_POLICIES_OPTIMIZATIONS_WIRING_20260227-211824
  - P5.11E Resilience / Budget Guards wiring: docs\evidence\P5_11E_RESILIENCE_BUDGET_WIRING_20260227-213627
  - P5.11F Resilience / Interceptors wiring: docs\evidence\P5_11F_RESILIENCE_INTERCEPTORS_WIRING_20260227-214919
  - P5.11G Dashboard wiring: docs\evidence\P5_11G_DASHBOARD_WIRING_20260227-220945
  - P5.11H Settings wiring: docs\evidence\P5_11H_SETTINGS_WIRING_20260227-223113
  - P5.11 Closure PASS (full-surface regression): docs\evidence\P5_11_FULL_SURFACE_REGRESSION_20260227-224528
  - P5.11 PRS live validation matrix PASS (Policies/Resilience/Settings get/set + persistence + validation contract): docs\evidence\P5_11_PRS_LIVE_VALIDATION_MATRIX_V1_RETRY_20260228-085227
  - P5.11 PRS persona runtime binding + live confirm PASS (runtime persona prompt injection verified with signature marker [PERSO_TEST_OK]; IDE tool restart required for fresh runtime pickup): docs\evidence\P5_11PRS_PERSONA_RUNTIME_BINDING_20260301-001548
  - P5.11 PRS manual live sweep NARROW (functional persistence PASS; unresolved UX/data-parity findings queued as F-PRS-01..08): docs\evidence\P5_11_PRS_MANUAL_SWEEP_EVIDENCE_INDEX_20260228-092749

- Package scope rule (all P5.11x packages):
  - One page (or one route group leaf) per package; no cross-page feature expansion.
  - Keep unrelated files unchanged; if drift is detected, classify as KEEP/DISCARD/DEFER before edits.
  - Placeholder/stub labels must be updated in the same package once that page becomes wired.

- Acceptance criteria (each P5.11x package):
  - Page actions dispatch via approved core/headless boundary and render explicit success/error messages.
  - No provider/network/protocol logic in UI production path.
  - Deterministic offline behavior for validation paths where applicable (no hidden retry/backoff/fallback).
  - Existing P5.8/P5.9/P5.10 behavior remains unchanged.

- Evidence required (each P5.11x package):
  - docs\evidence\P5_11x_<timestamp>\
  - commands_ran.txt, changed_files.txt, rollback.txt, anchor_proofs.txt, ssot_core.sha256.before.txt, ssot_core.sha256.after.txt
  - page_smoke.txt (+ exit code) and ui_static_check.txt (if UI touched)
  - grep_proofs.txt (UI provider/network callsites guard)

- P5.12 Post-P5.11 stability + contract audit hardening
  - Objective: After P5.11 closure PASS, harden cross-page state/contract stability with deterministic audit-first slices.
  - Objective: Keep thin-shell and single-entrypoint boundaries unchanged while reducing regression risk in wired pages.

- Scope IN:
  - Cross-page contract consistency checks for wired P5.11 routes (dispatcher/core response envelopes and validation errors).
  - Deterministic regression/audit packages and evidence index updates following P5.11 closure baseline.
  - Baseline reference: docs\evidence\P5_11_FULL_SURFACE_REGRESSION_20260227-224528.

- Scope OUT:
  - New provider/network/protocol logic in UI.
  - Non-deterministic runtime coupling, hidden retry/backoff/fallback additions.
  - Unscoped refactors outside explicitly approved package slices.

- Acceptance:
  - Wired P5.11 pages retain explicit success/error contract behavior under repeated regression runs.
  - Validation error paths remain explicit (`error.code` + `error.message`) and deterministic.
  - No scope drift outside per-package allowlist and no regression to P5.11 closure baseline.

- Evidence required:
  - docs\evidence\P5_12_<timestamp>\
  - commands_ran.txt, changed_files.txt, rollback.txt, anchor_proofs.txt, ssot_core.sha256.before.txt, ssot_core.sha256.after.txt
  - regression_matrix.md, dispatcher_contract_matrix.json, ui_static_check.txt

- Evidence (PASS slices):
  - P5.12B Active Bridges running semantic + stop/start parity PASS: docs\evidence\ACTIVE_BRIDGES_STOP_PARITY_V2_20260228-052546
  - P5.12B scope lock PASS: docs\evidence\DASHBOARD_POLISH_P6_SCOPE_LOCK_20260228-063115
  - P5.12B refresh + Usage/History Clear parity probe PASS (no-edit): docs\evidence\DASHBOARD_REFRESH_AND_HISTORY_CLEAR_PARITY_PROBE_20260228-063153
  - P5.12C dashboard parity apply PASS (fresh reconfirmation complete): docs\evidence\DASHBOARD_POLISH_P7_APPLY_20260228-063404; docs\evidence\P5_12C_REVALIDATE_SUPERVISOR_20260301-224444
  - P5.12C recent requests cap PASS (fresh reconfirmation complete): docs\evidence\DASHBOARD_POLISH_P8_RECENT12_20260228-065147; docs\evidence\P5_12C_REVALIDATE_SUPERVISOR_20260301-224444
  - P5.12C refresh feedback PASS (current behavior re-anchored and live reconfirmed): docs\evidence\DASHBOARD_POLISH_P8B_REFRESH_FEEDBACK_20260228-065232; docs\evidence\P5_12C_A1_REFRESH_FEEDBACK_REVALIDATE_20260301-235523; docs\evidence\P5_12C_1315_LIVE_20260302-030853
  - P5.12C final clear parity check PASS (fresh parity reconfirmation complete): docs\evidence\HISTORY_CLEAR_PARITY_FINAL_CHECK_20260228-065511; docs\evidence\P5_12C_REVALIDATE_SUPERVISOR_20260301-224444; docs\evidence\P5_12C_A1317_NO_STATIC_SEED_REVALIDATE_20260302-001319

- P5.12A Normative Slice (scope-locked, evidence-only)
  - Objective: Lock P5.12 baseline by running deterministic read/contract audit without changing product or SSOT files.

- Scope IN (exact):
  - Route load/read smoke for wired pages under `ui-tauri/src/routes/`.
  - Dispatcher contract checks using only these ops:
    - `dashboard.get_state`
    - `connections.list`
    - `connections.schema_hint`
    - `connections.preflight` (validation-path payload only)
    - `usage.recent`
    - `policies.persona.get_state`
    - `policies.optimizations.get_state`
    - `resilience.budget.get_state`
    - `resilience.interceptors.get_state`
    - `settings.get_state`
  - Evidence artifact generation under `docs\evidence\P5_12A_<timestamp>\`.

- Scope OUT (exact):
  - Any product file edit.
  - Any SSOT file edit.
  - Any dispatcher op that mutates persisted state or runtime:
    - `*.set_state`, `connections.create`, `connections.start`, `connections.stop`, `connections.delete`, `connections.copy_config`, `connections.dry_run`.
  - Any provider/network runtime orchestration changes.

- Allowed files (exact):
  - Read-only inputs:
    - `ui-tauri/src/routes/dashboard/+page.svelte`
    - `ui-tauri/src/routes/connections/+page.svelte`
    - `ui-tauri/src/routes/usage/summary/+page.svelte`
    - `ui-tauri/src/routes/usage/history/+page.svelte`
    - `ui-tauri/src/routes/policies/persona/+page.svelte`
    - `ui-tauri/src/routes/policies/optimizations/+page.svelte`
    - `ui-tauri/src/routes/resilience/budget/+page.svelte`
    - `ui-tauri/src/routes/resilience/interceptors/+page.svelte`
    - `ui-tauri/src/routes/settings/+page.svelte`
    - `tools/headless_dispatch_v1.py`
    - `src/mcp_server/manager.py`
    - `src/config/manager.py`
  - Writable outputs:
    - `docs\evidence\P5_12A_<timestamp>\**`

- Acceptance (deterministic, testable, evidence-bound):
  - `changed_files.txt` must be `NO_CHANGES_APPLIED`.
  - Contract matrix must show:
    - all listed get/list ops return `ok:true`,
    - validation-path response contains explicit `error.code` and `error.message`.
  - UI static check must report `exit_code=0`.
  - Any scope drift or forbidden op usage is `BLOCKER`.

- P5.12B Dashboard refresh + Usage clear parity probe (evidence-only)
  - Objective: Prove current behavior of global refresh and Usage/History Clear against dashboard live state, without product edits.
  - Scope IN:
    - Anchor extraction and runtime probe for:
      - `ui-tauri/src/routes/+layout.svelte` (global refresh trigger path)
      - `ui-tauri/src/routes/usage/history/+page.svelte` (clear action path)
      - `ui-tauri/src/routes/dashboard/+page.svelte` (dashboard state load path)
      - `tools/headless_dispatch_v1.py` (available usage ops contract)
    - Evidence generation only under `docs\evidence\P5_12B_<timestamp>\`.
  - Scope OUT:
    - Any product file edit.
    - Any SSOT file edit.
  - Acceptance:
    - Root-cause class for refresh/clear parity is explicit and anchor-backed.
    - `changed_files.txt` is `NO_CHANGES_APPLIED`.
    - Probe outputs include before/after payload snapshots for `usage.recent` and `dashboard.get_state`.

- P5.12C Dashboard polish apply (refresh parity + clear parity + micro polish)
  - Objective: Apply minimum-scope fixes from P5.12B findings while preserving thin-shell, single-entrypoint, and existing dashboard data binding.
  - Scope IN:
    - Global refresh propagation (header refresh must trigger dashboard/usage reload paths).
    - Usage/History Clear parity (clear action must clear usage source-of-truth, not only local table view).
    - Dashboard micro-polish slices (chart parity, alerts density, table readability/pagination) without changing provider/network logic.
  - Allowed files (exact):
    - `ui-tauri/src/routes/+layout.svelte`
    - `ui-tauri/src/routes/dashboard/+page.svelte`
    - `ui-tauri/src/routes/usage/summary/+page.svelte`
    - `ui-tauri/src/routes/usage/history/+page.svelte`
    - `tools/headless_dispatch_v1.py`
  - Scope OUT:
    - `src/mcp_server/*`, `src/config/*`, provider clients, runtime orchestration logic.
    - Any non-dashboard/non-usage route edits.
  - Acceptance:
    - Header refresh updates timestamp and causes dashboard/usage pages to re-fetch in the same app session.
    - Usage/History Clear removes rows from usage source-of-truth and dashboard reflects cleared state after refresh/navigation.
    - No reintroduction of static demo seed data.
    - `ui_static_check.txt` exit code is `0`.

- P5.12D Dashboard micro-polish backlog (non-blocking, post-audit)
  - Objective: Track remaining visual refinement items after parity closure without blocking release.
  - Scope IN:
    - KPI typography and icon semantics polish.
    - Cost Trend axis/point readability polish.
    - Cost Breakdown legend density/layout polish.
    - Quick Health Alerts single-item composition polish.
    - Recent Requests table spacing/column density/footer integration polish.
    - Top Expensive Requests label semantics polish.
  - Scope OUT:
    - Any provider/network/protocol logic changes.
    - Any runtime orchestration or dispatcher contract change unrelated to presentation.
  - Acceptance:
    - Each slice is packaged independently with before/after visual evidence and `ui_static_check` PASS.
    - No regression to P5.12C parity guarantees (refresh propagation + usage clear parity + recent12 + refresh feedback).
  - Evidence required:
    - `docs\evidence\P5_12D_<timestamp>\`
    - `commands_ran.txt`, `changed_files.txt`, `anchor_proofs.txt`, `summary.txt`, `ui_static_check.txt`
  - Evidence indexed (PASS):
    - `docs\evidence\P5_12D_SLICE_01_KPI_TYPO_ICON_POLISH_20260228-070644\`
    - `docs\evidence\P5_12D_SLICE_02B_TREND_VISUAL_TUNING_20260228-071905\`
    - `docs\evidence\P5_12D_SLICE_02C_TREND_XAXIS_READABILITY_20260228-072458\`
    - `docs\evidence\P5_12D_SLICE_03_BREAKDOWN_INFORMATION_ARCH_20260228-072632\`
    - `docs\evidence\P5_12D_SLICE_02D_03B_GRAPH_COMPOSITION_FINETUNE_20260228-074811\`
    - `docs\evidence\CHART_ALIGNMENT_FINAL_POLISH_PIE_UP20_20260228-075720\`

- P5.13 Dashboard residual polish plan (post-P5.12 closure)
  - Objective: Complete remaining dashboard UX polish items without changing wiring/data contracts.
  - Scope IN:
    - Quick Health Alerts low-density composition refinement (single alert visual balance).
    - Recent Requests table density/column balance/footer cohesion polish.
    - Top Expensive Requests semantic label polish (human-readable primary label strategy).
    - Global visual consistency pass for dashboard micro-typography/spacing.
  - Scope OUT:
    - Any provider/runtime/network/protocol logic change.
    - Any dispatcher/manager contract change.
    - Any non-dashboard route edit.
  - Allowed files (exact):
    - `ui-tauri/src/routes/dashboard/+page.svelte`
  - Acceptance:
    - Dashboard live data binding remains intact (no static seed reintroduction).
    - Each polish slice has independent evidence and `ui_static_check` PASS.
    - No regression to P5.12C parity guarantees.
  - Evidence required:
    - `docs\evidence\P5_13_<timestamp>\`
    - `commands_ran.txt`, `changed_files.txt`, `anchor_proofs.txt`, `summary.txt`, `ui_static_check.txt`
  - Evidence indexed (PASS):
    - `docs\evidence\P5_13A_ALERT_THRESHOLD_AND_SPACING_TUNE_20260228-081116\`
    - `docs\evidence\P5_13A_ALERT_CONTEXT_TRIM_20260228-081411\`
    - `docs\evidence\P5_13B_RECENT_TABLE_EQUAL_SPACING_CENTER_ALIGN_20260228-082716\`
    - `docs\evidence\P5_13C_REMOVE_ID_USE_TIMESTAMP_ONLY_20260228-083837\`

- P5.14 Runtime Feature-Effect Proof + Residual Wiring Closure (post-P5.13)
  - Decision ref: D-031 (Budget enforcement toggle deferred; monitor-only lock continues).
  - Objective: Prove runtime effectiveness of user-facing PRS features before new polish expansion.
  - Execution order (normative):
    1) P5.14A Interceptors runtime effect proof
    2) P5.14B Optimizations runtime effect proof (context caching + request dedup)
    3) P5.14C Usage/Connections residual behavior fixes
    4) P5.14D Settings functional validation
    5) P5.14E Tooltip/helper assessment (post-functional gate)
    6) P5.14F Final copy/meta corrections + UI polish + app icon
  - Scope IN:
    - Runtime-effect evidence packages for Interceptors/Optimizations.
    - Residual functional behavior fixes in Usage/Connections/Settings after proofs.
  - Scope OUT:
    - Budget enforcement/blocking behavior changes (deferred by D-031).
    - Broad visual refactors before functional gates are closed.
  - Acceptance:
    - Runtime-effect claims for Interceptors and Optimizations must be backed by deterministic evidence roots.
    - If effect is absent, package must close as NARROW/BLOCKER with explicit fix queue entry.
  - Evidence required (each slice):
    - `docs\evidence\P5_14x_<timestamp>\`
    - `commands_ran.txt`, `anchor_proofs.txt`, `ssot_core.sha256.before.txt`, `ssot_core.sha256.after.txt`, `summary.txt`
  - Evidence indexed (PASS):
    - `docs\evidence\P5_14A_FIX_INTERCEPTORS_RUNTIME_HOOK_V1_20260301-014756\`
    - `docs\evidence\P5_14B_FIX_OPTIMIZATIONS_RUNTIME_BINDING_V1_20260301-014827\`
    - P5.14C PASS (destructive usage.clear runtime reconfirmation completed): `docs\evidence\P5_14C_USAGE_CONNECTIONS_RESIDUAL_FIXES_V1_20260301-021346\`; `docs\evidence\SSOT_SYNC_P5_14C_PASS_20260303-234704\`
    - `docs\evidence\P5_14D_SETTINGS_FUNCTIONAL_VALIDATION_20260301-022031\`
    - P5.14E PASS (Slice-1 helper baseline for credentials_path implemented with deterministic toggle + modal reopen reset + live interaction reconfirmation): `docs\evidence\P5_14E_TOOLTIP_HELPER_ASSESSMENT_20260301-022540\`; `docs\evidence\SSOT_SYNC_P5_14E_CARRY_FORWARD_20260303-235345\`; `docs\evidence\P5_14E_SLICE1_HELPER_BASELINE_20260304-000254\`; `docs\evidence\P5_14E_SLICE1_HELPER_STATE_RESET_20260304-001918\`; `docs\evidence\SSOT_SYNC_P5_14E_PASS_20260304-002711\`; `docs\evidence\P5_14E_NON_DASH_HELPER_LIVE_RECONFIRM_20260304-010400\`
    - `docs\evidence\P5_14_RUNTIME_EFFECT_TERMINAL_PROOF_V3_20260301-020833\`
    - P5.14F PASS (historical evidence retained; fresh reconfirmation complete for edit+browse+usage filters+export save-dialog flow + dashboard hybrid polish re-check + global layout polish + Usage/History filter row release polish + Connections Vault credentials_path browse/use closure + Persona Lite connection-target de-legacy + built-in mini-library preset seed + post-hotfix dual-tool runtime reconfirmation): `docs\evidence\UI_FINAL_FIX_QUEUE_APPLY_V3_20260301-090446\`; `docs\evidence\P5_14F_RECONFIRM_20260302-020642\`; `docs\evidence\P5_14F_SLICE_A_20260302-023124\`; `docs\evidence\P5_14F_EXPORT_SLICE_20260302-024711\`; `docs\evidence\P5_14F_COST_BREAKDOWN_NONZERO_CENTER_20260303-045857\`; `docs\evidence\P5_14F_DASH_QUICK_ALERTS_THRESHOLDS_20260303-051400\`; `docs\evidence\P5_14F_DASH_RECENT_REQUESTS_FIX4_20260303-055859\`; `docs\evidence\P5_14F_DASH_TOP_EXPENSIVE_FIX2_20260303-061419\`; `docs\evidence\P5_14F_DASH_TOP_EXPENSIVE_DYNAMIC_ROWS_20260303-061747\`; `docs\evidence\P5_14F_GLOBAL_LAYOUT_POLISH_20260303-062339\`; `docs\evidence\P5_14F_USAGE_FILTERS_DROPDOWN_WIDTH_FIX_20260303-072429\`; `docs\evidence\P5_14F_USAGE_HISTORY_FILTERS_RIGHT_ALIGN_20260303-072949\`; `docs\evidence\VAULT_V1_0_BASIC_20260303-213215\`; `docs\evidence\VAULT_SLICE_B_HOTFIX_20260303-220024\`; `docs\evidence\VAULT_SLICE_B_SUPERVISOR_HOTFIX_20260303-222100\`; `docs\evidence\VAULT_SLICE_B_BROWSE_DIALOG_HOTFIX_20260303-225421\`; `docs\evidence\USAGE_FILTERS_MIXED_EVENT_HOTFIX_20260304-005358\`; `docs\evidence\USAGE_FAKE_DATA_MINI_RECONFIRM_20260304-011210\`; `docs\evidence\USAGE_MODELID_FILTER_HOTFIX_AND_SEED_20260304-013039\`; `docs\evidence\PERSONA_CONN_TARGETS_HOTFIX_20260304-033643\`; `docs\evidence\PERSONA_PRESET_LIBRARY_SEED_20260304-035015\`; `docs\evidence\VAULT_RUNTIME_BLOCKER_REPRO_20260304-082108\` (P5.14F slices: Connections edit+browse + Usage/History filters/export + Dashboard KPI/charts/alerts/recent/top-expensive + global layout polish + Usage/History filter row release polish + Connections Vault credentials_path browse/use + Persona Lite de-legacy target mapping + built-in mini-library presets + vault runtime blocker repro/hotfix + dual-tool runtime reconfirm)

- V1.0 Release Gate Closure Checklist (post-P5.14, no scope expansion)
  - Objective: Close release blockers on current surfaces before V1.1 provider/cost expansion.
  - Gate set (OPEN -> PASS required):
    1) GATE-V10-UI-SMOKE PASS: Single-session live smoke on Dashboard/Connections/Usage/Policies/Resilience/Settings with no blocker regressions. Evidence: `docs\evidence\V10_GATE_UI_SMOKE_20260304-20260304-090444\`
    2) GATE-V10-DATA-SAFETY PASS: Usage clear/export behavior reconfirmed with deterministic evidence and rollback-safe note. Evidence: `docs\evidence\V10_GATE_DATA_SAFETY_20260304-20260304-091329\`; `docs\evidence\V10_GATE_UI_SMOKE_20260304-20260304-090444\`; `docs\evidence\P5_14F_EXPORT_SLICE_20260302-024711\`
    3) GATE-V10-DOCS-LEGAL PASS: Minimum legal/compliance + user guide consistency review completed; comprehensive legal/compliance pack and official EU/provider source register are retained, and release contact map (security/support/legal/product/general) is finalized. Evidence: `docs\evidence\V10_GATE_DOCS_LEGAL_20260304-093733\`; `docs\evidence\V10_GATE_DOCS_LEGAL_PASS_20260304-214636\`
    4) GATE-V10-RC-READINESS PASS: Release candidate checklist completed (checkpoint + known issues + support boundaries) with explicit contact map and rollback-safe checkpoint references. Evidence: `docs\evidence\V10_GATE_RC_READINESS_20260304-223507\`
  - Acceptance:
    - All four gates are PASS with explicit evidence; any open item keeps V1.0 in REVALIDATE.
  - Evidence required:
    - `docs\evidence\V10_GATE_<timestamp>\`
    - `commands_ran.txt`, `anchor_proofs.txt`, `ssot_core.sha256.before.txt`, `ssot_core.sha256.after.txt`, `summary.txt`

- V1.1 Provider Freeze Gate (4-provider lock)
  - Decision ref: D-032.
  - Objective: Lock production-candidate provider scope before LLM cost module acceptance.
  - Scope IN:
    - Vertex AI, Azure OpenAI, Bedrock, OpenAI provider readiness checks.
  - Scope OUT:
    - Any fifth provider onboarding before freeze closure.
  - Acceptance:
    - For each of the 4 providers: connection create/update/preflight/runtime smoke evidence exists.
    - Usage rows preserve provider + model identity for downstream cost analysis.
    - Freeze statement is explicit in STATUS/TASKS (no extra provider promise).
  - Evidence required:
    - `docs\evidence\V11_PROVIDER_FREEZE_<timestamp>\`
    - `commands_ran.txt`, `anchor_proofs.txt`, `ssot_core.sha256.before.txt`, `ssot_core.sha256.after.txt`, `summary.txt`
  - Progress snapshot (current):
    - Vertex AI PASS (live reconfirm), OpenAI PASS (live create/update/preflight/runtime + usage identity), Bedrock BLOCKER (connection/auth + invocation path PASS but usable live generation blocked by account quota + current adapter model allowlist constraints), Azure OpenAI OPEN.
    - Evidence: `docs\evidence\V11_PROVIDER_VERTEX_20260305-001159\`; `docs\evidence\V11_PROVIDER_OPENAI_20260305-001159\`; `docs\evidence\V11_PROVIDER_OPENAI_PASS_SYNC_20260305-024128\`; `docs\evidence\Bedrock_Real_Tests\Bedrock_Live_Tests_Results_Evalution.md`; `docs\evidence\BEDROCK_LIVE_TEST_REVIEW_20260305-082619\`; `docs\evidence\V11_BEDROCK_APIKEY_MODE_20260305-085503\`
  - Carry-forward note (post-freeze UI consistency):
    - Usage Summary KPI cards currently remain global under active filters while table/export follows filters; non-blocking for provider freeze, to be handled as follow-up polish.

- V1.1 LLM Lite Cost Gate (trust + consistency)
  - Decision ref: D-032.
  - Objective: Prove user-visible cost control consistency after LLM Lite integration.
  - Acceptance:
    - Request-level cost is computed deterministically from stored usage fields and active pricing source.
    - Same-row values are consistent across backend payload, UI tables/cards, and CSV export.
    - Missing/unsupported pricing path is explicit and non-misleading (no silent fake-zero PASS).
    - Cross-provider sample set includes Vertex AI, Azure OpenAI, Bedrock, OpenAI.
  - Evidence required:
    - `docs\evidence\V11_LLM_COST_GATE_<timestamp>\`
    - `commands_ran.txt`, `anchor_proofs.txt`, `ssot_core.sha256.before.txt`, `ssot_core.sha256.after.txt`, `summary.txt`, `test.txt`
