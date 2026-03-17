## D-024 â€” Phase 3 scope + exit criteria + gates (UI thin shell)

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
- UI â€œthin shell boundaryâ€ is proven via evidence:
  - grep_proofs show provider client calls are absent from UI production path
  - dispatch chain points to headless/core execution surfaces
- All Phase 3 tasks in TASKS/STATUS have evidence roots and are marked DONE with anchor proof (+ pytest when applicable).

## D-029 â€” Phase 4 UI Prep Architecture Lock (Thin Shell)

- Date: 2026-02-22
- Decision: UI rewrite preparation is Phase 4 work (P4 UI PREP), not Phase 3.
- Rationale: Phase 3 stabilizes core + provider contract layer + regression guardrails; UI work is surface/presentation refactor.

### P4 UI PREP Scope Freeze (Consolidated)
- Cross-reference: D-024 â€œUI thin shellâ€ rule applies. UI may only configure + dispatch + render.
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
2) UI â†’ core dispatch boundary:
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


### Addendum â€” UI Implementation Stack Lock (Normative)
- **UI implementation stack is locked to:** **Tauri + Svelte (or SvelteKit) + shadcn/ui**.
- **No stack changes** (framework/runtime/UI kit) are permitted **without an explicit SSOT decision update** under this same D-029 section.
- This lock applies to the **UI production path** only and **does not alter** core/headless/provider-agnostic constraints.
- UI must remain a **thin shell**: no provider client imports/calls, no network/protocol logic, no credential/config I/O, no streaming, no hidden retries/backoff.

### Addendum â€” Navigation Layout (Normative)
- Primary navigation is LEFT SIDEBAR ONLY (no right-side panel/drawer).
- Sidebar supports collapsed icon-rail and expanded label mode.
- Nested rollouts: at most one level deep.
- Documentation (if added later) is a sidebar item that opens a full-page view with search.
- Thin-shell rule remains: all actions dispatch via the single approved Tauri command boundary.

### Addendum â€” Sidebar IA & Theme Defaults (Normative)
- Theme: default DARK mode (light mode may be added later).
- Sidebar IA (initial, top section): Bridges, Usage, Resilience, Automation/Policies.
- Settings is bottom-pinned in the sidebar (separate bottom section).
- No right-side panel/drawer; left sidebar is the only primary navigation.
- Nested rollouts: at most one level deep.

### Addendum â€” UI Hard-ban Scan Scope (Normative)
- Hard-ban provider token scans MUST be source-only.
- Exclude build artifacts: node_modules/, target/, src-tauri/target/.
- Exclude binary extensions (.lib, .rlib, .dll, .exe, .pdb, etc.).
- Scan only source/text extensions (e.g., .svelte .ts .js .css .json .rs .toml .md).

### Addendum â€” Navigation IA v2 (Normative)
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
- Footer: Solid Synapse Â© 2026 + last refresh timestamp (placeholder if not available).
- No right-side navigation panel/drawer. A right column inside a page grid is allowed (it is not a drawer).
- Visual style guidance (non-functional): dark theme; glass/neumorphic accents; hover emphasis; high contrast; system font stack (SF Pro on macOS, Segoe UI on Windows, fallback sans-serif).
- No new UI dependencies are introduced solely for charts/graphics; use placeholders or pure SVG only until SSOT explicitly allows otherwise.

### Addendum â€” Dashboard Design Language Reference:
- The canonical UI primitive definitions are located in: ui-tauri/src/app.css under: "/* ===== UI Primitives (Dashboard Design Language) ===== */"
- Usage and constraints are documented in docs/UI_STYLE_GUIDE.md.
- New UI pages MUST reuse these primitives and tokens.
- No alternative styling system is allowed.

## D-033 â€” BYOK + Local-Only Boundary and Forbidden Use Lock

- Date: 2026-03-04
- Decision:
  - Product operation model is BYOK + local-only orchestration.
  - Product MUST NOT be positioned or operated as a shared key pool, managed key broker, or proxy-as-a-service.
- Constraints (normative):
  - Provider credentials belong to the deploying user/organization account; credential sharing/pooling across unrelated third parties is forbidden.
  - UI/docs must clearly state that provider calls execute under user-configured provider terms, quotas, and legal obligations.
  - Product support boundaries must remain explicit: app behavior is supported, provider account governance remains user responsibility.
- Forbidden uses (release policy):
  1) Offering paid/free shared access to one provider key across external tenants via this app.
  2) Reselling the app endpoint as a generic hosted proxy service for third parties.
  3) Misrepresenting the app as a compliance substitute for provider-side contractual/regulatory duties.

## D-037 - Release Versioning Policy (Milestone-Based)

- Date: 2026-03-17
- Decision:
  - Current release lane is `v0.6.x (Early Access)`.
  - Milestone progression is normative:
    1) `v0.7.x` -> release hardening (DONE)
    2) `v0.8.x` -> capability depth + provider wave 1 (cost transparency, Bedrock proof, documentation pack, performance/security baseline)
    3) `v0.9.x` -> provider wave 2 + budget enforcement + auto-update + REST adapter snapshot
    4) `v1.0.x` -> pro developer surface (Chain Editor, advanced routing with new ADR, Vault expansion, Persona Studio)
    5) `v1.1.x` -> IDE compatibility polish + Routing Advisor + WebSocket/streaming adapter
    6) `v1.2.x` -> Chain graph editor + post-v1.0 polish
    7) `v1.3+` -> domain-agnostic migration + vertical adapters
