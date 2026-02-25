# Pipeline V1 Architecture Specification

## 1. Purpose

### Why Pipeline V1 exists

Pipeline V1 defines a structured, opt‑in execution path for handling agent‑scoped text generation requests in the MCP router backend. It provides a clear sequence of stages (preflight, routing, provider execution, observation) implemented as composable classes, while leaving all existing legacy flows untouched.

### What problem it solves

- Centralizes the logic for:
  - Validating that an agent and its credentials are correctly configured.
  - Resolving the effective execution context (project, location, model, pricing, credentials).
  - Invoking the current provider (Vertex AI) in a predictable way.
  - Logging usage in a non‑blocking manner.
- Encodes architectural guarantees in code:
  - Immutable execution context objects.
  - A hard preflight gate before any provider call.
  - A routing stage that can be extended without changing provider code.
  - An observer that cannot affect control flow.

### What it explicitly does NOT solve

- It does **not** replace or modify any existing MCP server, UI, or test flows.
- It does **not** change how `MCPAgentServer` handles tools or SSE connections.
- It does **not** introduce asynchronous execution or concurrency primitives.
- It does **not** manage multiple providers; it only uses the existing `VertexAIClient`.
- It does **not** introduce new configuration storage or schema; it relies entirely on existing `ConfigManager`, `CredentialManager`, and `UsageDatabase`.

Pipeline V1 is an additive, parallel execution path that can be used where its structured semantics are needed, without altering legacy behavior.


## 2. Design Principles

Each principle below is enforced by the current implementation in `src/mcp_server/pipeline_v1.py` and by `ServerManager.execute_request_v1` in `src/mcp_server/manager.py`.

### 2.1 Immutable execution context

- **Intent**  
  Ensure that once an execution context is resolved for a request, its key properties (agent, project, location, model, pricing, credentials) cannot be mutated by any pipeline stage.

- **Enforcement mechanism in code**  
  - `ExecutionContextV1` is defined as:
    ```python
    @dataclass(frozen=True)
    class ExecutionContextV1:
        ...
    ```
  - All stages receive an `ExecutionContextV1` instance and pass it along without modification.
  - The router returns the same context instance in Phase 1.

- **Risk avoided**  
  - Prevents downstream stages from altering routing decisions or configuration mid‑execution.
  - Avoids subtle bugs where one stage mutates state that a later stage or caller assumes is stable.

### 2.2 Hard preflight gating

- **Intent**  
  Ensure that provider execution only occurs when agent configuration and credentials are valid, and fail fast otherwise.

- **Enforcement mechanism in code**  
  - `PreflightGuardV1.run(...)`:
    - Calls `ConfigManager.get_agent(agent_id)` and raises `ValueError("Agent not found")` if missing.
    - Calls `CredentialManager.get_credential(agent_id)` and raises `ValueError("No credentials configured for agent")` if missing.
    - Constructs and returns an `ExecutionContextV1` when both are present.
  - `ServerManager.execute_request_v1(...)`:
    - Calls `PreflightGuardV1.run(...)` before any routing, provider invocation, or observation.
    - Does not catch preflight exceptions, so a failure short‑circuits the pipeline and no later stage is invoked.

- **Risk avoided**  
  - Prevents provider calls with missing or invalid agent configuration or credentials.
  - Keeps routing, provider, and observer logic free from configuration‑existence checks.

### 2.3 Pure routing stage

- **Intent**  
  Keep the routing logic separate from provider execution and observation, so routing can evolve without affecting those stages.

- **Enforcement mechanism in code**  
  - `RouterV1.route(context: ExecutionContextV1) -> ExecutionContextV1`:
    - Takes an immutable context as input.
    - Returns a context as output.
    - In Phase 1, simply returns the same context unchanged and performs no side effects.
  - Router does not call providers or touch databases.

- **Risk avoided**  
  - Avoids entangling routing with provider execution or logging, which would make future changes harder and risk cross‑cutting side effects.

### 2.4 Provider isolation

- **Intent**  
  Confine provider invocation to a dedicated stage that depends only on the execution context and does not make routing or logging decisions.

