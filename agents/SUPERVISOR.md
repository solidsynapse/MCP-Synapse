# agents/SUPERVISOR.md — Supervisor details

Always respond in this structure:
Verdict: PASS / FAIL / NARROW / BLOCKER / FLIP SSOT
Evidence check: SSOT anchors / command outputs / evidence excerpts only
If needed: minimum PS 5.1 proof command block (writes to evidence root)
If needed: FLIP SSOT patch text (normative, minimal)

ID discipline:
- Do not create new phase/task IDs unless FLIP SSOT.
- Prefer extending existing IDs with sub-bullets + evidence.

First-run bootstrap (no questions; run only after I say EXECUTE):
- Create evidence root: docs\evidence\SSOT_BOOTSTRAP_<yyyymmdd-hhmmss>\
- Hash SSOT-core + UI_STYLE_GUIDE + ui-tauri\src\app.css (before)
- Anchor proofs:
  - UI_STYLE_GUIDE key heading
  - app.css: "UI Primitives (Dashboard Design Language)" heading
  - DECISIONS thin-shell / single-entrypoint decision anchors (e.g., D-024/D-029 if present)
- Write summary.txt with PASS/FAIL per check
- Then emit Verdict.

Thin-shell constraints (hard):
- UI production path must not call provider clients.
- UI must call a single core/headless entrypoint.
- Provider/network/protocol logic must not live in UI.
- No new deps, no streaming unless SSOT explicitly authorizes.
