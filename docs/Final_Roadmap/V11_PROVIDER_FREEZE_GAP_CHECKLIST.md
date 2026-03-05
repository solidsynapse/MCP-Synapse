# V1.1 Provider Freeze Gap Checklist (4-Provider Lock)

Status: Supervisor prep checklist (pre-implementation)  
Scope: Vertex AI, Azure OpenAI, Bedrock, OpenAI only.

## 1) Gate Rule (from SSOT)

- Freeze scope is exactly 4 providers.
- For each provider, PASS requires: create/update/preflight/runtime smoke.
- Usage rows must keep provider + model identity.
- No fifth provider onboarding before freeze closure.

## 2) Current Gap Matrix

Legend:
- CLOSED: evidence already exists in current truth.
- OPEN: evidence missing and must be produced in V1.1 freeze wave.

| Provider | Create/Update | Preflight | Runtime Smoke | Usage Identity | Gate State |
|---|---|---|---|---|---|
| Vertex AI | CLOSED (historical + current runtime usage) | CLOSED | CLOSED | CLOSED | Baseline PASS candidate |
| OpenAI | CLOSED (live reconfirm) | CLOSED (live reconfirm) | CLOSED (live reconfirm) | CLOSED (live reconfirm) | PASS candidate |
| Azure OpenAI | OPEN | OPEN | OPEN | OPEN | REVALIDATE |
| Bedrock | OPEN | OPEN | OPEN | OPEN | REVALIDATE |

## 3) Execution Order (lowest-risk first)

1) Vertex AI fast reconfirm package (small anchor update only).  
2) OpenAI implementation + reconfirm.  
3) Bedrock implementation + reconfirm.  
4) Azure OpenAI implementation + reconfirm.

Rationale:
- Start with fastest closure first (Vertex reconfirm).
- Then progress from simpler cloud integration to higher auth complexity (Bedrock last).

## 4) Evidence Pack Contract (per provider)

Each provider package must create:
- `docs\evidence\V11_PROVIDER_<PROVIDER>_<timestamp>\`
- Required files:
  - `commands_ran.txt`
  - `anchor_proofs.txt`
  - `ssot_core.sha256.before.txt`
  - `ssot_core.sha256.after.txt`
  - `summary.txt`

Recommended add-ons:
- `runtime_smoke.txt`
- `usage_identity_probe.txt`
- `known_limits.txt` (if pricing/metadata is partial)

## 5) Freeze Closure Rule

`GATE-V11-PROVIDER-FREEZE` can be PASS only when:
- All 4 providers are PASS on create/update/preflight/runtime smoke.
- Usage identity (provider + model) is proven for all 4.
- STATUS/TASKS keep explicit 4-provider freeze language.
