<script lang="ts">
  import { onMount } from "svelte";
  import { uiCacheGet, uiCacheSet, uiRunDeduped } from "$lib/ui_session";

  type Unit = "usd_per_day" | "tokens_per_day";
  type ScopeId = string;

  type Option<T extends string> = { id: T; label: string };
  type AppliedGuard = { id: string; scopeId: ScopeId; limitValue: string; unit: Unit; appliedAt: string };
  type BannerKind = "idle" | "info" | "success" | "danger";
  type DispatchError = { code?: string; message?: string };
  type BudgetState = {
    selected_scope_id: string;
    limit_value: string;
    unit: Unit;
    applied_guards: Array<{
      id: string;
      scope_id: string;
      limit_value: string;
      unit: Unit;
      applied_at: string;
    }>;
  };
  type BudgetResponse = {
    ok: boolean;
    status?: string;
    state?: BudgetState | null;
    error?: DispatchError | null;
    errors?: string[];
  };
  type ConnectionItem = { id?: string; connection_name?: string };
  type ConnectionsListResponse = {
    ok: boolean;
    status?: string;
    error?: DispatchError | null;
    errors?: string[];
    connections?: ConnectionItem[];
    data?: { connections?: ConnectionItem[] } | null;
  };

  const ALL_BRIDGES_SCOPE_ID = "all";
  const ALL_BRIDGES_LABEL = "All Bridges";
  const DEFAULT_SCOPE_OPTIONS: Option<ScopeId>[] = [{ id: ALL_BRIDGES_SCOPE_ID, label: ALL_BRIDGES_LABEL }];

  const UNIT_LABEL: Record<Unit, string> = { usd_per_day: "USD/day", tokens_per_day: "Tokens/day" };

  let selectedScopeId = $state<ScopeId>(ALL_BRIDGES_SCOPE_ID);
  let scopeOptions = $state<Option<ScopeId>[]>(DEFAULT_SCOPE_OPTIONS);
  let limitValue = $state("");
  let unit = $state<Unit>("usd_per_day");
  let applied = $state<AppliedGuard[]>([]);
  let saveInFlight = $state(false);
  let bannerKind = $state<BannerKind>("idle");
  let bannerText = $state("");
  let bannerTimer: ReturnType<typeof setTimeout> | null = null;
  const BUDGET_STATE_CACHE_KEY = "resilience.budget.state";
  const BUDGET_SCOPES_CACHE_KEY = "resilience.budget.scopes";
  const BUDGET_CACHE_TTL_MS = 120000;

  function formatTimestamp(value: string | Date) {
    const d = value instanceof Date ? value : new Date(value);
    return d.toLocaleString(undefined, {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  }

  function bannerClass(kind: BannerKind) {
    if (kind === "success") return "border-emerald-900/40 bg-emerald-400/10 text-emerald-200";
    if (kind === "danger") return "border-rose-900/40 bg-rose-500/10 text-rose-200";
    if (kind === "info") return "border-slate-700/60 bg-white/5 text-slate-200";
    return "border-slate-800 bg-transparent text-slate-200";
  }

  function setBanner(kind: BannerKind, text: string) {
    if (bannerTimer) {
      clearTimeout(bannerTimer);
      bannerTimer = null;
    }
    bannerKind = kind;
    bannerText = text;
    if (kind !== "idle" && text) {
      bannerTimer = setTimeout(() => {
        bannerKind = "idle";
        bannerText = "";
        bannerTimer = null;
      }, 3200);
    }
  }

  function dismissBanner() {
    if (bannerTimer) {
      clearTimeout(bannerTimer);
      bannerTimer = null;
    }
    bannerKind = "idle";
    bannerText = "";
  }

  function normalizeState(state: BudgetState | null | undefined) {
    const selected = String(state?.selected_scope_id || ALL_BRIDGES_SCOPE_ID) as ScopeId;
    const normalizedUnit: Unit = state?.unit === "tokens_per_day" ? "tokens_per_day" : "usd_per_day";
    const appliedRows: AppliedGuard[] = Array.isArray(state?.applied_guards)
      ? state!.applied_guards
          .filter((row) => row && typeof row.scope_id === "string" && typeof row.limit_value === "string")
          .map((row) => ({
            id: String(row.id || ""),
            scopeId: String(row.scope_id || ALL_BRIDGES_SCOPE_ID) as ScopeId,
            limitValue: String(row.limit_value || ""),
            unit: row.unit === "tokens_per_day" ? "tokens_per_day" : "usd_per_day",
            appliedAt: String(row.applied_at || ""),
          }))
      : [];
    return {
      selectedScopeId: selected,
      limitValue: String(state?.limit_value || ""),
      unit: normalizedUnit,
      applied: appliedRows,
    };
  }

  function applyHydratedState(state: BudgetState | null | undefined): boolean {
    const next = normalizeState(state);
    const normalized = ensureValidScopeSelection(next.selectedScopeId);
    const fallbackApplied = normalized !== next.selectedScopeId;
    selectedScopeId = normalized;
    limitValue = next.limitValue;
    unit = next.unit;
    applied = next.applied;
    return fallbackApplied;
  }

  function currentStatePayload(): BudgetState {
    return {
      selected_scope_id: selectedScopeId,
      limit_value: limitValue,
      unit,
      applied_guards: applied.map((row) => ({
        id: row.id,
        scope_id: row.scopeId,
        limit_value: row.limitValue,
        unit: row.unit,
        applied_at: row.appliedAt,
      })),
    };
  }

  function parseConnections(result: ConnectionsListResponse): ConnectionItem[] {
    if (Array.isArray(result.connections)) return result.connections;
    if (result.data && Array.isArray(result.data.connections)) return result.data.connections;
    return [];
  }

  function ensureValidScopeSelection(candidate: string): ScopeId {
    const id = String(candidate || ALL_BRIDGES_SCOPE_ID);
    const exists = scopeOptions.some((opt) => opt.id === id);
    return exists ? id : ALL_BRIDGES_SCOPE_ID;
  }

  async function loadScopeOptions() {
    const result = await uiRunDeduped(BUDGET_SCOPES_CACHE_KEY, async () => await dispatchInvoke({ op: "connections.list" })) as ConnectionsListResponse;
    if (!result.ok) {
      const code = result.error?.code ? `${result.error.code}: ` : "";
      const msg = result.error?.message || (result.errors || []).join("; ") || "request failed";
      setBanner("danger", `Connections load failed: ${code}${msg}`);
      scopeOptions = DEFAULT_SCOPE_OPTIONS;
      selectedScopeId = ALL_BRIDGES_SCOPE_ID;
      return;
    }
    const rows = parseConnections(result)
      .map((row) => ({
        id: String(row.id || "").trim(),
        connectionName: String(row.connection_name || "").trim(),
      }))
      .filter((row) => row.id.length > 0)
      .sort((a, b) => {
        const byName = a.connectionName.localeCompare(b.connectionName, undefined, { sensitivity: "base" });
        if (byName !== 0) return byName;
        return a.id.localeCompare(b.id, undefined, { sensitivity: "base" });
      });

    const dynamic = rows.map((row) => ({
      id: row.id,
      label: row.connectionName ? `${row.connectionName} (${row.id})` : row.id,
    }));
    scopeOptions = [DEFAULT_SCOPE_OPTIONS[0], ...dynamic];
    uiCacheSet(BUDGET_SCOPES_CACHE_KEY, scopeOptions);
    selectedScopeId = ensureValidScopeSelection(selectedScopeId);
  }

  async function dispatchInvoke(promptPayload: Record<string, unknown>): Promise<BudgetResponse | ConnectionsListResponse> {
    const tauriGlobal = typeof window !== "undefined"
      ? (window as any).__TAURI__ ?? (window as any).__TAURI_INTERNALS__
      : null;
    if (!tauriGlobal) {
      return {
        ok: false,
        status: "error",
        error: { code: "desktop_required", message: "Desktop app required" },
      };
    }
    const { invoke } = await import("@tauri-apps/api/core");
    const prompt = JSON.stringify(promptPayload);
    return await invoke("dispatch_execute_request_v1", {
      agentId: "resilience",
      agent_id: "resilience",
      prompt,
    }) as BudgetResponse | ConnectionsListResponse;
  }

  async function loadBudgetState() {
    setBanner("idle", "");
    try {
      const result = await uiRunDeduped(BUDGET_STATE_CACHE_KEY, async () => await dispatchInvoke({ op: "resilience.budget.get_state" })) as BudgetResponse;
      if (!result.ok) {
        const code = result.error?.code ? `${result.error.code}: ` : "";
        const msg = result.error?.message || (result.errors || []).join("; ") || "request failed";
        setBanner("danger", `Budget state load failed: ${code}${msg}`);
        return;
      }
      const fallbackApplied = applyHydratedState(result.state);
      uiCacheSet(BUDGET_STATE_CACHE_KEY, result.state ?? null);
      if (fallbackApplied) {
        await persistBudgetState();
      }
    } catch (err: any) {
      setBanner("danger", `Budget state load failed: ${err?.message || String(err)}`);
    }
  }

  async function persistBudgetState(successMessage = "") {
    if (saveInFlight) return;
    saveInFlight = true;
    setBanner("idle", "");
    try {
      const result = await dispatchInvoke({ op: "resilience.budget.set_state", state: currentStatePayload() }) as BudgetResponse;
      if (!result.ok) {
        const code = result.error?.code ? `${result.error.code}: ` : "";
        const msg = result.error?.message || (result.errors || []).join("; ") || "request failed";
        setBanner("danger", `Budget state save failed: ${code}${msg}`);
        return;
      }
      applyHydratedState(result.state);
      uiCacheSet(BUDGET_STATE_CACHE_KEY, result.state ?? null);
      if (successMessage) {
        setBanner("success", successMessage);
      }
    } catch (err: any) {
      setBanner("danger", `Budget state save failed: ${err?.message || String(err)}`);
    } finally {
      saveInFlight = false;
    }
  }

  function scopeLabel(id: ScopeId, shorten = false) {
    const raw = scopeOptions.find((s) => s.id === id)?.label ?? id;
    if (!shorten || id === ALL_BRIDGES_SCOPE_ID) return raw;
    return raw.replace(/\(([0-9a-fA-F-]{36})\)/g, (_, full: string) => `(${full.slice(0, 8)}…${full.slice(-6)})`);
  }

  function guardKey(scopeId: ScopeId, selectedUnit: Unit) {
    return `${scopeId}::${selectedUnit}`;
  }

  function createGuardId() {
    return `guard_local_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
  }

  function validateLimit(raw: string, selectedUnit: Unit): string {
    const trimmed = raw.trim();
    if (!trimmed) return "Limit is required.";
    const n = Number(trimmed);
    if (!Number.isFinite(n)) return "Enter a valid number.";
    if (n <= 0) return "Limit must be greater than 0.";
    if (selectedUnit === "tokens_per_day" && !Number.isInteger(n)) return "Tokens/day must be an integer";
    return "";
  }

  const limitError = $derived(() => validateLimit(limitValue, unit));
  const duplicateGuardError = $derived(() => {
    const key = guardKey(selectedScopeId, unit);
    return applied.some((row) => guardKey(row.scopeId, row.unit) === key)
      ? "A guard for this connection/unit already exists."
      : "";
  });
  const limitPlaceholder = $derived(() => (unit === "tokens_per_day" ? "e.g. 10,000" : "e.g. 25"));
  const limitHint = $derived(() => (unit === "tokens_per_day" ? "Daily token limit per connection." : "Daily USD limit per connection."));

  function applyGuard() {
    if (limitError()) return;
    if (duplicateGuardError()) {
      setBanner("danger", `Budget state save failed: invalid_resilience_budget_state: ${duplicateGuardError()}`);
      return;
    }
    const row: AppliedGuard = {
      id: createGuardId(),
      scopeId: selectedScopeId,
      limitValue: limitValue.trim(),
      unit,
      appliedAt: new Date().toISOString(),
    };
    applied = [row, ...applied];
    void persistBudgetState("Budget guard applied.");
  }

  function removeApplied(id: string) {
    applied = applied.filter((r) => r.id !== id);
    void persistBudgetState("Budget guard removed.");
  }

  function onScopeChange(event: Event) {
    selectedScopeId = (event.currentTarget as HTMLSelectElement).value as ScopeId;
    void persistBudgetState();
  }

  function onLimitInput(event: Event) {
    limitValue = (event.currentTarget as HTMLInputElement).value;
  }

  function onUnitChange(event: Event) {
    unit = (event.currentTarget as HTMLSelectElement).value === "tokens_per_day" ? "tokens_per_day" : "usd_per_day";
    void persistBudgetState();
  }

  onMount(() => {
    const cachedScopes = uiCacheGet<Option<ScopeId>[]>(BUDGET_SCOPES_CACHE_KEY, BUDGET_CACHE_TTL_MS);
    let refreshDelayMs = 0;
    if (cachedScopes && cachedScopes.length > 0) {
      scopeOptions = cachedScopes;
      selectedScopeId = ensureValidScopeSelection(selectedScopeId);
      refreshDelayMs = 90;
    }
    const cachedState = uiCacheGet<BudgetState | null>(BUDGET_STATE_CACHE_KEY, BUDGET_CACHE_TTL_MS);
    if (cachedState) {
      applyHydratedState(cachedState);
      refreshDelayMs = 90;
    }
    window.setTimeout(() => {
      void Promise.all([loadScopeOptions(), loadBudgetState()]);
    }, refreshDelayMs);
    return () => {
      if (bannerTimer) {
        clearTimeout(bannerTimer);
        bannerTimer = null;
      }
    };
  });
</script>

<div class="space-y-4 p-6">
  {#if bannerText}
    <div class={`rounded-md border px-3 py-2 text-xs ${bannerClass(bannerKind)}`}>
      <div class="flex items-center justify-between gap-2">
        <div class="min-w-0 truncate">{bannerText}</div>
        <button type="button" class="shrink-0 rounded border px-1.5 py-0.5 text-[10px] hover:bg-white/10" style="border-color: var(--border-subtle);" onclick={dismissBanner}>x</button>
      </div>
    </div>
  {/if}
  <div class="flex items-start justify-between gap-4">
    <div class="min-w-0">
      <div class="ui-subtitle">Configure persisted budget guards by connection scope.</div>
    </div>
  </div>

  <div class="ui-card ui-pad-md">
    <div class="ui-title">Applied guards</div>
    <div class="ui-subtitle mt-1">Changes are saved to the persisted resilience policy state.</div>

    <div class="mt-3 overflow-hidden rounded-md border" style="border-color: var(--border-subtle);">
      <table class="ui-table text-left text-xs">
        <thead>
          <tr class="border-b" style="border-color: var(--border-subtle);">
            <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Connection scope</th>
            <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Limit</th>
            <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Applied at</th>
            <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Action</th>
          </tr>
        </thead>
        <tbody>
          {#if applied.length === 0}
            <tr class="border-b" style="border-color: var(--border-subtle);">
              <td class="px-4 py-4" colspan="3" style="color: var(--text-muted);">No guards applied yet.</td>
              <td class="px-4 py-4 text-center" style="color: var(--text-muted);">—</td>
            </tr>
          {:else}
            {#each applied as row (row.id)}
              <tr class="border-b ui-row-hover" style="border-color: var(--border-subtle);">
                <td class="px-4 py-3" style="color: var(--text-primary);" title={scopeLabel(row.scopeId)}>{scopeLabel(row.scopeId, true)}</td>
                <td class="px-4 py-3" style="color: var(--text-muted);">
                  {row.limitValue} {UNIT_LABEL[row.unit]}
                </td>
                <td class="px-4 py-3" style="color: var(--text-muted);">{formatTimestamp(row.appliedAt)}</td>
                <td class="px-4 py-3">
                  <button
                    type="button"
                    class="ui-focus rounded-md border px-3 py-2 text-xs font-semibold transition-colors hover:bg-white/5"
                    style="border-color: var(--border-subtle); background-color: transparent; color: var(--text-primary);"
                    onclick={() => removeApplied(row.id)}
                  >
                    Remove
                  </button>
                </td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
  </div>

  <div class="ui-card ui-pad-md">
    <div class="ui-title">Add budget guard</div>
    <div class="ui-subtitle mt-1">Set a daily limit and apply.</div>
    <div class="mt-2 text-[11px]" style="color: var(--text-muted);">
      Alert guidance: >=75% shows warning and >=90% shows critical in Dashboard health alerts.
    </div>

    <div class="mt-4 grid gap-3 lg:grid-cols-3">
      <div class="lg:col-span-1">
        <div class="ui-subtitle">Connection</div>
        <select
          class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
          style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
          value={selectedScopeId}
          disabled={saveInFlight}
          onchange={onScopeChange}
        >
          {#each scopeOptions as s (s.id)}
            <option value={s.id}>{s.label}</option>
          {/each}
        </select>
      </div>

      <div class="lg:col-span-2">
        <div class="ui-subtitle">Limit</div>
        <div class="mt-2 flex flex-wrap items-start gap-2">
          <div class="min-w-[180px] flex-1">
            <input
              class="ui-focus h-9 w-full rounded-md border px-3 text-xs"
              style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
              inputmode="decimal"
              placeholder={limitPlaceholder()}
              value={limitValue}
              disabled={saveInFlight}
              oninput={onLimitInput}
            />
            <div class="mt-1 text-[11px]" style="color: var(--text-muted);">{limitHint()}</div>
            {#if limitError()}
              <div class="mt-1 text-xs" style="color: rgb(253, 164, 175);">{limitError()}</div>
            {:else if duplicateGuardError()}
              <div class="mt-1 text-xs" style="color: rgb(253, 164, 175);">{duplicateGuardError()}</div>
            {/if}
          </div>

          <select
            class="ui-focus h-9 rounded-md border px-3 text-xs"
            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
            value={unit}
            disabled={saveInFlight}
            onchange={onUnitChange}
          >
            <option value="usd_per_day">USD/day</option>
            <option value="tokens_per_day">Tokens/day</option>
          </select>
        </div>
      </div>
    </div>

    <div class="mt-4 flex justify-end">
      <button
        type="button"
        class="ui-focus rounded-md border px-5 py-2.5 text-xs font-semibold transition-colors hover:bg-white/5 disabled:opacity-60"
        style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary); box-shadow: var(--shadow-1);"
        disabled={!!limitError() || !!duplicateGuardError() || saveInFlight}
        onclick={applyGuard}
      >
        Apply
      </button>
    </div>
  </div>
</div>