- **Enforcement mechanism in code**  
  - `ProviderAdapterV1.execute(context, prompt)`:
    - Builds a `VertexAIClient` from fields on `ExecutionContextV1` (project_id, location, model_id, pricing, credentials_path).
    - Calls `client.generate_content(prompt)` and returns the result dict.
    - Does not log usage, does not change configuration, and does not modify the context.
  - Provider exceptions are not caught in the pipeline; they propagate to the caller of `execute_request_v1`.

- **Risk avoided**  
  - Prevents provider code from becoming responsible for routing, logging, or configuration mutation.
  - Keeps provider invocation straightforward and testable.

### 2.5 Non‑blocking observer

- **Intent**  
  Allow usage logging and diagnostics without ever blocking or altering the main response path.

- **Enforcement mechanism in code**  
  - `ObserverV1.observe(usage_db, context, result)`:
    - Is wrapped in a single `try/except` block.
    - Extracts `tokens_input`, `tokens_output`, `cost_usd` from `result`.
    - Calls `UsageDatabase.log_usage(...)`.
    - Catches all exceptions and logs a warning, but does not re‑raise.
  - `ServerManager.execute_request_v1(...)`:
    - Always returns the provider `result` regardless of observer outcome.

- **Risk avoided**  
  - Prevents database or logging failures from breaking or delaying request handling.
  - Ensures that the pipeline’s behavior is not dependent on usage logging availability.

### 2.6 No async patterns

- **Intent**  
  Keep the pipeline purely synchronous and compatible with the existing synchronous codebase.

- **Enforcement mechanism in code**  
  - All interfaces (`PreflightGuardV1`, `RouterV1`, `ProviderAdapterV1`, `ObserverV1`, `ServerManager.execute_request_v1`) are synchronous methods.
  - No `async def`, no `await`, and no event loop interactions are used in the pipeline module.

- **Risk avoided**  
  - Avoids mixing sync and async paradigms in this part of the codebase.
  - Prevents implicit concurrency issues in a pipeline that relies on synchronous components (config, credentials, DB, Vertex client).

### 2.7 Backward compatibility with legacy path

- **Intent**  
  Introduce the pipeline without changing any existing behaviors or public APIs that legacy code depends on.

- **Enforcement mechanism in code**  
  - `ServerManager` gains a new method `execute_request_v1`, but existing methods (`create_agent`, `start_agent`, `stop_agent`, `test_agent_connection`, etc.) are unchanged.
  - No changes are made to:
    - `MCPAgentServer`.
    - UI in `src/ui/main_window.py`.
    - `VertexAIClient` behavior.
    - `UsageDatabase` behavior.
  - Pipeline V1 is only used when explicitly called via `ServerManager.execute_request_v1`.

- **Risk avoided**  
  - Ensures existing MCP and UI flows continue to work exactly as before.
  - Limits the blast radius of any issues in the new pipeline.


## 3. Component Breakdown

All components described below are implemented in `src/mcp_server/pipeline_v1.py`, except `ServerManager.execute_request_v1`, which lives in `src/mcp_server/manager.py`.

### 3.1 ExecutionRequestV1

- **Responsibility**  
  Represent the minimal input required to start the pipeline: an agent identifier and a prompt string.

- **Inputs**  
  - Constructed by callers (e.g., `ServerManager.execute_request_v1`) with:
    - `agent_id: str`
    - `prompt: str`

- **Outputs**  
  - None; it is a simple frozen dataclass used as a value object.

- **Failure behavior**  
  - None by itself; construction does not perform validation.

- **What it must NEVER do**  
  - Perform I/O or validation.
  - Contain mutable state.
  - Change during pipeline execution (enforced by `frozen=True`).
  - Introduce hidden side effects such as implicit logging, caching, or external mutations.
  - Perform lazy evaluation that depends on external state at later stages.
  - Implement retry logic, rate limiting, or quota evaluation.
  - Mutate any external state or upstream data structures.
  - Implement implicit fallback behavior or provider switching.

### 3.2 ExecutionContextV1

- **Responsibility**  
  Capture the fully‑resolved execution context for a request, including agent configuration, provider settings, and pricing.

- **Inputs**  
  - Constructed by `PreflightGuardV1.run(...)` from:
    - Agent dictionary returned by `ConfigManager.get_agent(...)`.
    - Credential path from `CredentialManager.get_credential(...)`.

- **Outputs**  
  - Passed as an immutable object to `RouterV1`, `ProviderAdapterV1`, and `ObserverV1`.

