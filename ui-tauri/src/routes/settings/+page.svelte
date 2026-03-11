<script lang="ts">
  import { onMount } from "svelte";
  import { uiCacheGet, uiCacheSet, uiRunDeduped } from "$lib/ui_session";

  type DataRetention = "1m" | "3m" | "6m" | "unlimited";
  type PortMode = "auto" | "manual";
  type BannerKind = "idle" | "info" | "success" | "danger";
  type DispatchError = { code?: string; message?: string };
  type SettingsState = {
    data_retention: DataRetention;
    port_mode: PortMode;
    port_min: string;
    port_max: string;
  };
  type SettingsResponse = {
    ok: boolean;
    status?: string;
    result?: SettingsState | null;
    error?: DispatchError | null;
  };

  const DEFAULT_STATE: SettingsState = {
    data_retention: "3m",
    port_mode: "auto",
    port_min: "5000",
    port_max: "6000",
  };

  let dataRetention = $state<DataRetention>(DEFAULT_STATE.data_retention);
  let portMode = $state<PortMode>(DEFAULT_STATE.port_mode);
  let portMin = $state(DEFAULT_STATE.port_min);
  let portMax = $state(DEFAULT_STATE.port_max);

  let resetConfirmOpen = $state(false);
  let shortcutsOpen = $state(false);
  let saveInFlight = $state(false);
  let bannerKind = $state<BannerKind>("idle");
  let bannerText = $state("");
  const SETTINGS_CACHE_KEY = "settings.state";
  const SETTINGS_CACHE_TTL_MS = 120000;
  let portPersistTimer: ReturnType<typeof setTimeout> | null = null;
  const ACTION_WIDTH_CLASS = "w-[140px]";
  const ACTION_COLUMN_WIDTH_CLASS = "w-[360px]";

  function bannerClass(kind: BannerKind) {
    if (kind === "success") return "border-emerald-900/40 bg-emerald-400/10 text-emerald-200";
    if (kind === "danger") return "border-rose-900/40 bg-rose-500/10 text-rose-200";
    if (kind === "info") return "border-slate-700/60 bg-white/5 text-slate-200";
    return "border-slate-800 bg-transparent text-slate-200";
  }

  function setBanner(kind: BannerKind, text: string) {
    bannerKind = kind;
    bannerText = text;
  }

  function normalizeState(state: SettingsState | null | undefined): SettingsState {
    const dataRetentionValue = state?.data_retention === "1m" || state?.data_retention === "6m" || state?.data_retention === "unlimited"
      ? state.data_retention
      : "3m";
    const portModeValue = state?.port_mode === "manual" ? "manual" : "auto";
    return {
      data_retention: dataRetentionValue,
      port_mode: portModeValue,
      port_min: String(state?.port_min ?? DEFAULT_STATE.port_min),
      port_max: String(state?.port_max ?? DEFAULT_STATE.port_max),
    };
  }

  function applyState(state: SettingsState | null | undefined) {
    const next = normalizeState(state);
    dataRetention = next.data_retention;
    portMode = next.port_mode;
    portMin = next.port_min;
    portMax = next.port_max;
  }

  function currentStatePayload(): SettingsState {
    return {
      data_retention: dataRetention,
      port_mode: portMode,
      port_min: portMin,
      port_max: portMax,
    };
  }

  async function dispatchInvoke(payload: Record<string, unknown>): Promise<SettingsResponse> {
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
      agentId: "settings",
      agent_id: "settings",
      prompt: JSON.stringify(payload),
    }) as SettingsResponse;
  }

  async function loadState() {
    setBanner("idle", "");
    try {
      const result = await uiRunDeduped(SETTINGS_CACHE_KEY, async () => await dispatchInvoke({ op: "settings.get_state" }));
      if (!result.ok) {
        const code = result.error?.code ? `${result.error.code}: ` : "";
        const msg = result.error?.message || "request failed";
        setBanner("danger", `Settings load failed: ${code}${msg}`);
        return;
      }
      applyState(result.result);
      uiCacheSet(SETTINGS_CACHE_KEY, result.result ?? null);
    } catch (err: any) {
      setBanner("danger", `Settings load failed: ${err?.message || String(err)}`);
    }
  }

  async function persistState(successMessage = "") {
    if (saveInFlight) return;
    saveInFlight = true;
    setBanner("idle", "");
    try {
      const result = await dispatchInvoke({ op: "settings.set_state", state: currentStatePayload() });
      if (!result.ok) {
        const code = result.error?.code ? `${result.error.code}: ` : "";
        const msg = result.error?.message || "request failed";
        setBanner("danger", `Settings save failed: ${code}${msg}`);
        return;
      }
      applyState(result.result);
      uiCacheSet(SETTINGS_CACHE_KEY, result.result ?? null);
      if (successMessage) {
        setBanner("success", successMessage);
      }
    } catch (err: any) {
      setBanner("danger", `Settings save failed: ${err?.message || String(err)}`);
    } finally {
      saveInFlight = false;
    }
  }

  function openResetConfirm() {
    resetConfirmOpen = true;
  }

  function closeResetConfirm() {
    resetConfirmOpen = false;
  }

  function confirmReset() {
    applyState(DEFAULT_STATE);
    void persistState("Settings reset.");
    closeResetConfirm();
  }

  function openShortcuts() {
    shortcutsOpen = true;
  }

  function closeShortcuts() {
    shortcutsOpen = false;
  }

  async function copyDiagnostics() {
    let versionText = "unknown";
    try {
      const tauriGlobal = typeof window !== "undefined"
        ? (window as any).__TAURI__ ?? (window as any).__TAURI_INTERNALS__
        : null;
      if (tauriGlobal) {
        const { getVersion } = await import("@tauri-apps/api/app");
        versionText = await getVersion();
      }
    } catch {
      versionText = "unknown";
    }
    const now = new Date();
    const timeText = now.toISOString();
    const portModeLabel = portMode === "manual" ? "manual" : "auto";
    const text = [
      "MCP Synapse Diagnostics",
      `Version: ${versionText}`,
      `Captured: ${timeText}`,
      `Data retention: ${dataRetention}`,
      `Port mode: ${portModeLabel}`,
      `Port range: ${portMin}-${portMax}`,
    ].join("\n");
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const el = document.createElement("textarea");
      el.value = text;
      el.style.position = "fixed";
      el.style.left = "-9999px";
      document.body.appendChild(el);
      el.focus();
      el.select();
      document.execCommand("copy");
      document.body.removeChild(el);
    }
  }

  function onDataRetentionChange(event: Event) {
    dataRetention = (event.currentTarget as HTMLSelectElement).value as DataRetention;
    void persistState();
  }

  function onPortModeChange(event: Event) {
    portMode = (event.currentTarget as HTMLSelectElement).value as PortMode;
    void persistState();
  }

  function onPortMinInput() {
    schedulePortPersist();
  }

  function onPortMaxInput() {
    schedulePortPersist();
  }

  function schedulePortPersist() {
    if (portPersistTimer) {
      clearTimeout(portPersistTimer);
      portPersistTimer = null;
    }
    portPersistTimer = setTimeout(() => {
      portPersistTimer = null;
      void persistState();
    }, 280);
  }

  onMount(() => {
    const onShortcutEscape = (event: Event) => {
      if (shortcutsOpen) {
        closeShortcuts();
        event.preventDefault();
        return;
      }
      if (resetConfirmOpen) {
        closeResetConfirm();
        event.preventDefault();
      }
    };
    window.addEventListener("synapse:shortcut-escape", onShortcutEscape as EventListener);

    const cached = uiCacheGet<SettingsState | null>(SETTINGS_CACHE_KEY, SETTINGS_CACHE_TTL_MS);
    let refreshDelayMs = 0;
    if (cached) {
      applyState(cached);
      refreshDelayMs = 90;
    }
    window.setTimeout(() => {
      void loadState();
    }, refreshDelayMs);
    return () => {
      window.removeEventListener("synapse:shortcut-escape", onShortcutEscape as EventListener);
      if (portPersistTimer) {
        clearTimeout(portPersistTimer);
        portPersistTimer = null;
      }
    };
  });
