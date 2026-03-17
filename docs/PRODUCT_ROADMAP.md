# MCP Synapse â€” Product Roadmap (Authoritative)

> **Status:** Active reference roadmap. Subordinate to `.gsd/DECISIONS.md` and `.gsd/REQUIREMENTS.md` as normative SSOT.  
> **Replaces:** All historical strategy documents, feature lists, master plans, and feasibility reports.  
> **Location:** `docs/PRODUCT_ROADMAP.md` â€” archive reference under docs/, subordinate to `.gsd/` SSOT.  
> **Governance:** Changes require explicit decision entry in `.gsd/DECISIONS.md`. In case of conflict, `.gsd/DECISIONS.md` wins.

---

## Product Identity (Locked)

MCP Synapse is a **local, deterministic MCP router** for developers who want to use any AI provider through their IDE without managing provider complexity directly.

**Core value proposition:**
- Any API-only AI service becomes an MCP-ready bridge in seconds
- Credentials stay local (BYOK, keyring, no cloud dependency)
- Full operational visibility: cost, latency, tokens, success rate per bridge
- Deterministic pipeline â€” no hidden retries, no silent fallbacks, no surprises

**Licensing stance:** Source-visible, closed license. Not MIT. Commercialization planned at monetization phase.

**The user journey in three sentences:**  
You open MCP Synapse, add a provider connection with your own credentials, copy the generated config into your IDE, and immediately get usage telemetry. No cloud account needed, no vendor lock-in, no black box. When something breaks, there's a local audit trail.

---

## Strategic Arc (The Three Phases)

### Phase I â€” IDE-Focused Hardening (Now â†’ v0.9.x)
**Goal:** Become the most reliable local MCP router for vibe-coders and solo builders.  
**Distribution:** Free. Open to grow. Wins by trust, not feature count.  
**Success signal:** Developer installs it, connects a provider, uses it in their IDE for a week without friction.

### Phase II â€” Pro Developer Surface (v1.0 â†’ v1.2)
**Goal:** Add depth that makes professional developers choose this over rolling their own.  
**Distribution:** Still free core. Optional paid features begin forming.  
**Success signal:** Developer uses chain editor or advanced routing in a real workflow.

### Phase III â€” Domain-Agnostic Platform (v1.3+)
**Goal:** The execution fabric becomes a foundation for vertical products (legal, finance, R&D).  
**Distribution:** Commercial. Plugin/hook architecture enables domain adapters.  
**Success signal:** A domain-specific adapter ships on top of the core without modifying the core.

---

## Current State (as of v0.6.1)

### What is delivered and working
- Pipeline V1 routing (deterministic execution, no silent fallback)
- Provider support: Vertex AI, OpenAI, Azure OpenAI, HuggingFace, Ollama (first-release surface)
- Bedrock: coded, not runtime-proven (own quota blocked testing â€” carry-forward to v0.8.x)
- Connection lifecycle: create / edit / delete / start / stop / preflight / copy config
- Usage: Summary + History with filters, CSV export
- Dashboard: KPI cards, 30-day cost trend, cost breakdown, health alerts, recent requests, top expensive
- Persona Lite: deterministic system prompt injection
- Optimizations: context cache + request deduplication runtime effect
- Interceptors: JSON syntax repair runtime effect
- Budget Guard: monitor-only (enforcement intentionally deferred â€” D-031)
- Settings: get/set/persist/validate
- Tauri + SvelteKit thin-shell UI (UI never calls provider clients directly)

### What is coded but not proven
- Bedrock provider adapter (own quota blocked runtime verification)

### What is intentionally absent
- Chain Editor (planned Phase II)
- Advanced routing: fan-out, branch, retry policies (planned Phase II)
- Persona/Memory Studio pro level (planned Phase II)
- Domain adapters (planned Phase III)
- Sigstore integrity + auto-update notify (v0.9.x) - commercial signed installer post-revenue per D-038
- Budget enforcement toggle (deferred by D-031 until dedicated package)

---

## Milestone Map (v0.7.x â†’ v1.3+)

> Normative milestone sequence per D-037 (updated). In case of conflict, `.gsd/DECISIONS.md` is authoritative.

---

### M002 â€” v0.7.x: Release Hardening âœ… COMPLETE
**Already done. Recorded for continuity.**

- Runtime hotfix closure (worker default ON, lazy imports)
- RC-EXT hygiene pack (health alerts, shortcuts, security minimum, debuggability)
- Packaging and install/uninstall readiness
- Repo and release surface sync (README, SECURITY, release docs v0.6.1)

