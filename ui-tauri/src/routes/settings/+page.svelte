<script lang="ts">
  import { getSettingsSession, patchSettingsSession, resetUiSession } from "$lib/ui_session";

  type DataRetention = "1m" | "3m" | "6m" | "unlimited";
  type PortMode = "auto" | "manual";

  const saved = getSettingsSession();
  let dataRetention = $state<DataRetention>(saved.dataRetention);
  let portMode = $state<PortMode>(saved.portMode);
  let portMin = $state(saved.portMin);
  let portMax = $state(saved.portMax);

  let resetConfirmOpen = $state(false);
  let shortcutsOpen = $state(false);

  function openResetConfirm() {
    resetConfirmOpen = true;
  }

  function closeResetConfirm() {
    resetConfirmOpen = false;
  }

  function confirmReset() {
    resetUiSession();
    const next = getSettingsSession();
    dataRetention = next.dataRetention;
    portMode = next.portMode;
    portMin = next.portMin;
    portMax = next.portMax;
    closeResetConfirm();
  }

  function openShortcuts() {
    shortcutsOpen = true;
  }

  function closeShortcuts() {
    shortcutsOpen = false;
  }

  async function copyDiagnostics() {
    const text = ["MCP Synapse", "Version: 0.0.0 (placeholder)"].join("\n");
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

  $effect(() => {
    patchSettingsSession({ dataRetention, portMode, portMin, portMax });
  });
</script>

<div class="space-y-4 p-6">
  <div class="flex items-start justify-between gap-4">
    <div class="min-w-0">
      <div class="ui-subtitle">Minimal settings (UI-only; not persisted).</div>
    </div>
  </div>

  <div class="ui-card ui-pad-md">
    <div class="overflow-hidden rounded-md border" style="border-color: var(--border-subtle);">
      <div class="px-4">
        <div class="flex items-center justify-between gap-4 py-3">
          <div class="min-w-0">
            <div class="text-sm font-semibold" style="color: var(--text-primary);">Data retention</div>
            <div class="mt-1 text-xs" style="color: var(--text-muted);">UI-only; not persisted.</div>
          </div>
          <select
            class="ui-focus h-9 rounded-md border px-3 text-xs"
            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
            value={dataRetention}
            onchange={(e) => (dataRetention = (e.currentTarget as HTMLSelectElement).value as DataRetention)}
          >
            <option value="1m">1 month</option>
            <option value="3m">3 months</option>
            <option value="6m">6 months</option>
            <option value="unlimited">Unlimited</option>
          </select>
        </div>

        <div class="border-b" style="border-color: var(--border-subtle);"></div>

        <div class="flex items-center justify-between gap-4 py-3">
          <div class="min-w-0">
            <div class="text-sm font-semibold" style="color: var(--text-primary);">Port range</div>
            <div class="mt-1 text-xs" style="color: var(--text-muted);">UI-only; not persisted.</div>
          </div>
          <div class="flex items-center justify-end gap-2">
            <select
              class="ui-focus h-9 rounded-md border px-3 text-xs"
              style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
              value={portMode}
              onchange={(e) => (portMode = (e.currentTarget as HTMLSelectElement).value as PortMode)}
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
                value={portMin}
                oninput={(e) => (portMin = (e.currentTarget as HTMLInputElement).value)}
              />
              <input
                class="ui-focus h-9 w-24 rounded-md border px-3 text-xs"
                style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
                inputmode="numeric"
                placeholder="Max"
                value={portMax}
                oninput={(e) => (portMax = (e.currentTarget as HTMLInputElement).value)}
              />
            {/if}
          </div>
        </div>

        <div class="border-b" style="border-color: var(--border-subtle);"></div>

        <div class="flex items-center justify-between gap-4 py-3">
          <div class="min-w-0">
            <div class="text-sm font-semibold" style="color: var(--text-primary);">Keyboard shortcuts</div>
            <div class="mt-1 text-xs" style="color: var(--text-muted);">Read-only.</div>
          </div>
          <button
            type="button"
            class="ui-focus rounded-md border px-3 py-2 text-xs font-semibold transition-colors hover:bg-white/5"
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
            <div class="mt-1 text-xs" style="color: var(--text-muted);">UI-only; not persisted.</div>
          </div>
          <button
            type="button"
            class="ui-focus rounded-md border px-3 py-2 text-xs font-semibold transition-colors hover:bg-white/5"
            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary); box-shadow: var(--shadow-1);"
            onclick={copyDiagnostics}
          >
            Copy
          </button>
        </div>

        <div class="border-b" style="border-color: var(--border-subtle);"></div>

        <div class="flex items-center justify-between gap-4 py-3">
          <div class="min-w-0">
            <div class="text-sm font-semibold" style="color: var(--text-primary);">Reset UI session</div>
            <div class="mt-1 text-xs" style="color: var(--text-muted);">Clears in-memory UI state only.</div>
          </div>
          <button
            type="button"
            class="ui-focus rounded-md border px-3 py-2 text-xs font-semibold transition-colors hover:bg-rose-500/15"
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
      <div>MCP Synapse is a local-first control plane for running and routing tools.</div>
      <div>Bring your own keys, keep the UI thin, and keep sensitive data on your machine by default.</div>
      <div>Most controls shown here are UI-only until core wiring exists.</div>
    </div>
    <div class="mt-4">
      <div class="ui-subtitle">Release notes (placeholder)</div>
      <ul class="mt-2 list-disc pl-5 text-sm" style="color: var(--text-muted);">
        <li>Added minimal Settings list layout.</li>
        <li>Added shortcuts modal and session reset control.</li>
        <li>Improved UI-only state continuity across pages.</li>
      </ul>
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
    <div class="absolute left-1/2 top-1/2 w-[720px] max-w-[calc(100vw-40px)] -translate-x-1/2 -translate-y-1/2">
      <div class="ui-card ui-pad-lg" style="background-color: var(--surface-1);">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <div class="ui-title">Keyboard shortcuts</div>
            <div class="ui-subtitle mt-1">Read-only; UI-only.</div>
          </div>
          <button
            type="button"
            class="ui-focus rounded-md border px-3 py-2 text-xs font-medium transition-colors hover:bg-white/5"
            style="border-color: var(--border-subtle); color: var(--text-primary); background-color: transparent;"
            onclick={closeShortcuts}
          >
            Close
          </button>
        </div>

        <div class="mt-4 overflow-hidden rounded-md border" style="border-color: var(--border-subtle);">
          <div class="px-4">
            <div class="flex items-center justify-between gap-3 py-3 text-sm">
              <div style="color: var(--text-primary);">Esc</div>
              <div style="color: var(--text-muted);">Close modal</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="flex items-center justify-between gap-3 py-3 text-sm">
              <div style="color: var(--text-primary);">Tab</div>
              <div style="color: var(--text-muted);">Next control</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="flex items-center justify-between gap-3 py-3 text-sm">
              <div style="color: var(--text-primary);">Shift + Tab</div>
              <div style="color: var(--text-muted);">Previous control</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="flex items-center justify-between gap-3 py-3 text-sm">
              <div style="color: var(--text-primary);">Enter</div>
              <div style="color: var(--text-muted);">Activate focused control</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="flex items-center justify-between gap-3 py-3 text-sm">
              <div style="color: var(--text-primary);">Space</div>
              <div style="color: var(--text-muted);">Toggle checkbox</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="flex items-center justify-between gap-3 py-3 text-sm">
              <div style="color: var(--text-primary);">Ctrl/Cmd + C</div>
              <div style="color: var(--text-muted);">Copy selection</div>
            </div>
            <div class="border-b" style="border-color: var(--border-subtle);"></div>
            <div class="flex items-center justify-between gap-3 py-3 text-sm">
              <div style="color: var(--text-primary);">Ctrl/Cmd + V</div>
              <div style="color: var(--text-muted);">Paste</div>
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
        <div class="ui-subtitle mt-2">This clears UI-only in-memory state. Nothing is persisted.</div>
        <div class="mt-4 flex justify-end gap-2">
          <button
            type="button"
            class="ui-focus h-9 rounded-md border px-3 text-xs font-medium transition-colors hover:bg-white/5"
            style="border-color: var(--border-subtle); background-color: transparent; color: var(--text-primary);"
            onclick={closeResetConfirm}
          >
            Cancel
          </button>
          <button
            type="button"
            class="ui-focus h-9 rounded-md border px-3 text-xs font-semibold transition-colors hover:bg-rose-500/15"
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