</script>

<div class="space-y-4 p-6">
  {#if bannerText}
    <div class={`rounded-md border px-3 py-2 text-xs ${bannerClass(bannerKind)}`}>{bannerText}</div>
  {/if}
  <div class="flex items-start justify-between gap-4">
    <div class="min-w-0">
      <div class="ui-subtitle">Settings are saved locally.</div>
    </div>
  </div>

  <div class="ui-card ui-pad-md">
    <div class="overflow-hidden rounded-md border" style="border-color: var(--border-subtle);">
      <div class="px-4">
        <div class="flex items-center justify-between gap-4 py-3">
          <div class="min-w-0">
            <div class="text-sm font-semibold" style="color: var(--text-primary);">Data retention</div>
            <div class="mt-1 text-xs" style="color: var(--text-muted);">Choose how long local usage records are retained.</div>
          </div>
          <div class={`flex items-center justify-end ${ACTION_COLUMN_WIDTH_CLASS}`}>
            <select
              class={`ui-focus h-9 rounded-md border px-3 text-xs ${ACTION_WIDTH_CLASS}`}
              style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
              value={dataRetention}
              disabled={saveInFlight}
              onchange={onDataRetentionChange}
            >
              <option value="1m">1 month</option>
              <option value="3m">3 months</option>
              <option value="6m">6 months</option>
              <option value="unlimited">Unlimited</option>
            </select>
          </div>
        </div>

        <div class="border-b" style="border-color: var(--border-subtle);"></div>

        <div class="flex items-center justify-between gap-4 py-3">
          <div class="min-w-0">
            <div class="text-sm font-semibold" style="color: var(--text-primary);">Port range</div>
            <div class="mt-1 text-xs" style="color: var(--text-muted);">Auto selects an available port at startup.</div>
          </div>
          <div class={`flex items-center justify-end gap-2 ${ACTION_COLUMN_WIDTH_CLASS}`}>
            <select
              class={`ui-focus h-9 rounded-md border px-3 text-xs ${ACTION_WIDTH_CLASS}`}
              style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
              value={portMode}
              disabled={saveInFlight}
              onchange={onPortModeChange}
            >
              <option value="auto">Auto</option>
              <option value="manual">Manual</option>
            </select>
            {#if portMode === "manual"}
              <input
                class="ui-focus h-9 w-24 rounded-md border px-3 text-xs"
                style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
                inputmode="numeric"
                placeholder="Min"
                bind:value={portMin}
                oninput={onPortMinInput}
              />
              <input
                class="ui-focus h-9 w-24 rounded-md border px-3 text-xs"
                style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
                inputmode="numeric"
                placeholder="Max"
                bind:value={portMax}
                oninput={onPortMaxInput}
              />
            {/if}
          </div>
        </div>

        <div class="border-b" style="border-color: var(--border-subtle);"></div>

        <div class="flex items-center justify-between gap-4 py-3">
          <div class="min-w-0">
            <div class="text-sm font-semibold" style="color: var(--text-primary);">Keyboard shortcuts</div>
            <div class="mt-1 text-xs" style="color: var(--text-muted);">Quick reference for common keys.</div>
          </div>
          <button
            type="button"
            class={`ui-focus rounded-md border px-3 py-2 text-xs font-semibold transition-colors hover:bg-white/5 active:scale-[0.98] ${ACTION_WIDTH_CLASS}`}
            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary); box-shadow: var(--shadow-1);"
            onclick={openShortcuts}
          >
            Show
          </button>
        </div>

        <div class="border-b" style="border-color: var(--border-subtle);"></div>

        <div class="flex items-center justify-between gap-4 py-3">
          <div class="min-w-0">
            <div class="text-sm font-semibold" style="color: var(--text-primary);">Diagnostics</div>
            <div class="mt-1 text-xs" style="color: var(--text-muted);">Copies diagnostics to clipboard only. No settings are changed.</div>
          </div>
          <button
            type="button"
            class={`ui-focus rounded-md border px-3 py-2 text-xs font-semibold transition-colors hover:bg-white/5 active:scale-[0.98] ${ACTION_WIDTH_CLASS}`}
            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary); box-shadow: var(--shadow-1);"
            onclick={copyDiagnostics}
          >
            Copy
          </button>
        </div>

        <div class="border-b" style="border-color: var(--border-subtle);"></div>

        <div class="flex items-center justify-between gap-4 py-3">
          <div class="min-w-0">
            <div class="text-sm font-semibold" style="color: var(--text-primary);">Check for updates</div>
            <div class="mt-1 text-xs" style="color: var(--text-muted);">Opens the latest desktop download page.</div>
          </div>
          <a
            href="https://mcpsynapse.dev/download"
            target="_blank"
            rel="noreferrer noopener"
            class={`ui-focus inline-flex items-center justify-center rounded-md border px-3 py-2 text-xs font-semibold transition-colors hover:bg-white/5 active:scale-[0.98] ${ACTION_WIDTH_CLASS}`}
            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary); box-shadow: var(--shadow-1);"
          >
            Open
          </a>
        </div>

        <div class="border-b" style="border-color: var(--border-subtle);"></div>

        <div class="flex items-center justify-between gap-4 py-3">
          <div class="min-w-0">
            <div class="text-sm font-semibold" style="color: var(--text-primary);">Reset UI session</div>
            <div class="mt-1 text-xs" style="color: var(--text-muted);">Resets settings to defaults. This only affects UI settings.</div>
          </div>
          <button
            type="button"
            class={`ui-focus rounded-md border px-3 py-2 text-xs font-semibold transition-colors hover:bg-rose-500/15 active:scale-[0.98] ${ACTION_WIDTH_CLASS}`}
            style="border-color: rgba(159, 18, 57, 0.6); background-color: rgba(244, 63, 94, 0.10); color: rgb(254, 202, 202);"
            onclick={openResetConfirm}
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  </div>

  <div class="ui-card ui-pad-md">
    <div class="ui-title">About</div>
    <div class="mt-2 space-y-2 text-sm" style="color: var(--text-muted);">
      <div class="font-medium" style="color: var(--text-primary);">What is MCP Synapse</div>
      <div>MCP Synapse is a local-first control plane for MCP connections and request routing. It provides one interface across providers without per-vendor rewrites.</div>
      <div class="pt-1 font-medium" style="color: var(--text-primary);">Why developers use it</div>
      <div>Developers use it for portable configuration, deterministic validation, and operational controls in a single workflow.</div>
      <div class="pt-1 font-medium" style="color: var(--text-primary);">Local-first and security</div>
      <div>Credentials stay local, usage visibility stays local, and automatic fallback safety helps keep request flows stable.</div>
    </div>
  </div>