---

### M003 â€” v0.8.x: Capability Depth + Provider Wave 1 âœ… COMPLETE

**Theme:** Make the product trustworthy at a deeper level â€” cost transparency, provider completeness, and documentation that a professional developer can rely on.

**Why this comes before domain-agnostic migration:**  
Adding providers now fits the current architecture cleanly. Doing domain-agnostic migration first would mean adding providers twice (before and after the contract change). The right order is: prove the provider wave works in the current model, then migrate.

#### S01 â€” Cost Transparency Layer + litellm Integration
**Scope:**
- Integrate **litellm** as the unified cost normalization layer â€” replaces per-provider `_estimate_cost()` functions
- Add `cost_source` field: `ACTUAL` / `ESTIMATED` / `UNKNOWN` per provider
- UI cost badge showing source type (so users know when cost is a guess)
- Cross-provider cost normalization: OpenAI, Azure OpenAI, Ollama currently return `cost_usd = None` â€” resolve via litellm or explicitly mark as UNKNOWN
- `estimation_confidence` field (LOW / MEDIUM / HIGH) â€” internal, feeds dashboard quality signal

**Why litellm:** The current codebase has separate `_estimate_cost()` functions per provider. Every new provider requires a new function, every pricing change requires updating multiple files. litellm provides a unified pricing database. This is the correct architecture for a multi-provider router.

**Migration:** Per-provider cost functions become thin adapters delegating to litellm. Where litellm has no data, explicit UNKNOWN is returned â€” never a silent zero.

**Not included:** pricing_version/timestamp, provider quality score â€” those are v1.1 depth.

#### S02 â€” Bedrock Runtime Proof (Blocked Deferred Lane)
**Scope:**
- Resolve own-account quota blocker (or use test account)
- Run full provider gate: preflight â†’ runtime smoke â†’ usage identity â†’ cost behavior
- Either PASS with evidence or explicitly BLOCKED with documented reason and public-facing note

**Current status:** R018 in `.gsd/REQUIREMENTS.md` â€” deferred/blocked pending SSOT promotion. This slice only activates if the quota blocker is resolved during M003. If not resolved, Bedrock remains deferred and explicitly labeled as "coded but not runtime-proven" on all public surfaces.

**Do not ship Bedrock as "supported" without runtime proof.**

#### S03 â€” Performance + Security Baseline Closure
**Scope:**
- Memory recheck: verify worker-ON steady RAM against <250 MB target (or document current band and set new target)
- Post-RC performance smoke: startup time, menu transition latency, dispatch latency under worker-ON
- Security baseline revalidation: credential flow, local storage, dispatch surface, error handling hygiene
- Pentest findings review: close open items or explicitly defer with documented reason

**Why:** These were deferred from RC. They cannot stay open indefinitely â€” a professional developer will ask about memory footprint and security before recommending the tool.

#### S04 â€” Documentation + Compliance Pack
**Scope:**
- Full English documentation: User Guide (install, connect, use, troubleshoot), Known Issues, Feature reference
- Legal/compliance minimum: privacy notice (local-only, no telemetry), retention/deletion policy, disclaimer
- P3.LG1 legal documentation pack completion
- In-app help baseline: credentials_path helper (S01 of tooltip system already exists â€” validate and extend minimally)

#### S05 â€” MCP Capability Types + IDE Compatibility Matrix
**Scope:**
- MCP capability type registry: copy config generates correct capability declarations per provider type (text, image, structured data) â€” fixes `_text_only` appearance in IDE tool pickers
- IDE compatibility matrix: one connection test + copy config verification for VS Code, Claude Code, Codex/GitHub Copilot, Gemini CLI
- Result documented as tested compatibility list

**Why:** The `_text_only` label in IDE tool pickers is a UX signal that the product only partially declares its capabilities. And untested IDE compatibility is invisible technical debt that surfaces as user-reported bugs.

### M004 â€” v0.9.x: Provider Wave 2 + Release Productization

**Theme:** Expand provider coverage and make the product shippable as a real product â€” Sigstore-backed release integrity, update channel, rollback.

#### S01 â€” Provider Wave 2: Anthropic + Groq + GLM
**Scope:**
- Anthropic provider adapter: contract exists (`anthropic_contract_pr4.py`), needs runtime client + factory registration
- Groq provider adapter: contract exists (`groq_contract_pr5.py`), needs runtime client + factory registration
- GLM (Zhipu AI) provider adapter: China-market path, API is MCP-ecosystem active
- Each must pass: preflight â†’ runtime smoke â†’ usage row written â†’ cost behavior via litellm
- UI provider picker updated

