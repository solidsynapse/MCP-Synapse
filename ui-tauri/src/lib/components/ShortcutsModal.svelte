<script lang="ts">
  type ShortcutRow = { key: string; description: string };

  let { open = false, onClose = () => {} } = $props<{ open?: boolean; onClose?: () => void }>();

  const rows: ShortcutRow[] = [
    { key: "Esc", description: "Close modal / cancel" },
    { key: "Tab", description: "Next control" },
    { key: "Shift + Tab", description: "Previous control" },
    { key: "Enter", description: "Activate focused control" },
    { key: "Space", description: "Toggle checkbox / switch" },
    { key: "Ctrl/Cmd + C", description: "Copy selection" },
    { key: "Ctrl/Cmd + V", description: "Paste" },
    { key: "Ctrl/Cmd + /", description: "Open help / shortcuts" },
    { key: "Ctrl/Cmd + R", description: "Refresh" },
    { key: "Ctrl/Cmd + Enter", description: "Primary action (save/apply)" },
    { key: "Alt + D", description: "Go to Dashboard" },
    { key: "Alt + C", description: "Go to Connections" },
    { key: "Alt + U", description: "Go to Usage" },
    { key: "Alt + P", description: "Go to Policies" },
    { key: "Alt + B", description: "Go to Resilience Budget" },
  ];
</script>

{#if open}
  <div class="fixed inset-0 z-50">
    <button
      type="button"
      class="absolute inset-0 h-full w-full"
      style="background-color: rgba(0, 0, 0, 0.55);"
      aria-label="Close keyboard shortcuts modal"
      onclick={onClose}
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
            onclick={onClose}
          >
            Close
          </button>
        </div>

        <div class="mt-4 overflow-hidden rounded-md border" style="border-color: var(--border-subtle);">
          <div class="px-4">
            {#each rows as row, index (row.key)}
              <div class="grid grid-cols-[140px,1fr] items-center gap-3 py-2 text-sm">
                <div style="color: var(--text-primary);">{row.key}</div>
                <div style="color: var(--text-muted);">{row.description}</div>
              </div>
              {#if index < rows.length - 1}
                <div class="border-b" style="border-color: var(--border-subtle);"></div>
              {/if}
            {/each}
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}
