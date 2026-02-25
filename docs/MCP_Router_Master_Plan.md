# MCP Router — Master Plan (Locked)

## Opportunity focus (what we’re building for)
**We win where IDEs already feel “easy” (1‑click MCP installs), but the provider does *not* have a native MCP server.**  
So the product is not “another IDE feature” — it’s a **local, reliable gateway** that turns *any* API-only AI service into an MCP-ready bridge with:
- safe credential handling,
- deterministic routing pipeline,
- operational usage/metrics,
- simple “copy config to IDE” UX.

### Vibe-coder usage example (the product in 30 seconds)
You’re in Cursor/VS Code/TRAE, you want **Gemini/Vertex** (because you have credits) but you don’t want Google tooling inside your IDE.

1) Open our app → “+ New Bridge” → paste **service account JSON path** (stored as path in keyring) and pick model  
2) Click **Copy Config** → paste into IDE MCP config  
3) In IDE: call the MCP server like any other tool → responses stream over SSE  
4) Back in app: **Usage** shows *success rate / latency / tokens / cost* per bridge and time range  
5) If something breaks, you get a **local audit trail** (no prompt/response logging).

That’s the “friction killer” for entry-level builders.

---

## Product line split (locked early, licensing later)
### CORE (never licensed)
- Router / MCP bridge
- Multi-agent management
- Usage **basic** stats + local persistence
- Deterministic pipeline (V1 principles)
- Basic UI (Bridges + Usage)

### EXTENDED (can be licensed later)
- Advanced routing (fan-out, branches, retries/failover policies)
- Chain Editor (Wizard v1 → later graph)
- Persona / Memory studio
- Quota guard (per-agent limits)
- Advanced analytics + snapshots
- Export (usage/chain/persona packs)
- Auto-update / signed installer conveniences

(Keep this split in the roadmap doc; implementation can stay open-core / closed-core later.)

---

## Ground truth snapshot (what already exists)
- UI already has **MCP Bridges** and **Usage** tabs, with “Copy Config” and a landing/help link. fileciteturn12file9  
- Usage view already computes KPI cards (Total Requests/Tokens/Cost/Success Rate/Avg Latency) from DB-filtered rows. fileciteturn12file9  
- Tests exist that verify V1 writes success/error rows + filters work. fileciteturn12file10  

---

## Constraints we accept (explicitly)
- **No Electron/Tauri rewrite.**
- “Local model *in-app* orchestration” (running models) is **later**.
- “Ollama *bridge*” is **kept** as the universal identity (IDE ↔ local Ollama via our MCP bridge).

---

# Roadmap (phased, stability-first)

## Phase 0 — Stabilization + SSOT hygiene (short, mechanical)
**Goal:** keep shipping without turning into a “forever project”.

Deliverables
- Single “How to run” + “How to test” commands in docs
- Evidence discipline: each phase has a tiny evidence pack folder under `docs/evidence/`

Exit checklist (evidence-based)
- `pytest -q` passes
- One cold-start run documented (log snippet + config file)

---

## Phase 1 — Usage becomes “Operational Reliability” (A — first priority)
**Goal:** the product feels like a trustworthy gateway, not a toy.

Scope
- DB is the only source of truth for KPIs/filters (already moving in this direction)
- Expand usage row model to support ops KPIs consistently:
  - status, latency_ms, error_type, request_id, provider, model_id
- Ensure “error row is written even when provider call fails” while still re-raising errors (observer remains non-blocking)

Exit checklist
- Evidence: schema before/after + sample rows
- Tests: success + error row written + filtering works
- UI smoke: filters + refresh + export + clear history (see UI checklist below)

---

## Phase 2 — Provider Adapter refactor to make “Universal” realistic
**Goal:** adding new providers is *surgical*, not a rewrite.

