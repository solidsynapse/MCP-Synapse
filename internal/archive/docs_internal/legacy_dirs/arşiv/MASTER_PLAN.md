MCP Router — Master Execution Plan
PRODUCT POSITIONING
MCP Router is a deterministic, provider-agnostic AI gateway that enables IDEs to connect frictionlessly to non-native AI providers via MCP.
________________________________________
CORE (Never Licensed)
•	Deterministic Routing Core
•	MCP Bridge Engine
•	Multi-Agent Management
•	Basic Usage Stats
•	Provider Abstraction Layer
•	Basic UI
•	Local-First Operation
________________________________________
EXTENDED (Future Licensed)
•	Advanced Routing (parallel/conditional)
•	Chain Editor
•	Persona & Memory
•	Quota Guard
•	Advanced Analytics
•	Export (CSV/Reports)
•	Auto-Update System
•	Secure Vault (Enhanced)
________________________________________
PHASE PLAN
________________________________________







Application identity (app name, window title, installer name, appdata/log paths) must be configuration-driven and centrally defined; no hard-coded product name strings.
PHASE 1.5 — Provider Abstraction Hardening
Goal: Remove Vertex coupling and enable universal provider support.
Tasks:
•	Refactor ProviderAdapterV1 into true interface
•	Isolate VertexClient
•	Remove legacy Vertex paths
•	Make credentials provider-agnostic
•	Ensure usage schema supports multi-provider
Exit Criteria:
•	Adding a new provider requires no core modification
•	No Vertex hard dependency in routing layer
________________________________________
PHASE 2 — Operational Usage Layer
Goal: Become a reliable AI gateway.
Tasks:
•	Success Rate computation
•	Avg Latency computation
•	Error type logging
•	DB-level filtering
•	CSV export (basic)
•	Strict KPI derivation rule (single source of truth)
Exit Criteria:
•	Usage tab reflects real DB data
•	Clean install test passes
•	Phase Exit Checklist completed
________________________________________
PHASE 3 — Ollama Bridge
Goal: Strengthen universal identity.
Tasks:
•	Ollama HTTP adapter
•	Provider selection in UI
•	Streaming compatibility
Exit Criteria:
•	IDE request works through Ollama via MCP
•	No routing refactor required
________________________________________
PHASE 4 — Chain Editor v1 (Wizard)
Goal: Router-level orchestration (not IDE-level fan-out)
Scope:
•	Sequential model chaining
•	No parallel routing yet
•	Form-based configuration
•	Deterministic execution
Exit Criteria:
•	IDE request → Router → Multi-step execution → Single response
________________________________________
PHASE 5 — Persona Lite
•	JSON persona profile
•	Attach to chain
•	No vector DB
•	No heavy RAG
________________________________________
PHASE EXIT PRINCIPLE (SSOT Rule)
At the end of every phase:
•	Run Phase Exit Checklist
•	Checklist must be mechanical
•	Evidence-based (log / command / file+line)
•	No subjective validation
________________________________________
4️⃣ Düzeltmeleri Kim Yapacak?
Strateji
•	Architecture changes → Solo Coder
•	Audit / verification → Verifier agent
•	Bug isolation → Debugger
•	Plan validation → Sen + ben
Sen manuel kod yazmayacaksın.
Ama:
•	Final kararları sen vereceksin
•	Phase exit onayı sen vereceksin
________________________________________
5️⃣ Bu Ne Kadar Sürecek?
Gerçekçi tahmin:
Phase 1.5 → 1–2 hafta
Phase 2 → 1 hafta
Phase 3 → 1 hafta
Phase 4 → 2–3 hafta
Toplam:
~6–8 hafta disiplinli çalışma ile
Ama:
Spaghetti çözülmezse → uzar.

