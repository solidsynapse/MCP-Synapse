<script lang="ts">
  import { onMount } from "svelte";
  import { uiCacheGet, uiCacheSet, uiPersistentCacheGet, uiPersistentCacheSet, uiRunDeduped } from "$lib/ui_session";

  type BannerKind = "idle" | "info" | "success" | "danger";
  type DispatchError = { code?: string; message?: string };
  type Kpi = { label: string; value: string; icon?: string };
  type RecentRequest = { time: string; status: string; provider: string; latency: string; tokens: string; cost: string };
  type TopExpensive = { id: string; cost: string };
  type Breakdown = { name: string; color: string; cost: string };
  type Trend = { label: string; valueFormatted: string };
  type Alert = { level: string; text: string };

  type DashboardState = {
    kpis: Kpi[];
    recent_requests: RecentRequest[];
    top_expensive: TopExpensive[];
    breakdown_legend: Breakdown[];
    trend_data: Trend[];
    quick_alerts: Alert[];
  };

  type DashboardResponse = {
    ok: boolean;
    status?: string;
    result?: DashboardState | null;
    text?: unknown;
    data?: unknown;
    error?: DispatchError | null;
  };

  const KPI_SLOTS: Array<{ label: string; icon: string; t1: string; t2: string }> = [
    { label: "Total Cost USD", icon: "$", t1: "Total Cost", t2: "USD" },
    { label: "Total Requests", icon: "R", t1: "Total", t2: "Requests" },
    { label: "Total Tokens", icon: "T", t1: "Total", t2: "Tokens" },
    { label: "Success Rate %", icon: "S", t1: "Success Rate", t2: "%" },
    { label: "Avg Latency ms", icon: "L", t1: "Avg Latency", t2: "ms" },
    { label: "Active Bridges count", icon: "B", t1: "Active Bridges", t2: "count" },
  ];

  const DEFAULT_STATE: DashboardState = {
    kpis: [],
    recent_requests: [],
    top_expensive: [],
    breakdown_legend: [],
    trend_data: [],
    quick_alerts: [],
  };

  const RECENT_PAGE_SIZE = 3;
  const RECENT_MAX_ROWS = 12;
  const ALERT_COLLAPSE_VISIBLE = 3;
  const TREND_W = 300;
  const TREND_H = 150;
  const TREND_PAD_X = 10;
  const TREND_PAD_Y = 12;
  const DONUT_CX = 50;
  const DONUT_CY = 50;
  const DONUT_R = 40;
  const DONUT_STROKE = 12;

  let kpis = $state<Kpi[]>(DEFAULT_STATE.kpis);
  let recentRequests = $state<RecentRequest[]>(DEFAULT_STATE.recent_requests);
  let recentPage = $state(1);
  let topExpensive = $state<TopExpensive[]>(DEFAULT_STATE.top_expensive);
  let breakdownLegend = $state<Breakdown[]>(DEFAULT_STATE.breakdown_legend);
  let trendData = $state<Trend[]>(DEFAULT_STATE.trend_data);
  let quickAlerts = $state<Alert[]>(DEFAULT_STATE.quick_alerts);
  let alertsExpanded = $state(false);
  let trendHoverIndex = $state<number | null>(null);
  let breakdownHoverIndex = $state<number | null>(null);
  let bannerKind = $state<BannerKind>("idle");
  let bannerText = $state("");
  const DASHBOARD_CACHE_KEY = "dashboard.state";
  const DASHBOARD_CACHE_TTL_MS = 45000;
  const DASHBOARD_PERSISTENT_CACHE_TTL_MS = 5 * 60 * 1000;

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

  function asDictList(value: unknown): Record<string, unknown>[] {
    if (!Array.isArray(value)) return [];
    return value.filter((v) => typeof v === "object" && v !== null) as Record<string, unknown>[];
  }

  function normalizeState(state: DashboardState | null | undefined): DashboardState {
    const src = state ?? DEFAULT_STATE;
    return {
      kpis: asDictList(src.kpis).map((v) => ({ label: String(v.label || ""), value: String(v.value || ""), icon: String(v.icon || "") })),
      recent_requests: asDictList(src.recent_requests).map((v) => ({ time: String(v.time || ""), status: String(v.status || ""), provider: String(v.provider || ""), latency: String(v.latency || ""), tokens: String(v.tokens || ""), cost: String(v.cost || "") })),
      top_expensive: asDictList(src.top_expensive).map((v) => ({ id: String(v.id || ""), cost: String(v.cost || "") })),
      breakdown_legend: asDictList(src.breakdown_legend).map((v) => ({ name: String(v.name || ""), color: String(v.color || "#64748b"), cost: String(v.cost || "") })),
      trend_data: asDictList(src.trend_data).map((v) => ({ label: String(v.label || ""), valueFormatted: String(v.valueFormatted || "") })),
      quick_alerts: asDictList(src.quick_alerts).map((v) => ({ level: String(v.level || "info"), text: String(v.text || "") })),
    };
  }

  function applyState(state: DashboardState | null | undefined) {
    const next = normalizeState(state);
    kpis = next.kpis;
    recentRequests = next.recent_requests;
    topExpensive = next.top_expensive;
    breakdownLegend = next.breakdown_legend;
    trendData = next.trend_data;
    quickAlerts = next.quick_alerts;
    recentPage = 1;
    alertsExpanded = false;
    trendHoverIndex = null;
    breakdownHoverIndex = null;
  }

  function kpiValue(label: string): string {
    const row = kpis.find((item) => item.label === label);
    const value = String(row?.value || "").trim();
    return value || "-";
  }

  function parseJsonCandidate(value: unknown): Record<string, unknown> | null {
    if (typeof value !== "string") return null;
    const raw = value.trim();
    if (!raw.startsWith("{")) return null;
    try {
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === "object") return parsed as Record<string, unknown>;
      return null;
    } catch {
      return null;
    }
  }

  function asState(candidate: unknown): DashboardState | null {
    if (!candidate || typeof candidate !== "object") return null;
    const obj = candidate as Record<string, unknown>;
    const hasDashboardKeys = Array.isArray(obj.kpis) || Array.isArray(obj.recent_requests) || Array.isArray(obj.top_expensive) || Array.isArray(obj.breakdown_legend) || Array.isArray(obj.trend_data) || Array.isArray(obj.quick_alerts);
    return hasDashboardKeys ? (obj as unknown as DashboardState) : null;
  }

  function responseState(result: DashboardResponse & Record<string, unknown>): DashboardState | null {
    const direct = asState(result.result);
    if (direct) return direct;
    const dataObj = result.data && typeof result.data === "object" ? (result.data as Record<string, unknown>) : null;
    if (dataObj) return asState(dataObj.result) ?? asState(dataObj);
    if (result.text && typeof result.text === "object") {
      const textObj = result.text as Record<string, unknown>;
      return asState(textObj.result) ?? asState(textObj);
    }
    const parsed = parseJsonCandidate(result.text);
    if (parsed) return asState(parsed.result) ?? asState(parsed);
    return null;
  }

  async function dispatchInvoke(promptPayload: Record<string, unknown>): Promise<DashboardResponse> {
    const tauriGlobal = typeof window !== "undefined" ? (window as any).__TAURI__ ?? (window as any).__TAURI_INTERNALS__ : null;
    if (!tauriGlobal) return { ok: false, status: "error", error: { code: "desktop_required", message: "Desktop app required" } };
    const { invoke } = await import("@tauri-apps/api/core");
    return await invoke("dispatch_execute_request_v1", { agentId: "dashboard", agent_id: "dashboard", prompt: JSON.stringify(promptPayload) }) as DashboardResponse;
  }

  async function loadDashboardState(fromGlobalRefresh = false) {
    setBanner("idle", "");
    try {
      const result = await uiRunDeduped(DASHBOARD_CACHE_KEY, async () => await dispatchInvoke({ op: "dashboard.get_state" }));
      if (!result.ok) {
        const code = result.error?.code ? `${result.error.code}: ` : "";
        const message = result.error?.message || "request failed";
        setBanner("danger", `Dashboard load failed: ${code}${message}`);
        return;
      }
      const state = responseState(result as DashboardResponse & Record<string, unknown>);
      const normalized = normalizeState(state);
      applyState(normalized);
      if (state) {
        uiCacheSet(DASHBOARD_CACHE_KEY, normalized);
        uiPersistentCacheSet(DASHBOARD_CACHE_KEY, normalized);
      } else {
        uiCacheSet(DASHBOARD_CACHE_KEY, null);
      }
      if (fromGlobalRefresh) {
        setBanner("success", "Dashboard refreshed.");
        window.setTimeout(() => {
          if (bannerKind === "success") setBanner("idle", "");
        }, 1200);
      }
    } catch (err: any) {
      setBanner("danger", `Dashboard load failed: ${err?.message || String(err)}`);
    }
  }

  function parseUsd(value: string): number {
    const n = Number.parseFloat(String(value || "").replace(/[^0-9.\-]/g, ""));
    return Number.isFinite(n) ? n : 0;
  }

  function formatShortDate(raw: string): string {
    const d = new Date(raw);
    if (Number.isNaN(d.getTime())) return String(raw || "").slice(-5) || "--";
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${mm}/${dd}`;
  }

  function trendPath(rows: Trend[]) {
    if (rows.length === 0) return { line: "", area: "", labels: [] as string[], points: [] as Array<{ x: number; y: number; label: string; formatted: string }> };
    const values = rows.map((r) => parseUsd(r.valueFormatted));
    const min = Math.min(...values);
    const max = Math.max(...values);
    const upper = max === min ? max + 1 : max;
    const stepX = rows.length > 1 ? (TREND_W - TREND_PAD_X * 2) / (rows.length - 1) : 0;
    const points = rows.map((r, i) => {
      const ratio = (upper - values[i]) / (upper - min);
      return { x: TREND_PAD_X + stepX * i, y: TREND_PAD_Y + ratio * (TREND_H - TREND_PAD_Y * 2), label: formatShortDate(r.label), formatted: r.valueFormatted || "$0.00" };
    });
    const line = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
    const baseY = TREND_H - TREND_PAD_Y;
    const area = `${line} L ${points[points.length - 1].x} ${baseY} L ${points[0].x} ${baseY} Z`;
    const idx = [0, Math.round((rows.length - 1) * 0.25), Math.round((rows.length - 1) * 0.5), Math.round((rows.length - 1) * 0.75), rows.length - 1];
    const labels = [...new Set(idx)].map((i) => points[i]?.label || "--");
    return { line, area, labels, points };
  }

  function donutSegments(rows: Breakdown[]) {
    const ranked = rows.map((r) => ({ ...r, value: parseUsd(r.cost) })).sort((a, b) => b.value - a.value);
    const top = ranked.slice(0, 3);
    const rest = ranked.slice(3);
    const others = rest.reduce((s, r) => s + r.value, 0);
    const merged = [...top];
    if (others > 0) merged.push({ name: "Others", color: "#64748b", cost: `$${others.toFixed(2)}`, value: others });
    const total = merged.reduce((s, r) => s + r.value, 0);
    let cursor = 0;
    return merged.map((r) => {
      const pct = total > 0 ? (r.value / total) * 100 : 0;
      const start = cursor;
      const end = cursor + pct * 3.6;
      cursor = end;
      return { ...r, pct, start, end };
    });
  }

  function arcPath(startAngle: number, endAngle: number): string {
    const span = Math.min(359.99, Math.max(0.01, endAngle - startAngle));
    const end = startAngle + span;
    const toXY = (r: number, a: number) => {
      const rad = (a - 90) * (Math.PI / 180);
      return { x: DONUT_CX + r * Math.cos(rad), y: DONUT_CY + r * Math.sin(rad) };
    };
    const outerStart = toXY(DONUT_R, startAngle);
    const outerEnd = toXY(DONUT_R, end);
    const innerStart = toXY(DONUT_R - DONUT_STROKE, end);
    const innerEnd = toXY(DONUT_R - DONUT_STROKE, startAngle);
    const large = span > 180 ? 1 : 0;
    return `M ${outerStart.x} ${outerStart.y} A ${DONUT_R} ${DONUT_R} 0 ${large} 1 ${outerEnd.x} ${outerEnd.y} L ${innerStart.x} ${innerStart.y} A ${DONUT_R - DONUT_STROKE} ${DONUT_R - DONUT_STROKE} 0 ${large} 0 ${innerEnd.x} ${innerEnd.y} Z`;
  }

  function normalizeAlertLevel(level: string): "danger" | "warning" | "info" {
    const v = String(level || "").toLowerCase();
    if (v.includes("danger") || v.includes("critical") || v.includes("error")) return "danger";
    if (v.includes("warn")) return "warning";
    return "info";
  }

  function orderedAlerts(rows: Alert[]): Alert[] {
    const norm = [...rows];
    const success = norm.filter((a) => /success\s*rate/i.test(a.text));
    const budget = norm.filter((a) => !/success\s*rate/i.test(a.text) && /budget|threshold|quota|limit|spend/i.test(a.text));
    const other = norm.filter((a) => !success.includes(a) && !budget.includes(a));
    budget.sort((a, b) => normalizeAlertLevel(a.level).localeCompare(normalizeAlertLevel(b.level)));
    return [...success, ...budget, ...other];
  }

  function visibleAlerts(rows: Alert[]): Alert[] {
    if (rows.length <= ALERT_COLLAPSE_VISIBLE || alertsExpanded) return rows;
    return rows.slice(0, ALERT_COLLAPSE_VISIBLE);
  }

  function formatRequestTime(raw: string): string {
    const value = String(raw || "").trim();
    if (!value) return "-";
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value.length > 19 ? `${value.slice(0, 19)}...` : value;
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    const hh = String(d.getHours()).padStart(2, "0");
    const mi = String(d.getMinutes()).padStart(2, "0");
    const ss = String(d.getSeconds()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`;
  }

  function recentWindow(): RecentRequest[] {
    return recentRequests.slice(0, RECENT_MAX_ROWS);
  }

  function totalRecentPages(): number {
    return Math.max(1, Math.ceil(recentWindow().length / RECENT_PAGE_SIZE));
  }

  function recentRowsForCurrentPage(): RecentRequest[] {
    const start = (recentPage - 1) * RECENT_PAGE_SIZE;
    return recentWindow().slice(start, start + RECENT_PAGE_SIZE);
  }

  function canPrevRecentPage(): boolean {
    return recentPage > 1;
  }

  function canNextRecentPage(): boolean {
    return recentPage < totalRecentPages();
  }

  function prevRecentPage() {
    if (canPrevRecentPage()) recentPage -= 1;
  }

  function nextRecentPage() {
    if (canNextRecentPage()) recentPage += 1;
  }

  function topPrimary(_item: TopExpensive, idx: number): string {
    return recentWindow()[idx]?.provider || "Provider";
  }

  function topSecondary(_item: TopExpensive, idx: number): string {
    return formatRequestTime(recentWindow()[idx]?.time || "");
  }

  function getStatusColor(status: string) {
    if (status.includes("Success") || status === "Status") return "text-emerald-400 bg-emerald-400/10";
    if (status.includes("Error") || status.includes("Failure")) return "text-rose-400 bg-rose-400/10";
    return "text-slate-400 bg-slate-400/10";
  }

  onMount(() => {
    const persistent = uiPersistentCacheGet<DashboardState | null>(DASHBOARD_CACHE_KEY, DASHBOARD_PERSISTENT_CACHE_TTL_MS);
    if (persistent) applyState(persistent);
    const cached = uiCacheGet<DashboardState | null>(DASHBOARD_CACHE_KEY, DASHBOARD_CACHE_TTL_MS);
    let refreshDelayMs = 0;
    if (cached) {
      applyState(cached);
      refreshDelayMs = 90;
    } else if (persistent) {
      refreshDelayMs = 90;
    }
    window.setTimeout(() => {
      void loadDashboardState();
    }, refreshDelayMs);
    // Emergency perf mode: disable background polling and focus-triggered refreshes.
    // Dashboard refresh stays manual via global refresh button event.
    const handleGlobalRefresh = () => void loadDashboardState(true);
    window.addEventListener("synapse:global-refresh", handleGlobalRefresh as EventListener);
    return () => {
      window.removeEventListener("synapse:global-refresh", handleGlobalRefresh as EventListener);
    };
  });
