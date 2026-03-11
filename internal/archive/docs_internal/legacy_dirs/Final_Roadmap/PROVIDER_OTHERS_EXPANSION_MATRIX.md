# Provider + Others Expansion Matrix

Status: Strategic expansion map (post-V1.0), scope-locked by waves.
Date: 2026-03-04

## Objective
Grow MCP Synapse from a stable V1.1 provider core to a universal MCP router, without breaking determinism, trust, or SSOT discipline.

## Fixed Rules
- BYOK + local-only boundary (no key pooling, no proxy-as-a-service).
- Wave-gated rollout only; no ad-hoc provider expansion.
- Same gate for every provider: contract -> preflight -> runtime smoke -> usage identity -> cost behavior.

## Wave Plan

| Wave | Scope | Value | Risk | Pass Criteria |
|---|---|---|---|---|
| V1.1 Freeze | Vertex AI, Azure OpenAI, Bedrock, OpenAI | Core multi-provider credibility + cost trust baseline | Medium | 4/4 provider runtime and cost consistency evidence |
| V1.2-A | Hugging Face, Ollama | Ecosystem breadth + strong local option | Medium | Both providers pass full gate set |
| V1.2-B | Anthropic, Groq, Alibaba | Latency/performance diversity + China-market path | Medium-High | Runtime stability + explicit region/compliance notes |
| V1.2-C | LM Studio, Google AI Studio | Local/dev speed + alt Google path | Medium | Stable preflight/runtime and usage identity mapping |
| V1.3-A | GLM + fast iteration tools (e.g., V0/Figma workflow) | Product iteration speed + new ecosystem bridge | Medium | Tool bridge works without core contract drift |
| V1.3-B | RAG + DB layer (Postgres+pgvector, Qdrant, Pinecone) | Router becomes execution + knowledge platform | High | Retrieval quality, latency/cost visibility, data-boundary safety |

## RAG/DB Priority
1) Postgres + pgvector (self-host/Supabase): balanced first baseline.
2) Qdrant: high-performance vector workload path.
3) Pinecone: managed speed option when ops simplicity is prioritized.

## Strategic Add-on (Accepted)
Routing Advisor (Simulation Mode):
- Uses usage history to simulate provider/model alternatives.
- First phase is monitor-only recommendation mode.
- Later phase can map recommendations to policy actions.

## Decision Lock
- V1.1 remains strictly 4-provider freeze (no expansion before closure).
- HF+Ollama start only in next wave after V1.1 closure.
- Every future wave must preserve BYOK/local-only and deterministic evidence gates.

## Execution Artifacts
- V1.1 freeze prep checklist: `docs/Final_Roadmap/V11_PROVIDER_FREEZE_GAP_CHECKLIST.md`
- V1.1 builder handoffs: `docs/Final_Roadmap/V11_PROVIDER_FREEZE_BUILDER_HANDOFFS.md`
- V1.2-A deferred checklist (HF+Ollama): `docs/Final_Roadmap/V12A_HF_OLLAMA_GATE_CHECKLIST.md`