Scope
- Introduce a provider-agnostic adapter interface (minimal shape):
  - `execute(prompt, stream=False) -> {text, tokens_in, tokens_out, cost_usd, model_id, provider, raw_error?}`
- Keep Router/Guard/Observer boundaries intact
- Define provider capability flags (streaming, tool-calls, etc.) without leaking provider logic into UI

Exit checklist
- Add one “toy provider adapter” (mock) and prove pipeline wiring with tests
- Document “How to add a provider adapter” in 15 lines max

---

## Phase 3 — Universal Bridge targets (B — second priority)
**Goal:** win on “non-native MCP” integrations.

Scope (initial)
- **Ollama bridge**: connect to user’s local Ollama and expose as MCP server
- Add one mainstream API provider (OpenAI or Anthropic) *only after* Phase 2 adapter refactor is stable
- Keep creds handling local-first (API keys / paths in keyring where applicable)

Exit checklist
- One bridge works end-to-end in an IDE (copy config → call → usage row written)
- “Failure path” produces an error row and clear UX messaging

---

## Phase 4 — Chain Editor v1 (Wizard)
**Goal:** add real value without UI complexity blow-up.

Definition (v1)
- **Sequential** chain first (form wizard): Step 1 → Step 2 → Step 3
- Each step can target:
  - a bridge (provider) + model
  - a prompt template
- Output of step N becomes input to step N+1

Non-goals (Phase 4 v1)
- Parallel fan-out (A→B and A→C simultaneously) is **Advanced Routing** (Phase 5+)
- Graph drag-drop is a later upgrade (Phase 4.2)

Why it adds value even though we already have multiple bridges
- Bridges are “connectivity units”
- Chain wizard is “workflow unit” — reusable multi-call patterns *without* external orchestration tools

Exit checklist
- Wizard can save/load a chain config locally
- Run chain produces multiple usage rows (one per step) with the same request_id group marker (optional)

---

## Phase 5 — Persona/Memory studio (lite → pro)
**Goal:** keep it optional and non-invasive.

v0 (lite)
- JSON persona profile attached to a chain step (injected into prompt)

Later (pro)
- Local embeddings + searchable memory
- Export/import persona packs

Exit checklist
- Persona injection is deterministic and testable (snapshot-style tests)

---

# Cross-cutting checklists (SSOT rules)

## UI Phase Exit — Smoke Checklist (5–10 items)
1) Cold start: window opens with stable size (no visible resize jump if possible)  
2) “+ New Bridge” creates a bridge and it appears in list  
3) Start/Stop works for an existing bridge  
4) Copy Config puts valid JSON on clipboard  
5) Usage Refresh updates KPI cards and table  
6) Date range filter changes rows (Last 1h / 24h / All)  
7) Export CSV writes a file under `data/exports/`  
8) Clear History prompts with **Cancel as default focus** (UX fix)  
9) Help opens landing page  
10) App closes without crashing (no orphan background process)

Evidence rule: each item has either a log line, a screenshot, or a command output.

## “At least one clean install / first launch test”
Add this as a single sentence rule in SSOT:
- Every UI phase must include **one clean-start run** (fresh state) to catch flicker/storage/first-run issues.

---

# Naming strategy (least painful)
**Do not lock a public name now.**  
Instead, make renaming cheap by centralizing:
- `APP_DISPLAY_NAME`
- `LANDING_URL`
- window title strings
- installer metadata placeholders

When we pick a final name, we run a short “rename checklist” across UI title, docs, and packaging.

---

# Operating model (how we execute with TRAE agents)
- **New phase = new Task in TRAE**, not one infinite task.
- Each task starts with: “read SSOT docs + last evidence pack + current STATUS.”
- Solo Coder does implementation.
- We (humans) trigger:
  - **Verifier** at phase gates (PASS/FAIL only)
  - **Debugger** only when we have an error/stack trace
  - **Reviewer** when we need design critique or UX wording
- Keep callables off unless you intentionally want cross-agent invocation.