</script>

<div class="space-y-4 p-5">
  {#if bannerText}
    <div class={`rounded-md border px-3 py-2 text-xs ${bannerClass(bannerKind)}`}>{bannerText}</div>
  {/if}

  <div class="grid grid-cols-6 gap-3">
    {#each KPI_SLOTS as slot (slot.label)}
      <div class="flex min-w-0 flex-col justify-between rounded-2xl border p-3 shadow-sm transition-all hover:-translate-y-0.5" style="background-color: var(--surface-1); border-color: var(--border-subtle); box-shadow: var(--shadow-1); height: 110px;">
        <div class="flex min-w-0 items-start justify-between gap-2">
          <div class="min-w-0 text-[12px] font-medium leading-[1.1] text-slate-400">
            <div>{slot.t1}</div>
            <div>{slot.t2}</div>
          </div>
          <span class="shrink-0 text-xs text-slate-500 opacity-60">{slot.icon}</span>
        </div>
        <div class="mt-2 text-xl font-semibold tracking-tight text-white">{kpiValue(slot.label)}</div>
      </div>
    {/each}
  </div>

  <div class="grid grid-cols-3 gap-4">
    <div class="col-span-1 rounded-2xl border p-4 shadow-sm" style="background-color: var(--surface-1); border-color: var(--border-subtle); height: 250px;">
      <h3 class="mb-3 text-sm font-medium text-slate-300">Cost Trend (Last 30 Days)</h3>
      {#if trendData.length > 0}
        {@const tm = trendPath(trendData)}
        <div class="relative w-full" style="height: 172px;">
          <svg viewBox={`0 0 ${TREND_W} ${TREND_H}`} class="h-full w-full overflow-visible">
            <defs>
              <linearGradient id="trend-gradient-live" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="var(--accent-base)" stop-opacity="0.2" />
                <stop offset="100%" stop-color="var(--accent-base)" stop-opacity="0" />
              </linearGradient>
            </defs>
            <path d={tm.area} fill="url(#trend-gradient-live)" stroke="none" />
            <path d={tm.line} fill="none" stroke="var(--accent-base)" stroke-width="2" vector-effect="non-scaling-stroke" />
            {#each tm.points as point, idx (`${point.label}-${idx}`)}
              <circle cx={point.x} cy={point.y} r={trendHoverIndex === idx ? 4 : 3} fill="rgba(191,219,254,0.95)" stroke="rgba(30,41,59,0.9)" stroke-width="1" onmouseenter={() => (trendHoverIndex = idx)} onmouseleave={() => (trendHoverIndex = null)} />
            {/each}
          </svg>
          {#if trendHoverIndex !== null && tm.points[trendHoverIndex]}
            <div class="pointer-events-none absolute right-1 top-1 rounded-md border px-2 py-1 text-[12px] leading-5 text-slate-100" style="background-color: rgba(2,6,23,0.92); border-color: rgba(100,116,139,0.45);">
              <div>{tm.points[trendHoverIndex].label}</div>
              <div class="font-medium">{tm.points[trendHoverIndex].formatted}</div>
            </div>
          {/if}
        </div>
        <div class="mt-2 flex justify-between pb-1 text-[12px] text-slate-500">
          {#each tm.labels as t, i (`tick-${i}`)}
            <div>{t}</div>
          {/each}
        </div>
      {:else}
        <div class="text-xs text-slate-500">No data.</div>
      {/if}
    </div>

    <div class="col-span-1 rounded-2xl border p-4 shadow-sm" style="background-color: var(--surface-1); border-color: var(--border-subtle); height: 250px;">
      <h3 class="mb-3 text-sm font-medium text-slate-300">Cost Breakdown by Provider</h3>
      {#if breakdownLegend.length > 0}
        {@const segs = donutSegments(breakdownLegend)}
        {#if segs.length > 0}
          <div class="flex items-center justify-center" style="height: 145px;">
            <div class="relative">
              <svg width="132" height="132" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" fill="none" stroke="#21262d" stroke-width={DONUT_STROKE} />
                {#each segs as seg, idx (`${seg.name}-${idx}`)}
                  <path d={arcPath(seg.start, seg.end)} fill={seg.color} opacity={breakdownHoverIndex === null || breakdownHoverIndex === idx ? 1 : 0.35} onmouseenter={() => (breakdownHoverIndex = idx)} onmouseleave={() => (breakdownHoverIndex = null)} />
                {/each}
              </svg>
              {#if breakdownHoverIndex !== null && segs[breakdownHoverIndex]}
                <div class="pointer-events-none absolute -top-2 left-1/2 -translate-x-1/2 rounded-md border px-2 py-1 text-[11px] leading-4 text-slate-100" style="background-color: rgba(2,6,23,0.92); border-color: rgba(100,116,139,0.45);">
                  <div>{segs[breakdownHoverIndex].name}</div>
                  <div class="font-medium">{segs[breakdownHoverIndex].cost} ({segs[breakdownHoverIndex].pct.toFixed(1)}%)</div>
                </div>
              {/if}
            </div>
          </div>
          <div class="mt-2 grid grid-cols-2 gap-x-3 gap-y-2 text-[11px] text-slate-300">
            {#each segs as row, idx (`legend-${row.name}-${idx}`)}
              <div class="flex min-w-0 items-center justify-between gap-2">
                <span class="flex min-w-0 items-center gap-2">
                  <span class="h-2 w-2 rounded-full" style={`background-color: ${row.color};`}></span>
                  <span class="truncate">{row.name}</span>
                </span>
                <span class="shrink-0 tabular-nums text-slate-400">{row.cost}</span>
              </div>
            {/each}
          </div>
        {:else}
          <div class="text-xs text-slate-500">No data.</div>
        {/if}
      {:else}
        <div class="text-xs text-slate-500">No data.</div>
      {/if}
    </div>

    <div class="col-span-1 rounded-2xl border p-4 shadow-sm" style="background-color: var(--surface-1); border-color: var(--border-subtle); height: 250px;">
      <h3 class="mb-3 text-sm font-medium text-slate-300">Quick Health Alerts</h3>
      {#if orderedAlerts(quickAlerts).length > 0}
        <div class="space-y-2">
          {#each visibleAlerts(orderedAlerts(quickAlerts)) as alert (alert.text)}
            {@const lvl = normalizeAlertLevel(alert.level)}
            <div class={`flex items-center gap-3 rounded-lg px-3 py-2 ${lvl === "danger" ? "border border-red-900/30 bg-red-900/10" : lvl === "warning" ? "border border-amber-900/30 bg-amber-900/10" : "border border-slate-700/40 bg-slate-700/20"}`}>
              <span class={`text-xs ${lvl === "danger" ? "text-red-400" : lvl === "warning" ? "text-amber-400" : "text-slate-300"}`}>{lvl === "danger" ? "!" : lvl === "warning" ? "i" : "*"}</span>
              <span class={`text-xs font-medium ${lvl === "danger" ? "text-red-200" : lvl === "warning" ? "text-amber-200" : "text-slate-200"}`}>{alert.text}</span>
            </div>
          {/each}
        </div>
        {#if orderedAlerts(quickAlerts).length > ALERT_COLLAPSE_VISIBLE}
          <div class="mt-2 flex justify-end">
            <button type="button" class="rounded-md border px-2 py-1 text-[11px] text-slate-300 hover:bg-white/5" style="border-color: var(--border-subtle);" onclick={() => (alertsExpanded = !alertsExpanded)}>
              {alertsExpanded ? "Show less" : `Show ${orderedAlerts(quickAlerts).length - ALERT_COLLAPSE_VISIBLE} more`}
            </button>
          </div>
        {/if}
      {:else}
        <div class="text-xs text-slate-500">No data.</div>
      {/if}
    </div>
  </div>

  <div class="grid grid-cols-3 gap-4">
    <div class="col-span-2 flex flex-col rounded-2xl border p-4 shadow-sm" style="background-color: var(--surface-1); border-color: var(--border-subtle); min-height: 240px;">
      <h3 class="mb-3 text-sm font-medium text-slate-300">Recent Requests</h3>
      <div class="flex-1 overflow-hidden rounded-lg border" style="border-color: var(--border-subtle);">
        <table class="w-full table-fixed text-left text-[11px] leading-4">
          <colgroup>
            <col style="width: 26%;" />
            <col style="width: 12%;" />
            <col style="width: 14%;" />
            <col style="width: 13%;" />
            <col style="width: 18%;" />
            <col style="width: 17%;" />
          </colgroup>
          <thead class="bg-slate-900/50 text-slate-400">
            <tr>
              <th class="h-8 whitespace-nowrap px-3 py-2 font-medium">Time</th>
              <th class="h-8 whitespace-nowrap px-3 py-2 text-center font-medium">Status</th>
              <th class="h-8 whitespace-nowrap px-3 py-2 text-center font-medium">Provider</th>
              <th class="h-8 whitespace-nowrap px-3 py-2 text-center font-medium">Latency</th>
              <th class="h-8 whitespace-nowrap px-3 py-2 text-center font-medium">Tokens In/Out</th>
              <th class="h-8 whitespace-nowrap px-3 py-2 text-center font-medium">Cost</th>
            </tr>
          </thead>
          <tbody>
            {#if recentWindow().length > 0}
              {#each recentRowsForCurrentPage() as req (`${req.time}-${req.provider}-${req.cost}`)}
                <tr class="h-9 border-t hover:bg-white/5" style="border-color: rgba(100,116,139,0.18);">
                  <td class="truncate px-3 py-2 text-slate-300" title={req.time}>{formatRequestTime(req.time)}</td>
                  <td class="px-3 py-2 text-center"><span class={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${getStatusColor(req.status)}`}>{req.status.includes("Error") ? "Error" : "Success"}</span></td>
                  <td class="truncate px-3 py-2 text-center text-slate-300" title={req.provider}>{req.provider || "-"}</td>
                  <td class="px-3 py-2 text-center text-slate-300">{req.latency || "-"}</td>
                  <td class="px-3 py-2 text-center text-slate-300">{req.tokens || "-"}</td>
                  <td class="px-3 py-2 text-center text-slate-300">{req.cost || "-"}</td>
                </tr>
              {/each}
            {:else}
              <tr>
                <td class="px-3 py-4 text-center text-slate-500" colspan="6">No data.</td>
              </tr>
            {/if}
          </tbody>
        </table>
      </div>
      <div class="mt-2 flex items-center justify-between text-[11px] text-slate-400">
        <span>{recentWindow().length > 0 ? `Showing ${Math.min(RECENT_MAX_ROWS, recentWindow().length)} latest requests` : "No requests yet"}</span>
        <div class="flex items-center gap-2">
          <button type="button" class="rounded-md border px-2 py-1 text-[11px] hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-45" style="border-color: var(--border-subtle);" disabled={!canPrevRecentPage()} onclick={prevRecentPage}>Prev</button>
          <span>Page {recentPage} / {totalRecentPages()}</span>
          <button type="button" class="rounded-md border px-2 py-1 text-[11px] hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-45" style="border-color: var(--border-subtle);" disabled={!canNextRecentPage()} onclick={nextRecentPage}>Next</button>
        </div>
      </div>
    </div>

    <div class="col-span-1 flex flex-col rounded-2xl border p-4 shadow-sm" style="background-color: var(--surface-1); border-color: var(--border-subtle); min-height: 240px;">
      <h3 class="mb-3 text-sm font-medium text-slate-300">Top Expensive Requests</h3>
      <div class="flex-1 space-y-0 overflow-hidden">
        {#if topExpensive.length > 0}
          {#each topExpensive.slice(0, 3) as item, idx (item.id)}
            <div class="flex items-center justify-between border-b py-2 last:border-0" style="border-color: var(--border-subtle);">
              <div class="min-w-0 pr-2">
                <div class="truncate text-xs text-slate-300">{topPrimary(item, idx)}</div>
                <div class="truncate text-[10px] text-slate-500/90">{topSecondary(item, idx)}</div>
              </div>
              <div class="text-xs font-medium text-slate-200 tabular-nums">{item.cost}</div>
            </div>
          {/each}
        {:else}
          <div class="text-xs text-slate-500">No data.</div>
        {/if}
      </div>
    </div>
  </div>
</div>
