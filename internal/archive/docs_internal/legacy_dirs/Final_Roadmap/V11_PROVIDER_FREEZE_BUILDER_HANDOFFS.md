# V1.1 Provider Freeze - Builder Handoffs (Task-Bounded)

Note: Prompts are intentionally in English for IDE Builder usage.

## Handoff 1 - Vertex AI Fast Reconfirm (No Expansion)

Supervisor note:
- Scope is Vertex AI only.
- Do not add features/providers.
- Produce fresh evidence and confirm freeze baseline.

Builder prompt:
```text
Task: V1.1 Freeze - Vertex AI fast reconfirm only.

Scope in:
- Existing Vertex AI connection flow
- Existing preflight
- Existing runtime smoke path
- Usage row identity fields (provider + model)

Scope out:
- Any new provider
- UI redesign/refactor
- Cost module changes
- SSOT edits

Required output:
1) Findings
2) Minimal patch (if any)
3) Verification (create/update/preflight/runtime smoke + usage identity)
4) Verdict: PASS / REVALIDATE / BLOCKER
5) Exact reason
6) Next narrow step

Evidence root:
- docs/evidence/V11_PROVIDER_VERTEX_<timestamp>/
```

## Handoff 2 - OpenAI Provider Freeze Slice

Supervisor note:
- Implement only OpenAI provider slice needed for freeze acceptance.
- Preserve BYOK + local-only boundaries.

Builder prompt:
```text
Task: V1.1 Freeze - OpenAI provider slice (create/update/preflight/runtime + usage identity).

Scope in:
- Provider contract/wiring for OpenAI
- Connections create/update fields and persistence
- Preflight validation path
- Runtime smoke viability
- Usage identity mapping (provider/model)

Scope out:
- Azure/Bedrock/HF/Ollama
- Non-freeze provider expansion
- Cost module changes
- Broad refactor
- SSOT edits

Acceptance checklist:
- Connection create works
- Connection update works
- Preflight deterministic pass/fail messaging works
- Runtime smoke request succeeds
- Usage row preserves provider + model for OpenAI

Required output:
Findings -> Minimal patch -> Verification -> Verdict -> Exact reason -> Next narrow step

Evidence root:
- docs/evidence/V11_PROVIDER_OPENAI_<timestamp>/
```

## Handoff 3 - Bedrock Provider Freeze Slice

Supervisor note:
- Bedrock is expected to be auth-heavier; keep task narrow and explicit.

Builder prompt:
```text
Task: V1.1 Freeze - Bedrock provider slice (create/update/preflight/runtime + usage identity).

Scope in:
- Bedrock provider contract integration
- Required connection fields for AWS auth/region/model access
- Preflight
- Runtime smoke
- Usage provider/model identity

Scope out:
- Any fifth provider
- Global policy/architecture changes
- Cost gate features
- SSOT edits

Acceptance checklist:
- Create/update/preflight/runtime smoke complete
- Usage rows retain provider/model identity

Required output format:
Findings -> Minimal patch -> Verification -> Verdict -> Exact reason -> Next narrow step

Evidence root:
- docs/evidence/V11_PROVIDER_BEDROCK_<timestamp>/
```

## Handoff 4 - Azure OpenAI Provider Freeze Slice

Supervisor note:
- Keep strictly Azure OpenAI slice.
- No cross-provider cleanup scope.

Builder prompt:
```text
Task: V1.1 Freeze - Azure OpenAI provider slice (create/update/preflight/runtime + usage identity).

Scope in:
- Azure OpenAI provider wiring
- Connection config fields for Azure endpoint/deployment/auth
- Preflight
- Runtime smoke
- Usage provider/model identity

Scope out:
- OpenAI/Bedrock/HF/Ollama
- Cost model implementation
- UI redesign
- SSOT edits

Acceptance checklist:
- Create/update/preflight/runtime smoke complete
- Usage rows retain provider/model identity

Evidence root:
- docs/evidence/V11_PROVIDER_AZURE_OPENAI_<timestamp>/
```