**Why Anthropic first:** Most-requested missing provider from target user base.
**Why Groq:** Speed differentiation â€” lowest latency option for vibe-coders.
**Why GLM over Alibaba:** GLM API is more mature and MCP-ecosystem active. Alibaba (Qwen) moves to v1.1.
**Why not LM Studio here:** Narrower local-model audience, lower urgency. Post-v1.0.

#### S02 â€” Provider Wave 2: Bedrock Resolution
**Scope:** Only if S02 of M003 did not achieve PASS. Final attempt or explicit public BLOCKED declaration.

#### S03 â€” Budget Enforcement Toggle
**Scope:**
- D-031 dedicated package: implement budget enforcement (block / throttle modes)
- This is the flip from monitor-only to actionable budget control
- Requires: separate SSOT decision, dedicated test suite, explicit user-facing control

**Why now:** By v0.9 the core is stable enough to add enforcement without regression risk. Budget guard has been monitor-only since the beginning. Professional developers expect actionable limits.

#### S04 â€” Release Productization (Revised)
**Scope:**
- **Sigstore** artifact integrity proof (free, developer-credible alternative to commercial signing)
- Auto-update channel: notify user of new version, manual install. Silent auto-install requires signed binary â€” deferred.
- Rollback procedure documented and tested
- Packaging: MSI (Windows) hardening, install/uninstall clean on all supported paths

**Sigstore integrity (D-038) stance:** Commercial certificate (~$300-400/year) deferred to post-revenue. Sigstore provides cryptographic artifact integrity for developer audience. UNSIGNED_NOTICE.md remains until commercial signing ships.

#### S05 â€” REST Adapter (Non-LLM Sources)
**Scope:**
- Any REST API endpoint becomes an MCP bridge via ProviderFactory
- User configures: endpoint URL, auth method, request/response mapping
- Usage telemetry: request count, latency, status â€” same as LLM providers
- Example use case: Binance market data â†’ IDE agent gets live price snapshot on demand

**Why now:** Fits current ProviderFactory architecture cleanly, no migration needed. Extends "everything-to-everything" from AI providers to any API. Strong differentiator â€” no other local MCP router does this.

**Not included:** WebSocket/streaming adapters â€” persistent connection management is cleaner post-migration. v1.3+.

---

### M005 â€” v1.0: Pro Developer Surface (Phase II Entry)

**Theme:** The product graduates from "reliable tool" to "platform developers build workflows on."

#### S01 â€” Chain Editor v1 (Sequential Wizard)
**Scope:**
- Sequential chain: Step 1 â†’ Step 2 â†’ Step 3
- Each step targets: a connection + model + prompt template
- Output of step N feeds input of step N+1
- Save/load chain config locally
- Each step produces a usage row; steps share a `chain_id` marker
- No parallel fan-out (that is Advanced Routing, v1.1)

**Why wizard first, not graph:** Graph drag-drop is a v1.2 upgrade. Wizard delivers 80% of chain value at 20% of UI complexity. Ship the wizard, learn from usage, then build the graph.

#### S02 â€” Advanced Routing Policies (Basic Set)
**Scope:**
- Retry policy: max attempts, backoff strategy (configurable per connection)
- Failover policy: primary â†’ fallback connection on error
- NOT included: fan-out (parallel), branch conditions â€” those are v1.2+

**Important:** This slice requires a new ADR amending D-029 before implementation. D-029 locks "no hidden retry/backoff/fallback." Retry and failover as explicit user-configured policies are architecturally different from hidden behavior â€” but the distinction must be formally recorded in `.gsd/DECISIONS.md` before any code is written. This slice is blocked until that ADR exists.

#### S03 â€” Vault UX Expansion
**Scope:**
- Vault basic (keyring-backed store/list/select/delete) is already delivered and working
- This slice covers: multi-credential profiles, connection-scoped vault selection UX polish, vault entry validation improvements
- No cloud sync, no team sharing â€” local only, BYOK boundary preserved (D-033)

#### S04 â€” Persona/Memory Studio Lite
**Scope:**
- Persona profiles: named profiles with system prompt templates, attachable to connections or chains
- Memory: session-scoped context (not persistent embeddings â€” that is pro level)
- Export/import persona profiles as JSON

**Why lite first:** Persistent embeddings and searchable memory require a local vector store â€” that is a significant dependency. Session-scoped memory delivers meaningful value without it.

