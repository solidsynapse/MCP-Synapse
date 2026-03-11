# V1.2-A Gate Checklist (Hugging Face + Ollama)

Status: Deferred wave checklist (prepared now, executed after V1.1 freeze PASS).

## 1) Scope Lock

Scope IN:
- Hugging Face provider slice
- Ollama provider slice
- Provider-specific create/update/preflight/runtime smoke
- Usage identity preservation (provider + model)

Scope OUT:
- Anthropic, Groq, Alibaba
- LM Studio, Google AI Studio
- LLM Cost Gate expansion
- RAG/DB feature scope

## 2) Wave Dependency

This wave must not start until:
1) V1.1 4-provider freeze is PASS.
2) Freeze language remains unchanged in SSOT.
3) No unresolved freeze blocker exists.

## 3) Acceptance Checklist (per provider)

For Hugging Face:
- Connection create/update works.
- Preflight behavior is deterministic.
- Runtime smoke succeeds.
- Usage rows keep `provider=HuggingFace` + model identity.
- If pricing metadata is partial, unknown/estimated state is explicit.

For Ollama:
- Connection create/update works.
- Preflight behavior is deterministic.
- Runtime smoke succeeds (local endpoint path).
- Usage rows keep `provider=Ollama` + model identity.
- Offline/local failure messages are explicit.

## 4) Evidence Contract

Required evidence roots:
- `docs\evidence\V12A_PROVIDER_HUGGINGFACE_<timestamp>\`
- `docs\evidence\V12A_PROVIDER_OLLAMA_<timestamp>\`

Required files per package:
- `commands_ran.txt`
- `anchor_proofs.txt`
- `ssot_core.sha256.before.txt`
- `ssot_core.sha256.after.txt`
- `summary.txt`

## 5) Closure Rule

`GATE-V12A-HF-OLLAMA` is PASS only when both providers pass all acceptance items and usage identity is proven for each.
