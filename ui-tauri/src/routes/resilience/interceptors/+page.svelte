<script lang="ts">
  import { getResilienceSession, patchResilienceSession } from "$lib/ui_session";

  type InterceptorId = "json_syntax_repair";
  type Mode = "off" | "safe" | "aggressive";

  type Interceptor = { id: InterceptorId; name: string; description: string };
  type InterceptorSettings = { mode: Mode; maxAttempts: number; strictJson: boolean; note: string };

  const INTERCEPTORS: Interceptor[] = [
    { id: "json_syntax_repair", name: "JSON Syntax Repair", description: "Attempts to repair minor JSON issues in tool outputs (UI-only)."},
  ];

  const defaultEnabled: Record<InterceptorId, boolean> = { json_syntax_repair: false };
  const defaultSettings: Record<InterceptorId, InterceptorSettings> = {
    json_syntax_repair: { mode: "safe", maxAttempts: 2, strictJson: true, note: "Stub settings for UI replication only. No runtime wiring." },
  };

  const savedResilience = getResilienceSession();
  const savedEnabled = savedResilience.interceptorEnabledById as Record<string, boolean>;
  const savedSettings = savedResilience.interceptorSettingsById as Record<string, unknown>;

  let enabledById = $state<Record<InterceptorId, boolean>>(
    savedEnabled?.json_syntax_repair === true ? { json_syntax_repair: true } : defaultEnabled,
  );
  let settingsById = $state<Record<InterceptorId, InterceptorSettings>>(
    (savedSettings?.json_syntax_repair as InterceptorSettings) ? { json_syntax_repair: savedSettings.json_syntax_repair as InterceptorSettings } : defaultSettings,
  );

  let configOpen = $state(false);
  let configId = $state<InterceptorId | null>(null);
  let draftMode = $state<Mode>("safe");
  let draftMaxAttempts = $state("2");
  let draftStrictJson = $state(true);

  function openConfig(id: InterceptorId) {
    configId = id;
    const s = settingsById[id];
    draftMode = s.mode;
    draftMaxAttempts = String(s.maxAttempts);
    draftStrictJson = s.strictJson;
    configOpen = true;
  }

  function closeConfig() {
    configOpen = false;
    configId = null;
  }

  function saveConfig() {
    const id = configId;
    if (!id) return;
    const raw = draftMaxAttempts.trim();
    const n = Number(raw);
    const maxAttempts = Number.isFinite(n) && n >= 0 ? Math.floor(n) : 0;
    settingsById = {
      ...settingsById,
      [id]: { ...settingsById[id], mode: draftMode, maxAttempts, strictJson: draftStrictJson },
    };
    closeConfig();
  }

  $effect(() => {
    patchResilienceSession({ interceptorEnabledById: enabledById, interceptorSettingsById: settingsById });
  });
</script>

<div class="space-y-4 p-6">
  <div class="flex items-start justify-between gap-4">
    <div class="min-w-0">
      <div class="ui-subtitle">Manage resilience interceptors (UI-only; not wired).</div>
    </div>
  </div>

  <div class="grid gap-3 lg:grid-cols-2">
    {#each INTERCEPTORS as interceptor (interceptor.id)}
      <div class="ui-card ui-pad-md">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <div class="ui-title">{interceptor.name}</div>
            <div class="ui-subtitle mt-1">{interceptor.description}</div>
          </div>

          <label class="flex items-center gap-2 text-xs" style="color: var(--text-primary);">
            <input
              type="checkbox"
              class="ui-focus h-4 w-4 rounded border"
              style="border-color: var(--border-subtle); background-color: var(--surface-2);"
              bind:checked={enabledById[interceptor.id]}
            />
            <span>{enabledById[interceptor.id] ? "Enabled" : "Disabled"}</span>
          </label>
        </div>

        <div class="mt-4 flex items-center justify-between gap-3">
          <div class="text-xs" style="color: var(--text-muted);">UI-only; not persisted.</div>
          <button
            type="button"
            class="ui-focus rounded-md border px-3 py-2 text-xs font-semibold transition-colors hover:bg-white/5"
            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary); box-shadow: var(--shadow-1);"
            onclick={() => openConfig(interceptor.id)}
          >
            Configure
          </button>
        </div>
      </div>
    {/each}
  </div>
</div>

{#if configOpen}
  {@const id = configId}
  {@const current = id ? settingsById[id] : null}
  <div class="fixed inset-0 z-50">
    <button
      type="button"
      class="absolute inset-0 h-full w-full"
      style="background-color: rgba(0, 0, 0, 0.55);"
      aria-label="Close interceptor config modal"
      onclick={closeConfig}
    ></button>
    <div class="absolute left-1/2 top-1/2 w-[720px] max-w-[calc(100vw-40px)] -translate-x-1/2 -translate-y-1/2">
      <div class="ui-card ui-pad-lg" style="background-color: var(--surface-1);">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <div class="ui-title">Configure interceptor</div>
            <div class="ui-subtitle mt-1">UI-only; not persisted.</div>
          </div>
          <button
            type="button"
            class="ui-focus rounded-md border px-3 py-2 text-xs font-medium transition-colors hover:bg-white/5"
            style="border-color: var(--border-subtle); color: var(--text-primary); background-color: transparent;"
            onclick={closeConfig}
          >
            Close
          </button>
        </div>

        {#if current}
          <div class="mt-4 grid gap-3">
            <div class="grid gap-3 sm:grid-cols-2">
              <div>
                <div class="ui-subtitle">Mode</div>
                <select
                  class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
                  style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
                  value={draftMode}
                  onchange={(e) => (draftMode = ((e.currentTarget as HTMLSelectElement).value as Mode) || "safe")}
                >
                  <option value="off">Off</option>
                  <option value="safe">Safe</option>
                  <option value="aggressive">Aggressive</option>
                </select>
              </div>
              <div>
                <div class="ui-subtitle">Max attempts</div>
                <input
                  class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
                  style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
                  inputmode="numeric"
                  value={draftMaxAttempts}
                  oninput={(e) => (draftMaxAttempts = (e.currentTarget as HTMLInputElement).value)}
                />
              </div>
            </div>

            <label class="flex items-center gap-2 text-xs" style="color: var(--text-primary);">
              <input
                type="checkbox"
                class="ui-focus h-4 w-4 rounded border"
                style="border-color: var(--border-subtle); background-color: var(--surface-2);"
                bind:checked={draftStrictJson}
              />
              <span>Strict JSON output</span>
            </label>

            <div class="ui-card ui-pad-md" style="background-color: var(--surface-2);">
              <div class="ui-subtitle">Notes</div>
              <div class="mt-2 text-xs" style="color: var(--text-muted);">{current.note}</div>
            </div>
          </div>

          <div class="mt-4 flex justify-end gap-2">
            <button
              type="button"
              class="ui-focus h-9 rounded-md border px-3 text-xs font-medium transition-colors hover:bg-white/5"
              style="border-color: var(--border-subtle); background-color: transparent; color: var(--text-primary);"
              onclick={closeConfig}
            >
              Cancel
            </button>
            <button
              type="button"
              class="ui-focus h-9 rounded-md border px-3 text-xs font-semibold transition-colors hover:bg-white/5"
              style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary); box-shadow: var(--shadow-1);"
              onclick={saveConfig}
            >
              Save
            </button>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}
