<script lang="ts">
  import { getResilienceSession, patchResilienceSession } from "$lib/ui_session";

  type Unit = "usd_per_day" | "tokens_per_day";
  type ScopeId = "all" | "bridge_alpha" | "bridge_beta" | "bridge_gamma";

  type Option<T extends string> = { id: T; label: string };
  type AppliedGuard = { id: string; scopeId: ScopeId; limitValue: string; unit: Unit; timestampLabel: string };

  const SCOPES: Option<ScopeId>[] = [
    { id: "all", label: "All bridges" },
    { id: "bridge_alpha", label: "Bridge Alpha" },
    { id: "bridge_beta", label: "Bridge Beta" },
    { id: "bridge_gamma", label: "Bridge Gamma" },
  ];

  const UNIT_LABEL: Record<Unit, string> = { usd_per_day: "USD/day", tokens_per_day: "Tokens/day" };

  let selectedScopeId = $state<ScopeId>("all");
  let limitValue = $state("");
  let unit = $state<Unit>("usd_per_day");
  const savedApplied = getResilienceSession().appliedGuards as AppliedGuard[];
  let applied = $state<AppliedGuard[]>(Array.isArray(savedApplied) ? savedApplied : []);

  function formatTimestamp(value: Date) {
    return value.toLocaleString(undefined, {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  }

  function scopeLabel(id: ScopeId) {
    return SCOPES.find((s) => s.id === id)?.label ?? id;
  }

  function validateLimit(raw: string, selectedUnit: Unit): string {
    const trimmed = raw.trim();
    if (!trimmed) return "Enter a limit";
    const n = Number(trimmed);
    if (!Number.isFinite(n)) return "Enter a number";
    if (n <= 0) return "Must be > 0";
    if (selectedUnit === "tokens_per_day" && !Number.isInteger(n)) return "Tokens/day must be an integer";
    return "";
  }

  const limitError = $derived(() => validateLimit(limitValue, unit));

  function applyGuard() {
    if (limitError()) return;
    const row: AppliedGuard = {
      id: `guard_${Math.random().toString(16).slice(2)}_${Date.now()}`,
      scopeId: selectedScopeId,
      limitValue: limitValue.trim(),
      unit,
      timestampLabel: formatTimestamp(new Date()),
    };
    applied = [row, ...applied];
  }

  function removeApplied(id: string) {
    applied = applied.filter((r) => r.id !== id);
  }

  $effect(() => {
    patchResilienceSession({ appliedGuards: applied });
  });
</script>

<div class="space-y-4 p-6">
  <div class="flex items-start justify-between gap-4">
    <div class="min-w-0">
      <div class="ui-subtitle">Configure UI-only budget guards by bridge/connection scope (not persisted).</div>
    </div>
  </div>

  <div class="ui-card ui-pad-md">
    <div class="ui-title">Applied guards (UI-only)</div>
    <div class="ui-subtitle mt-1">Applies add rows locally; nothing is persisted.</div>

    <div class="mt-3 overflow-hidden rounded-md border" style="border-color: var(--border-subtle);">
      <table class="ui-table text-left text-xs">
        <thead>
          <tr class="border-b" style="border-color: var(--border-subtle);">
            <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Bridge scope</th>
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
                <td class="px-4 py-3" style="color: var(--text-primary);">{scopeLabel(row.scopeId)}</td>
                <td class="px-4 py-3" style="color: var(--text-muted);">
                  {row.limitValue} {UNIT_LABEL[row.unit]}
                </td>
                <td class="px-4 py-3" style="color: var(--text-muted);">{row.timestampLabel}</td>
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
    <div class="ui-title">Budget Guard</div>
    <div class="ui-subtitle mt-1">Set a daily limit and apply (UI-only).</div>

    <div class="mt-4 grid gap-3 lg:grid-cols-3">
      <div class="lg:col-span-1">
        <div class="ui-subtitle">Bridge / Connection</div>
        <select
          class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
          style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
          value={selectedScopeId}
          onchange={(e) => (selectedScopeId = (e.currentTarget as HTMLSelectElement).value as ScopeId)}
        >
          {#each SCOPES as s (s.id)}
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
              placeholder="e.g. 25"
              value={limitValue}
              oninput={(e) => (limitValue = (e.currentTarget as HTMLInputElement).value)}
            />
            {#if limitError()}
              <div class="mt-1 text-xs" style="color: rgb(253, 164, 175);">{limitError()}</div>
            {/if}
          </div>

          <select
            class="ui-focus h-9 rounded-md border px-3 text-xs"
            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
            value={unit}
            onchange={(e) => (unit = ((e.currentTarget as HTMLSelectElement).value === 'tokens_per_day' ? 'tokens_per_day' : 'usd_per_day'))}
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
        disabled={!!limitError()}
        onclick={applyGuard}
      >
        Apply
      </button>
    </div>
  </div>
</div>
