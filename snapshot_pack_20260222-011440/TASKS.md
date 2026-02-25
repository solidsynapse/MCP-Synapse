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
  - produced artifact: dist\MCP Router.exe



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
- Goal: Make backend proof sustainable: one command produces a complete evidence pack (pytest + key greps + SSOT hashes).
- Constraints: no new runtime deps; PS 5.1 compatible; deterministic outputs.
- Deliverable:
  - A repo script (or documented command) that writes:
    - commands_ran.txt
    - pytest.txt + pytest_exit_code.txt
    - grep_proofs (core guardrails + UI provider refs count)
    - ssot_core.sha256.txt
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
- Contract:
  - A deterministic config payload is produced for a selected agent/bridge.
  - Output is stable (ordering + encoding UTF-8) and safe (no secrets).
- Evidence pack (when implemented):
  - commands_ran.txt
  - pytest_exit_code.txt == 0
  - copy_config.out.txt (generated payload)
  - ssot_core.sha256.txt
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
- Goal: Add Ollama as a ProviderClient via ProviderFactory seam (provider-agnostic core).
- Constraints:
  - No new runtime deps.
  - No streaming unless SSOT-approved (default non-streaming).
  - No silent fallback/retry/backoff.
- Contract (normative):
  - provider_id: ollama
  - Endpoint: local HTTP base URL (operator-provided) with deterministic timeout/error mapping.
  - Output: MUST follow D-011 canonical output keys.
  - Network: local-only; still treat as explicit operator opt-in (enable flag) if required.
- Evidence (when implemented):
  - pytest_exit_code == 0
  - headless MCP probe PASS for this provider
  - determinism grep proof
- Evidence: docs\evidence\G_P3_ollama_contract_<timestamp>\
### P3.PR2.I1 — Ollama feasibility smoke (headless; non-streaming; no deps)
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
### P3.PR2.I1a — Ollama unreachable behavior (fail-fast; deterministic)
- Goal: When Ollama is not running/reachable, the probe must fail fast with an explicit error and no retries.
- Evidence: docs\evidence\G_P3_ollama_feasibility_20260221-063541\ (EXIT_CODE=1 + WinError 10061)
- Result: PASS when evidence shows explicit connection-refused error and no streaming.

### P3.PR2.I1b — Ollama reachable smoke (requires local Ollama running)
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
  - Output: MUST follow D-011 canonical output keys.
  - Network: explicit enable flag if real calls introduced; fail-fast otherwise.
- Evidence (when implemented): pytest PASS + headless MCP probe PASS + determinism grep proof.
- Evidence: docs\evidence\G_P3_openai_contract_<timestamp>\

### P3.PR4 — Anthropic provider (contract-first; docs-only; BYOK/local-only)
- Decision ref: D-026 (BYOK + local-only; no pooling; no SaaS proxy).
- Constraints: no new runtime deps; no streaming unless SSOT-approved; no silent fallback/retry/backoff.
- Contract (normative):
  - provider_id: nthropic
  - Auth: user-supplied credential only (file-path/keyring ref); secrets never stored in config.
  - Output: MUST follow D-011 canonical output keys.
  - Network: explicit enable flag if real calls introduced; fail-fast otherwise.
- Evidence (when implemented): pytest PASS + headless MCP probe PASS + determinism grep proof.
- Evidence: docs\evidence\G_P3_anthropic_contract_<timestamp>\

### P3.PR5 — Groq provider (contract-first; docs-only; BYOK/local-only)
- Decision ref: D-026 (BYOK + local-only; no pooling; no SaaS proxy).
- Constraints: no new runtime deps; no streaming unless SSOT-approved; no silent fallback/retry/backoff.
- Contract (normative):
  - provider_id: groq
  - Auth: user-supplied credential only (file-path/keyring ref); secrets never stored in config.
  - Output: MUST follow D-011 canonical output keys.
  - Network: explicit enable flag if real calls introduced; fail-fast otherwise.
- Evidence (when implemented): pytest PASS + headless MCP probe PASS + determinism grep proof.
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
### P3.PR3.I0 — Offline fake-provider proof (no network; high-confidence core test)
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
### P3.PR4.I0 — Offline fake-provider proof (Anthropic) (no network; high-confidence core test)
- Decision ref: D-008 (tests can inject a deterministic fake provider via ProviderFactory registry).
- Goal: Same as PR3.I0, but using provider_id nthropic_fake to prove provider-agnostic seam behavior.
- Scope/Constraints/Evidence: identical to P3.PR3.I0 (no deps, no streaming, no network, determinism hash).
- Evidence: docs\evidence\G_P3_anthropic_offline_fake_provider_<timestamp>\

### P3.PR5.I0 — Offline fake-provider proof (Groq) (no network; high-confidence core test)
- Decision ref: D-008 (tests can inject a deterministic fake provider via ProviderFactory registry).
- Goal: Same as PR3.I0, but using provider_id groq_fake to prove provider-agnostic seam behavior.
- Scope/Constraints/Evidence: identical to P3.PR3.I0 (no deps, no streaming, no network, determinism hash).
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
  - Output contract: MUST follow D-011 canonical output keys.
- ToS gate: record LM Studio App Terms reference; any ambiguity => contract-only until clarified.
- Evidence (when implemented):
  - headless probe PASS (models + chat/completions)
  - no streaming grep proof
  - pytest PASS
- Evidence: docs\evidence\G_P3_lmstudio_contract_<timestamp>\
### P3.PR7.I1 — LM Studio reachable smoke (headless; non-streaming; no deps)
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

1) P3.PR7.I1 — LM Studio reachable smoke (headless; non-streaming; no deps)
2) P3.P1/P3.P2/P3.P3 — Premium contract-first (docs-only) + headless proof runners later
3) P3.PR3.I1 — OpenAI online feasibility (requires BYOK key; otherwise stays blocked)
4) UI rewrite prep → UI (thin shell; last major step before release)
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
- Evidence (when implemented): offline tests showing stable injected prompt shape + pytest PASS.
- Evidence: docs\evidence\G_P3_persona_lite_contract_<timestamp>\

### P3.P3 — Context caching (contract-first; docs-only)
- Goal: Define provider-agnostic caching contract (capability-detected; never assumed).
- Constraints: no provider-specific branching in core; no streaming; no hidden fallback.
- Evidence (when implemented): contract tests with fake providers; metrics show cost/token deltas without storing payload.
- Evidence: docs\evidence\G_P3_context_caching_contract_<timestamp>\
