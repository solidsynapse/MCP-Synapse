<script lang="ts">
  import { onMount } from "svelte";
  import UsageFilters from "../usage-filters.svelte";
  import { getUsageSession, patchUsageSession, uiCacheGet, uiCacheSet, uiRunDeduped } from "$lib/ui_session";

  type UsageRow = {
    id: number | null;
    timestamp: string | null;
    connection_id: string | null;
    connection_name: string | null;
    provider: string | null;
    model_id: string | null;
    request_id: string | null;
    status: string | null;
    latency_ms: number | null;
    tokens_input: number | null;
    tokens_output: number | null;
    cost_usd: number | null;
  };

  const limit = 200;

  type ProviderId = "all" | "openai" | "azure_openai" | "vertex" | "bedrock" | "huggingface" | "ollama";
  type DateRangeId = "all" | "1h" | "4h" | "24h" | "7d" | "30d";
  type SortId = "time_desc" | "time_asc" | "cost_desc" | "latency_desc";
  type TokenRangeId = "all" | "0_100" | "101_1000" | "1001_10000" | "10001_plus";
  type BannerKind = "idle" | "info" | "success" | "danger";
  type DispatchError = { code?: string; message?: string };
  type UsageRecentResponse = {
    ok: boolean;
    status?: string;
    text?: string | null;
    error?: DispatchError | null;
  };
  type ConnectionsListResponse = {
    ok: boolean;
    connections?: Array<{ id?: string; model_id?: string }>;
    error?: DispatchError | null;
  };

  const session = getUsageSession();

  let provider = $state<ProviderId>(session.provider as ProviderId);
  let dateRange = $state<DateRangeId>(session.dateRange as DateRangeId);
  let sort = $state<SortId>(session.sort as SortId);
  let modelIdFilter = $state<string>("all");
  let totalTokensRange = $state<TokenRangeId>("all");

  $effect(() => {
    patchUsageSession({ provider, dateRange, sort });
  });

  let bannerKind = $state<BannerKind>("idle");
  let bannerText = $state("");
  let clearConfirmOpen = $state(false);
  let exportConfirmOpen = $state(false);
  let currentPage = $state(1);
  let pageSize = $state(12);
  let tableWrap: HTMLDivElement | null = null;
  let pageSizeTimer: ReturnType<typeof setTimeout> | null = null;
  let exportProvider = $state<ProviderId>("all");
  let exportDateRange = $state<DateRangeId>("all");
  let exportSort = $state<SortId>("time_desc");
  let exportModelIdFilter = $state<string>("all");
  let exportTotalTokensRange = $state<TokenRangeId>("all");

  let rows = $state<UsageRow[]>([]);
  let modelIdByConnectionId = $state<Record<string, string>>({});
  const USAGE_HISTORY_CACHE_KEY = "usage.history.recent";
  const USAGE_HISTORY_CACHE_TTL_MS = 60000;

  function resolvedModelId(row: UsageRow): string {
    const direct = String(row.model_id || "").trim();
    if (direct) return direct;
    const cid = String(row.connection_id || "").trim();
    if (!cid) return "";
    return String(modelIdByConnectionId[cid] || "").trim();
  }

  function providerModelTooltip(row: UsageRow): string | undefined {
    const modelId = resolvedModelId(row);
    return modelId || undefined;
  }

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

  function dateRangeStart(range: DateRangeId): number {
    const now = Date.now();
    if (range === "1h") return now - 1 * 60 * 60 * 1000;
    if (range === "4h") return now - 4 * 60 * 60 * 1000;
    if (range === "24h") return now - 24 * 60 * 60 * 1000;
    if (range === "7d") return now - 7 * 24 * 60 * 60 * 1000;
    if (range === "30d") return now - 30 * 24 * 60 * 60 * 1000;
    return 0;
  }

  function totalTokens(row: UsageRow): number | null {
    if (typeof row.tokens_input !== "number" || typeof row.tokens_output !== "number") return null;
    return row.tokens_input + row.tokens_output;
  }

  function pricingStatus(row: UsageRow): string {
    const total = totalTokens(row);
    if (total == null) return "N/A";
    if (total <= 0) return "No usage";
    if (typeof row.cost_usd === "number" && !Number.isNaN(row.cost_usd) && row.cost_usd > 0) return "Estimated";
    return "Missing pricing data";
  }

  function tokenRangeLabel(range: TokenRangeId): string {
    if (range === "0_100") return "0-100";
    if (range === "101_1000") return "101-1,000";
    if (range === "1001_10000") return "1,001-10,000";
    if (range === "10001_plus") return "10,001+";
    return "All";
  }

  function tokenRangeMatch(value: number | null, range: TokenRangeId): boolean {
    if (range === "all") return true;
    if (value == null) return false;
    if (range === "0_100") return value >= 0 && value <= 100;
    if (range === "101_1000") return value >= 101 && value <= 1000;
    if (range === "1001_10000") return value >= 1001 && value <= 10000;
    if (range === "10001_plus") return value >= 10001;
    return true;
  }

  const modelIdFilterOptions = $derived(() => {
    const seen = new Map<string, string>();
    for (const row of rows) {
      const id = resolvedModelId(row);
      if (!id) continue;
      if (seen.has(id)) continue;
      seen.set(id, id);
    }
    return [{ id: "all", label: "All" }, ...Array.from(seen.entries()).map(([id, label]) => ({ id, label }))];
  });

  function applyUsageFilters(
    source: UsageRow[],
    args: {
      provider: ProviderId;
      dateRange: DateRangeId;
      sort: SortId;
      modelIdFilter: string;
      totalTokensRange: TokenRangeId;
    },
  ): UsageRow[] {
    const copy = source.slice();
    const filtered = copy
      .filter((row) => (args.provider === "all" ? true : canonicalProvider(row.provider) === args.provider))
      .filter((row) => {
        const startMs = dateRangeStart(args.dateRange);
        if (startMs <= 0) return true;
        return parseTimeMs(row.timestamp) >= startMs;
      })
      .filter((row) => (args.modelIdFilter === "all" ? true : resolvedModelId(row) === args.modelIdFilter))
      .filter((row) => tokenRangeMatch(totalTokens(row), args.totalTokensRange));
    filtered.sort((a, b) => {
      if (args.sort === "time_desc") return parseTimeMs(b.timestamp) - parseTimeMs(a.timestamp);
      if (args.sort === "time_asc") return parseTimeMs(a.timestamp) - parseTimeMs(b.timestamp);
      if (args.sort === "cost_desc") return (b.cost_usd ?? -1) - (a.cost_usd ?? -1);
      if (args.sort === "latency_desc") return (b.latency_ms ?? -1) - (a.latency_ms ?? -1);
      return 0;
    });
    return filtered;
  }

  const displayRows = $derived(() =>
    applyUsageFilters(rows, {
      provider,
      dateRange,
      sort,
      modelIdFilter,
      totalTokensRange,
    })
  );

  const hasMissingPricingDisclosure = $derived(() =>
    displayRows().some((row) => {
      const total = totalTokens(row);
      if (total == null || total <= 0) return false;
      return !(typeof row.cost_usd === "number" && !Number.isNaN(row.cost_usd) && row.cost_usd > 0);
    })
  );

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
    const nextSize = Math.min(18, Math.max(4, Math.floor(available / rowHeight)));
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

  async function dispatchConnectionsInvoke(promptPayload: Record<string, unknown>): Promise<ConnectionsListResponse> {
    const tauriGlobal = typeof window !== "undefined"
      ? (window as any).__TAURI__ ?? (window as any).__TAURI_INTERNALS__
      : null;
    if (!tauriGlobal) {
      return { ok: false, error: { code: "desktop_required", message: "Desktop app required" } };
    }
    const { invoke } = await import("@tauri-apps/api/core");
    const prompt = JSON.stringify(promptPayload);
    return await invoke("dispatch_execute_request_v1", {
      agentId: "connections",
      agent_id: "connections",
      prompt,
    }) as ConnectionsListResponse;
  }

  async function refreshModelIdMap() {
    try {
      const result = await dispatchConnectionsInvoke({ op: "connections.list" });
      if (!result.ok || !Array.isArray(result.connections)) return;
      const next: Record<string, string> = {};
      for (const row of result.connections) {
        const id = String(row?.id || "").trim();
        const model = String(row?.model_id || "").trim();
        if (!id || !model) continue;
        next[id] = model;
      }
      modelIdByConnectionId = next;
    } catch {
      // Keep usage table functional even if connections list is unavailable.
    }
  }

  async function loadUsageHistory() {
    setBanner("idle", "");
    try {
      const nextRows = await uiRunDeduped(USAGE_HISTORY_CACHE_KEY, async (): Promise<UsageRow[]> => {
        const result = await dispatchInvoke({ op: "usage.recent", limit });
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
        const parsedRows = Array.isArray(parsed?.rows) ? parsed.rows : [];
        return parsedRows.map((row: any) => ({
          id: typeof row?.id === "number" ? row.id : null,
          timestamp: typeof row?.timestamp === "string" ? row.timestamp : null,
          connection_id: typeof row?.connection_id === "string" ? row.connection_id : null,
          connection_name: typeof row?.connection_name === "string" ? row.connection_name : null,
          provider: typeof row?.provider === "string" ? row.provider : null,
          model_id: typeof row?.model_id === "string" ? row.model_id : null,
          request_id: typeof row?.request_id === "string" ? row.request_id : null,
          status: typeof row?.status === "string" ? row.status : null,
          latency_ms: typeof row?.latency_ms === "number" ? row.latency_ms : null,
          tokens_input: typeof row?.tokens_input === "number" ? row.tokens_input : null,
          tokens_output: typeof row?.tokens_output === "number" ? row.tokens_output : null,
          cost_usd: typeof row?.cost_usd === "number" ? row.cost_usd : null,
        }));
      });
      rows = nextRows;
      await refreshModelIdMap();
      uiCacheSet(USAGE_HISTORY_CACHE_KEY, nextRows);
      currentPage = 1;
    } catch (err: any) {
      setBanner("danger", `Usage load failed: ${err?.message || String(err)}`);
    }
  }

  function csvDelimiter() {
    const sample = (1.1).toLocaleString();
    return sample.includes(",") ? ";" : ",";
  }

  function csvEscape(value: string, delimiter: string) {
    if (value.includes('"') || value.includes(delimiter) || value.includes("\n") || value.includes("\r")) {
      return `"${value.replaceAll('"', '""')}"`;
    }
    return value;
  }

  function buildCsv(rowsToExport: UsageRow[]) {
    const delimiter = csvDelimiter();
    const headers = ["Time", "Connection", "ID", "Provider", "Status", "Latency (ms)", "Tokens in", "Tokens out", "Cost (USD)", "Pricing status"];
    const lines: string[] = [headers.join(delimiter)];
    for (const r of rowsToExport) {
      const cols = [
        formatTimestamp(r.timestamp),
        r.connection_name ?? "N/A",
        r.request_id ?? "N/A",
        providerLabel(r.provider),
        statusLabel(r.status),
        r.latency_ms == null ? "N/A" : String(r.latency_ms),
        r.tokens_input == null ? "N/A" : String(r.tokens_input),
        r.tokens_output == null ? "N/A" : String(r.tokens_output),
        formatMoneyPrecise(r.cost_usd),
        pricingStatus(r),
      ];
      lines.push(cols.map((c) => csvEscape(c, delimiter)).join(delimiter));
    }

    const csv = "\uFEFF" + lines.join("\n") + "\n";
    return csv;
  }

  function downloadCsv(csv: string, filename: string) {
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  async function saveCsvWithDialog(csv: string, filename: string) {
    const picker = typeof window !== "undefined" ? (window as any).showSaveFilePicker : null;
    if (picker) {
      try {
        const handle = await picker({
          suggestedName: filename,
          types: [{ description: "CSV", accept: { "text/csv": [".csv"] } }],
        });
        const writable = await handle.createWritable();
        await writable.write(csv);
        await writable.close();
        return { status: "saved", destination: String(handle.name || filename) };
      } catch (err: any) {
        if (err?.name === "AbortError") {
          return { status: "canceled", destination: "" };
        }
        throw err;
      }
    }
    downloadCsv(csv, filename);
    return { status: "fallback", destination: filename };
  }

  function openExportConfirm() {
    exportProvider = provider;
    exportDateRange = dateRange;
    exportSort = sort;
    exportModelIdFilter = modelIdFilter;
    exportTotalTokensRange = totalTokensRange;
    exportConfirmOpen = true;
  }

  function closeExportConfirm() {
    exportConfirmOpen = false;
  }

  async function confirmExportCsv() {
    const rowsToExport = applyUsageFilters(rows, {
      provider: exportProvider,
      dateRange: exportDateRange,
      sort: exportSort,
      modelIdFilter: exportModelIdFilter,
      totalTokensRange: exportTotalTokensRange,
    });
    const csv = buildCsv(rowsToExport);
    setBanner("idle", "");
    try {
      const filename = "usage_history.csv";
      const result = await saveCsvWithDialog(csv, filename);
      if (result.status === "canceled") {
        setBanner("info", "Export canceled.");
        return;
      }
      exportConfirmOpen = false;
      if (result.status === "saved") {
        setBanner("success", `CSV saved (${rowsToExport.length} rows) to ${result.destination}.`);
        return;
      }
      setBanner("info", `Download started (${rowsToExport.length} rows): ${result.destination}.`);
    } catch (err: any) {
      setBanner("danger", `Export failed: ${err?.message || String(err)}`);
    }
  }

  function openClearConfirm() {
    clearConfirmOpen = true;
  }

  function closeClearConfirm() {
    clearConfirmOpen = false;
  }

  async function confirmClear() {
    try {
      const result = await dispatchInvoke({ op: "usage.clear" });
      if (!result.ok) {
        const code = result.error?.code ? `${result.error.code}: ` : "";
        const message = result.error?.message || "dispatch failed";
        setBanner("danger", `Clear failed: ${code}${message}`);
        clearConfirmOpen = false;
        return;
      }
      rows = [];
      currentPage = 1;
      setBanner("success", "History cleared.");
      clearConfirmOpen = false;
      if (typeof window !== "undefined") {
        window.dispatchEvent(
          new CustomEvent("synapse:global-refresh", {
            detail: { source: "usage.history.clear", at: Date.now() },
          }),
        );
      }
      void loadUsageHistory();
    } catch (err: any) {
      setBanner("danger", `Clear failed: ${err?.message || String(err)}`);
      clearConfirmOpen = false;
    }
  }

  onMount(() => {
    const cached = uiCacheGet<UsageRow[]>(USAGE_HISTORY_CACHE_KEY, USAGE_HISTORY_CACHE_TTL_MS);
    let refreshDelayMs = 0;
    if (cached) rows = cached;
    if (cached) refreshDelayMs = 90;
    window.setTimeout(() => {
      void loadUsageHistory();
    }, refreshDelayMs);
    const onGlobalRefresh = () => {
      void loadUsageHistory();
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
    const onShortcutEscape = (event: Event) => {
      if (exportConfirmOpen) {
        closeExportConfirm();
        event.preventDefault();
        return;
      }
      if (clearConfirmOpen) {
        closeClearConfirm();
        event.preventDefault();
      }
    };
    if (typeof window !== "undefined") {
      window.addEventListener("synapse:global-refresh", onGlobalRefresh);
      window.addEventListener("resize", onResize);
      window.addEventListener("synapse:shortcut-escape", onShortcutEscape as EventListener);
    }
    return () => {
      if (typeof window !== "undefined") {
        window.removeEventListener("synapse:global-refresh", onGlobalRefresh);
        window.removeEventListener("resize", onResize);
        window.removeEventListener("synapse:shortcut-escape", onShortcutEscape as EventListener);
        if (pageSizeTimer) {
          clearTimeout(pageSizeTimer);
          pageSizeTimer = null;
        }
      }
    };
  });

  $effect(() => {
    provider;
    dateRange;
    sort;
    modelIdFilter;
    totalTokensRange;
    currentPage = 1;
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
  <div class="flex items-start justify-between gap-4">
    <div class="min-w-0">
      <div class="ui-subtitle mt-1">Full request log.</div>
    </div>
    <div class="flex shrink-0 items-center gap-2">
      <button
        type="button"
        class="ui-focus rounded-md border px-3 py-2 text-xs font-semibold transition-colors hover:bg-white/5"
        style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
        onclick={openExportConfirm}
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
    <div class={`rounded-md border px-3 py-2 text-xs ${bannerClass(bannerKind)}`}>{bannerText}</div>
  {/if}

  <UsageFilters
    bind:provider
    bind:dateRange
    bind:sort
    showHistoryExtras={true}
    bind:modelIdFilter
    modelOptions={modelIdFilterOptions()}
    bind:totalTokensRange
  />

  {#if hasMissingPricingDisclosure()}
    <div
      class="rounded-md border px-3 py-2 text-xs"
      style="border-color: rgba(245, 158, 11, 0.35); background-color: rgba(245, 158, 11, 0.08); color: #fcd34d;"
    >
      Some rows contain token usage but have no cost estimate yet. CSV includes a <span class="font-semibold">Pricing status</span> column for explicit tracking.
    </div>
  {/if}

  <div class="ui-card overflow-hidden" bind:this={tableWrap}>
    <table class="ui-table text-left text-xs">
      <thead>
        <tr class="border-b" style="border-color: var(--border-subtle);">
          <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Time</th>
          <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Connection</th>
          <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">ID</th>
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
            <td class="px-4 py-4" colspan="9" style="color: var(--text-muted);">No rows.</td>
          </tr>
        {:else}
          {#each pagedRows() as row, idx (idx)}
            <tr class={`border-b ui-row-hover ${idx % 2 === 0 ? "bg-transparent" : "bg-white/[0.02]"}`} style="border-color: var(--border-subtle);">
              <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-muted);">{formatTimestamp(row.timestamp)}</td>
              <td class="px-4 py-3 max-w-[220px] truncate whitespace-nowrap" style="color: var(--text-muted);" title={row.connection_name ?? "N/A"}>{row.connection_name ?? "N/A"}</td>
              <td class="px-4 py-3 max-w-[140px] truncate whitespace-nowrap font-mono" style="color: var(--text-muted);" title={row.request_id ?? "N/A"}>{row.request_id ?? "N/A"}</td>
              <td class="px-4 py-3 max-w-[140px] truncate whitespace-nowrap" style="color: var(--text-muted);" title={providerModelTooltip(row)}>{providerLabel(row.provider)}</td>
              <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-primary);">{statusLabel(row.status)}</td>
              <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-muted);">{row.latency_ms ?? "N/A"}</td>
              <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-muted);">{row.tokens_input ?? "N/A"}</td>
              <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-muted);">{row.tokens_output ?? "N/A"}</td>
              <td class="px-4 py-3 whitespace-nowrap" style="color: var(--text-muted);">{formatMoneyPrecise(row.cost_usd)}</td>
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

{#if exportConfirmOpen}
  <div class="fixed inset-0 z-50">
    <button
      type="button"
      class="absolute inset-0 h-full w-full"
      style="background-color: rgba(0, 0, 0, 0.55);"
      aria-label="Close export confirmation"
      onclick={closeExportConfirm}
    ></button>
    <div class="absolute left-1/2 top-1/2 w-[620px] max-w-[calc(100vw-40px)] -translate-x-1/2 -translate-y-1/2">
      <div class="ui-card ui-pad-lg">
        <div class="ui-title">Export CSV</div>
        <div class="ui-subtitle mt-2">Select filters for export output.</div>
        <div class="mt-2 text-[11px]" style="color: var(--text-muted);">
          Export uses the same filter logic as the table for provider/date/model/tokens/sort.
        </div>

        <div class="mt-4 grid gap-3 sm:grid-cols-2">
          <div>
            <label class="ui-subtitle" for="export-provider">Provider</label>
            <select
              id="export-provider"
              class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
              style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
              bind:value={exportProvider}
            >
              <option value="all">All</option>
              <option value="openai">OpenAI</option>
              <option value="azure_openai">Azure OpenAI</option>
              <option value="vertex">Vertex AI</option>
              <option value="huggingface">Hugging Face</option>
              <option value="ollama">Ollama</option>
            </select>
          </div>
          <div>
            <label class="ui-subtitle" for="export-date-range">Date range</label>
            <select
              id="export-date-range"
              class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
              style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
              bind:value={exportDateRange}
            >
              <option value="all">All time</option>
              <option value="1h">Last 1h</option>
              <option value="4h">Last 4h</option>
              <option value="24h">Last 24h</option>
              <option value="7d">Last 7d</option>
              <option value="30d">Last 30d</option>
            </select>
          </div>
          <div>
            <label class="ui-subtitle" for="export-sort">Sort</label>
            <select
              id="export-sort"
              class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
              style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
              bind:value={exportSort}
            >
              <option value="time_desc">Time (newest)</option>
              <option value="time_asc">Time (oldest)</option>
              <option value="cost_desc">Cost (high-&gt;low)</option>
              <option value="latency_desc">Latency (high-&gt;low)</option>
            </select>
          </div>
          <div>
            <label class="ui-subtitle" for="export-model-id">Model ID</label>
            <select
              id="export-model-id"
              class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
              style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
              bind:value={exportModelIdFilter}
            >
              {#each modelIdFilterOptions() as option (option.id)}
                <option value={option.id}>{option.label}</option>
              {/each}
            </select>
          </div>
          <div class="sm:col-span-2">
            <label class="ui-subtitle" for="export-total-tokens-range">Total Tokens Range</label>
            <select
              id="export-total-tokens-range"
              class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
              style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
              bind:value={exportTotalTokensRange}
            >
              <option value="all">All</option>
              <option value="0_100">0-100</option>
              <option value="101_1000">101-1,000</option>
              <option value="1001_10000">1,001-10,000</option>
              <option value="10001_plus">10,001+</option>
            </select>
          </div>
        </div>

        <div class="mt-2 text-[11px]" style="color: var(--text-muted);">
          Tokens filter: {tokenRangeLabel(exportTotalTokensRange)}
        </div>

        <div class="mt-4 flex justify-end gap-2">
          <button
            type="button"
            class="ui-focus h-9 rounded-md border px-3 text-xs font-medium transition-colors hover:bg-white/5"
            style="border-color: var(--border-subtle); background-color: transparent; color: var(--text-primary);"
            onclick={closeExportConfirm}
          >
            Cancel
          </button>
          <button
            type="button"
            class="ui-focus h-9 rounded-md border px-3 text-xs font-semibold transition-colors hover:bg-white/5"
            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
            onclick={confirmExportCsv}
          >
            Export
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

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
        <div class="ui-subtitle mt-2">Clearing removes rows from persisted usage history.</div>
        <div class="mt-2 text-[11px]" style="color: var(--text-muted);">
          This action is destructive and cannot be undone.
        </div>
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
            Clear
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}
