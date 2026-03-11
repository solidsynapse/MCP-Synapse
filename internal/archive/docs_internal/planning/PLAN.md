# PLAN — Stabilization → Gates → Pipeline V1 Rollout

## Principles
- No assumptions: every plan item must link to evidence (file+line or command output).
- SSOT: docs/* is the only source of truth.

## Milestones (Gated)

### M0 — SSOT Baseline (Docs)
Goal: STATUS/PLAN/TASKS/DECISIONS exist and are internally consistent.
Gate:
- `tree docs /F` shows all 4 files.
- Each file has "Evidence Index" or references to the others.

### M1 — Activation Path Discovery (V1 vs Legacy)
Goal: Determine exactly how V1 can be invoked today.
Gate (evidence required):
- Exact file+line: where legacy vs V1 is selected.
- Exact file+line: execute_request_v1 definition and call sites (if any).
- Config key(s) influencing selection (if any) with proof from data/config.json + config manager code.

### M2 — Build Gate (Deterministic)
Goal: One deterministic build/run command documented.
Gate (evidence required):
- `python --version` output
- `pip --version` output
- `python build.py --help` output (or actual run command) captured
- requirements.txt head captured

### M3 — QA Gate (Deterministic)
Goal: One deterministic test command documented.
Gate (evidence required):
- `python -m pytest --version` output (or alternative test runner)
- One test run output (start → end) captured
- List of tests considered baseline (e.g., tests/test_pipeline_v1.py, src/tests/test_phase*.py) [baseline set is evidence-driven]

### M4 — Stabilization Checkpoint
Goal: STATUS.md checkpoint criteria satisfied with links to evidence.

### M5 — Rollout Plan Ready
Goal: incremental activation plan (% opt-in → 10 → 50 → 100) written with gates + rollback.

#### Stage 1 activation standard (SSOT; not implemented yet)
- Source of truth: DECISIONS.md D-007.
- Control env vars:
  - Stage 0 override: `MCP_ROUTER_USE_V1` ⇒ force V1.
  - Stage 1 percent split: `MCP_ROUTER_V1_PCT` (int 0–100) ⇒ deterministic bucket split.
- Precedence: `MCP_ROUTER_USE_V1` > valid `MCP_ROUTER_V1_PCT` > legacy default.
- Hash standard: SHA-256 only.
- Split key: `split_key = agent_id + <LF> + prompt` (prompt-bazlı split bilinçli kabul).
- Logging standard (Stage 1): routing, pct, bucket, key_type, key_hash_prefix, outcome.


## Deliverables
- docs/STATUS.md (state + checkpoint criteria + evidence)
- docs/PLAN.md (this file)
- docs/TASKS.md (prioritized backlog with evidence fields)
- docs/DECISIONS.md (ADR-style decisions + rationale)

## SOP — Builder ↔ Verifier Workflow (SSOT + Gates)


### Roles
- Builder: implements changes and produces evidence outputs.
- Verifier: blocks next step until evidence is provided and matches gates.

### SSOT Rules
- Every change must be reflected in docs/STATUS.md, docs/PLAN.md, docs/TASKS.md, docs/DECISIONS.md.
- Chat is not a source of truth.

### Evidence Format (mandatory)
Each task must include:
- File evidence: <path>:<line> (for code/design decisions)
- Command evidence: exact command + pasted output (logs allowed)
- If failure: paste the error output as evidence and log as a blocking task.

### Daily Rhythm (15–30 min cycles)
1) Builder selects exactly one task from docs/TASKS.md (P0 first).
2) Builder writes intended change in docs/TASKS.md under the task (1–3 bullets).
3) Builder executes change and collects evidence.
4) Builder updates docs/STATUS.md (what changed + evidence refs).
5) Verifier checks gates:
   - If pass: marks task Done evidence complete.
   - If fail: adds blocking note + required evidence.

### Gate Checklist (must pass before rollout expansion)
Build Gate:
- python --version + pip --version evidence
- python build.py --help OR documented reason it cannot run + blocking task

QA Gate:
- python -m pytest --version OR documented reason it cannot run + blocking task
- One deterministic test command output (once pytest is available)

Pipeline Activation Gate:
- Explicit call-site exists for V1 (file+line)
- Legacy call path remains available (file+line)
- Opt-in selection mechanism is evidenced (env/flag/config) with proof

UX/Integration Gate:
- UI must not call provider directly for production path (file+line evidence)
- UI routes through ServerManager for requests (file+line evidence)

Rollback Gate:
- Single switch disables V1 and forces legacy path (evidence: file+line + log proof)

## Rollout Plan — Pipeline V1 (opt-in → 10% → 50% → 100%)


### Stage 0 — Opt-in (developer-only)
Activation:
- Mechanism: explicit switch (env var or request flag) — must be evidenced in code (file+line).
Gates:
- V1 call-site exists in Server/Manager layer (file+line).
- Legacy path still callable (file+line).
- Log evidence shows which path executed (V1 vs Legacy) for the same prompt.
Rollback:
- Disable switch forces legacy (file+line + log proof).

### Stage 1 — 10%
Activation:
- Route 10% of eligible requests via V1 (eligibility definition must be documented).
Gates:
- Usage logging still non-blocking (proof: observer try/except in V1 + one forced DB failure does not break response).
- Error rate comparison: V1 error rate <= legacy error rate (requires log counters).
Rollback:
- Immediate switch back to Stage 0 (opt-in only) if error spike observed.

### Stage 2 — 50%
Activation:
- Route 50% via V1 for same eligible set.
Gates:
- Build gate + QA gate must be green (tooling installed and one deterministic test run output exists).
- UI integration gate: production path must route via ServerManager (no direct VertexAIClient calls in UI for the production request path).
Rollback:
- Force legacy for all traffic with single switch.

### Stage 3 — 100% (default)
Activation:
- V1 is default for eligible requests; legacy remains as fallback.
Gates:
- Clear fallback rule documented (when to fallback to legacy).
- Regression test baseline exists and passes.
Rollback:
- Default flips back to legacy with a single switch; V1 remains available for debugging.

---

## Build Phase — Start (post-stabilization)

**Entry criteria (PASS):**
- Stage 1 deterministic percent split IMPLEMENTED (T1.5) with pytest + runtime proof
- Stage 1 canary execution (%10) proof PASS + rollback proof (T1.6)
- Stabilization Closeout recorded in docs/ARCHITECTURE_EVOLUTION_LOG.md

**Operating rules:**
- One change-set per task: code + tests + evidence (when relevant) + SSOT update (only if state changes)
- No new decision points for routing; Stage 1 decision remains inside `MCPAgentServer._generate_text()`

**Next focus (Build Phase):**
- Define next tasks as feature work items (telemetry hardening / cost & limits / Stage 2 rollout), each with explicit PASS evidence.