---

## Post-v1.0: Domain-Agnostic Migration (Phase III)

This is the execution fabric transformation. It does not ship as a user-visible milestone â€” it is an architectural migration that happens beneath the surface while Phase II features continue shipping.

### Why this order (Phase II features before migration)
The domain-agnostic migration changes the core contract. Doing it before Phase II features means building Phase II features twice â€” once in the old contract, once in the new. That is wasteful and risky.

The correct sequence:
1. Ship Phase II features in the current architecture (v1.0 â†’ v1.2)
2. Migrate the core contract in a compatibility-first, phase-gated way (v1.3+)
3. Ship Phase III domain adapter packs on top of the new fabric

### Migration approach (when the time comes)
- **Compatibility-first:** old payload surfaces continue working via compatibility envelope
- **Phase-gated:** each migration phase has entry/exit criteria and evidence
- **Monitor-only policy start:** new hook system begins monitor-only, enforcement added per gate
- **Kill-switch:** every migration phase has a documented rollback

### What the migration enables (Phase III)
- Plugin/hook architecture: new capabilities added without touching core
- Domain adapter packs: legal, finance, R&D vertical products
- Provider capability registry: structured metadata, not hardcoded flags
- Full observability normalization: unified event schema across all providers
- Enterprise compliance packs: audit log, policy enforcement, data-boundary controls

### Provider expansion wave (post-migration, v1.3+)
Per PROVIDER_OTHERS_EXPANSION_MATRIX (original strategic document):
- V1.2: HuggingFace + Ollama hardening (already present, full gate pass)
- V1.3-A: LM Studio, Google AI Studio
- V1.3-B: GLM + fast iteration tool bridges
- V1.4+: RAG/DB layer (Postgres+pgvector, Qdrant, Pinecone)

---

## Feature Classification (Complete)

### Delivered (v0.6.1)
Pipeline V1, ProviderFactory, Connection lifecycle, Copy Config, Usage Summary/History/Export, Dashboard (KPI/trend/breakdown/alerts/recent/top-expensive), Persona Lite, Optimizations, Interceptors, Budget Guard (monitor-only), Settings, Vault basic (keyring store/select/delete), Thin-shell UI dispatch, Deterministic error contract, Runtime terminal proof discipline.

### Active (M003â€“M005)
Cost transparency layer, Performance/security baseline closure, Documentation/compliance pack, Anthropic + Groq providers, Budget enforcement toggle, Sigstore integrity (D-038), Auto-update, Chain Editor v1, Advanced routing (retry/failover), Vault UX expansion, Persona/Memory Studio Lite.

### Deferred (post-v1.0, pre-migration)
Pricing version/timestamp tracking, Provider quality score, Full tooltip/helper system, Usage Summary filter parity polish, Usage History row-details modal, Audit log (basic), Performance optimization pack (async+cache), Full destructive confirmations surface, LM Studio provider, Google AI Studio provider, Bedrock runtime proof (R018 - blocked pending quota resolution).

### Post-Migration (v1.3+)
Core RequestEnvelope/ExecutionResult/EventEnvelope v0, Compatibility adapter, Hook chain registry, Hook semantics (sync/async/timeout/cancel), Policy modules via executable hooks, Provider metadata contract cleanup, Observability capability/event schema, Dispatcher op registry modularization, Domain adapter packs, Enterprise compliance/audit packs, Advanced analytics/observability pack, Chain Editor graph upgrade, Persona/Memory Studio pro (persistent embeddings), Export packs (chain/persona), RAG/DB layer.

### Explicitly Out of Scope (never)
- Running models in-app (local model orchestration)
- Cloud credential storage or key pooling
- Proxy-as-a-service pattern
- Any architecture that breaks BYOK/local-only boundary (D-033)

---

## Architectural Constraints (Permanent)

These do not change. Any roadmap item that conflicts with these is rejected before planning.

| Constraint | Source | Rule |
|---|---|---|
| Thin-shell UI | D-024, D-029 | UI never calls provider clients. UI calls single core entrypoint. Provider/network logic lives in core only. |
| BYOK + local-only | D-033 | No shared keys. No proxy-as-a-service. Credentials stay on user's machine. |
| No silent fallback | D-029 | No hidden retry, no silent backoff, no undocumented behavior. Failures surface explicitly. |
| Deterministic pipeline | Core principle | Same input produces same routing decision. No probabilistic routing. |
| Evidence-first | D-002 | Nothing is DONE unless current repo state + SSOT + evidence align. |
| Normative versioning | D-037 | v0.7 â†’ v0.8 â†’ v0.9 â†’ v1.0 progression is locked. Minor bumps require milestone closure evidence. |
| Public repo surface | D-039 | Repo presents product-first surface. Internal orchestration materials stay internal. |

