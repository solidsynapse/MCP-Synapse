<script lang="ts">
  import UsageFilters from "../usage-filters.svelte";

  type UsageRow = {
    timestamp: string | null;
    status: string | null;
    error_type: string | null;
    latency_ms: number | null;
    tokens_input: number | null;
    tokens_output: number | null;
    cost_usd: number | null;
  };

  const limit = 200;

  type ProviderId = "all" | "openai" | "azure_openai" | "vertex" | "bedrock" | "huggingface" | "ollama";
  type DateRangeId = "1h" | "4h" | "24h" | "7d" | "30d";
  type SortId = "time_desc" | "time_asc" | "cost_desc" | "latency_desc";

  let provider = $state<ProviderId>("all");
  let dateRange = $state<DateRangeId>("24h");
  let sort = $state<SortId>("time_desc");

  let bannerText = $state("");
  let clearConfirmOpen = $state(false);

  let rows = $state<UsageRow[]>([
    {
      timestamp: "2026-02-25T04:18:59.000Z",
      status: "ok",
      error_type: null,
      latency_ms: 332,
      tokens_input: 256,
      tokens_output: 64,
      cost_usd: 0.004321,
    },
    {
      timestamp: "2026-02-25T04:18:11.000Z",
      status: "error",
      error_type: "rate_limit",
      latency_ms: 1200,
      tokens_input: 1024,
      tokens_output: null,
      cost_usd: 0.020001,
    },
    {
      timestamp: "2026-02-25T04:17:42.000Z",
      status: "ok",
      error_type: null,
      latency_ms: 481,
      tokens_input: 4096,
      tokens_output: 512,
      cost_usd: 0.123456,
    },
    {
      timestamp: null,
      status: null,
      error_type: null,
      latency_ms: null,
      tokens_input: null,
      tokens_output: null,
      cost_usd: null,
    },
  ]);

  function parseTimeMs(ts: string | null) {
    if (!ts) return 0;
    const d = new Date(ts);
    const t = d.getTime();
    return Number.isNaN(t) ? 0 : t;
  }

  const displayRows = $derived(() => {
    const copy = rows.slice();
    copy.sort((a, b) => {
      if (sort === "time_desc") return parseTimeMs(b.timestamp) - parseTimeMs(a.timestamp);
      if (sort === "time_asc") return parseTimeMs(a.timestamp) - parseTimeMs(b.timestamp);
      if (sort === "cost_desc") return (b.cost_usd ?? -1) - (a.cost_usd ?? -1);
      if (sort === "latency_desc") return (b.latency_ms ?? -1) - (a.latency_ms ?? -1);
      return 0;
    });
    return copy;
  });

  function formatTimestamp(value: string | null) {
    if (!value) return "N/A";
    const d = new Date(value);
    const t = d.getTime();
    if (Number.isNaN(t)) return "N/A";
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

  function formatMoneyPrecise(value: number | null) {
    if (value == null || Number.isNaN(value)) return "N/A";
    return `$${Number(value).toFixed(6)}`;
  }

  function csvEscape(value: string) {
    if (value.includes('"') || value.includes(",") || value.includes("\n") || value.includes("\r")) {
      return `"${value.replaceAll('"', '""')}"`;
    }
    return value;
  }

  function exportCsv() {
    const headers = ["Time", "Status", "Error", "Latency (ms)", "Tokens in", "Tokens out", "Cost (USD)"];
    const lines: string[] = [headers.join(",")];
    for (const r of displayRows()) {
      const cost = r.cost_usd == null || Number.isNaN(r.cost_usd) ? "N/A" : Number(r.cost_usd).toFixed(6);
      const cols = [
        formatTimestamp(r.timestamp),
        r.status ?? "N/A",
        r.error_type ?? "N/A",
        r.latency_ms == null ? "N/A" : String(r.latency_ms),
        r.tokens_input == null ? "N/A" : String(r.tokens_input),
        r.tokens_output == null ? "N/A" : String(r.tokens_output),
        cost,
      ];
      lines.push(cols.map((c) => csvEscape(c)).join(","));
    }

    const csv = lines.join("\n") + "\n";
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "usage_history_stub.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  function openClearConfirm() {
    clearConfirmOpen = true;
  }

  function closeClearConfirm() {
    clearConfirmOpen = false;
  }

  function confirmClear() {
    rows = [];
    bannerText = "Cleared usage history (stub).";
    clearConfirmOpen = false;
  }
</script>

<div class="space-y-4 p-6">
  <div class="flex items-start justify-between gap-4">
    <div class="min-w-0">
      <div class="ui-subtitle mt-1">Most recent {limit} request rows.</div>
    </div>
    <div class="flex shrink-0 items-center gap-2">
      <button
        type="button"
        class="ui-focus rounded-md border px-3 py-2 text-xs font-semibold transition-colors hover:bg-white/5"
        style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
        onclick={exportCsv}
      >
        Export CSV
      </button>
      <button
        type="button"
        class="ui-focus rounded-md border px-3 py-2 text-xs font-semibold transition-colors hover:bg-white/5"
        style="border-color: var(--border-subtle); background-color: transparent; color: var(--text-primary);"
        onclick={openClearConfirm}
      >
        Clear
      </button>
    </div>
  </div>

  {#if bannerText}
    <div class="ui-subtitle">{bannerText}</div>
  {/if}

  <UsageFilters bind:provider bind:dateRange bind:sort />

  <div class="ui-card overflow-hidden">
    <table class="ui-table text-left text-xs">
      <thead>
        <tr class="border-b" style="border-color: var(--border-subtle);">
          <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Time</th>
          <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Status</th>
          <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Error</th>
          <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Latency (ms)</th>
          <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Tokens in</th>
          <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Tokens out</th>
          <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Cost (USD)</th>
        </tr>
      </thead>
      <tbody>
        {#if displayRows().length === 0}
          <tr class="border-b" style="border-color: var(--border-subtle);">
            <td class="px-4 py-4" colspan="7" style="color: var(--text-muted);">No rows.</td>
          </tr>
        {:else}
          {#each displayRows() as row, idx (idx)}
            <tr class="border-b ui-row-hover" style="border-color: var(--border-subtle);">
              <td class="px-4 py-3" style="color: var(--text-muted);">{formatTimestamp(row.timestamp)}</td>
              <td class="px-4 py-3" style="color: var(--text-primary);">{row.status ?? "N/A"}</td>
              <td class="px-4 py-3" style="color: var(--text-muted);">{row.error_type ?? "N/A"}</td>
              <td class="px-4 py-3" style="color: var(--text-muted);">{row.latency_ms ?? "N/A"}</td>
              <td class="px-4 py-3" style="color: var(--text-muted);">{row.tokens_input ?? "N/A"}</td>
              <td class="px-4 py-3" style="color: var(--text-muted);">{row.tokens_output ?? "N/A"}</td>
              <td class="px-4 py-3" style="color: var(--text-muted);">{formatMoneyPrecise(row.cost_usd)}</td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>
</div>

{#if clearConfirmOpen}
  <div class="fixed inset-0 z-50">
    <button
      type="button"
      class="absolute inset-0 h-full w-full"
      style="background-color: rgba(0, 0, 0, 0.55);"
      aria-label="Close clear confirmation"
      onclick={closeClearConfirm}
    ></button>
    <div class="absolute left-1/2 top-1/2 w-[560px] max-w-[calc(100vw-40px)] -translate-x-1/2 -translate-y-1/2">
      <div class="ui-card ui-pad-lg">
        <div class="ui-title">Clear usage history?</div>
        <div class="ui-subtitle mt-2">This is UI-only. Clearing removes stub rows from this page for this session.</div>
        <div class="mt-4 flex justify-end gap-2">
          <button
            type="button"
            class="ui-focus h-9 rounded-md border px-3 text-xs font-medium transition-colors hover:bg-white/5"
            style="border-color: var(--border-subtle); background-color: transparent; color: var(--text-primary);"
            onclick={closeClearConfirm}
          >
            Cancel
          </button>
          <button
            type="button"
            class="ui-focus h-9 rounded-md border px-3 text-xs font-semibold transition-colors hover:bg-white/5"
            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
            onclick={confirmClear}
          >
            Clear (stub)
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}
