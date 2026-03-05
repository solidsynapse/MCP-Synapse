<script lang="ts">
  import { onMount } from "svelte";
  import { uiCacheGet, uiCacheSet, uiRunDeduped } from "$lib/ui_session";

  type InterceptorId = "json_syntax_repair";
  type Mode = "off" | "safe" | "aggressive";
  type BannerKind = "idle" | "info" | "success" | "danger";
  type DispatchError = { code?: string; message?: string };

  type Interceptor = { id: InterceptorId; name: string; description: string };
  type InterceptorSettings = { mode: Mode; maxAttempts: number; strictJson: boolean; note: string };
  type InterceptorsState = {
    enabled_by_id: Record<string, boolean>;
    settings_by_id: Record<string, { mode: Mode; max_attempts: number; strict_json: boolean; note?: string }>;
  };
  type InterceptorsResponse = {
    ok: boolean;
    status?: string;
    result?: InterceptorsState | null;
    error?: DispatchError | null;
  };

  const INTERCEPTORS: Interceptor[] = [
    { id: "json_syntax_repair", name: "JSON Syntax Repair", description: "Attempts to repair minor JSON issues in tool outputs."},
  ];

  const defaultEnabled: Record<InterceptorId, boolean> = { json_syntax_repair: false };
  const defaultSettings: Record<InterceptorId, InterceptorSettings> = {
    json_syntax_repair: { mode: "safe", maxAttempts: 2, strictJson: true, note: "Deterministic resilience setting persisted in core state." },
  };
  let enabledById = $state<Record<InterceptorId, boolean>>(defaultEnabled);
  let settingsById = $state<Record<InterceptorId, InterceptorSettings>>(defaultSettings);

  let configOpen = $state(false);
  let configId = $state<InterceptorId | null>(null);
  let draftMode = $state<Mode>("safe");
  let draftMaxAttempts = $state("2");
  let draftStrictJson = $state(true);
  let saveInFlight = $state(false);
  let bannerKind = $state<BannerKind>("idle");
  let bannerText = $state("");
  let bannerTimer: ReturnType<typeof setTimeout> | null = null;
  const INTERCEPTORS_CACHE_KEY = "resilience.interceptors.state";
  const INTERCEPTORS_CACHE_TTL_MS = 120000;

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

  function normalizeState(state: InterceptorsState | null | undefined) {
    const enabledRaw = state?.enabled_by_id ?? {};
    const settingsRaw = state?.settings_by_id ?? {};
    const normalizedEnabled: Record<InterceptorId, boolean> = {
      json_syntax_repair: Boolean(enabledRaw.json_syntax_repair),
    };
    const row = settingsRaw.json_syntax_repair;
    const normalizedSettings: Record<InterceptorId, InterceptorSettings> = {
      json_syntax_repair: {
        mode: row?.mode === "aggressive" ? "aggressive" : "safe",
        maxAttempts: Number.isFinite(Number(row?.max_attempts)) ? Math.max(0, Math.floor(Number(row?.max_attempts))) : 2,
        strictJson: Boolean(row?.strict_json),
        note: typeof row?.note === "string" ? row.note : defaultSettings.json_syntax_repair.note,
      },
    };
    return { enabled: normalizedEnabled, settings: normalizedSettings };
  }

  function currentStatePayload(): InterceptorsState {
    return {
      enabled_by_id: {
        json_syntax_repair: Boolean(enabledById.json_syntax_repair),
      },
      settings_by_id: {
        json_syntax_repair: {
          mode: settingsById.json_syntax_repair.mode,
          max_attempts: settingsById.json_syntax_repair.maxAttempts,
          strict_json: settingsById.json_syntax_repair.strictJson,
          note: settingsById.json_syntax_repair.note,
        },
      },
    };
  }

  function applyHydratedState(state: InterceptorsState | null | undefined) {
    const normalized = normalizeState(state);
    enabledById = normalized.enabled;
    settingsById = normalized.settings;
  }

  async function dispatchInvoke(payload: Record<string, unknown>): Promise<InterceptorsResponse> {
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
    return await invoke("dispatch_execute_request_v1", {
      agentId: "resilience",
      agent_id: "resilience",
      prompt: JSON.stringify(payload),
    }) as InterceptorsResponse;
  }

  async function loadState() {
    setBanner("idle", "");
    try {
      const result = await uiRunDeduped(INTERCEPTORS_CACHE_KEY, async () => await dispatchInvoke({ op: "resilience.interceptors.get_state" }));
      if (!result.ok) {
        const code = result.error?.code ? `${result.error.code}: ` : "";
        const msg = result.error?.message || "request failed";
        setBanner("danger", `Interceptors load failed: ${code}${msg}`);
        return;
      }
      applyHydratedState(result.result);
      uiCacheSet(INTERCEPTORS_CACHE_KEY, result.result ?? null);
    } catch (err: any) {
      setBanner("danger", `Interceptors load failed: ${err?.message || String(err)}`);
    }
  }

  async function persistState(successText = "") {
    if (saveInFlight) return;
    saveInFlight = true;
    setBanner("idle", "");
    try {
      const result = await dispatchInvoke({ op: "resilience.interceptors.set_state", state: currentStatePayload() });
      if (!result.ok) {
        const code = result.error?.code ? `${result.error.code}: ` : "";
        const msg = result.error?.message || "request failed";
        setBanner("danger", `Interceptors save failed: ${code}${msg}`);
        return;
      }
      applyHydratedState(result.result);
      uiCacheSet(INTERCEPTORS_CACHE_KEY, result.result ?? null);
      if (successText) setBanner("success", successText);
    } catch (err: any) {
      setBanner("danger", `Interceptors save failed: ${err?.message || String(err)}`);
    } finally {
      saveInFlight = false;
    }
  }

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
    void persistState("Interceptor settings saved.");
  }

  function modeDescription(mode: Mode): string {
    if (mode === "aggressive") return "Aggressive: may rewrite more structure; best for noisy outputs.";
    return "Safe: applies low-risk fixes such as trailing commas or minor formatting issues.";
  }

  function onToggle(interceptorId: InterceptorId, checked: boolean) {
    enabledById = {
      ...enabledById,
      [interceptorId]: checked,
    };
    void persistState("Interceptor state updated.");
  }

  onMount(() => {
    const cached = uiCacheGet<InterceptorsState | null>(INTERCEPTORS_CACHE_KEY, INTERCEPTORS_CACHE_TTL_MS);
    let refreshDelayMs = 0;
    if (cached) applyHydratedState(cached);
    if (cached) refreshDelayMs = 90;
    window.setTimeout(() => {
      void loadState();
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
      <div class="ui-subtitle">Manage persisted resilience interceptors.</div>
      <div class="mt-1 text-[11px]" style="color: var(--text-muted);">Changes apply to new requests after you click Save.</div>
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
              checked={enabledById[interceptor.id]}
              disabled={saveInFlight}
              onchange={(e) => onToggle(interceptor.id, (e.currentTarget as HTMLInputElement).checked)}
            />
            <span>{enabledById[interceptor.id] ? "On" : "Off"}</span>
          </label>
        </div>

        <div class="mt-4 flex items-center justify-between gap-3">
          <div class="text-xs" style="color: var(--text-muted);">Saved to your local policy state.</div>
          <button
            type="button"
            class="ui-focus rounded-md border px-3 py-2 text-xs font-semibold transition-colors hover:bg-white/5"
            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary); box-shadow: var(--shadow-1);"
            disabled={saveInFlight}
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
            <div class="ui-subtitle mt-1">Changes are saved to your local resilience policy state.</div>
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
                  disabled={saveInFlight}
                  onchange={(e) => (draftMode = ((e.currentTarget as HTMLSelectElement).value as Mode) || "safe")}
                >
                  <option value="safe">Safe</option>
                  <option value="aggressive">Aggressive</option>
                </select>
                <div class="mt-1 text-[11px]" style="color: var(--text-muted);">{modeDescription(draftMode)}</div>
              </div>
              <div>
                <div class="ui-subtitle">Max attempts</div>
                <input
                  class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
                  style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
                  inputmode="numeric"
                  value={draftMaxAttempts}
                  disabled={saveInFlight}
                  oninput={(e) => (draftMaxAttempts = (e.currentTarget as HTMLInputElement).value)}
                />
                <div class="mt-1 text-[11px]" style="color: var(--text-muted);">1-4 recommended. Higher values may increase latency.</div>
              </div>
            </div>

            <label class="flex items-center gap-2 text-xs" style="color: var(--text-primary);">
              <input
                type="checkbox"
                class="ui-focus h-4 w-4 rounded border"
                style="border-color: var(--border-subtle); background-color: var(--surface-2);"
                bind:checked={draftStrictJson}
                disabled={saveInFlight}
              />
              <span>Strict JSON output</span>
            </label>
            <div class="text-[11px]" style="color: var(--text-muted);">If enabled, the interceptor enforces strict JSON formatting.</div>

            <div class="ui-card ui-pad-md" style="background-color: var(--surface-2);">
              <div class="ui-subtitle">Mode guidance</div>
              <div class="mt-2 text-xs" style="color: var(--text-muted);">{modeDescription(draftMode)}</div>
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
              disabled={saveInFlight}
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