---

## Technical Reality (Code-Level Decisions)

### Current module inventory (verified from codebase)
| Package | Purpose | Status |
|---|---|---|
| `keyring` | OS keychain â€” Vault secret store/read/delete | Active, working |
| `google-cloud-aiplatform` | Vertex AI SDK | Active |
| `mcp` | MCP server/SSE surface and tool types | Active |
| `uvicorn` | ASGI server for MCP surface | Active |
| `tiktoken` | Fallback token count when Vertex metadata absent | Active |
| `flet` | Legacy Python desktop UI shell | Active but superseded by Tauri UI |
| `pyperclip` | Clipboard copy for config JSON | Active |
| `boto3` + `botocore` | Bedrock runtime client | Coded, not runtime-proven |

### Cost calculation â€” technical debt
Cost is currently calculated per-provider in separate functions:
- `openai_client.py` â†’ `_estimate_cost()`
- `azure_openai_client.py` â†’ `_estimate_cost()`
- `vertex/client.py` â†’ `_calc_cost()`
- HuggingFace, Ollama â†’ `cost_usd = None`

The original plan was to use **litellm's cost module** as a unified pricing layer. The previous coder instead wrote per-provider cost functions. This is technical debt: every new provider requires a new cost function, and every pricing change requires updating multiple files.

**Delivered in M003/S01 (D-040):** litellm is now the approved cost-normalization layer. Provider-specific cost paths delegate to the unified normalizer, with explicit fallback behavior and no silent zero-cost success.

### Provider contracts vs runtime registration gap
Three providers have contract files but are not registered in `factory.py`:
- `anthropic_contract_pr4.py` â€” contract exists, no runtime client
- `groq_contract_pr5.py` â€” contract exists, no runtime client
- `lmstudio_contract_pr7.py` â€” contract exists, no runtime client

These are M004/S01 (Anthropic + Groq) and post-v1.0 (LM Studio) work items.

### Python â€” long-term sustainability
Python backend is the right choice through Phase II. Reasons:
- AI/ML provider SDKs arrive in Python first
- Async (uvicorn/FastAPI) is sufficient for MCP SSE workload
- Pipeline V1 is stable and mature

Pressure points to watch:
- Memory footprint (startup import cost â€” lazy loading partially addressed in M002/S01)
- Cold start latency (subprocess/import overhead â€” known, tracked)
- High concurrency (Python GIL â€” not a current bottleneck, monitor at scale)

**Long-term decision (v1.3+):** During domain-agnostic migration, evaluate moving the dispatcher core to Rust. Tauri is already Rust â€” the bridge exists. This is not a now decision.

### Memory target â€” realistic assessment
Current band: ~200MB worker-ON steady state (post-M002 lazy import optimization).
Target from historical docs: <250MB (current lane), <150MB (aspirational).
100MB target: possible only if heavy provider SDK imports are moved fully out of the startup path. Verify actual numbers in M003/S03 before committing to any target.

### Sigstore integrity (D-038) â€” stance
- **Sigstore:** Supplementary integrity option. Free, developer-credible. Does not replace D-038 commercial signing requirement. Relationship clarified in D-038 - Sigstore is the v0.9.x integrity solution, commercial signing is post-revenue.
- **Commercial signing (~$300-400/year):** D-038 timeline unchanged â€” post-revenue. Ship when the product generates income.
- **Until then:** UNSIGNED_NOTICE.md + SHA256 manifest. Target audience (developers) understands this.

### MCP capability types â€” current limitation
Copy config currently generates JSON with text-only capability declaration. This is why connections appear as `_text_only` in IDE tool pickers. This reflects the current product reality (LLM text responses). As the product expands to image generation providers, structured data sources, and real-time feeds, capability types must be declared correctly.

**Action:** M003 or M004 â€” add MCP capability type registry. Copy config generates correct capability declarations per provider type.

### IDE compatibility â€” current state
Actively tested: VS Code, Cursor, and TRAE.
PASS status:
- VS Code: PASS
- Cursor: PASS
- TRAE: PASS
- Claude Code CLI: skipped in M003/S05 due environment and budget constraints

**Delivered in M003/S05:** IDE compatibility matrix and IDE-specific copy-config UX are now in place for the tested IDE set above.

