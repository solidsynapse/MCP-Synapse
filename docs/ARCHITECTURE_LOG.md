# MCP Router — Architecture Evolution Log (Legacy → Pipeline V1 Routing)

> Scope: This record describes the evolution from legacy, direct provider calls to the current Pipeline V1 routing architecture, based on observed repository file paths/components and runtime log evidence (including `routing=legacy` / `routing=v1` path logs).

---

## 1) Original Architecture (Legacy Direct Provider Calls)

### Legacy provider call flow (MCP agent request path)

The initial MCP “agent server” implementation executed text generation by directly instantiating the provider client and calling the provider in-process.

**Primary production-adjacent call path (MCP tool call):**

* `src/mcp_server/agent_server.py`

  * MCP tool `call_google_vertex_ai` registered by `_create_tools()`
  * Tool dispatch: `_call_tool()` → `_generate_text(prompt)`
  * Legacy provider call: `_generate_text()` constructs `VertexAIClient(...)` and invokes `client.generate_content(prompt)`.

**Direct provider callsite details:**

* `src/mcp_server/agent_server.py`

  * `VertexAIClient.generate_content(prompt)` used for request execution.
  * Model and pricing were fixed at the callsite (e.g., `model_id="gemini-2.0-flash-001"`, `price_per_1m_* = 0.0`).
  * `credentials_path` was set to an empty string in this legacy path, making it unsuitable for authenticated production usage without additional external environment configuration.

### Legacy provider call flow (connection test path)

The server management layer also contained a direct provider call for connectivity testing, separate from MCP request execution.

* `src/mcp_server/manager.py`

  * `ServerManager.test_agent_connection(agent_id)` constructs `VertexAIClient(...)` using agent config values and a credential path from `CredentialManager`.
  * Executes `client.generate_content(...)` with a fixed “three words” response instruction.
  * Extracts usage metrics (tokens and cost) from the result where present and logs them via `UsageDatabase`.

### ServerManager role (initial)

* `src/mcp_server/manager.py`

  * Owned agent lifecycle operations: create/start/stop.
  * Maintained `active_agents: Dict[str, MCPAgentServer]`.
  * Served as the orchestration layer for agent instantiation and for non-request utilities (e.g., connectivity tests).
  * Did not initially provide a unified “request execution pipeline” abstraction to the MCP agent request path; the request path executed provider calls directly in `MCPAgentServer`.

---

## 2) Pipeline V1 Introduction (Defined but Not Wired)

Pipeline V1 was introduced as a structured, multi-stage request execution pipeline intended to replace or mediate direct provider calls.

**Pipeline V1 components:**

* `src/mcp_server/pipeline_v1.py` (component module reference)

  * `ExecutionRequestV1`: encapsulates request identity (e.g., `agent_id`) and the prompt payload.
  * `PreflightGuardV1`: validates prerequisites (e.g., agent exists, credentials are present/valid, config integrity).
  * `RouterV1`: selects route/provider strategy based on context (e.g., policy, configuration, gating).
  * `ProviderAdapterV1`: executes the routed request against the selected provider implementation.
  * `ObserverV1`: post-execution observation (usage logging, metrics recording, audit data emission).

**ServerManager Pipeline V1 entrypoint:**

* `src/mcp_server/manager.py`

  * `ServerManager.execute_request_v1(agent_id: str, prompt: str) -> dict[str, object]`
  * Constructs `ExecutionRequestV1`, runs `PreflightGuardV1`, routes via `RouterV1`, executes via `ProviderAdapterV1`, and observes via `ObserverV1`.

### Original problem: defined but not wired

Despite the presence of `execute_request_v1(...)` in `ServerManager`, the MCP request execution path in `MCPAgentServer._generate_text()` continued to call `VertexAIClient.generate_content(...)` directly. Consequently, Pipeline V1 existed as an isolated capability without a callsite in the MCP tool execution path.

---

## 3) Integration Point Decision (T0.8)

### Selected integration point: `MCPAgentServer._generate_text`

Pipeline V1 routing was integrated at the MCP “tool execution” choke point:

* `src/mcp_server/agent_server.py` — `MCPAgentServer._generate_text(prompt)`

**Rationale (architectural):**

* `_generate_text()` is the single execution function invoked by the MCP tool handler (`_call_tool()`), which is in turn invoked by MCP calls over the SSE transport.
* Integrating here centralizes routing decisions at the boundary where “text generation” actually occurs, without requiring UI coupling or duplicating routing logic across other layers.
* This location preserves the legacy behavior as a fallback while enabling opt-in routing without reworking higher-level orchestration.

### Why not UI or manager layer

* UI:

  * UI contained a direct provider call in the “Test” action path (non-production request flow) and therefore was not suitable as the single authoritative production routing boundary.
  * Routing decisions at UI-level risk divergence between UI execution and MCP server execution paths.
* Manager layer:

  * `ServerManager` already exposes `execute_request_v1(...)`, but the MCP request path does not inherently pass through manager request methods during tool execution unless explicitly injected.
  * The manager remains a lifecycle orchestrator; request execution is naturally localized to the MCP agent’s tool execution handler.

### Ensuring agent_id propagation

The integration required `agent_id` to be available inside `MCPAgentServer._generate_text()`.

This was ensured by constructor-based injection and wiring from `ServerManager` at agent creation/start time:

* `src/mcp_server/manager.py` passes `agent_id=...` into `MCPAgentServer(...)` creation sites.
* `src/mcp_server/agent_server.py` stores `self._agent_id` and uses it for routing decisions and logging.

---

## 4) Routing Switch Implementation (T0.8)

### Environment variable switch

A gating switch was implemented via environment variable:

* `MCP_ROUTER_USE_V1`