</div>

{#if shortcutsOpen}
  <div class="fixed inset-0 z-50">
    <button
      type="button"
      class="absolute inset-0 h-full w-full"
      style="background-color: rgba(0, 0, 0, 0.55);"
      aria-label="Close keyboard shortcuts modal"
      onclick={closeShortcuts}
    ></button>
    <div class="absolute left-1/2 top-1/2 w-[650px] max-w-[calc(100vw-40px)] -translate-x-1/2 -translate-y-1/2">
      <div class="ui-card ui-pad-lg" style="background-color: var(--surface-1);">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <div class="ui-title">Keyboard shortcuts</div>
          </div>
          <button
            type="button"
            class="ui-focus rounded-md border px-3 py-2 text-xs font-medium transition-colors hover:bg-white/5 active:scale-[0.98]"
            style="border-color: var(--border-subtle); color: var(--text-primary); background-color: transparent;"
            onclick={closeShortcuts}
          >
            Close
          </button>
        </div>

        <div class="mt-4 overflow-hidden rounded-md border" style="border-color: var(--border-subtle);">
          <div class="px-4">
            <div class="grid grid-cols-[140px,1fr] items-center gap-3 py-2 text-sm">
              <div style="color: var(--text-primary);">Esc</div>
              <div style="color: var(--text-muted);">Close modal / cancel</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="grid grid-cols-[140px,1fr] items-center gap-3 py-2 text-sm">
              <div style="color: var(--text-primary);">Tab</div>
              <div style="color: var(--text-muted);">Next control</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="grid grid-cols-[140px,1fr] items-center gap-3 py-2 text-sm">
              <div style="color: var(--text-primary);">Shift + Tab</div>
              <div style="color: var(--text-muted);">Previous control</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="grid grid-cols-[140px,1fr] items-center gap-3 py-2 text-sm">
              <div style="color: var(--text-primary);">Enter</div>
              <div style="color: var(--text-muted);">Activate focused control</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="grid grid-cols-[140px,1fr] items-center gap-3 py-2 text-sm">
              <div style="color: var(--text-primary);">Space</div>
              <div style="color: var(--text-muted);">Toggle checkbox / switch</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="grid grid-cols-[140px,1fr] items-center gap-3 py-2 text-sm">
              <div style="color: var(--text-primary);">Ctrl/Cmd + C</div>
              <div style="color: var(--text-muted);">Copy selection</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="grid grid-cols-[140px,1fr] items-center gap-3 py-2 text-sm">
              <div style="color: var(--text-primary);">Ctrl/Cmd + V</div>
              <div style="color: var(--text-muted);">Paste</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="grid grid-cols-[140px,1fr] items-center gap-3 py-2 text-sm">
              <div style="color: var(--text-primary);">Ctrl/Cmd + /</div>
              <div style="color: var(--text-muted);">Open help / shortcuts</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="grid grid-cols-[140px,1fr] items-center gap-3 py-2 text-sm">
              <div style="color: var(--text-primary);">Ctrl/Cmd + R</div>
              <div style="color: var(--text-muted);">Refresh</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="grid grid-cols-[140px,1fr] items-center gap-3 py-2 text-sm">
              <div style="color: var(--text-primary);">Ctrl/Cmd + Enter</div>
              <div style="color: var(--text-muted);">Primary action (save/apply)</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="grid grid-cols-[140px,1fr] items-center gap-3 py-2 text-sm">
              <div style="color: var(--text-primary);">Alt + D</div>
              <div style="color: var(--text-muted);">Go to Dashboard</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="grid grid-cols-[140px,1fr] items-center gap-3 py-2 text-sm">
              <div style="color: var(--text-primary);">Alt + C</div>
              <div style="color: var(--text-muted);">Go to Connections</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="grid grid-cols-[140px,1fr] items-center gap-3 py-2 text-sm">
              <div style="color: var(--text-primary);">Alt + U</div>
              <div style="color: var(--text-muted);">Go to Usage</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="grid grid-cols-[140px,1fr] items-center gap-3 py-2 text-sm">
              <div style="color: var(--text-primary);">Alt + P</div>
              <div style="color: var(--text-muted);">Go to Policies</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="grid grid-cols-[140px,1fr] items-center gap-3 py-2 text-sm">
              <div style="color: var(--text-primary);">Alt + B</div>
              <div style="color: var(--text-muted);">Go to Resilience Budget</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}