- **Failure behavior**  
  - None in its own constructor; it is built with values already validated by preflight.

- **What it must NEVER do**  
  - Change after construction (enforced by `@dataclass(frozen=True)`).
  - Perform I/O or logic; it is purely a data holder.
  - Introduce hidden side effects, lazy evaluation, or deferred computation that depends on external state.
  - Implement any retry logic, rate limiting, quota enforcement, or caching.
  - Mutate upstream data structures, including the underlying `agent` dict.
  - Trigger implicit fallback behavior or any change in provider selection.

### 3.3 PreflightGuardV1

- **Responsibility**  
  Enforce that an agent and its credentials exist before execution proceeds; construct `ExecutionContextV1`.

- **Inputs**  
  - `ConfigManager`
  - `CredentialManager`
  - `ExecutionRequestV1`

- **Outputs**  
  - Returns an `ExecutionContextV1` with populated fields:
    - `agent`, `project_id`, `location`, `model_id`, `credentials_path`, `price_per_1m_input`, `price_per_1m_output`.

- **Failure behavior**  
  - Raises `ValueError("Agent not found")` if `ConfigManager.get_agent(...)` returns `None`.
  - Raises `ValueError("No credentials configured for agent")` if `CredentialManager.get_credential(...)` returns a falsy value.

- **What it must NEVER do**  
  - Call the provider.
  - Write to the database.
  - Mutate any existing objects; it only constructs new context instances.
  - Introduce hidden side effects such as logging beyond what is explicitly configured at a higher level.
  - Implement lazy evaluation, retry logic, rate limiting, quota enforcement, or caching.
  - Mutate upstream data or external shared state.
  - Implement implicit fallback behavior or silently skip validation failures.

### 3.4 RouterV1

- **Responsibility**  
  Represent the routing stage between preflight and provider; currently a no‑op that returns the context unchanged.

- **Inputs**  
  - An `ExecutionContextV1` instance.

- **Outputs**  
  - An `ExecutionContextV1` instance (same instance in Phase 1).

- **Failure behavior**  
  - None in Phase 1; it does not raise.

- **What it must NEVER do**  
  - Call providers.
  - Perform usage logging or other side effects.
  - Mutate the input context.
  - Introduce hidden side effects, including any I/O beyond routing decisions.
  - Implement lazy evaluation, retry logic, rate limiting, quota checks, or caching.
  - Mutate upstream data structures or external shared state.
  - Change provider or model selection in a way not reflected in the returned context.
  - Implement implicit fallback behavior or silently alter routing decisions.

### 3.5 ProviderAdapterV1

- **Responsibility**  
  Execute the actual provider call using the resolved execution context and prompt.

- **Inputs**  
  - `ExecutionContextV1`
  - `prompt: str`

- **Outputs**  
  - A `dict[str, Any]` representing the provider result, directly from `VertexAIClient.generate_content`.

- **Failure behavior**  
  - May raise any exceptions that `VertexAIClient` raises (`CredentialError`, `QuotaError`, `APIError`, or others).
  - The pipeline does not catch these; they propagate to the caller of `execute_request_v1`.

- **What it must NEVER do**  
  - Decide which provider or model to use; it reads these from the context.
  - Log usage or write to the database.
  - Modify the context or agent configuration.
  - Introduce hidden side effects such as caching, rate limiting, or quota enforcement.
  - Implement lazy evaluation that changes behavior across calls for the same input.
  - Implement retry logic or automatic failover.
  - Mutate upstream data or external shared state.
  - Switch to a fallback provider or model implicitly.

### 3.6 ObserverV1

- **Responsibility**  
  Observe the result of provider execution and log usage metrics in a best‑effort, non‑blocking fashion.

- **Inputs**  
  - `UsageDatabase`
  - `ExecutionContextV1`
  - Provider result dict

- **Outputs**  
  - None (returns `None`).

- **Failure behavior**  
  - Wrapped in a `try/except`:
    - On success, calls `UsageDatabase.log_usage(...)`.
    - On any exception (from metric extraction or DB operations), logs a warning and swallows the exception.

- **What it must NEVER do**  
  - Raise exceptions to the caller.
  - Modify the context or provider result.
  - Influence whether a response is returned.
  - Introduce hidden side effects beyond explicit logging and usage recording.
  - Implement lazy evaluation, retry logic, rate limiting, quota enforcement, or caching.
  - Mutate upstream data or external shared state.
  - Trigger implicit fallback behavior or alter provider execution outcomes.


