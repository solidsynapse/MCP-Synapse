<!-- Naming: MCP Synapse (formerly MCP Router) -->
﻿﻿﻿﻿﻿﻿﻿# STATUS — MCP Router Stabilization

## Snapshot
- Date: 2026-02-14
- OS: Windows 10 LTSC
- Repo root: C:\MCP-ROUTER
- VCS: Git is available, repo is not git-initialized (evidence: Step-1 output)
- Docs present: docs/architecture/pipeline-v1.md
- Legacy path: active (evidence pending)
- Pipeline V1: implementation exists, not default (evidence: docs/architecture/pipeline-v1.md + src path list)
- Phase 2 / D-004 verification: **DONE** (Evidence root: docs\evidence\D004_verify_20260219-050337\)
- Current phase: P5 post-closure stabilization (P5.13 closure PASS; PRS manual live sweep NARROW fix queue F-PRS-01..08 active).
- Budget guard policy: monitor-only lock active; optional enforcement toggle deferred by D-031 pending dedicated future package + SSOT FLIP.

## What we know (Evidence-based facts)
- Pipeline V1 code: src/mcp_server/pipeline_v1.py
- V1 entrypoint method exists per architecture doc: ServerManager.execute_request_v1 (src/mcp_server/manager.py) [EVIDENCE NEEDED: line refs]
- Legacy server/manager: src/mcp_server/agent_server.py, src/mcp_server/manager.py
- UI entry: src/ui/main_window.py
- UI (Tauri/Svelte) thin-shell progress (P4 no-wiring baseline + P5 scoped wiring evidence):
  - SSOT/UI bootstrap anchors PASS: docs\evidence\SSOT_UI_BOOTSTRAP_20260225-010058
  - Connections page replication + triage PASS: docs\evidence\P4_UI_REPL_P1_20260225-012036
  - Connections polish verify PASS (hardcode review pending): docs\evidence\P4_UI_REPL_P1_POLISH_VERIFY_20260225-025002
  - Provider registry confirmed registered set (6): docs\evidence\P4_PROVIDER_REGISTRY_LOCATE_20260225-033559
  - LM Studio clarified (contract/test exists; not registered): docs\evidence\P4_LMSTUDIO_TRACE_FAST_20260225-035913
  - New Connection modal (provider-locked; triage PASS): docs\evidence\P4_UI_NEWCONN_MODAL_20260225-042356
  - Usage (Summary/History) UI polish (no wiring; triage PASS): docs\evidence\P4_UI_USAGE_MICROFIX_20260225-054440
  - UI final gate PASS (no wiring + hardcode triage + ui check): docs\evidence\P4_UI_FINAL_GATE_20260225-084502
  - P5.3 UI session state PASS (UI-only): docs\evidence\P5_3_UI_SESSION_STATE_VERIFY_20260226-012544
  - P5.2 UI→core dry_run dispatch PASS: docs\evidence\P5_WIRING_UI_DISPATCH_20260225-104400
  - P5.5 Preflight validation PASS (provider-free): docs\evidence\P5_5_PREFLIGHT_VERIFY_20260226-022803
  - P5.6 Copy Config canonicalization PASS (core-generated + UI row Copy enabled): docs\evidence\P5_6_COPY_CONFIG_VERIFY_20260226-024338; docs\evidence\P5_6_COPY_UI_ENABLE_20260227-070630
  - P5.8 Connections lifecycle wiring PASS (Start/Stop/Delete row actions wired via single-entrypoint; thin-shell guard preserved): docs\evidence\P5_8A_DELETE_WIRING_20260227-073626;
docs\evidence\P5_8B_START_STOP_WIRING_20260227-074309; docs\evidence\P5_8C_DELETE_ROW_UNGATE_20260227-075607
  - P5.9 Runtime orchestration PASS (core runtime Start/Stop + SSE lifecycle + runtime/encoding stabilization): docs\evidence\P5_9_TASK_PACKAGE_ADD_20260227-091534;
