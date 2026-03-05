# DOCS-MIN-01 - User Guide, Known Issues, Feature Wiki

Scope: User-facing documentation for the current release. This document does not change runtime behavior.

## 1) Quick Start
1) Open the app and go to Connections.
2) Create a new connection:
   - Choose a provider.
   - Fill required fields.
   - Save.
3) Run Preflight on the connection to validate credentials and configuration.
4) Start the connection.
5) Send your first request through your configured workflow.

## 2) Core Workflow Guide

### Connections
- Create/Edit/Delete: Manage provider connections from the Connections page.
- Preflight: Runs a validation check before you start. Fix any reported errors and run again.
- Start/Stop: Start a connection to make it available for requests; stop to disable it.
- Copy Config: Use this to export the connection config for deployment or troubleshooting.

### Usage Summary / Usage History
- Usage Summary shows aggregated totals for the selected period.
- Usage History lists individual requests with filters and export options.
- Export CSV uses your current filters and saves a file to your selected location.

### Dashboard
- KPI cards provide high-level status for cost, requests, tokens, success rate, latency, and active bridges.
- Cost Trend shows the last 30 days by default; hover points to see exact values.
- Cost Breakdown shows provider distribution for the selected period.
- Alerts highlight operational warnings and budget monitor signals.

Budget behavior is monitor-only: it shows informational warnings but does not block or throttle requests.

### Settings
- Settings are stored locally and persist across app restarts.
- Validation errors appear inline; fix and save again.

## 3) Known Issues
- Some UI sections may require manual refresh to show the latest data.
- Export dialogs can be blocked by OS permissions or restricted folders.
- If a provider changes credentials externally, a previously working connection can fail until updated.

## 4) Troubleshooting

### Connection / Preflight Errors
- Double-check provider credentials and required fields.
- Re-run Preflight after changes.
- If errors persist, delete the connection and recreate it.

### Export / Save Dialog Issues
- Choose a writable folder.
- Avoid system-protected locations.
- Check OS permissions and retry.

### Refresh / Visibility Confusion
- Use the global refresh control to re-fetch dashboard and usage data.
- If the UI appears stale, close and reopen the page.
- If the issue continues, use the support contact defined in LC-MIN-01.

## 5) Feature Wiki (Current Feature Set)
- Connections lifecycle: create/edit/delete/start/stop/preflight/copy config.
- Usage Summary + History with filters and CSV export.
- Dashboard: KPI, Cost Trend (30-day), Cost Breakdown, Alerts, Recent Requests, Top Expensive.
- Persona Lite + Optimizations + Interceptors runtime effect surfaces.
- Settings persistence and validation.

## 6) Acceptable Use and Forbidden Use
- Operation model: BYOK + local-only orchestration.
- You must use provider credentials/accounts that you own or are authorized to operate.

Forbidden:
1) Sharing/pooling one provider credential set to serve unrelated third parties.
2) Operating this app as a hosted proxy-as-a-service for external tenants.
3) Presenting this app as a substitute for provider-side legal/compliance obligations.