## 4. Execution Flow

### 4.1 Orchestration: ServerManager.execute_request_v1

The method `ServerManager.execute_request_v1(self, agent_id: str, prompt: str) -> dict[str, object]` (in `src/mcp_server/manager.py`) orchestrates the pipeline:

1. **Request construction**  
   - Builds `ExecutionRequestV1(agent_id=agent_id, prompt=prompt)`.

2. **Preflight**  
   - Calls `PreflightGuardV1.run(self._config, self._creds, request)`:
     - Resolves agent and credentials.
     - Builds `ExecutionContextV1`.
     - If preflight fails, raises `ValueError` and stops; no further stages run.

3. **Routing**  
   - Calls `RouterV1.route(context)`:
     - Returns a routed context (same instance in Phase 1).

4. **Provider execution**  
   - Calls `ProviderAdapterV1.execute(routed_context, prompt)`:
     - Builds `VertexAIClient` from context.
     - Calls `generate_content(prompt)`.
     - Returns the provider result dict.
     - Exceptions from provider propagate out of `execute_request_v1`.

5. **Observation**  
   - Calls `ObserverV1.observe(self._usage_db, routed_context, result)`:
     - Attempts to log usage.
     - Swallows all internal errors and logs warnings.

6. **Response return**  
   - Returns the `result` dict from `ProviderAdapterV1.execute(...)` to the caller.

### 4.2 Data transitions

- `agent_id`, `prompt` → `ExecutionRequestV1`.
- `ExecutionRequestV1` + managers → `ExecutionContextV1`.
- `ExecutionContextV1` → routed `ExecutionContextV1` (same in Phase 1).
- `ExecutionContextV1` + `prompt` → provider `result` dict.
- `ExecutionContextV1` + `result` → usage log entries (best effort).
- `result` → response to caller.

### 4.3 Error boundaries and isolation guarantees

- **Preflight errors**
  - Raised inside `PreflightGuardV1.run(...)`.
  - Stop the pipeline before provider and observer.

- **Provider errors**
  - Raised inside `ProviderAdapterV1.execute(...)` or underlying `VertexAIClient`.
  - Propagate out of `execute_request_v1` to its caller.
  - Observer is not run if provider fails (because observer is called only after provider returns a result).

- **Observer errors**
  - Caught inside `ObserverV1.observe(...)` and logged as warnings.
  - Do not affect the returned result.

### 4.4 System Boundary Diagram

The diagram below shows the system boundaries and how Pipeline V1 interacts with other components.

```text
        +-----------------------+
        |     External Caller   |
        |  (e.g. UI, CLI, test) |
        +-----------+-----------+
                    |
                    v
        +-----------------------+
        |     ServerManager     |
        | execute_request_v1()  |
        +-----------+-----------+
                    |
                    v
          +---------+---------+
          |     Pipeline V1   |
          |  (in-process,     |
          |   synchronous)    |
          +---------+---------+
                    |
     +--------------+--------------+--------------+--------------+
     v                             v                             v
+------------+              +------------+              +----------------+
| Preflight  |              |  Router    |              |   Provider     |
| Guard V1   |              |   V1       |              | Adapter V1     |
+-----+------+              +-----+------+              +--------+-------+
      |                           |                              |
      |                           |                              v
      |                           |                    +-------------------+
      |                           |                    |  VertexAIClient   |
      |                           |                    | (External provider|
      |                           |                    |   integration)    |
      |                           |                    +-------------------+
      |                           |
      v                           v
+----------------+        +----------------+
|  Observer V1   |        | Legacy Flows   |
| (Usage logging)|        | (MCP/other)    |
+-------+--------+        +----------------+
        |
        v
+---------------------------+
|      UsageDatabase        |
|  (External storage layer) |
+---------------------------+
```

- **Pipeline V1 boundary**  
  - Encloses `PreflightGuardV1`, `RouterV1`, `ProviderAdapterV1`, and `ObserverV1`, executed via `ServerManager.execute_request_v1`.
- **Legacy flows boundary**  
  - Represents all existing MCP and UI paths that do not use Pipeline V1 and remain unchanged.
- **External provider boundary**  
  - `VertexAIClient` interacts with external Vertex AI services outside Pipeline V1.