### REST adapter and real-time data sources
Current: non-streaming SSE, each request independent.
The architecture naturally extends to REST adapters (any REST API as MCP bridge) and eventually WebSocket adapters (real-time data feeds).

**Per updated D-037:** REST adapter is v1.1.x scope. It fits the current ProviderFactory model technically, but adding it before v1.0 would dilute focus. v1.1.x is the correct placement â€” after pro developer surface is established.
WebSocket adapter: requires persistent connection management â€” cleaner post-migration (v1.3+).

### "Everything-to-everything" positioning
The product motto aligns with a clear trajectory:
- v0.x: AI provider bridges (LLMs)
- v1.x: Any API as MCP bridge (REST adapters, real-time feeds)
- v1.3+: Domain adapters (knowledge stores, RAG, vertical data sources)

RAG layer (Supabase, Postgres+pgvector, Qdrant) is the Phase III expression of this motto â€” connecting knowledge stores as MCP sources alongside LLMs. This is where "universal MCP router" becomes genuinely universal.

---

## What Was Left Out and Why

**Chain graph editor (drag-drop):** Wizard delivers the core value. Graph is a UI complexity investment that should wait for real usage data from the wizard. Included as v1.2 upgrade.

**Fan-out / parallel routing:** Architecturally clean only after domain-agnostic migration. Adding it now would create technical debt that complicates the migration. Deferred to post-migration.

**Full persistent memory (embeddings):** Requires a local vector store dependency. Session-scoped memory covers the practical need without that complexity. Pro level deferred to post-migration.

**Enterprise compliance packs:** These require the hook/policy architecture from the domain-agnostic fabric. Building them before the migration means building them twice. Post-migration only.

**Routing Advisor (simulation mode):** Good idea from the strategic documents. Using usage history to simulate provider alternatives is genuinely useful. But it requires stable usage schema and cost normalization first (M003/S01). Added as a post-v1.0 candidate â€” not forgotten, just sequenced correctly.

**GLM / China-market path:** Legitimate expansion target per PROVIDER_OTHERS_EXPANSION_MATRIX. Sequenced to v1.3-A after core provider waves are proven. Compliance and region notes required before shipping.

**Auto-update with silent install:** Dangerous without code signing. Sigstore integrity comes in v0.9.x (S04). Commercial code signing is post-revenue per D-038. Auto-update with silent install is a v1.0+ feature. Notify-only update (check and inform) is acceptable in v0.9.x.

**Usage History row-details modal:** Currently not on the product surface. Low urgency relative to other items. Deferred â€” not forgotten.

**Full tooltip/helper system:** The credentials_path helper baseline exists. Full tooltip coverage is a polish investment that should happen after core features stabilize. Post-v1.0.

**Audit log:** Valuable for enterprise. But enterprise is Phase III. Building audit log before the observability event schema is normalized (migration) means building it twice. Post-migration.

---

## One Thing Not in the Original Documents

**Routing Advisor â€” Simulation Mode** was mentioned in the strategic documents but never fully scoped. I am including it explicitly as a **v1.1 candidate** with this definition:

> After v1.0 ships, usage history contains enough data to ask: "If I had used Groq instead of OpenAI for these 50 requests, what would the cost and latency difference have been?" The Routing Advisor surfaces this as a read-only recommendation panel â€” no automatic routing changes, no policy actions. The user sees the simulation, makes their own decision.

This is not a new idea â€” it exists in the strategic documents. But it was never given a concrete scope or milestone placement. It belongs at v1.1, after cost normalization (M003/S01) and Anthropic/Groq providers (M004/S01) are proven. Without those two, the simulation has no meaningful comparison data.

---

## Summary Timeline

| Version | Theme |
|---|---|
| v0.6.1 | Current release (Early Access) |
| v0.7.x âœ… | Release hardening (DONE) |
| v0.8.x | Capability depth + provider wave 1 (cost transparency, Bedrock proof attempt, docs, perf/security) |
| v0.9.x | Provider wave 2 + release productization (Anthropic, Groq, GLM, Sigstore (D-038), auto-update) |
| v1.0.x | Pro developer surface (Chain Editor wizard, routing ADR + basic policies, Vault expansion, Persona Studio) |
| v1.1.x | REST adapter + IDE compatibility matrix + Routing Advisor |
| v1.2.x | Chain graph editor + post-v1.0 polish + deferred items |
| v1.3+ | Domain-agnostic migration + vertical adapters + RAG layer |
