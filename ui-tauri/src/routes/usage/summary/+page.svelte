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

  type ProviderId = "all" | "openai" | "azure_openai" | "vertex" | "bedrock" | "huggingface" | "ollama";
  type DateRangeId = "1h" | "4h" | "24h" | "7d" | "30d";
  type SortId = "time_desc" | "time_asc" | "cost_desc" | "latency_desc";

  let provider = $state<ProviderId>("all");
  let dateRange = $state<DateRangeId>("24h");
  let sort = $state<SortId>("time_desc");

  let kpis = $state({
    total_requests: 128,
    success_rate: 98.4,
    total_cost_usd: 3.27,
    avg_latency_ms: 412,
  });

  let rows = $state<UsageRow[]>([
    {
      timestamp: "2026-02-25T04:23:18.000Z",
      status: "ok",
      error_type: null,
      latency_ms: 238,
      tokens_input: 512,
      tokens_output: 128,
      cost_usd: 0.012345,
    },
    {
      timestamp: "2026-02-25T04:22:05.000Z",
      status: "error",
      error_type: "timeout",
      latency_ms: 2000,
      tokens_input: 128,
      tokens_output: null,
      cost_usd: 0.001234,
    },
    {
      timestamp: "2026-02-25T04:21:44.000Z",
      status: "ok",
      error_type: null,
      latency_ms: 511,
      tokens_input: 2048,
      tokens_output: 1024,
      cost_usd: 0.09876,
    },
    {
      timestamp: "2026-02-25T04:19:10.000Z",
      status: "ok",
      error_type: null,
      latency_ms: null,
      tokens_input: null,
      tokens_output: null,
      cost_usd: null,
    },
  ]);

  const tokenTotals = $derived(() => {
    let tokensIn = 0;
    let tokensOut = 0;
    let hasAny = false;
    for (const r of rows) {
      if (typeof r.tokens_input === "number" && !Number.isNaN(r.tokens_input)) {
        tokensIn += r.tokens_input;
        hasAny = true;
      }
      if (typeof r.tokens_output === "number" && !Number.isNaN(r.tokens_output)) {
        tokensOut += r.tokens_output;
        hasAny = true;
      }
    }
    return hasAny ? { tokens_input_total: tokensIn, tokens_output_total: tokensOut } : { tokens_input_total: null, tokens_output_total: null };
  });

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

  function formatInt(value: number | null) {
    if (value == null || Number.isNaN(value)) return "N/A";
    return `${Math.round(value)}`;
  }

  function formatPercent(value: number | null) {
    if (value == null || Number.isNaN(value)) return "N/A";
    return `${value.toFixed(1)}%`;
  }

  function formatMoney(value: number | null) {
    if (value == null || Number.isNaN(value)) return "N/A";
    return `$${value.toFixed(2)}`;
  }

  function formatMoneyPrecise(value: number | null) {
    if (value == null || Number.isNaN(value)) return "N/A";
    return `$${Number(value).toFixed(6)}`;
  }
</script>

<div class="space-y-4 p-6">
  <div class="flex items-start justify-between gap-4">
    <div class="min-w-0">
      <div class="ui-subtitle mt-1">KPIs and recent request rows.</div>
    </div>
  </div>

  <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
    <div class="ui-card ui-pad-md">
      <div class="ui-subtitle">Total requests</div>
      <div class="mt-2 text-xl font-semibold tracking-tight">{formatInt(kpis.total_requests)}</div>
    </div>
    <div class="ui-card ui-pad-md">
      <div class="ui-subtitle">Tokens in</div>
      <div class="mt-2 text-xl font-semibold tracking-tight">{formatInt(tokenTotals().tokens_input_total)}</div>
    </div>
    <div class="ui-card ui-pad-md">
      <div class="ui-subtitle">Tokens out</div>
      <div class="mt-2 text-xl font-semibold tracking-tight">{formatInt(tokenTotals().tokens_output_total)}</div>
    </div>
    <div class="ui-card ui-pad-md">
      <div class="ui-subtitle">Avg latency (ms)</div>
      <div class="mt-2 text-xl font-semibold tracking-tight">{formatInt(kpis.avg_latency_ms)}</div>
    </div>
    <div class="ui-card ui-pad-md">
      <div class="ui-subtitle">Success rate</div>
      <div class="mt-2 text-xl font-semibold tracking-tight">{formatPercent(kpis.success_rate)}</div>
    </div>
    <div class="ui-card ui-pad-md">
      <div class="ui-subtitle">Total cost (USD)</div>
      <div class="mt-2 text-xl font-semibold tracking-tight">{formatMoney(kpis.total_cost_usd)}</div>
    </div>
  </div>

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