docs\evidence\P5_9A_RETRY_CORE_ONLY_V2_20260227-092552; docs\evidence\INCIDENT_START_TEST_SPLIT_FIX_V1_20260227-100837;
docs\evidence\P5_9A_DRYRUN_PROJECTID_REGRESSION_TEST_20260227-101255; docs\evidence\P5_9_REAL_SURFACE_SMOKE_V1_20260227-101926;
docs\evidence\FULL_OWNERSHIP_STOP_WIN87_FIX_20260227-120009; docs\evidence\ENCODING_CHARMAP_FIX_20260227-123051; docs\evidence\DRYRUN_BANNER_COMPACT_V1_20260227-123854;
docs\evidence\P5_9_RUNTIME_ENCODING_CLOSURE_AUDIT_20260227-124419
  - P5.10 IDE tool response contract PASS (success non-empty MCP content/text + explicit error.code/error.message on failure): docs\evidence\P5_10_TASK_PACKAGE_ADD_20260227-195403; docs\evidence\P5_10A_MCP_CONTENT_ERROR_CONTRACT_20260227-195727; docs\evidence\P5_10A_CLOSURE_AUDIT_20260227-203253
  - P5.11A Usage/Summary wiring PASS (dispatcher-backed KPIs/rows; static seed removed; explicit error rendering): docs\evidence\P5_11A_USAGE_SUMMARY_WIRING_20260227-205310
  - P5.11B Usage/History wiring PASS (dispatcher-backed rows; stub wording removed on wired read path; explicit parse/dispatch error rendering): docs\evidence\P5_11B_USAGE_HISTORY_WIRING_20260227-210405
  - P5.11C Policies/Persona wiring PASS (core-backed persona state get/set; persisted canonical state; explicit validation errors): docs\evidence\P5_11C_POLICIES_PERSONA_WIRING_20260227-211026
  - P5.11D Policies/Optimizations wiring PASS (core-backed toggle state get/set; explicit validation errors): docs\evidence\P5_11D_POLICIES_OPTIMIZATIONS_WIRING_20260227-211824
  - P5.11E Resilience/Budget wiring PASS (core-backed budget state get/set; explicit validation errors): docs\evidence\P5_11E_RESILIENCE_BUDGET_WIRING_20260227-213627
  - P5.11F Resilience/Interceptors wiring PASS (core-backed interceptors state get/set; explicit validation errors): docs\evidence\P5_11F_RESILIENCE_INTERCEPTORS_WIRING_20260227-214919
  - P5.11G Dashboard wiring PASS (core-backed dashboard state get/set; explicit validation errors): docs\evidence\P5_11G_DASHBOARD_WIRING_20260227-220945
  - P5.11H Settings wiring PASS (core-backed settings state get/set; explicit validation errors): docs\evidence\P5_11H_SETTINGS_WIRING_20260227-223113
  - P5.11 Closure PASS (full-surface regression): docs\evidence\P5_11_FULL_SURFACE_REGRESSION_20260227-224528
  - P5.11 PRS live validation matrix PASS (Policies/Resilience/Settings get/set + persistence + validation contract): docs\evidence\P5_11_PRS_LIVE_VALIDATION_MATRIX_V1_RETRY_20260228-085227
  - P5.11 PRS persona runtime binding + live confirm PASS (runtime persona prompt injection verified with signature marker [PERSO_TEST_OK]; IDE tool restart required for fresh runtime pickup): docs\evidence\P5_11PRS_PERSONA_RUNTIME_BINDING_20260301-001548
  - P5.11 PRS manual live sweep NARROW (functional persistence PASS; unresolved UX/data-parity findings queued as F-PRS-01..08): docs\evidence\P5_11_PRS_MANUAL_SWEEP_EVIDENCE_INDEX_20260228-092749
  - P5.12 Closure PASS (post-P5.11 stability + dashboard parity/polish + SSOT index + closure audit): docs\evidence\P5_12_TASK_PACKAGE_ADD_20260227-225744; docs\evidence\ACTIVE_BRIDGES_STOP_PARITY_V2_20260228-052546; docs\evidence\DASHBOARD_REFRESH_AND_HISTORY_CLEAR_PARITY_PROBE_20260228-063153; docs\evidence\DASHBOARD_POLISH_P7_APPLY_20260228-063404; docs\evidence\DASHBOARD_POLISH_P8_RECENT12_20260228-065147; docs\evidence\DASHBOARD_POLISH_P8B_REFRESH_FEEDBACK_20260228-065232; docs\evidence\HISTORY_CLEAR_PARITY_FINAL_CHECK_20260228-065511; docs\evidence\P5_12D_CLOSURE_AUDIT_20260228-075948
  - P5.12B Active Bridges running semantic + stop/start parity PASS (runtime-stuck listener guard + dashboard KPI parity): docs\evidence\ACTIVE_BRIDGES_STOP_PARITY_V2_20260228-052546
  - P5.12B Dashboard refresh + History Clear parity probe PASS (no-edit root-cause evidence): docs\evidence\DASHBOARD_REFRESH_AND_HISTORY_CLEAR_PARITY_PROBE_20260228-063153
  - P5.12C Dashboard parity+polish apply PASS (fresh live/session reconfirmation complete): docs\evidence\DASHBOARD_POLISH_P7_APPLY_20260228-063404; docs\evidence\DASHBOARD_POLISH_P8_RECENT12_20260228-065147; docs\evidence\DASHBOARD_POLISH_P8B_REFRESH_FEEDBACK_20260228-065232; docs\evidence\HISTORY_CLEAR_PARITY_FINAL_CHECK_20260228-065511; docs\evidence\P5_12C_REVALIDATE_SUPERVISOR_20260301-224444; docs\evidence\P5_12C_A1_REFRESH_FEEDBACK_REVALIDATE_20260301-235523; docs\evidence\P5_12C_A1317_NO_STATIC_SEED_REVALIDATE_20260302-001319; docs\evidence\P5_12C_1315_LIVE_20260302-030853
  - P5.12D Dashboard micro-polish slices PASS (KPI typography/icons + trend readability/composition + breakdown Top3+Others/legend + final chart alignment): docs\evidence\P5_12D_SLICE_01_KPI_TYPO_ICON_POLISH_20260228-070644; docs\evidence\P5_12D_SLICE_02B_TREND_VISUAL_TUNING_20260228-071905; docs\evidence\P5_12D_SLICE_02C_TREND_XAXIS_READABILITY_20260228-072458; docs\evidence\P5_12D_SLICE_03_BREAKDOWN_INFORMATION_ARCH_20260228-072632; docs\evidence\P5_12D_SLICE_02D_03B_GRAPH_COMPOSITION_FINETUNE_20260228-074811; docs\evidence\CHART_ALIGNMENT_FINAL_POLISH_PIE_UP20_20260228-075720
  - P5.13 Closure PASS (dashboard residual polish: alerts density + recent table balance + top expensive semantic labels): docs\evidence\P5_13A_ALERT_THRESHOLD_AND_SPACING_TUNE_20260228-081116; docs\evidence\P5_13A_ALERT_CONTEXT_TRIM_20260228-081411; docs\evidence\P5_13B_RECENT_TABLE_EQUAL_SPACING_CENTER_ALIGN_20260228-082716; docs\evidence\P5_13C_REMOVE_ID_USE_TIMESTAMP_ONLY_20260228-083837; docs\evidence\STEP_P513_SSOT_INDEX_AND_CLOSURE_AUDIT_20260228-083945
  - P5.14 queue active (proof-first): Interceptors runtime effect -> Optimizations runtime effect -> Usage/Connections residual fixes -> Settings functional validation -> tooltip/helper assessment -> final copy/meta + UI polish/app icon.
  - P5.14A Interceptors runtime effect PASS (state-only gap fixed; execute path hook proven): docs\evidence\P5_14A_FIX_INTERCEPTORS_RUNTIME_HOOK_V1_20260301-014756
  - P5.14B Optimizations runtime effect PASS (context cache toggle binding + request dedup runtime hit path proven): docs\evidence\P5_14B_FIX_OPTIMIZATIONS_RUNTIME_BINDING_V1_20260301-014827
  - P5.14C Usage/Connections residual behavior fixes PASS (destructive usage.clear runtime reconfirmation completed in single-session live check): docs\evidence\P5_14C_USAGE_CONNECTIONS_RESIDUAL_FIXES_V1_20260301-021346; docs\evidence\SSOT_SYNC_P5_14C_PASS_20260303-234704
  - P5.14D Settings functional validation PASS (get/set persistence + validation error code/message + restore baseline): docs\evidence\P5_14D_SETTINGS_FUNCTIONAL_VALIDATION_20260301-022031
  - P5.14E Tooltip/helper assessment PASS (Slice-1 helper baseline implemented for credentials_path with scoped wiring + live interaction reconfirmation): docs\evidence\P5_14E_TOOLTIP_HELPER_ASSESSMENT_20260301-022540; docs\evidence\SSOT_SYNC_P5_14E_CARRY_FORWARD_20260303-235345; docs\evidence\P5_14E_SLICE1_HELPER_BASELINE_20260304-000254; docs\evidence\P5_14E_SLICE1_HELPER_STATE_RESET_20260304-001918; docs\evidence\SSOT_SYNC_P5_14E_PASS_20260304-002711; docs\evidence\P5_14E_NON_DASH_HELPER_LIVE_RECONFIRM_20260304-010400
  - P5.14F UI final fix queue slice PASS (fresh reconfirmation complete after latest adjustments, including dashboard hybrid polish re-check + Usage/History filter row release polish + Connections Vault credentials_path browse/use flow closure + Persona Lite connection-target de-legacy + built-in mini-library preset seed + post-hotfix dual-tool runtime reconfirmation): docs\evidence\UI_FINAL_FIX_QUEUE_APPLY_V3_20260301-090446; docs\evidence\P5_14F_RECONFIRM_20260302-020642; docs\evidence\P5_14F_SLICE_A_20260302-023124; docs\evidence\P5_14F_EXPORT_SLICE_20260302-024711; docs\evidence\P5_14F_COST_BREAKDOWN_NONZERO_CENTER_20260303-045857; docs\evidence\P5_14F_DASH_QUICK_ALERTS_THRESHOLDS_20260303-051400; docs\evidence\P5_14F_DASH_RECENT_REQUESTS_FIX4_20260303-055859; docs\evidence\P5_14F_DASH_TOP_EXPENSIVE_FIX2_20260303-061419; docs\evidence\P5_14F_DASH_TOP_EXPENSIVE_DYNAMIC_ROWS_20260303-061747; docs\evidence\P5_14F_USAGE_FILTERS_DROPDOWN_WIDTH_FIX_20260303-072429; docs\evidence\P5_14F_USAGE_HISTORY_FILTERS_RIGHT_ALIGN_20260303-072949; docs\evidence\VAULT_V1_0_BASIC_20260303-213215; docs\evidence\VAULT_SLICE_B_HOTFIX_20260303-220024; docs\evidence\VAULT_SLICE_B_SUPERVISOR_HOTFIX_20260303-222100; docs\evidence\VAULT_SLICE_B_BROWSE_DIALOG_HOTFIX_20260303-225421; docs\evidence\USAGE_FILTERS_MIXED_EVENT_HOTFIX_20260304-005358; docs\evidence\USAGE_FAKE_DATA_MINI_RECONFIRM_20260304-011210; docs\evidence\USAGE_MODELID_FILTER_HOTFIX_AND_SEED_20260304-013039; docs\evidence\PERSONA_CONN_TARGETS_HOTFIX_20260304-033643; docs\evidence\PERSONA_PRESET_LIBRARY_SEED_20260304-035015; docs\evidence\VAULT_RUNTIME_BLOCKER_REPRO_20260304-082108
  - P5.14 runtime terminal proof PASS (deterministic interceptor+dedup+cache behavior gate): docs\evidence\P5_14_RUNTIME_EFFECT_TERMINAL_PROOF_V3_20260301-020833
  - Pre-dashboard safety checkpoint created (docs-only + git recovery refs): docs\evidence\PRE_DASHBOARD_SAFETY_CHECKPOINT_20260302-094944 (head branch: checkpoint/pre-dashboard-head-20260302-094944; working snapshot ref: refs/checkpoints/pre-dashboard-snapshot-20260302-094944)
  - Global layout polish PASS (right-edge scroll/jitter suppression + collapsed-sidebar chevron alignment): docs\evidence\P5_14F_GLOBAL_LAYOUT_POLISH_20260303-062339
  - Next sequence locked (D-032): V1.0 gate closure -> V1.1 provider freeze (Vertex AI, Azure OpenAI, Bedrock, OpenAI) -> V1.1 LLM Lite cost gate (backend/UI/CSV consistency).
  - V1.0 GATE-V10-UI-SMOKE PASS (single-session live smoke on Dashboard/Connections/Usage/Policies/Resilience/Settings completed; no blocker regressions in current truth): docs\evidence\V10_GATE_UI_SMOKE_20260304-20260304-090444
  - V1.0 GATE-V10-DATA-SAFETY PASS (usage.clear reconfirmed with deterministic backup/restore probe; export behavior remains covered by latest live UI smoke and P5.14F export runtime evidence): docs\evidence\V10_GATE_DATA_SAFETY_20260304-20260304-091329; docs\evidence\V10_GATE_UI_SMOKE_20260304-20260304-090444; docs\evidence\P5_14F_EXPORT_SLICE_20260302-024711
  - V1.0 GATE-V10-DOCS-LEGAL PASS (LC-MIN security/support/legal/product/general contact map finalized; comprehensive legal/compliance pack and official EU/provider source register remain aligned with current truth): docs\evidence\V10_GATE_DOCS_LEGAL_20260304-093733; docs\evidence\V10_GATE_DOCS_LEGAL_PASS_20260304-214636
  - V1.0 GATE-V10-RC-READINESS PASS (RC checklist completed with checkpoint references + known issues coverage + support boundaries/contact map): docs\evidence\V10_GATE_RC_READINESS_20260304-223507
  - V1.1 Provider Freeze progress (order: Vertex -> OpenAI -> Bedrock -> Azure OpenAI): Vertex AI PASS (live reconfirm; preflight probe upgraded to single-targeted classification + performance-safe execution), OpenAI PASS (live create/update/preflight/runtime + usage identity), Bedrock BLOCKER (connection/auth + invocation path PASS but usable live generation blocked by account quota + current adapter model allowlist constraints), Azure OpenAI PASS (live connection/create/preflight/update/runtime smoke + dashboard/usage visibility + modal contract lock + targeted hotfix closure): docs\evidence\V11_PROVIDER_VERTEX_20260305-001159; docs\evidence\VERTEX_PREFLIGHT_SINGLE_PROBE_20260307-005435; docs\evidence\VERTEX_PREFLIGHT_PERF_HOTFIX_20260307-011139; docs\evidence\VERTEX_PROBE_CLASSIFIER_HOTFIX_20260307-012751; docs\evidence\VERTEX_PREFLIGHT_EMPTY_TEXT_HOTFIX_20260307-013304; docs\evidence\V11_PROVIDER_OPENAI_20260305-001159; docs\evidence\V11_PROVIDER_OPENAI_PASS_SYNC_20260305-024128; docs\evidence\Bedrock_Real_Tests\Bedrock_Live_Tests_Results_Evalution.md; docs\evidence\BEDROCK_LIVE_TEST_REVIEW_20260305-082619; docs\evidence\V11_BEDROCK_APIKEY_MODE_20260305-085503; docs\evidence\Azure_real_tests\Azure OpenAI entegrasyonu.md; docs\evidence\V11_AZURE_MODAL_CONTRACT_PATCH_20260305-223056; docs\evidence\HOTFIX_AZURE_DASH_VAULT_20260306-012035
  - V1.1 contingency lane status (D-034/D-035): Hugging Face OpenAI-compatible chat-only PASS (network gate explicit enable + preflight enforcement + non-streaming `/v1/chat/completions` + IDE smoke + usage provider/model identity + vault credential source), Ollama local chat-only PASS (endpoint contract/hydration + create/update/preflight/runtime smoke + usage provider/model identity). These remain non-closure lanes; D-032 freeze closure is still blocked by Bedrock external dependency: docs\evidence\HF_MODAL_CONTRACT_TEXT_SYNC_20260306-054615; docs\evidence\HF_NETWORK_GATE_UI_PREFLIGHT_FIX_20260306-060946; docs\evidence\OLLAMA_ENDPOINT_HYDRATE_HOTFIX_20260306-052107; docs\evidence\OLLAMA_PREFLIGHT_REQUIRED_FIX_20260306-053551; docs\evidence\SSOT_SYNC_HF_CONTINGENCY_20260306-072439
  - V1.1 LLM Lite Cost Gate progress: A1 kickoff matrix prepared; A2 pricing disclosure + CSV `Pricing status` PASS; A3 dashboard disclosure dismiss + overflow-compact polish PASS; A5 priced-lane deterministic compute PASS (OpenAI live request chain shows non-zero USD with cross-surface consistency + CSV `Estimated`); A6 Vertex live explicit unknown-pricing path PASS (`cost=$0.0000` + `Pricing status=Missing pricing data` with cross-surface parity); A7 Azure live known-pricing path PASS (`cost_usd>0` + `Pricing status=Estimated` with same-request cross-surface parity); A8 Vertex live known-pricing path PASS (`cost_usd>0` + `Pricing status=Estimated` with same-request parity across payload/DB/UI/CSV); A9 closure bundle PASS (A7+A8 live artifacts consolidated under one gate-level reconfirm package); A10 release-cut reconciliation PASS (no-code SSOT/evidence reconciliation confirms Usage/Budget rails closure boundary while Bedrock remains external): docs\evidence\V11_LLM_COST_GATE_A1_KICKOFF_20260307-020000; docs\evidence\V11_LLM_COST_GATE_A2_PRICING_DISCLOSURE_20260307-023238; docs\evidence\V11_LLM_COST_GATE_A3_DASHBOARD_DISCLOSURE_SCROLLFIX_20260307-024406; docs\evidence\V11_LLM_COST_GATE_A5_20260307-030532; docs\evidence\V11_LLM_COST_GATE_A5_PASS_SYNC_20260307-033321; docs\evidence\V11_LLM_COST_GATE_A6_20260307-034036; docs\evidence\V11_LLM_COST_GATE_A6_PASS_SYNC_20260307-065351; docs\evidence\V11_LLM_COST_GATE_A7_20260307-065850; docs\evidence\V11_LLM_COST_GATE_A7_PASS_SYNC_20260307-070531; docs\evidence\V11_LLM_COST_GATE_A8_20260307-071112; docs\evidence\V11_LLM_COST_GATE_A8_PASS_SYNC_20260307-073958; docs\evidence\V11_LLM_COST_GATE_A9_CLOSURE_BUNDLE_20260307-074738; docs\evidence\V11_LLM_COST_GATE_A10_RELEASE_RECONCILE_20260307-075241
  - Remaining open set (post-A10 reconciliation): Bedrock provider allowlist/quota stays external BLOCKER; network gate matrix (VertexAI/OpenAI/Azure/Ollama/HF) + persona enforcement + copy-config regression + Usage/Budget rails (V1.1 LLM cost gate) are treated as PASS on current evidence; RC-EXT final release hygiene pack is OPEN (health alerts calibration, shortcuts baseline with current-surface scope, security hygiene, debuggability minimum, packaging/versioning readiness). Usage History "View Details" modal is not a current surface and is tracked as future enhancement.
  - First release scope lock (current truth): Bedrock is blocked and de-scoped/hidden from first-release surface until quota/allowlist unblock. Re-enable path is fixed and narrow: unhide provider in UI -> run provider regression smoke -> reconfirm usage/dashboard parity.
  - Carry-forward (non-blocking for current gate): Usage Summary KPI cards currently stay global under active filters while table/export filters behave correctly; disclosure parity (Summary) + residual right-edge scrollbar polish deferred to final release UI pass; post-RC P1 perf smoke remains deferred; full English documentation pack is deferred until technical freeze is completed (technical-first sequencing lock).
