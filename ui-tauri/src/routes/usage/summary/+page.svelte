<script lang="ts">
  import { onMount } from "svelte";
  import UsageFilters from "../usage-filters.svelte";
  import { uiCacheGet, uiCacheSet, uiRunDeduped } from "$lib/ui_session";

  type UsageRow = {
    id: number | null;
    timestamp: string | null;
    connection_id: string | null;
    connection_name: string | null;
    provider: string | null;
    request_id: string | null;
    status: string | null;
    latency_ms: number | null;
    tokens_input: number | null;
    tokens_output: number | null;
    cost_usd: number | null;
  };

  type ProviderId = "all" | "openai" | "azure_openai" | "vertex" | "bedrock" | "huggingface" | "ollama";
  type DateRangeId = "all" | "1h" | "4h" | "24h" | "7d" | "30d";
  type SortId = "time_desc" | "time_asc" | "cost_desc" | "latency_desc";
  type BannerKind = "idle" | "info" | "success" | "danger";

  type DispatchError = { code?: string; message?: string };
  type UsageRecentResponse = {
    ok: boolean;
    status?: string;
    text?: string | null;
    error?: DispatchError | null;
  };

  let provider = $state<ProviderId>("all");
  let dateRange = $state<DateRangeId>("24h");
  let sort = $state<SortId>("time_desc");
  let bannerKind = $state<BannerKind>("idle");
  let bannerText = $state("");
  let currentPage = $state(1);
  let pageSize = $state(10);
  let tableWrap: HTMLDivElement | null = null;
  let pageSizeTimer: ReturnType<typeof setTimeout> | null = null;

  let kpis = $state({
    total_requests: null as number | null,
    success_rate: null as number | null,
    total_cost_usd: null as number | null,
    avg_latency_ms: null as number | null,
  });

  let rows = $state<UsageRow[]>([]);
  const USAGE_SUMMARY_CACHE_KEY = "usage.summary.recent";
  const USAGE_SUMMARY_CACHE_TTL_MS = 60000;
  type UsageSummaryCache = {
    kpis: typeof kpis;
    rows: UsageRow[];
  };

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

  function canonicalProvider(value: string | null): string {
    const raw = String(value || "").trim().toLowerCase();
    if (!raw) return "unknown";
    if (raw.includes("vertex")) return "vertex";
    if (raw.includes("openai") && raw.includes("azure")) return "azure_openai";
    if (raw === "openai") return "openai";
    if (raw.includes("bedrock")) return "bedrock";
    if (raw.includes("huggingface")) return "huggingface";
    if (raw.includes("ollama")) return "ollama";
    return raw;
  }

  function dateRangeStart(range: DateRangeId): number {
    const now = Date.now();
    if (range === "1h") return now - 1 * 60 * 60 * 1000;
    if (range === "4h") return now - 4 * 60 * 60 * 1000;
    if (range === "24h") return now - 24 * 60 * 60 * 1000;
    if (range === "7d") return now - 7 * 24 * 60 * 60 * 1000;
    if (range === "30d") return now - 30 * 24 * 60 * 60 * 1000;
    return 0;
  }

  const displayRows = $derived(() => {
    const copy = rows.slice();
    const filtered = copy
      .filter((row) => (provider === "all" ? true : canonicalProvider(row.provider) === provider))
      .filter((row) => {
        const startMs = dateRangeStart(dateRange);
        if (startMs <= 0) return true;
        return parseTimeMs(row.timestamp) >= startMs;
      });
    filtered.sort((a, b) => {
      if (sort === "time_desc") return parseTimeMs(b.timestamp) - parseTimeMs(a.timestamp);
      if (sort === "time_asc") return parseTimeMs(a.timestamp) - parseTimeMs(b.timestamp);
      if (sort === "cost_desc") return (b.cost_usd ?? -1) - (a.cost_usd ?? -1);
      if (sort === "latency_desc") return (b.latency_ms ?? -1) - (a.latency_ms ?? -1);
      return 0;
    });
    return filtered;
  });

  const pagedRows = $derived(() => {
    const start = (currentPage - 1) * pageSize;
    return displayRows().slice(start, start + pageSize);
  });

  const totalPages = $derived(() => Math.max(1, Math.ceil(displayRows().length / pageSize)));

  function prevPage() {
    if (currentPage <= 1) return;
    currentPage -= 1;
  }

  function nextPage() {
    if (currentPage >= totalPages()) return;
    currentPage += 1;
  }

  function updatePageSize() {
    if (!tableWrap || typeof window === "undefined") return;
    const rect = tableWrap.getBoundingClientRect();
    const header = tableWrap.querySelector("thead") as HTMLElement | null;
    const footer = tableWrap.querySelector("[data-usage-pagination]") as HTMLElement | null;
    const bodyRow = tableWrap.querySelector("tbody tr") as HTMLElement | null;
    const headerHeight = header?.getBoundingClientRect().height ?? 0;
    const footerHeight = footer?.getBoundingClientRect().height ?? 0;
    const rowHeight = bodyRow?.getBoundingClientRect().height ?? 28;
    const available = window.innerHeight - rect.top - headerHeight - footerHeight - 48;
    const nextSize = Math.max(3, Math.floor(available / rowHeight));
    if (nextSize !== pageSize) pageSize = nextSize;
  }

  function formatTimestamp(value: string | null) {
    if (!value) return "N/A";
    const d = new Date(value);
    const t = d.getTime();
    if (Number.isNaN(t)) return "N/A";
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    const hh = String(d.getHours()).padStart(2, "0");
    const mi = String(d.getMinutes()).padStart(2, "0");
    const ss = String(d.getSeconds()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`;
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
    const normalized = Number(value);
    if (normalized > 0 && normalized < 0.0001) return "<$0.0001";
    return `$${normalized.toFixed(4)}`;
  }

  function formatMoneyPrecise(value: number | null) {
    if (value == null || Number.isNaN(value)) return "N/A";
    const normalized = Number(value);
    if (normalized > 0 && normalized < 0.0001) return "<$0.0001";
    return `$${normalized.toFixed(4)}`;
  }

  function statusLabel(value: string | null): string {
    const raw = String(value || "").trim().toLowerCase();
    if (raw === "success") return "Success";
    if (raw === "error") return "Error";
    if (!raw) return "N/A";
    return raw.charAt(0).toUpperCase() + raw.slice(1);
  }

  function providerLabel(value: string | null): string {
    const raw = canonicalProvider(value);
    if (raw === "vertex") return "Vertex AI";
    if (raw === "openai") return "OpenAI";
    if (raw === "azure_openai") return "Azure OpenAI";
    if (raw === "bedrock") return "Bedrock";
    if (raw === "huggingface") return "Hugging Face";
    if (raw === "ollama") return "Ollama";
    return value ?? "N/A";
  }

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

  async function dispatchInvoke(promptPayload: Record<string, unknown>): Promise<UsageRecentResponse> {
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
      agentId: "usage",
      agent_id: "usage",
      prompt,
    }) as UsageRecentResponse;
  }

  async function loadUsageSummary() {
    setBanner("idle", "");
    try {
      const snapshot = await uiRunDeduped(USAGE_SUMMARY_CACHE_KEY, async (): Promise<UsageSummaryCache> => {
        const result = await dispatchInvoke({ op: "usage.recent", limit: 200 });
        if (!result.ok) {
          const code = result.error?.code ? `${result.error.code}: ` : "";
          const message = result.error?.message || "dispatch failed";
          throw new Error(`${code}${message}`);
        }
        const text = typeof result.text === "string" ? result.text : "";
        if (!text) throw new Error("empty text payload");
        let parsed: any;
        try {
          parsed = JSON.parse(text);
        } catch (err: any) {
          throw new Error(err?.message || String(err));
        }
        const parsedKpis = parsed?.kpis ?? {};
        const parsedRows = Array.isArray(parsed?.rows) ? parsed.rows : [];
        return {
          kpis: {
            total_requests: typeof parsedKpis.total_requests === "number" ? parsedKpis.total_requests : null,
            success_rate: typeof parsedKpis.success_rate === "number" ? parsedKpis.success_rate : null,
            total_cost_usd: typeof parsedKpis.total_cost_usd === "number" ? parsedKpis.total_cost_usd : null,
            avg_latency_ms: typeof parsedKpis.avg_latency_ms === "number" ? parsedKpis.avg_latency_ms : null,
          },
          rows: parsedRows.map((row: any) => ({
            id: typeof row?.id === "number" ? row.id : null,
            timestamp: typeof row?.timestamp === "string" ? row.timestamp : null,
            connection_id: typeof row?.connection_id === "string" ? row.connection_id : null,
            connection_name: typeof row?.connection_name === "string" ? row.connection_name : null,
            provider: typeof row?.provider === "string" ? row.provider : null,
            request_id: typeof row?.request_id === "string" ? row.request_id : null,
            status: typeof row?.status === "string" ? row.status : null,
            latency_ms: typeof row?.latency_ms === "number" ? row.latency_ms : null,
            tokens_input: typeof row?.tokens_input === "number" ? row.tokens_input : null,
            tokens_output: typeof row?.tokens_output === "number" ? row.tokens_output : null,
            cost_usd: typeof row?.cost_usd === "number" ? row.cost_usd : null,
          })),
        };
      });
      kpis = snapshot.kpis;
      rows = snapshot.rows;
      uiCacheSet(USAGE_SUMMARY_CACHE_KEY, snapshot);
      currentPage = 1;
    } catch (err: any) {
      setBanner("danger", `Usage load failed: ${err?.message || String(err)}`);
    }
  }

  onMount(() => {
    const cached = uiCacheGet<UsageSummaryCache>(USAGE_SUMMARY_CACHE_KEY, USAGE_SUMMARY_CACHE_TTL_MS);
    let refreshDelayMs = 0;
    if (cached) {
      kpis = cached.kpis;
      rows = cached.rows;
      refreshDelayMs = 90;
    }
    window.setTimeout(() => {
      void loadUsageSummary();
    }, refreshDelayMs);
    const onGlobalRefresh = () => {
      void loadUsageSummary();
    };
    const onResize = () => {
      if (pageSizeTimer) {
        clearTimeout(pageSizeTimer);
      }
      pageSizeTimer = setTimeout(() => {
        pageSizeTimer = null;
        updatePageSize();
      }, 80);
    };
    if (typeof window !== "undefined") {
      window.addEventListener("synapse:global-refresh", onGlobalRefresh);
      window.addEventListener("resize", onResize);
    }
    return () => {
      if (typeof window !== "undefined") {
        window.removeEventListener("synapse:global-refresh", onGlobalRefresh);
        window.removeEventListener("resize", onResize);
        if (pageSizeTimer) {
          clearTimeout(pageSizeTimer);
          pageSizeTimer = null;
        }
      }
    };
  });

  $effect(() => {
    if (currentPage > totalPages()) currentPage = totalPages();
    if (currentPage < 1) currentPage = 1;
  });

  $effect(() => {
    displayRows();
    updatePageSize();
  });
</script>

<div class="space-y-4 px-6 pt-5 pb-1">
  {#if bannerText}
    <div class={`rounded-md border px-3 py-2 text-xs ${bannerClass(bannerKind)}`}>{bannerText}</div>
  {/if}
  <div class="flex items-start justify-between gap-4">
    <div class="min-w-0">
      <div class="ui-subtitle mt-1">Overview of recent usage and key metrics.</div>
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

  <div class="ui-card overflow-hidden" bind:this={tableWrap}>
    <table class="ui-table text-left text-xs">
      <thead>
        <tr class="border-b" style="border-color: var(--border-subtle);">
          <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Time</th>
          <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Connection</th>
          <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Provider</th>
          <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Status</th>
          <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Latency (ms)</th>
          <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Tokens in</th>
          <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Tokens out</th>
          <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Cost (USD)</th>
        </tr>
      </thead>
      <tbody>
        {#if displayRows().length === 0}
          <tr class="border-b" style="border-color: var(--border-subtle);">
            <td class="px-4 py-4" colspan="8" style="color: var(--text-muted);">No rows.</td>
          </tr>
        {:else}
          {#each pagedRows() as row, idx (idx)}
            <tr class={`border-b ui-row-hover ${idx % 2 === 0 ? "bg-transparent" : "bg-white/[0.02]"}`} style="border-color: var(--border-subtle);">
              <td class="px-4 py-3" style="color: var(--text-muted);">{formatTimestamp(row.timestamp)}</td>
              <td class="px-4 py-3" style="color: var(--text-muted);">{row.connection_name ?? "N/A"}</td>
              <td class="px-4 py-3" style="color: var(--text-muted);">{providerLabel(row.provider)}</td>
              <td class="px-4 py-3" style="color: var(--text-primary);">{statusLabel(row.status)}</td>
              <td class="px-4 py-3" style="color: var(--text-muted);">{row.latency_ms ?? "N/A"}</td>
              <td class="px-4 py-3" style="color: var(--text-muted);">{row.tokens_input ?? "N/A"}</td>
              <td class="px-4 py-3" style="color: var(--text-muted);">{row.tokens_output ?? "N/A"}</td>
              <td class="px-4 py-3" style="color: var(--text-muted);">{formatMoneyPrecise(row.cost_usd)}</td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
    <div class="flex items-center justify-between border-t px-4 py-2 text-[11px]" style="border-color: var(--border-subtle); color: var(--text-muted);" data-usage-pagination>
      <div>Page {currentPage} / {totalPages()}</div>
      <div class="flex items-center gap-2">
        <button type="button" class="ui-focus rounded-md border px-2 py-1 disabled:opacity-50" style="border-color: var(--border-subtle);" disabled={currentPage <= 1} onclick={prevPage}>Prev</button>
        <button type="button" class="ui-focus rounded-md border px-2 py-1 disabled:opacity-50" style="border-color: var(--border-subtle);" disabled={currentPage >= totalPages()} onclick={nextPage}>Next</button>
      </div>
    </div>
  </div>
</div>