- Rationale:
  - Provider waves and pro-surface features must land before the domain-agnostic migration.
  - Starting migration after the provider/product surface is deeper creates a cleaner contract boundary and avoids building the same expansion set twice.
  - REST adapter is the first visible signal of the domain-agnostic expansion and is strategically central to product positioning: `Any API. Any model. One gateway.`
- Constraints (normative):
  - Patch bump (`0.6.1` etc.) is hotfix/regression-only.
  - Minor bump (`0.7.0`, `0.8.0`, `0.9.0`, `1.0.0`, `1.1.0`, `1.2.0`) requires closure evidence for the corresponding milestone package.
  - Advanced routing is not authorized by this decision alone; it requires an explicit ADR before entering the shipped scope.
  - UI/About must avoid implying domain-agnostic platform completion before the `v1.3+` migration lane is completed.
  - Product logo/app icon freeze is tied to packaging/versioning readiness closure (same release asset freeze point).

## D-038 â€” Licensing & Distribution Policy (Visible-Source Freemium, Official Channel)

- Date: 2026-03-17
- Decision:
  - Product licensing/distribution model is visible-source freemium with official-channel control.
  - First 3-5 months may run unsigned distribution mode, but release integrity controls are mandatory.
  - Core feature set remains strong free layer in the current lane; monetization is deferred to later Pro layer based on operational depth/collaboration/compliance features.
- Rationale:
  - The target audience is developer-first and can understand and trust Sigstore-backed artifact integrity.
  - Commercial code signing is a distribution/marketing investment, not a current development milestone.
- Constraints (normative):
  - Official distribution channel is single-source and controlled by product owner.
  - Every public release must include:
    - tagged release,
    - SHA256 hashes,
    - changelog + "what changed" note,
    - explicit SmartScreen/unsigned warning note while unsigned mode is active.
  - Security disclosure path must remain explicit (`security@` contact + disclosure policy).
  - Trademark policy is mandatory before broad public distribution:
    - forks/re-distributions must not present product name/logo as official.
  - `v0.9.x` uses Sigstore artifact integrity proof as the planned cryptographic trust layer; the SHA256 manifest remains mandatory and complementary.
  - Commercial code signing (`~$300-400/year`) is deferred until post-revenue; it is required later for full SmartScreen trust but is outside the current budget lane.
  - `UNSIGNED_NOTICE.md` remains active until commercial code signing is introduced.
  - Integrity and traceability controls above remain non-optional while unsigned distribution mode is active.

## D-039 â€” Public Repository Surface Policy

- Date: 2026-03-11
- Decision:
  - The public repository MUST present a product-first surface.
  - Internal orchestration materials, handoff packs, backup/recovery files, probe dumps, local logs, temporary exports, and internal workflow contracts MUST NOT remain on the primary public-facing repository surface unless explicitly required by SSOT or release integrity policy.
  - Historical or internal-only materials that must be retained SHALL live under a clearly labeled internal/archive path.
- Constraints:
  - This policy does not authorize deletion of SSOT documents or release-integrity artifacts.
  - Cleanup must remain deterministic, evidence-backed, and reversible.
  - Historical RC references in docs/evidence/ and docs/release/releases/v0.6.0-rc.1/ are intentionally retained as release history. Public-facing surface v0.6.1 alignment is sufficient per D-039.

## D-040 - litellm integration for unified cost normalization

- Date: 2026-03-17
- Current state:
  - Cost calculation is currently split across provider-specific functions such as `_estimate_cost()` and `_calc_cost()`.
  - Each new provider currently requires another cost function, and pricing changes require updating multiple files.
- Problem:
  - The current cost model scales poorly as provider count grows.
  - Pricing maintenance is duplicated and error-prone across provider implementations.
- Decision:
  - The project will integrate the litellm cost module as the unified cost-normalization layer.
  - Existing provider-specific cost functions will become thin adapters that delegate to litellm where pricing data is available.
- Fallback:
  - If litellm has no pricing data for a provider or model, the system must return explicit `UNKNOWN`.
  - Silent zero-cost success is forbidden.
- Runtime dependency rule:
  - Because litellm is a new runtime dependency, fallback behavior must be explicitly tested.
  - A litellm-unavailable scenario must have graceful degradation behavior defined and implemented before rollout.
- Boundary constraint:
  - D-033 remains binding.
  - litellm is authorized only for local cost normalization logic and must not introduce any cloud call or shared-service behavior.

## D-041 - REST adapter as a strategic expansion milestone

- Date: 2026-03-18
- Decision:
  - The REST adapter is a strategic expansion milestone, not a minor feature.
  - It belongs in the `v0.9.x / M004` lane as part of the first visible domain-agnostic expansion signal.
- Positioning:
  - `Any API. Any model. One gateway. Full audit trail.`
- Constraints:
  - The REST adapter must enter through the existing Connections product surface, not a separate primary navigation surface.
  - It must preserve D-024 and D-029 thin-shell/core boundaries.
  - It must preserve D-033 BYOK + local-only rules and must not become a hosted proxy or shared-service path.
  - The `v0.9.x` lane authorizes a REST adapter snapshot only; WebSocket/streaming adapters remain later-lane work.