- Versioning policy lock (D-037): current line is `v0.6.x (Early Access)`; milestone progression is `0.7` (RC-EXT + packaging), `0.8` (hardening/security+perf baseline/docs), `0.9` (domain-agnostic migration-readiness), `1.0` (domain-agnostic execution-fabric completion). Logo/app icon freeze remains coupled to packaging/versioning closure.
- Licensing/distribution lock (D-038): visible-source freemium + official-channel control is active; unsigned release mode is allowed only as a temporary phase with mandatory release integrity set (tag + SHA256 + changelog/"what changed" + explicit unsigned warning). Code signing is scheduled for `0.9.x -> 1.0.0`.
- SSOT checkpoint (2026-03-08; minimal sync, no scope expansion):
  - Blocker-1 CLOSED: visible CMD flash is treated as closed on packaged path after no-console hotfix + revalidation (`RC_EXT_BLOCKER1_NO_CONSOLE_HOTFIX_20260308-064011`, `RC_EXT_BLOCKER1_CHOKEPOINT_COMPLETE_20260308-070019`).
  - Packaging/meta CLOSED set (current truth): branded product naming reflected in produced installer artifact names; MSI numeric override path confirmed; packaged build generation PASS (`PAK_01_MSI_OVERRIDE_FIX_20260308-061847`, `PAK_01_POST_BUILD_SMOKE_20260308-062840`).
  - Perf classification lock: direct backend latency is route-independent in ~4.4s band; dominant cost is per-call Python subprocess/import/bootstrap overhead; TTL cache remains UX mitigation only (`V12_TTL_CACHE_HOTFIX_20260308-074535`).
  - Phase-2 worker track:
    - V16 decision slice PASS: worker spike worth integrating (`V16_PHASE2_WORKER_SPIKE_20260308-090923`).
    - V17 minimum integration PASS: default OFF flag-gated worker path, strict 3-op whitelist, mandatory immediate legacy fallback on worker timeout/error/invalid response (`V17_PHASE2_MIN_INTEGRATION_20260308-101000`).
  - Remaining release-blocking technical gates (OPEN):
    1) Worker OFF revalidation
    2) Worker ON revalidation
    3) Fallback revalidation
    4) Packaged clean first-run stability
    5) No-dispatch-regression packaged smoke
  - Non-blocking polish/meta backlog (OPEN):
    - icon/branding packaged consistency
    - perf/debug marker visibility hygiene
    - observability hygiene (retention/size discipline)
    - final evidence/release-note organization