{#if resetConfirmOpen}
  <div class="fixed inset-0 z-50">
    <button
      type="button"
      class="absolute inset-0 h-full w-full"
      style="background-color: rgba(0, 0, 0, 0.55);"
      aria-label="Close reset confirmation"
      onclick={closeResetConfirm}
    ></button>
    <div class="absolute left-1/2 top-1/2 w-[560px] max-w-[calc(100vw-40px)] -translate-x-1/2 -translate-y-1/2">
      <div class="ui-card ui-pad-lg" style="background-color: var(--surface-1);">
        <div class="ui-title">Reset UI session</div>
        <div class="ui-subtitle mt-2">This only affects UI settings and resets values to defaults.</div>
        <div class="mt-4 flex justify-end gap-2">
          <button
            type="button"
            class="ui-focus h-9 rounded-md border px-3 text-xs font-medium transition-colors hover:bg-white/5 active:scale-[0.98]"
            style="border-color: var(--border-subtle); background-color: transparent; color: var(--text-primary);"
            onclick={closeResetConfirm}
          >
            Cancel
          </button>
          <button
            type="button"
            class="ui-focus h-9 rounded-md border px-3 text-xs font-semibold transition-colors hover:bg-rose-500/15 active:scale-[0.98]"
            style="border-color: rgba(159, 18, 57, 0.6); background-color: rgba(244, 63, 94, 0.10); color: rgb(254, 202, 202);"
            onclick={confirmReset}
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}