**Routing behavior:**

* If `MCP_ROUTER_USE_V1` evaluates truthy (`"1"`, `"true"`, `"yes"`, `"on"`), and both `self._execute_request_v1` and `self._agent_id` are available, then the V1 pipeline path is executed.
* Otherwise, the legacy direct provider call path is executed.

**Implementation location:**

* `src/mcp_server/agent_server.py`

  * `_generate_text()` reads `os.getenv("MCP_ROUTER_USE_V1", ...)` and selects between:

    * V1 path: `self._execute_request_v1(agent_id, prompt)`
    * Legacy path: `VertexAIClient(...).generate_content(prompt)`

### Default legacy behavior preserved

When `MCP_ROUTER_USE_V1` is not set, the system defaults to legacy behavior. This preserves operational continuity while enabling incremental opt-in activation.

### Logging implementation

Path logging was added for auditability and runtime proof:

* `routing=legacy agent_id=... prompt_len=...`
* `routing=v1 agent_id=... prompt_len=...`

These logs are emitted inside `_generate_text()` prior to executing the selected branch.

---

## 5) ServerManager Wiring Changes (Constructor-Based Injection)

### Passing `execute_request_v1` into `MCPAgentServer`

To enable the MCP agent to call into Pipeline V1, the function handle is injected at agent instantiation:

* `src/mcp_server/manager.py`

  * In `create_agent(...)`, instantiation includes `execute_request_v1=self.execute_request_v1`.
  * In `start_agent(...)`, instantiation includes `execute_request_v1=self.execute_request_v1`.

### Removal of `server._agent_id` hack

Earlier patterns relied on setting `server._agent_id = ...` after construction. The wiring was migrated to constructor parameters:

* `MCPAgentServer(...)` now receives `agent_id` at construction time.
* This ensures `agent_id` is consistently available before any tool requests arrive and eliminates reliance on out-of-band mutation.

### Constructor-based injection outcome

* `MCPAgentServer` becomes an explicit execution boundary with injected dependencies:

  * `agent_id`
  * `execute_request_v1` callable
* `ServerManager` remains responsible for lifecycle and for providing the V1 execution function.

---

## 6) Dependency and Build Fixes (SSOT Restoration)

### Flet upgrade and entrypoint correction

* `requirements.txt` pin moved from `flet==0.21.2` to `flet==0.80.5`.
* `src/main.py` entrypoint updated to match the installed Flet API surface:

  * Restored compatibility with `ft.run(...)` when supported.
* CLI verification used as authoritative evidence:

  * `.\venv\Scripts\flet.exe --version`
  * `pip show flet` metadata

### pyperclip installation

* `pyperclip` was installed into the venv and pinned in `requirements.txt` to eliminate interpreter drift between system Python and venv Python:

  * `pyperclip==1.11.0`

### pytest installation

* `pytest` installed to restore test/QA gate operation and baseline pipeline tests.

### Build pipeline restoration

* Build packaging verified via `build.py` execution through venv Python, producing `dist\MCP Router.exe`.
* The packaging pipeline uses the venv Flet CLI entrypoint and PyInstaller.

---

## 7) Runtime Validation Proof (Legacy vs V1 Confirmed)

### Validation scenario

A runtime proof was executed using a single agent instance and a single prompt, with only the routing switch toggled.

**Observed runtime behavior:**

1. Agent lifecycle logs confirm the agent starts successfully:

   * `Starting MCPAgentServer ...`
   * `MCPAgentServer ... started ...`
2. With `MCP_ROUTER_USE_V1` unset:

   * Log contains `routing=legacy ...`
   * Output returns legacy stub result (`OUT1: LEGACY_OK`) when legacy provider call is monkeypatched for determinism.
3. With `MCP_ROUTER_USE_V1=1` set:

   * Log contains `routing=v1 ...`
   * Output returns V1 stub result (`OUT2: V1_OK`) when `execute_request_v1` is stubbed for determinism.
4. Agent stop logs confirm shutdown completion. A `uvicorn` `CancelledError` may appear during stop as part of lifespan cancellation; it does not change the routing determination because both routing logs and outputs are recorded prior to shutdown.

### Evidence interpretation

* The presence of `routing=legacy` and `routing=v1` logs on the same agent instance and same prompt demonstrates:

  * The integration point (`_generate_text`) is effective.
  * The switch (`MCP_ROUTER_USE_V1`) is functional.
  * Agent identity is propagated and recorded (`agent_id=...`).
  * Default behavior remains legacy when the environment switch is absent.

---

## Final Architecture (Current Behavior Summary)

### Request execution boundary

* `src/mcp_server/agent_server.py`

  * MCP tool → `_call_tool()` → `_generate_text()`
  * `_generate_text()` selects:

    * **V1 pipeline** via injected `execute_request_v1(agent_id, prompt)` when opt-in enabled
    * **Legacy provider call** via `VertexAIClient.generate_content(prompt)` otherwise

### Orchestration boundary

* `src/mcp_server/manager.py`

  * Owns agent lifecycle and provides `execute_request_v1(...)`.
  * Injects `agent_id` and `execute_request_v1` into each `MCPAgentServer` instance at construction time.

### Pipeline V1 execution

* `src/mcp_server/pipeline_v1.py`

  * Structured flow: `ExecutionRequestV1` → `PreflightGuardV1` → `RouterV1` → `ProviderAdapterV1` → `ObserverV1`
  * Invocation is centralized through the MCP agent’s tool execution path via injected callsite.

---

## Current Rollout Status

Pipeline V1 is currently opt-in only and controlled via environment variable MCP_ROUTER_USE_V1.

Legacy routing remains default and active production path until full rollout decision.

This allows safe staged migration and rollback capability.