- SSOT checkpoint (2026-03-09; performance closeout + next-phase ordering, no new decision):
  - Performance gates closure:
    - Main navigation perf gate CLOSED (`V34_WAVE1_PERF_EXPANSION_20260308-233749`).
    - Persona Lite -> Optimizations transition lag CLOSED (`V37_PERSONA_ROUTE_LEAVE_COALESCE_20260309-002548`).
    - Lifecycle mini-slice CLOSED on worker-on release exe path (`V44_LIFECYCLE_MINI_SLICE_20260309-220452`):
      - startup_ready_ms ~1.0-1.1s
      - shutdown close_to_exit_ms_estimate ~1.52s
    - Packaging install-root tmp-path blocker CLOSED (`V43_INSTALL_LOCATION_HARD_CLOSURE_20260309-211154`).
    - Overall performance gates: PASS (release-complete enough for current lane).
  - Deferred items (OPEN, non-blocking for current release closeout):
    - Connections detail interaction rough edge (Wave-2A residual).
    - Worker-ON steady RAM < 250 MB optimization target (future slice).
  - Preferred immediate order lock (post-perf):
    1) post-perf cleanup/hardening
    2) security review / mini pentest
    3) release prep / known issues / worker launch stance
    4) then first future optimization slice: worker-on memory reduction below 250 MB
- SSOT checkpoint (2026-03-09; release-prep runtime stance realignment):
  - This snapshot supersedes prior user-facing dual runtime mode wording in release-prep context.
  - Revised runtime stance:
    - installed product uses a single fast default runtime profile (worker-primary default),
    - legacy subprocess path remains internal fallback safety only (timeout/error/invalid response),
    - worker OFF/ON distinction is removed from user-facing stance.
  - Release-prep scope update:
    - default packaged worker-primary behavior becomes the primary smoke target,
    - fallback verification remains required but internal-only,
    - docs/release-note/support wording must avoid runtime mode switching guidance.
  - Deferred items unchanged:
    - Connections detail interaction rough edge (Wave-2A residual).
    - Worker-ON steady RAM < 250 MB optimization target (future slice).
- SSOT checkpoint (2026-03-10; security closeout packaging):
  - Security mini-gate PASS (`V50_RELEASE_SECURITY_MINI_GATE_20260309-234645`).
  - Narrow security polish PASS (`V52_NARROW_SECURITY_POLISH_PATCH_20260310-000816`):
    - unknown-op / invalid-request semantic hardening applied,
    - vault plaintext-read related generic exception hygiene applied.
  - Security closeout conclusion:
    - no release-blocking finding in scoped security lane.
  - Security deferred (single item):
    - `MCP_SYNAPSE_PYTHON` boundary tightening.
