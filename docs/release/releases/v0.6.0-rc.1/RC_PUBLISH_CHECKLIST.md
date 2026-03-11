# RC Publish Checklist - v0.6.0-rc.1

Date: 2026-03-11  
Status: Finalized for release runway closeout

## 1) Required evidence chain (must exist before publish)
- `docs/evidence/V68_FINAL_PACKAGED_SMOKE_TRUTH_RC_20260311-103015/`
- `docs/evidence/V69_IDENTITY_PARITY_CLOSURE_20260311-104200/`
- `docs/evidence/V70_SPEED_COMPARE_WORKER_ON_OFF_20260311-110543/`
- `docs/evidence/V71_RELEASE_CHECKSUM_UPDATE_20260311-111229/`
- `docs/evidence/V72_FINAL_PREFLIGHT_RC_DECISION_20260311-113622/`

## 2) Commit package (exact scope)
Commit all release-closeout changes except local probe/temp artifacts.

Include:
- `docs/DECISIONS.md`
- `docs/STATUS.md`
- `docs/TASKS.md`
- `docs/release/releases/v0.6.0-rc.1/*`
- `docs/brand_assets/*`
- `ui-tauri/src-tauri/Cargo.toml`
- `ui-tauri/src-tauri/Cargo.lock`
- `ui-tauri/src-tauri/tauri.conf.json`
- `ui-tauri/src-tauri/src/lib.rs`
- `ui-tauri/src-tauri/src/worker_dispatch.rs`
- `ui-tauri/src-tauri/icons/*`
- `ui-tauri/src-tauri/nsis/*`
- `ui-tauri/src/routes/*` (only changed files)
- `ui-tauri/src/lib/ui_session.ts`
- `ui-tauri/static/brand/*`
- `src/mcp_server/manager.py`
- `tools/dispatch_worker_v1.py`
- `tools/bench_dispatch_ab_v1.py`
- `tools/headless_dispatch_v1.py`

Exclude:
- `docs/evidence/*`
- `tmp_*`
- `smoke_runs.json`
- `smoke_runs_table.txt`
- `ui-tauri/perf_poll.txt`
- `tmp_write_probe*.txt`
- `current_evidence_path.txt`

## 3) Commit + tag commands (PowerShell)
```powershell
Set-Location -LiteralPath C:\mcp-router

# Stage intended release scope only (do not use git add .)
git add docs/DECISIONS.md docs/STATUS.md docs/TASKS.md
git add docs/release/releases/v0.6.0-rc.1
git add docs/brand_assets
git add src/mcp_server/manager.py tools/headless_dispatch_v1.py tools/dispatch_worker_v1.py tools/bench_dispatch_ab_v1.py
git add ui-tauri/src-tauri/Cargo.toml ui-tauri/src-tauri/Cargo.lock ui-tauri/src-tauri/tauri.conf.json
git add ui-tauri/src-tauri/src/lib.rs ui-tauri/src-tauri/src/worker_dispatch.rs
git add ui-tauri/src-tauri/icons ui-tauri/src-tauri/nsis
git add ui-tauri/src/routes ui-tauri/src/lib/ui_session.ts ui-tauri/static/brand

# Remove tracked local leftovers if still tracked in index
git add -u ui-tauri/src/routes/connections

git status --short
git commit -m "release(rc): v0.6.0-rc.1 runway closeout and RC-ready checkpoint"

# Do not rewrite an existing release tag.
# If v0.6.0-rc.1 already exists, create a closeout tag on the final commit.
git tag -a v0.6.0-rc.1-final -m "MCP Synapse v0.6.0-rc.1 final runway closeout"
git show --stat --oneline HEAD
git tag -n1 v0.6.0-rc.1-final
```

## 4) Publish payload
- `MCP Synapse_0.6.0-rc.1_x64-setup.exe`
- `MCP Synapse_0.6.0-1_x64_en-US.msi`
- `SHA256SUMS.txt`
- `RELEASE_NOTES.md`
- `WHAT_CHANGED.md`
- `INSTALL_RUN_NOTES.md`
- `KNOWN_ISSUES.md`
- `TRUST_SECURITY.md`
- `UNSIGNED_NOTICE.md`

## 5) Final gate before clicking publish
- Tag points to the intended release-closeout commit.
- `SHA256SUMS.txt` values match released artifacts.
- Installed runtime identity is `mcp-synapse.exe` (not `ui-tauri.exe`).
- No user-facing runtime mode split wording in release docs.
- Deferred list in release docs matches SSOT deferred set exactly.