- **External storage boundary**  
  - `UsageDatabase` persists usage information outside Pipeline V1; failures here do not affect the pipeline result.


## 5. Invariants

The following invariants are enforced by the current implementation and should be treated as architectural guarantees:

1. **Context is immutable**  
   - `ExecutionContextV1` is a frozen dataclass; attributes cannot be reassigned after construction.

2. **Request is immutable**  
   - `ExecutionRequestV1` is a frozen dataclass; its fields cannot be changed after construction.

3. **Preflight must run before provider**  
   - `ServerManager.execute_request_v1` always calls `PreflightGuardV1.run(...)` before `RouterV1.route(...)` and `ProviderAdapterV1.execute(...)`.

4. **Observer must never block response**  
   - Any exception in `ObserverV1.observe(...)` is caught and logged; the response from `ProviderAdapterV1.execute(...)` is always returned unchanged.

5. **Provider must not modify context**  
   - `ProviderAdapterV1.execute(...)` only reads from `ExecutionContextV1` and constructs a `VertexAIClient`; the context is frozen and cannot be changed.

6. **No stage mutates upstream data**  
   - All data passed between stages (`ExecutionRequestV1`, `ExecutionContextV1`, provider `result` dict) is either immutable or treated as read‑only by the stages.

7. **Pipeline order is fixed**  
   - The order `PreflightGuardV1 -> RouterV1 -> ProviderAdapterV1 -> ObserverV1` is fixed in `execute_request_v1` and must not be reordered without explicit architectural change.

8. **Provider execution occurs exactly once per request**  
   - For each call to `ServerManager.execute_request_v1`, `ProviderAdapterV1.execute(...)` must be invoked at most once, and only after successful preflight and routing.

9. **No stage may conditionally skip earlier stages**  
   - No pipeline stage is allowed to execute unless all preceding stages in the defined order have completed successfully for that request.

10. **No implicit retries**  
    - The pipeline does not perform automatic retries of preflight, routing, provider execution, or observation; any retry behavior must be implemented explicitly by the caller outside Pipeline V1.

11. **No silent fallback provider switching**  
    - The provider and model used by `ProviderAdapterV1` must be derived directly from the `ExecutionContextV1`; no stage may silently switch to an alternative provider or model without reflecting that change in the context.

12. **Legacy flows are unaffected**  
   - No existing methods or flows are routed through Pipeline V1 by default; using the pipeline requires explicit calls to `execute_request_v1`.

Each invariant can be tested via unit tests (e.g., immutability via attempted attribute assignment, hard gate via mocking managers and checking provider is not called, observer isolation via mocking `UsageDatabase.log_usage` to raise).


## 6. Safe Extension Zones

### 6.1 Safe extension zones

- **New methods inside `ServerManager` that call `execute_request_v1`**  
  - Adding additional methods in `ServerManager` that orchestrate or wrap calls to `execute_request_v1` is safe, as long as:
    - Existing methods (`create_agent`, `start_agent`, `stop_agent`, `test_agent_connection`) are not modified.
    - The pipeline order and invariants listed above are respected.

- **Additional helper functions or classes in `pipeline_v1.py`**  
  - Adding new, internal helpers that:
    - Do not change the behavior of existing classes.
    - Do not break the invariants.
    - Are used only by new pipeline consumers.

- **New tests exercising Pipeline V1**  
  - Tests that mock out `ConfigManager`, `CredentialManager`, `UsageDatabase`, and `VertexAIClient` to validate invariants without real side effects.

### 6.2 High‑risk zones

The following areas are high‑risk and should not be modified without a formal Architecture Decision Record (ADR):

- **ExecutionContextV1 and ExecutionRequestV1 structure or mutability**  
  - Changing fields, mutability, or meaning would break invariants and consumers.

- **Pipeline stage ordering or semantics in `execute_request_v1`**  
  - Reordering stages, skipping preflight, or moving observation earlier in the pipeline.

- **PreflightGuardV1 semantics**  
  - Changing what constitutes a valid agent or credentials path, or adding side effects.

- **ProviderAdapterV1 semantics**  
  - Changing which provider is used or how models are resolved, beyond what is encoded in the context.

- **ObserverV1 error‑handling model**  
  - Allowing observer errors to propagate would violate the non‑blocking observer principle.