- SSOT checkpoint (2026-03-11; release runway sync, no new decision):
  - Release package prep PASS (`V57_RELEASE_PACKAGE_PREP_20260310-022825`):
    - fresh bundled build generated,
    - artifact inventory + SHA256 manifest captured,
    - install/shortcut sanity captured for that step.
  - Narrow UI polish progression:
    - Step 2A PASS (`V58_STEP2A_UI_MINI_POLISH_2SURFACES_20260311-063054`, `V59_STEP2A_DASHBOARD_FINAL_POLISH_20260311-064604`),
    - Step 2B PASS (`V60_STEP2B_UI_POLISH_CONNECTIONS_USAGE_METADATA_20260311-070451`),
    - Step 2C PASS (`V61_STEP2C_SETTINGS_HELP_FINALIZE_20260311-074026`, `V62_STEP2C_HELP_LINK_HOTFIX_20260311-074647`, `V63_HELP_LINK_EXECUTE_SAFE_20260311-075115`),
    - Step 2D closure patch applied (`V65_STEP2D_CLOSURE_INSTALL_ROOT_ICON_20260311-090522`) after blocker in `V64_STEP2D_DESKTOP_SHELL_BRANDING_20260311-081331`,
    - Step 2E desktop UX hardening patch applied (`V66_STEP2E_DESKTOP_UX_HARDENING_20260311-093444`).
  - Release docs finalize package created under `docs/release/releases/v0.6.0-rc.1/`:
    - `RELEASE_NOTES.md`, `WHAT_CHANGED.md`, `SHA256SUMS.txt`,
    - `KNOWN_ISSUES.md`, `INSTALL_RUN_NOTES.md`, `TRUST_SECURITY.md`,
    - existing `UNSIGNED_NOTICE.md` retained.
  - Runtime/product stance unchanged:
    - single fast default runtime profile for installed product,
    - legacy subprocess path is internal fallback safety only.
  - Deferred items remain unchanged:
    - Connections detail interaction rough edge (Wave-2A residual),
    - worker-on RAM optimization target (<250 MB),
    - `MCP_SYNAPSE_PYTHON` boundary tightening.
  - RC decision status:
    - REVALIDATE until final packaged smoke-truth evidence is consolidated in one release-close evidence pack.
- SSOT checkpoint (2026-03-11; final preflight + RC decision, no new decision):
  - Consolidated packaged closure set:
    - `V68_FINAL_PACKAGED_SMOKE_TRUTH_RC_20260311-103015` PASS,
    - `V69_IDENTITY_PARITY_CLOSURE_20260311-104200` PASS,
    - `V70_SPEED_COMPARE_WORKER_ON_OFF_20260311-110543` PASS,
    - `V71_RELEASE_CHECKSUM_UPDATE_20260311-111229` PASS.
  - Current release-close classification:
    - RC READY.
  - Deferred carry-forward remains unchanged:
    - Connections detail interaction rough edge (Wave-2A residual),
    - worker-on RAM optimization target (<250 MB),
    - `MCP_SYNAPSE_PYTHON` boundary tightening.
- Usage DB: data/usage.db + src/data/usage_db.py
- Config: data/config.json + src/config/manager.py
- Provider integration: src/vertex/client.py (uses Google Vertex AI)
- Provider abstraction seam (Pipeline V1): src/providers/* + ProviderFactory selection in pipeline_v1

## Unknowns (Must provide evidence before decisions)
1) Pipeline V1 activation mechanism:
   - Is it a config flag, UI toggle, CLI arg, or codepath selection today's legacy flow never hits?
   - [EVIDENCE NEEDED] search results with line numbers for:
     - execute_request_v1
     - any "enable/opt-in/rollout" logic
     - any config keys in data/config.json that affect routing
2) Build/Run commands:
   - build.py usage, expected entrypoints, dependency install steps
   - [EVIDENCE NEEDED] build.py --help output + requirements.txt head
3) QA commands:
   - pytest presence, test suite command, expected passing set
   - [EVIDENCE NEEDED] pytest version + one test run output
4) "Pipeline V1 used to work but not now" proof:
   - log excerpt / error / repro steps
   - [EVIDENCE NEEDED] shared log + exact repro steps

## Stabilization Checkpoint (Definition)
Checkpoint is achieved when ALL are true (with evidence links below):
1) SSOT bootstrap exists (historical): STATUS/PLAN/TASKS/DECISIONS were created and linked. Current active SSOT core is DECISIONS/STATUS/TASKS (D-001).
2) V1 activation path identified:
   - We can point to exact file+line where V1 is selected OR why it cannot be selected.
3) Repro baseline established:
   - One deterministic command (or minimal steps) reproduces legacy path output.
4) QA baseline established:
   - One deterministic command runs tests (subset allowed) and output is captured.
5) Rollback safety stated:
   - A single switch/flag/branching decision can turn off V1 without affecting legacy.

## Evidence Index (Commands + Outputs)
- Phase 2 / D-004 verification — Evidence pointers: docs\evidence\D004_verify_20260219-050337\ (pytest.txt, pytest_exit_code.txt, grep_proofs.txt, commands_ran.txt, changed_files.txt, rollback.txt)
- T2.X MCP Tool Discovery probe (headless) — Evidence root: `docs\evidence\T2X_mcp_tool_discovery_probe_20260220-044918\`
- T2.Y Remove duplicate tree src/mcp_server/1 — Evidence root: `docs\evidence\T2Y_remove_duplicate_mcp_server_1_20260220-052104\`
  - Phase 2 verification:
    - pytest: PASS (evidence: docs\evidence\G_P2_pytest_and_determinism_20260220-051113\pytest.txt + pytest_exit_code.txt)
    - determinism scan: no retry/backoff/fallback patterns found in src (evidence: docs\evidence\G_P2_pytest_and_determinism_20260220-051113\grep_proofs.txt)
  - Canonical headless harness command: python src\tests\test_phase2.py
  - Canonical MCP probe command: py -3.11 -m src.tests.mcp_sse_probe --start-local-server --port 5055 --out-dir docs/evidence/T2X_mcp_tool_discovery_probe_20260220-044918/mcp_probe
  - Evidence: docs\evidence\T2X_mcp_tool_discovery_probe_20260220-044918\mcp_probe\ (raw initialize/tools_list/tools_call dumps)
  - docs tree: `tree docs /F`
  - architecture head: `Get-Content docs\architecture\pipeline-v1.md -TotalCount 160`
  - src grep: `Select-String ...`
- Step-2 (this commit):
  - docs tree: `tree docs /F`
  - file heads: `Get-Content docs\STATUS.md -TotalCount 80`
  
  - MVP release gate (Vertex + Azure):
  - Status: **GO**
  - Evidence root: `docs\evidence\MVP_release_gate_20260218_050710\`

  - T2.2 Usage → Cost Map Discovery (evidence-only):
  - Evidence root: `docs\evidence\T2.2_usage_cost_map_20260216-103822\`
  - Key files:
    - `usage_db.linenum.txt` (Usage DB schema + log_usage signature)
    - `log_usage.callsites.txt` (all `.log_usage(` callsites)
    - `pipeline_v1.flow_extract.txt` (Preflight → ProviderAdapterV1 → ObserverV1 → log_usage flow)
    - `enforcement.search.txt` (no budget/limit enforcement found beyond QuotaError)
    - `v1_observer_probe.out.txt` + `db.count.txt` + `db.rows.txt` (ObserverV1 can write DB without Vertex call)

  - T2.2 SSOT lock prep (extracts):
  - Evidence root: `docs\evidence\T2.2_ssot_lock_prep_20260216-104920\`
  - Key files:
    - `ARCH.T2.extract.txt` (ARCHLOG first T2.* section, line-numbered)
    - `TASKS.T2.extract.txt` (TASKS T2.* section, line-numbered)

  - T3.1 Usage: operational metrics + filtering + KPI correctness:
  - Evidence root: `docs\evidence\T3.1_20260217-095736\`

  - Phase 1.5 Provider abstraction seam (ProviderFactory + ProviderClient):
  - Evidence root: `docs\evidence\T1.5_provider_abstraction_20260217-161800\`
  - Key files:
    - `pytest.txt` (QA PASS)
    - `grep_proofs.txt` (factory seam + no direct VertexAIClient in ProviderAdapterV1)
    - `rollback.txt` (copy-back rollback steps + snapshots)

  - Phase 1.5 Provider abstraction hardening (config compatibility + invariant tests):
  - Evidence root: `docs\evidence\T1.5_hardening_20260217-163300\`
  - Key files:
    - `pytest.txt` (QA PASS)
    - `grep_proofs.txt` (no VertexAIClient in pipeline_v1 + uses ProviderFactory.create)
    - `rollback.txt` (copy-back rollback + snapshot)

  - Phase 1.5 Azure OpenAI provider adapter (via ProviderFactory):
  - Evidence root: `docs\evidence\T1.5_azure_openai_20260217-170200\`
  - Key files:
    - `pytest.txt` (QA PASS)
    - `grep_proofs.txt` (factory registration + pipeline_v1 invariants)
    - `rollback.txt` (rollback steps)

  - Phase 1.5 Azure OpenAI UI config surface (provider fields; no secret):
  - Evidence root: `docs\evidence\T1.5_azure_ui_config_20260217-184200\`
  - Key files:
    - `pytest.txt` (QA PASS)
    - `grep_proofs.txt` (factory + pipeline invariants)
    - `rollback.txt` (rollback steps)


## Current Risks
- No git history => change tracking/review gates are weaker (mitigation: optional git init task).
- Stage 1 percent split is implemented (evidence: docs\evidence\T1.5_20260216-031619\pytest_T1.5.txt + docs\evidence\T1.5_20260216-031619\runtime_tmp_routing_test.txt).
- T1.6 canary execution (%10) runtime proof + rollback verified (evidence: docs\evidence\T1.6_20260216-042251\verify_T1.6_runtime.txt + docs\evidence\T1.6_20260216-042251\runtime_tmp_routing_test_T1.6.txt).
- Stage 1 production-ready gate passed (evidence: docs\evidence\T1.6_20260216-042251\verify_T1.6_runtime.txt + docs\evidence\T1.6_20260216-042251\runtime_tmp_routing_test_T1.6.txt).
- Docs encoding mojibake observed in console copy => need consistent UTF-8 handling for SSOT.

## Next Action (Verifier-gated)
- Define + implement Stage 1 deterministic percent split per DECISIONS.md D-007 (with rollback).

## Evidence Update (Step-3)
- Encoding mojibake is a PowerShell display artifact; files read correctly with UTF-8.
- execute_request_v1 is defined at: src/mcp_server/manager.py:173 (definition).
- execute_request_v1 call-site exists via MCPAgentServer._generate_text routing switch (src/mcp_server/agent_server.py:79-95) and is wired from ServerManager into MCPAgentServer (src/mcp_server/manager.py:52-58, 78-84).
- data/config.json: no keys matching pipeline|v1|opt|rollout|gate|enable.




## Historical Blocking Evidence (Step-5) — resolved in T0.5/T0.6/T0.8
- Build gate was failing in Step-5 (missing flet); resolved in T0.5 (flet + entrypoint fix + PyInstaller).
- QA gate was failing in Step-5 (missing pytest); resolved in T0.6 (pytest + baseline test run).
- Legacy provider calls exist in multiple layers (bypass risk):
  - src/mcp_server/agent_server.py:66/74
  - src/mcp_server/manager.py:134/142
  - src/ui/main_window.py:574/583
- Pipeline V1 is runnable via env opt-in MCP_ROUTER_USE_V1 (see: ## Pipeline V1 Activation Status (T0.8)).


## QA Gate Status
- QA gate is unblocked: pytest installed (9.0.2) and baseline test run passes:
  - .\venv\Scripts\python.exe -m pytest -q tests\test_pipeline_v1.py -vv → 5 passed in 4.09s

## Blocking Evidence Update (Step-6)
- QA gate was failing in Step-5 due to missing pytest; now resolved:
  - .\venv\Scripts\python.exe -m pytest --version → pytest 9.0.2
  - .\venv\Scripts\python.exe -m pytest -q tests\test_pipeline_v1.py -vv → 5 passed in 4.09s


## Build Gate Status
- Build gate is unblocked: flet pack packaging completes and produces dist\MCP Router.exe (legacy filename).
- Root cause was incorrect entrypoint (python -m flet); fixed by using .\venv\Scripts\flet.exe.
- PyInstaller installed to satisfy flet pack dependency.

## Known-good dependency set (SSOT drift check)
- requirements.txt pins:
  - flet==0.80.5
  - pyperclip==1.11.0
- venv verification:
  - pip show flet → Version: 0.80.5
  - flet.exe --version → Flet: 0.80.5
  - pyperclip import → 1.11.0
- Note:
  - flet.__version__ may return None; CLI and pip metadata are used as authoritative evidence.



## UI Integration Status (T0.7)
- Direct provider call exists only in UI ""Test"" action (not production request path):
  - src/ui/main_window.py:702-705 (Test button)
  - src/ui/main_window.py:574-585 (VertexAIClient.generate_content)
- No production prompt/send/execute_request flow found in UI scan.
- ServerManager is used for agent operations (create/start/stop) in UI.


## Pipeline V1 Activation Status (T0.8)
- Activation mechanism: env var `MCP_ROUTER_USE_V1` selects routing inside `MCPAgentServer._generate_text`.
- Default remains legacy when env var is unset.
- Path logging:
  - legacy: `routing=legacy agent_id=... prompt_len=...`
  - v1: `routing=v1 agent_id=... prompt_len=...`
- Evidence (same prompt, same instance):
  - OUT1 (legacy): `LEGACY_OK`
  - OUT2 (v1): `V1_OK`






- Runtime proof (agent started + same prompt, both routes):
  - routing=legacy ... prompt_len=4 -> OUT1: LEGACY_OK
  - routing=v1 ... prompt_len=4 -> OUT2: V1_OK
  - agent_id=f80e81c2-cb67-4d71-9baf-c74e851ff830 port=5009
  - Note: uvicorn CancelledError during stop is shutdown noise (does not affect routing proof).



## Stage 1 Activation Standard (Implemented)

- Purpose: define the exact activation interface and log schema before any Stage 1 code change.
- Source of truth: DECISIONS.md D-007.

### Env vars
- Stage 0 override: `MCP_ROUTER_USE_V1` ⇒ force V1.
- Stage 1 percent split: `MCP_ROUTER_V1_PCT` (int in `[0,100]`) ⇒ deterministic split.
- Precedence (routing decision order): `MCP_ROUTER_USE_V1` > valid `MCP_ROUTER_V1_PCT` > legacy default.
  - Invalid / non-integer / out-of-range `MCP_ROUTER_V1_PCT` behaves as “unset” (falls through to legacy default).

### Split key + hash
- `split_key = agent_id + <LF> + prompt`
- Hash algorithm: SHA-256 only.
- `key_type=agent_id_prompt`
- `key_hash_prefix` = first 8 hex chars of `sha256(split_key)` digest.

### Stage 1 log fields (standard; must appear once implemented)
- `routing=legacy|v1`
- `outcome=force_v1|pct_v1|pct_legacy|legacy_default`
- `pct=<0..100>` (only when Stage 1 percent split is evaluated)
- `bucket=<0..99>` (only when Stage 1 percent split is evaluated)
- `key_type=agent_id_prompt`
- `key_hash_prefix=<8-hex>`
- Keep existing fields: `agent_id`, `prompt_len`

- Current status: Stage 1 percent split mechanism is **IMPLEMENTED**; T1.6 canary execution (%10) proof is **PASS** (evidence: docs\evidence\T1.6_20260216-042251\verify_T1.6_runtime.txt + docs\evidence\T1.6_20260216-042251\runtime_tmp_routing_test_T1.6.txt).

- T2.2 Usage → Cost Map Discovery:
  - Evidence root: docs\evidence\T2.2_usage_cost_map_20260216-103822\
  - Key files:
    - usage_db.linenum.txt
    - log_usage.callsites.txt
    - pipeline_v1.flow_extract.txt
    - enforcement.search.txt
    - db.rows.txt

---

## Phase 1.5 — Stabilization / Close-out

- Status: **CLOSED (stable)**
- Date: 2026-02-18
- Evidence: docs/evidence/T1.5_flip_ssot_20260218-000100/
- Locked proofs:
  - Vertex streaming determinism: stream=True => NotImplementedError (no silent ignore)
  - No silent swallow (scoped):
    - UI refresh_loop: no except: pass; visible error path
    - CredentialManager.delete_credential: no silent pass; visible warning path
  - Tests: pytest -q PASS (exit code 0)


- T2.E Bedrock real-call gate implemented (explicit opt-in; post-MVP):
  - Evidence root: docs\evidence\T2E_bedrock_realcall_20260218_053156\

- T2.F Hugging Face start authorization (docs-only):
  - Evidence root: docs\evidence\T2F_hf_start_auth_20260218-054605\

- T2.G Hugging Face provider implemented (Inference API over HTTP, deterministic, non-streaming):
  - Evidence root: docs\evidence\T2G_hf_provider_20260218-055322\

- T2.H Hugging Face real-call gate implemented (explicit opt-in; post-MVP):
  - Evidence root: docs\\evidence\\T2H_hf_realcall_gate_20260218-060300\



- T0.3 UI/UX triage opened (crash + destructive action correctness):
  - Evidence root: docs\evidence\T0.3_triage_20260218-080141\


- T0.3.P0 UI crash + destructive action correctness fixed:
  - Evidence root: docs\evidence\T0.3_triage_20260218-080141\

- T0.3.P1 Bridges list ordering fixed (new bridge appears at top):
  - Evidence root: docs\evidence\T0.3P1_ui_triage_20260218-082900\


- T0.3.P2 ProbeAgent stale status reconcile fixed (running -> stopped via local port probe on refresh):
  - Evidence root: docs\evidence\T0.3.P2_20260218-085543\


- T2.Y Remove or justify duplicate tree src/mcp_server/1 — Evidence root: docs\evidence\T2Y_remove_dup_tree_20260220-054120\

# Phase 2 — Core Productization: DONE

- MVP.1 Release gate (Vertex + Azure): PASS
  - Date: 2026-02-20
  - Smoke tests: PASS (evidence: docs\evidence\MVP1_smoke_tests_20260220-064633\smoke_tests.out.txt + smoke_tests_exit_code.txt)
  - MCP probe: PASS (evidence: docs\evidence\MVP1_smoke_run_20260220-064637\mcp_probe\initialize.* + tools_list.* + tools_call.* + probe.out.txt + probe.err.txt)

- MCP Tool Discovery: PASS (evidence: docs\evidence\T2X_mcp_tool_discovery_probe_20260220-044918\)
- Headless harness surface: PASS (canonical commands recorded under T2.X in STATUS)
- Usage contract: PASS (evidence: docs\evidence\G_P2_pytest_and_determinism_20260220-051113\)
- Determinism audit: PASS (evidence: docs\evidence\T2Y_remove_dup_tree_20260220-054120\)

- T3.B Safe code deletion batch-1 (generated artifacts only) — Evidence root: docs\evidence\T3B_delete_generated_artifacts_20260220-054924\
  - Result: removed src/**/__pycache__/ and src/**/*.pyc; pytest PASS