- **Legacy components**  
  - `MCPAgentServer`, UI modules, `VertexAIClient`, `UsageDatabase`, and `ConfigManager` are outside the pipeline and are heavily used by existing flows.

### 6.3 Changes that must never occur without ADR

- Changing `ServerManager.execute_request_v1` signature or return shape.
- Making `ExecutionContextV1` or `ExecutionRequestV1` mutable.
- Introducing asynchronous behavior into Pipeline V1.
- Using Pipeline V1 implicitly from existing legacy flows without an explicit migration plan.

### 6.4 Change Control Rules

- Any change to the order of stages (`PreflightGuardV1`, `RouterV1`, `ProviderAdapterV1`, `ObserverV1`) requires a formal Architecture Decision Record (ADR) and corresponding test updates.
- Any change to the structure, semantics, or mutability of `ExecutionContextV1` or `ExecutionRequestV1` requires an ADR.
- Introducing asynchronous execution, concurrency primitives, or event-driven behavior into Pipeline V1 requires an ADR.
- Introducing shared mutable state between stages (such as global caches or shared mutable objects) is prohibited; any proposal to do so must be rejected or redesigned.


## 7. Known Trade‑offs

### 7.1 Sync‑only limitation

- The pipeline is fully synchronous and invokes `VertexAIClient` synchronously.
- This keeps the implementation simple and consistent with the rest of the codebase but limits scalability in high‑latency scenarios.

### 7.2 Mutable agent dict inside context

- `ExecutionContextV1` is frozen, but it holds an `agent: dict[str, Any]` that is itself mutable.
- The pipeline treats this dict as read‑only, but external code could mutate it if it retains a reference.
- This is acceptable within current usage patterns but is a potential source of subtle bugs if external mutation occurs.

### 7.3 Tight coupling to Vertex client

- `ProviderAdapterV1` is hard‑wired to `VertexAIClient` and uses its constructor and `generate_content` interface directly.
- This coupling makes it straightforward to use existing provider logic but requires caution if `VertexAIClient` changes.

### 7.4 Observer best‑effort logging

- `ObserverV1` logs usage on a best‑effort basis and swallows all errors.
- This ensures robustness but means that usage metrics may be incomplete or missing in some failure scenarios without affecting the primary behavior.

### 7.5 Shared configuration and credentials managers

- Pipeline V1 uses the same `ConfigManager` and `CredentialManager` instances as other parts of the system via `ServerManager`.
- This guarantees consistency of configuration and credentials but also couples pipeline behavior to the existing config and keyring semantics.

These trade‑offs reflect deliberate choices in the current implementation and should be considered when evaluating future changes to Pipeline V1. 


## 8. Explicit Non‑Goals

Pipeline V1 does **not** implement the following behaviors or mechanisms:

1. **Retry logic**  
   - The pipeline performs no automatic retries of any stage. If a stage fails, the error is propagated (or logged and swallowed in the case of the observer) without retry.

2. **Rate limiting**  
   - No per‑agent, per‑project, or global rate limiting is enforced within Pipeline V1.

3. **Quota enforcement**  
   - The pipeline does not track or enforce quotas; it relies on external systems or providers for any quota enforcement.

4. **Cost guard**  
   - There is no built‑in mechanism to prevent execution based on estimated or accumulated cost.

5. **Circuit breaker**  
   - Pipeline V1 does not include any circuit breaker logic to disable providers or routes after repeated failures.

6. **Caching**  
   - The pipeline does not cache inputs or outputs; each call to `execute_request_v1` results in a fresh provider invocation (subject to provider behavior).

7. **Streaming responses**  
   - All interactions with `VertexAIClient` are request/response; streaming semantics are not provided by Pipeline V1.

8. **Batching**  
   - The pipeline operates on a single request (`agent_id`, `prompt`) at a time and does not batch multiple prompts or agents into a single provider call.

9. **Multi‑provider orchestration**  
   - Only the existing `VertexAIClient` is invoked. There is no orchestration across multiple providers.

10. **Fallback models**  
    - The pipeline does not select alternative models if the configured model fails; it uses the model defined in the context.

11. **Automatic failover**  
    - There is no automatic failover to alternative providers, regions, or configurations.

Each of these non‑goals would require separate architectural decisions and dedicated implementation beyond the current scope of Pipeline V1.