- T3.C Legacy path retirement decision gate (docs-only) — Decision: D-022

# Phase 3 — UI Shell/Rewrite (Historical carry-over)
- Policy reminder: Phase 2 forbids UI code changes (see D-019).
- Items below are historical carry-over; do NOT reopen UI work under Phase 2.

- T0.3.P3 UI smoke/layout stabilization fixed:
  - Evidence root: docs\evidence\T0.3.P3_ui_smoke_20260220-065459\

## P3.TS1 — UI thin shell compliance (D-024)
- Evidence: docs\evidence\G_P3_thinshell_boundary_probe_20260221-003424\
- Result: Proven (MATCHES=0; dispatch chain UI->ServerManager). 
## P3.BE1 — Backend health proof (pytest + D-024 safe)
- Evidence:
  - docs\evidence\G_P3_backend_health_fix_importerror_20260221-014205\  (PYTEST_EXIT_CODE=0)
  - docs\evidence\G_P3_thinshell_boundary_probe_20260221-003424\  (MATCHES=0)
- Result: PASS
## P3.BE2 — Backend regression guardrails (pre-UI rewrite)
- Evidence: docs\evidence\G_P3_backend_regression_guardrails_<timestamp>\
- Result: TBD (PASS only when proofs recorded)

## P3.BE3 — Backend health proof: single-command reproducible runner
- Evidence: docs\evidence\G_P3_backend_health_runner_<timestamp>\
- Evidence run: docs\evidence\G_P3_backend_health_runner_20260221-034734\
- Result: PASS
## P3.BE2A — Core provider-agnostic compliance: remove provider-specific tool routing from core
- Evidence: docs\evidence\G_P3_core_provider_specific_violation_20260221-024237\
- Result: BLOCKED (BYOK key required; no key provided in SSOT)
## P3.BE4 — Headless backend smoke (pre-UI rewrite)
- Evidence: docs\evidence\G_P3_headless_backend_smoke_<timestamp>\
- Result: TBD
- Evidence run: docs\evidence\G_P3_headless_backend_smoke_20260221-035548\
- Result: PASS (SMOKE_EXIT_CODE=0; PYTEST_EXIT_CODE=0)
## P3.F1 — Copy Config UX (contract-first; headless proof)
- Evidence: docs\evidence\G_P3_copy_config_contract_<timestamp>\
- Result: TBD

## P3.F2 — CSV Export (headless) implement + evidence
- Evidence: docs\evidence\G_P3_csv_export_headless_<timestamp>\
- Result: PASS
- Evidence run: docs\evidence\G_P3_copy_config_contract_20260221-042830\
- Result: PASS (IDENTICAL=1; SECRET_MATCHES=0; PYTEST_EXIT_CODE=0)
- Evidence run: docs\evidence\G_P3_csv_export_headless_20260221-045807\
- Result: PASS (export.csv + SHA256; UI dispatches to core; UI file-write MATCHES=0; PYTEST_EXIT_CODE=0)
## P3.F3 — Budget Guard (monitor-only) contract + headless report
- Evidence: docs\evidence\G_P3_budget_guard_monitor_<timestamp>\
- Result: PASS
- Evidence run: docs\evidence\G_P3_budget_guard_monitor_20260221-051533\
- Result: PASS (IDENTICAL=1; RAISE_MATCHES=0; PYTEST_EXIT_CODE=0)
## P3.PR1 — Google AI Studio provider (contract-first; docs-only)
- Evidence: docs\evidence\G_P3_aistudio_contract_<timestamp>\
- Result: TBD
- Policy update:
  - Deferred to post-MVP; implementation blocked pending written ToS clarification/approval (D-026).
## P3.PR2 — Ollama provider (contract-first; docs-only)
- Evidence: docs\evidence\G_P3_ollama_contract_<timestamp>\
- Result: PASS
- Evidence run: docs\evidence\P3PR2_verify_20260222-073452\
## P3.PR2 — Ollama feasibility smoke (headless; non-streaming; no deps)
- Evidence: docs\evidence\G_P3_ollama_feasibility_<timestamp>\
- Result: TBD
- I1a: Ollama unreachable behavior (fail-fast; deterministic)
- Evidence: docs\evidence\G_P3_ollama_feasibility_20260221-063541\
- Result: PASS

- I1b: Ollama reachable smoke (requires local Ollama running)
- Evidence: docs\evidence\G_P3_ollama_reachable_<timestamp>\
- Result: TBD
- Evidence run: docs\evidence\G_P3_ollama_feasibility_20260221-071248\
- Result: PASS (EXIT_CODE=0; STREAM_KEY_MATCHES=0; SSE_MATCHES=0; PYTEST_EXIT_CODE=0)
## P3.LG1 — Final legal documentation pack (post-technical; docs-only)
- Evidence: docs\evidence\G_P3_legal_pack_<timestamp>\
- Result: TBD
## P3.PR3 — OpenAI provider (contract-first; docs-only; BYOK/local-only)
- Evidence: docs\evidence\G_P3_openai_contract_<timestamp>\
- Result: PASS
- Evidence run: docs\evidence\P3PR3_verify_20260222-074535\
## P3.PR4 — Anthropic provider (contract-first; docs-only; BYOK/local-only)
- Evidence: docs\evidence\G_P3_anthropic_contract_<timestamp>\
- Result: PASS
- Evidence run: docs\evidence\P3PR_batch_verify_20260222-080207\
## P3.PR5 — Groq provider (contract-first; docs-only; BYOK/local-only)
- Evidence: docs\evidence\G_P3_groq_contract_<timestamp>\
- Result: PASS
- Evidence run: docs\evidence\P3PR_batch_verify_20260222-080207\
## P3.PR3.I1 — OpenAI online feasibility smoke
Result: BLOCKED (BYOK key not provided; network calls disallowed by gate)
## P3.PR3 — Offline fake-provider proof (no network; high-confidence core test)
- Evidence: docs\evidence\G_P3_openai_offline_fake_provider_<timestamp>\
- Result: TBD
- Evidence run: docs\evidence\G_P3_openai_offline_fake_provider_20260221-083227\
- Result: PASS (IDENTICAL=1; NET_MATCHES=0; PYTEST_EXIT_CODE=0)
## P3.PR4 — Offline fake-provider proof (Anthropic) (no network; high-confidence core test)
- Evidence: docs\evidence\G_P3_anthropic_offline_fake_provider_<timestamp>\
- Result: TBD

## P3.PR5 — Offline fake-provider proof (Groq) (no network; high-confidence core test)
- Evidence: docs\evidence\G_P3_groq_offline_fake_provider_<timestamp>\
- Result: TBD
- Evidence run: docs\evidence\G_P3_pr4_pr5_offline_fake_provider_20260221-091705\
- Result: PASS (IDENTICAL=1; NET_MATCHES=0; PYTEST_EXIT_CODE=0)
- Evidence run: docs\evidence\G_P3_pr4_pr5_offline_fake_provider_20260221-091705\
- Result: PASS (IDENTICAL=1; NET_MATCHES=0; PYTEST_EXIT_CODE=0)
## P3.PR7 — LM Studio provider (contract-first; docs-only; local-only)
- Evidence: docs\evidence\G_P3_lmstudio_contract_<timestamp>\
- Result: PASS
- Evidence run: docs\evidence\P3PR_batch_verify_20260222-080207\
## P3.PR7 — LM Studio reachable smoke (headless; non-streaming; no deps)
- Evidence: docs\evidence\G_P3_lmstudio_feasibility_<timestamp>\
- Result: TBD

## Roadmap (Next)
- 1) PR7.I1 LM Studio feasibility → PASS required before enabling LM Studio
- 2) P3.P1/P3.P2/P3.P3 contract-first docs-only
- 3) PR3.I1 OpenAI online feasibility (BYOK key required) — BLOCKED until key provided
- 4) Phase 4 UI PREP (architecture-first; thin shell; see D-029)
- 5) Documentation closeout (post-UI): P3.LG1 + User Guide

## P3.P1 — Interceptor (JSON syntax repair) (contract-first; docs-only)
- Evidence: docs\evidence\G_P3_interceptor_contract_<timestamp>\
- Result: TBD

## P3.P2 — Persona Lite (system prompt injection) (contract-first; docs-only)
- Evidence: docs\evidence\G_P3_persona_lite_contract_<timestamp>\
- Result: TBD

## P3.P3 — Context caching (contract-first; docs-only)
- Evidence: docs\evidence\G_P3_context_caching_contract_<timestamp>\
- Result: TBD
- Evidence run: docs\evidence\G_P3_lmstudio_feasibility_20260222-001041\
- Result: PASS (EXIT_CODE=0; STREAM_KEY_MATCHES=0; SSE_MATCHES=0; PYTEST_EXIT_CODE=0)



## P4 — UI (Tauri + SvelteKit) thin-shell

### P4.PREP gates
- P4.1 docs contract updated — (see TASKS for required evidence)
- P4.2 guard gates PASS (evidence: docs\evidence\P4_2_guard_run_20260222-121431)
- P4.3 strict entrypoint/guard PASS (evidence: docs\evidence\P4_3_strict_guard_run_refined_20260222-122356)
- P4 UI PREP exit criteria satisfied: P4.1/P4.2/P4.3 PASS (see TASKS anchors)

### UI milestones (evidence-indexed)
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

### UI design language
- Design language captured in docs\UI_STYLE_GUIDE.md
- Shared primitives captured in ui-tauri\src\app.css ("UI Primitives (Dashboard Design Language)")

  - P5.7 Dry-run test binding PASS (deterministic trace): docs\evidence\P5_7_DRYRUN_BIND_VERIFY_20260226-030311
