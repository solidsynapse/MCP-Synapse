<script lang="ts">
  import { onMount } from "svelte";
  import {
    PHASE1_TTL_CACHE_OPS,
    PHASE1_TTL_CACHE_TTL_MS,
    uiBuildOpCacheKey,
    uiCacheGet,
    uiCacheSet,
    uiInvalidateOpCaches,
    uiRunDeduped,
    uiTraceOpCache,
  } from "$lib/ui_session";

  type BannerKind = "idle" | "info" | "success" | "danger";
  type DispatchError = { code?: string; message?: string };
  type Kpi = { label: string; value: string; icon?: string };
  type RecentRequest = { time: string; request_id?: string; status: string; connection?: string; provider: string; model_id?: string; latency: string; tokens: string; cost: string };
  type TopExpensive = { id: string; time?: string; connection?: string; provider?: string; model_id?: string; cost: string };
  type Breakdown = { name: string; color: string; cost: string };
  type Trend = { label: string; valueFormatted: string };
  type Alert = { level: string; text: string; detail?: string; monitor_only?: boolean; enforcement_mode?: string };

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

  const KPI_SLOTS: Array<{ label: string; valueKey: string; icon: string; t1: string; t2: string }> = [
    { label: "Total Cost USD", valueKey: "Total Cost USD", icon: "cost", t1: "Total Cost", t2: "USD" },
    { label: "Total Requests", valueKey: "Total Requests", icon: "requests", t1: "Total", t2: "Requests" },
    { label: "Total Tokens", valueKey: "Total Tokens", icon: "tokens", t1: "Total", t2: "Tokens" },
    { label: "Success Rate %", valueKey: "Success Rate %", icon: "success", t1: "Success Rate", t2: "%" },
    { label: "Avg Latency ms", valueKey: "Avg Latency ms", icon: "latency", t1: "Avg Latency", t2: "ms" },
    { label: "Active Bridges", valueKey: "Active Bridges count", icon: "bridges", t1: "Active Bridges", t2: "count" },
  ];
  const KPI_ICON_PATHS: Record<string, string[]> = {
    cost: ["M4 8h16v10H4V8z", "M4 11h16", "M9 14h3"],
    requests: ["M7 7h10", "M7 12h10", "M7 17h10", "M5 7l2 2-2 2", "M19 17l-2-2 2-2"],
    tokens: ["M8 7c0 1.1 1.8 2 4 2s4-.9 4-2-1.8-2-4-2-4 .9-4 2z", "M8 7v6c0 1.1 1.8 2 4 2s4-.9 4-2V7", "M8 10c0 1.1 1.8 2 4 2s4-.9 4-2"],
    success: ["M12 3l7 4v5c0 5-3 9-7 11-4-2-7-6-7-11V7l7-4z", "M9.5 12.5l1.8 1.8 3.4-3.4"],
    latency: ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z", "M12 7v5l3 2"],
    bridges: ["M10 13a5 5 0 0 1 0-7l1.5-1.5a5 5 0 1 1 7 7L17 12", "M14 11a5 5 0 0 1 0 7L12.5 19.5a5 5 0 1 1-7-7L7 12"],
  };

  function kpiIconPaths(key: string): string[] {
    return KPI_ICON_PATHS[key] ?? [];
  }

  const DEFAULT_STATE: DashboardState = {
    kpis: [],
    recent_requests: [],
    top_expensive: [],
    breakdown_legend: [],
    trend_data: [],
    quick_alerts: [],
  };

  const RECENT_MIN_PAGE_SIZE = 3;
  const RECENT_MAX_PAGE_SIZE = 10;
  const RECENT_VIEWPORT_OFFSETS_PX = 520;
  const RECENT_HEADER_PX = 32;
  const RECENT_ROW_PX = 34;
  const RECENT_MAX_ROWS = 30;
  const TOP_EXPENSIVE_MIN_ROWS = 3;
  const TOP_EXPENSIVE_MAX_ROWS = 6;
  const TOP_EXPENSIVE_VIEWPORT_OFFSETS_PX = 520;
  const TOP_EXPENSIVE_ROW_PX = 44;
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
  let recentPageSize = $state(RECENT_MIN_PAGE_SIZE);
  let topExpensiveVisibleRows = $state(TOP_EXPENSIVE_MIN_ROWS);
  let topExpensive = $state<TopExpensive[]>(DEFAULT_STATE.top_expensive);
  let breakdownLegend = $state<Breakdown[]>(DEFAULT_STATE.breakdown_legend);
  let trendData = $state<Trend[]>(DEFAULT_STATE.trend_data);
  let quickAlerts = $state<Alert[]>(DEFAULT_STATE.quick_alerts);
  let alertsExpanded = $state(false);
  let trendHoverIndex = $state<number | null>(null);
  let breakdownHoverIndex = $state<number | null>(null);
  let trendTooltipX = $state(0);
  let trendTooltipY = $state(0);
  let breakdownTooltipX = $state(0);
  let breakdownTooltipY = $state(0);
  let bannerKind = $state<BannerKind>("idle");
  let bannerText = $state("");
  let recentTableViewport: HTMLDivElement | null = null;
  let topExpensiveViewport: HTMLDivElement | null = null;
  let trendChartWrap: HTMLDivElement | null = null;
  let breakdownChartWrap: HTMLDivElement | null = null;
  const DASHBOARD_OP = "dashboard.get_state";

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
      recent_requests: asDictList(src.recent_requests).map((v) => ({ time: String(v.time || ""), request_id: String(v.request_id || ""), status: String(v.status || ""), connection: String(v.connection || ""), provider: String(v.provider || ""), model_id: String(v.model_id || ""), latency: String(v.latency || ""), tokens: String(v.tokens || ""), cost: String(v.cost || "") })),
      top_expensive: asDictList(src.top_expensive).map((v) => ({ id: String(v.id || ""), time: String(v.time || ""), connection: String(v.connection || ""), provider: String(v.provider || ""), model_id: String(v.model_id || ""), cost: String(v.cost || "") })),
      breakdown_legend: asDictList(src.breakdown_legend).map((v) => ({ name: String(v.name || ""), color: String(v.color || "#64748b"), cost: String(v.cost || "") })),
      trend_data: asDictList(src.trend_data).map((v) => ({ label: String(v.label || ""), valueFormatted: String(v.valueFormatted || "") })),
      quick_alerts: asDictList(src.quick_alerts).map((v) => ({
        level: String(v.level || "info"),
        text: String(v.text || ""),
        detail: String(v.detail || ""),
        monitor_only: Boolean(v.monitor_only),
        enforcement_mode: String(v.enforcement_mode || ""),
      })),
    };
  }

  function alertEnforcementLabel(alert: Alert) {
    const mode = String(alert.enforcement_mode || "").trim().toLowerCase();
    if (mode === "block") return "Block active";
    if (mode === "throttle") return "Throttle active";
    return alert.monitor_only ? "Monitor-only" : "";
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
  function kpiValueByKey(key: string): string {
    const row = kpis.find((item) => item.label === key);
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

  function dashboardCacheKey() {
    return uiBuildOpCacheKey(DASHBOARD_OP, { op: DASHBOARD_OP }, {});
  }

  async function loadDashboardState(fromGlobalRefresh = false, forceRefresh = false) {
    setBanner("idle", "");
    const source = fromGlobalRefresh ? "dashboard.global_refresh_event" : "dashboard.load";
    const cacheKey = dashboardCacheKey();
    if (forceRefresh) {
      uiInvalidateOpCaches(PHASE1_TTL_CACHE_OPS, {
        reason: fromGlobalRefresh ? "global_refresh_event" : "force_refresh",
        source,
        route: "/dashboard",
      });
    }
    try {
      const cached = uiCacheGet<DashboardState>(cacheKey, PHASE1_TTL_CACHE_TTL_MS);
      uiTraceOpCache({
        op: DASHBOARD_OP,
        status: cached ? "HIT" : "MISS",
        route: "/dashboard",
        source,
        reason: "ttl_lookup",
        key: cacheKey,
      });
      if (cached) {
        applyState(cached);
        if (fromGlobalRefresh) {
          setBanner("success", "Dashboard refreshed.");
          window.setTimeout(() => {
            if (bannerKind === "success") setBanner("idle", "");
          }, 1200);
        }
        return;
      }
      const result = await uiRunDeduped(cacheKey, async () => await dispatchInvoke({ op: DASHBOARD_OP }));
      if (!result.ok) {
        const code = result.error?.code ? `${result.error.code}: ` : "";
        const message = result.error?.message || "request failed";
        setBanner("danger", `Dashboard load failed: ${code}${message}`);
        return;
      }
      const state = responseState(result as DashboardResponse & Record<string, unknown>);
      const normalized = normalizeState(state);
      applyState(normalized);
      uiCacheSet(cacheKey, normalized);
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
    if (rows.length === 0) return { line: "", area: "", ticks: [] as string[], points: [] as Array<{ x: number; y: number; label: string; formatted: string }> };
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
    const tickCount = rows.length <= 4 ? rows.length : 5;
    const idx = Array.from({ length: tickCount }, (_, i) => Math.round(((rows.length - 1) * i) / (tickCount - 1 || 1)));
    const ticks = [...new Set(idx)].map((i) => points[i]?.label || "--");
    return { line, area, ticks, points };
  }

  function donutSegments(rows: Breakdown[]) {
    const ranked = rows.map((r) => ({ ...r, value: parseUsd(r.cost) })).sort((a, b) => b.value - a.value);
    const top = ranked.slice(0, 3);
    const rest = ranked.slice(3);
    const others = rest.reduce((s, r) => s + r.value, 0);
    const merged = [...top];
    if (others > 0) merged.push({ name: "Others", color: "#64748b", cost: `$${others.toFixed(2)}`, value: others });
    const nonZero = merged.filter((r) => r.value > 0);
    const total = nonZero.reduce((s, r) => s + r.value, 0);
    let cursor = 0;
    return nonZero.map((r) => {
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

  function normalizeAlertLevel(level: string): "critical" | "warning" | "info" {
    const v = String(level || "").toLowerCase();
    if (v.includes("danger") || v.includes("critical") || v.includes("error")) return "critical";
    if (v.includes("warn")) return "warning";
    return "info";
  }

  function orderedAlerts(rows: Alert[]): Alert[] {
    const norm = [...rows];
    const success = norm.filter((a) => /success\s*rate/i.test(a.text));
    const budget = norm.filter((a) => !/success\s*rate/i.test(a.text) && /budget|threshold|quota|limit|spend/i.test(a.text));
    const other = norm.filter((a) => !success.includes(a) && !budget.includes(a));
    const rank = (alert: Alert): number => {
      const lvl = normalizeAlertLevel(alert.level);
      if (lvl === "critical") return 0;
      if (lvl === "warning") return 1;
      return 2;
    };
    budget.sort((a, b) => rank(a) - rank(b));
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

  function recomputeRecentPageSize() {
    const viewportHeight = typeof window !== "undefined" ? window.innerHeight : 0;
    const tableHeight = recentTableViewport?.clientHeight || 0;
    const h = tableHeight > 0 ? tableHeight : (viewportHeight - RECENT_VIEWPORT_OFFSETS_PX);
    if (h <= 0) return;
    const next = Math.max(
      RECENT_MIN_PAGE_SIZE,
      Math.min(RECENT_MAX_PAGE_SIZE, Math.floor((h - RECENT_HEADER_PX - 8) / RECENT_ROW_PX))
    );
    if (next !== recentPageSize) {
      recentPageSize = next;
      if (recentPage > totalRecentPages()) recentPage = totalRecentPages();
    }
  }

  function totalRecentPages(): number {
    return Math.max(1, Math.ceil(recentWindow().length / recentPageSize));
  }

  function recentRowsForCurrentPage(): RecentRequest[] {
    const start = (recentPage - 1) * recentPageSize;
    return recentWindow().slice(start, start + recentPageSize);
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

  function topPrimary(item: TopExpensive): string {
    const connection = String(item.connection || "").trim();
    const provider = String(item.provider || "").trim();
    if (connection && provider && connection.toLowerCase() !== provider.toLowerCase()) {
      return `${provider} / ${connection}`;
    }
    return connection || provider || "Provider";
  }

  function topSecondary(item: TopExpensive): string {
    const rawTime = String(item.time || "");
    const d = new Date(rawTime);
    const shortTime = Number.isNaN(d.getTime())
      ? (rawTime ? rawTime.slice(0, 16) : "-")
      : `${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getDate()).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
    const reqId = String(item.id || "").trim();
    const shortId = reqId ? `#${reqId.slice(-8)}` : "#-";
    return `${shortTime} | ${shortId}`;
  }

  function requestConnectionProvider(req: RecentRequest): string {
    const connection = String(req.connection || "").trim();
    const provider = String(req.provider || "").trim();
    if (connection && provider && connection.toLowerCase() !== provider.toLowerCase()) {
      return `${connection} / ${provider}`;
    }
    return connection || provider || "-";
  }

  function requestModelTooltip(req: RecentRequest): string | undefined {
    const modelId = String(req.model_id || "").trim();
    return modelId || undefined;
  }

  function topModelTooltip(item: TopExpensive): string | undefined {
    const modelId = String(item.model_id || "").trim();
    return modelId || undefined;
  }

  function recomputeTopExpensiveVisibleRows() {
    const viewportHeight = typeof window !== "undefined" ? window.innerHeight : 0;
    const boxHeight = topExpensiveViewport?.clientHeight || 0;
    const h = boxHeight > 0 ? boxHeight : (viewportHeight - TOP_EXPENSIVE_VIEWPORT_OFFSETS_PX);
    if (h <= 0) return;
    const next = Math.max(
      TOP_EXPENSIVE_MIN_ROWS,
      Math.min(TOP_EXPENSIVE_MAX_ROWS, Math.floor(h / TOP_EXPENSIVE_ROW_PX))
    );
    if (next !== topExpensiveVisibleRows) topExpensiveVisibleRows = next;
  }

  function tokenTotalTooltip(tokens: string): string {
    const m = String(tokens || "").match(/^\s*(\d+)\s*\/\s*(\d+)\s*$/);
    if (!m) return "";
    const total = Number.parseInt(m[1], 10) + Number.parseInt(m[2], 10);
    return `Total: ${total}`;
  }

  function updateTrendTooltip(event: MouseEvent) {
    if (!trendChartWrap) return;
    const rect = trendChartWrap.getBoundingClientRect();
    trendTooltipX = event.clientX - rect.left + 10;
    trendTooltipY = event.clientY - rect.top - 14;
  }

  function updateBreakdownTooltip(event: MouseEvent) {
    if (!breakdownChartWrap) return;
    const rect = breakdownChartWrap.getBoundingClientRect();
    breakdownTooltipX = event.clientX - rect.left + 10;
    breakdownTooltipY = event.clientY - rect.top - 14;
  }

  function getStatusColor(status: string) {
    if (status.includes("Success") || status === "Status") return "text-emerald-400 bg-emerald-400/10";
    if (status.includes("Error") || status.includes("Failure")) return "text-rose-400 bg-rose-400/10";
    return "text-slate-400 bg-slate-400/10";
  }

  onMount(() => {
    const bootstrapKey = dashboardCacheKey();
    const cached = uiCacheGet<DashboardState>(bootstrapKey, PHASE1_TTL_CACHE_TTL_MS);
    uiTraceOpCache({
      op: DASHBOARD_OP,
      status: cached ? "HIT" : "MISS",
      route: "/dashboard",
      source: "dashboard.on_mount.bootstrap",
      reason: "ttl_lookup",
      key: bootstrapKey,
    });
    let refreshDelayMs = 0;
    if (cached) {
      applyState(cached);
      refreshDelayMs = 90;
    }
    window.setTimeout(() => {
      void loadDashboardState();
    }, refreshDelayMs);
    // Emergency perf mode: disable background polling and focus-triggered refreshes.
    // Dashboard refresh stays manual via global refresh button event.
    const handleGlobalRefresh = () => void loadDashboardState(true, true);
    const handleWindowResize = () => {
      recomputeRecentPageSize();
      recomputeTopExpensiveVisibleRows();
    };
    window.addEventListener("synapse:global-refresh", handleGlobalRefresh as EventListener);
    window.addEventListener("resize", handleWindowResize);
    const ro = new ResizeObserver(() => recomputeRecentPageSize());
    if (recentTableViewport) ro.observe(recentTableViewport);
    const roTop = new ResizeObserver(() => recomputeTopExpensiveVisibleRows());
    if (topExpensiveViewport) roTop.observe(topExpensiveViewport);
    window.setTimeout(() => recomputeRecentPageSize(), 0);
    window.setTimeout(() => recomputeTopExpensiveVisibleRows(), 0);
    return () => {
      window.removeEventListener("synapse:global-refresh", handleGlobalRefresh as EventListener);
      window.removeEventListener("resize", handleWindowResize);
      ro.disconnect();
      roTop.disconnect();
    };
  });

</script>

<div class="space-y-4 px-5 pt-4 pb-0 overflow-x-hidden">
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
          <span class="inline-flex h-6 w-6 items-center justify-center rounded-md border text-slate-300" style="border-color: rgba(100,116,139,0.35); background-color: rgba(15,23,42,0.35);">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              {#each kpiIconPaths(slot.icon) as d (`${slot.icon}-${d}`)}
                <path d={d} />
              {/each}
            </svg>
          </span>
        </div>
        <div class="mt-1.5 text-xl font-semibold tracking-tight text-white">{kpiValueByKey(slot.valueKey)}</div>
      </div>
    {/each}
  </div>

  <div class="grid grid-cols-3 gap-4">
    <div
      class="col-span-1 rounded-2xl border p-4 shadow-sm"
      style="background-color: var(--surface-1); border-color: var(--border-subtle); height: 250px;"
    >
      <h3 class="mb-3 text-sm font-medium text-slate-300">Cost Trend (Last 30 Days)</h3>
      {#if trendData.length > 0}
        {@const tm = trendPath(trendData)}
        <div class="relative w-full" style="height: 172px;" bind:this={trendChartWrap}>
          <svg viewBox={`0 0 ${TREND_W} ${TREND_H}`} class="h-full w-full overflow-visible">
            <defs>
              <linearGradient id="trend-gradient-live" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="var(--accent-base)" stop-opacity="0.14" />
                <stop offset="100%" stop-color="var(--accent-base)" stop-opacity="0" />
              </linearGradient>
            </defs>
            <path d={tm.area} fill="url(#trend-gradient-live)" stroke="none" />
            <path d={tm.line} fill="none" stroke="var(--accent-base)" stroke-width="1.75" vector-effect="non-scaling-stroke" />
            {#each tm.points as point, idx (`${point.label}-${idx}`)}
              <circle cx={point.x} cy={point.y} r={trendHoverIndex === idx ? 3.5 : 2.5} fill="rgba(148,163,184,0.9)" stroke="rgba(30,41,59,0.6)" stroke-width="0.8" onmouseenter={() => (trendHoverIndex = idx)} onmousemove={updateTrendTooltip} onmouseleave={() => (trendHoverIndex = null)} />
            {/each}
          </svg>
          {#if trendHoverIndex !== null && tm.points[trendHoverIndex]}
            <div class="pointer-events-none absolute rounded-md border px-2 py-1 text-[12px] leading-5 text-slate-100" style={`left:${trendTooltipX}px; top:${trendTooltipY}px; transform: translateY(-100%); background-color: rgba(2,6,23,0.92); border-color: rgba(100,116,139,0.45);`}>
              <div>{tm.points[trendHoverIndex].label}</div>
              <div class="font-medium">{tm.points[trendHoverIndex].formatted}</div>
            </div>
          {/if}
        </div>
        <div class="mt-2 flex justify-between px-2 pb-1 text-[11px] text-slate-400/90">
          {#each tm.ticks as t, i (`tick-${i}`)}
            <div class="min-w-[44px] text-center">{t}</div>
          {/each}
        </div>
      {:else}
        <div class="text-xs text-slate-500">No data.</div>
      {/if}
    </div>

    <div
      class="col-span-1 rounded-2xl border p-4 shadow-sm"
      style="background-color: var(--surface-1); border-color: var(--border-subtle); height: 250px;"
    >
      <h3 class="mb-3 text-sm font-medium text-slate-300">Cost Breakdown by Provider</h3>
      {#if breakdownLegend.length > 0}
        {@const segs = donutSegments(breakdownLegend)}
        {#if segs.length > 0}
          <div class="flex items-center justify-center" style="height: 132px;">
            <div class="relative" bind:this={breakdownChartWrap}>
              <svg width="132" height="132" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" fill="none" stroke="#21262d" stroke-width={DONUT_STROKE} />
                {#each segs as seg, idx (`${seg.name}-${idx}`)}
                  <path d={arcPath(seg.start, seg.end)} fill={seg.color} opacity={breakdownHoverIndex === null || breakdownHoverIndex === idx ? 1 : 0.35} onmouseenter={() => (breakdownHoverIndex = idx)} onmousemove={updateBreakdownTooltip} onmouseleave={() => (breakdownHoverIndex = null)} />
                {/each}
              </svg>
              {#if breakdownHoverIndex !== null && segs[breakdownHoverIndex]}
                <div class="pointer-events-none absolute rounded-md border px-2 py-1 text-[11px] leading-4 text-slate-100" style={`left:${breakdownTooltipX}px; top:${breakdownTooltipY}px; transform: translateY(-100%); background-color: rgba(2,6,23,0.92); border-color: rgba(100,116,139,0.45);`}>
                  <div>{segs[breakdownHoverIndex].name}</div>
                  <div class="font-medium">{segs[breakdownHoverIndex].cost} ({segs[breakdownHoverIndex].pct.toFixed(1)}%)</div>
                </div>
              {/if}
            </div>
          </div>
          <div class="mx-auto mt-1 flex max-w-[220px] flex-wrap items-center justify-center gap-x-2 gap-y-1 text-[10px] text-slate-300">
            {#each segs as row, idx (`legend-${row.name}-${idx}`)}
              <div class="inline-flex min-w-0 items-center gap-1.5 rounded-full border px-1.5 py-[2px] leading-none" style="border-color: rgba(100,116,139,0.3);">
                <span class="h-2 w-2 shrink-0 rounded-full" style={`background-color: ${row.color};`}></span>
                <span class="truncate">{row.name}</span>
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

    <div
      class="col-span-1 rounded-2xl border p-4 shadow-sm"
      style="background-color: var(--surface-1); border-color: var(--border-subtle); height: 250px;"
    >
      <h3 class="mb-3 text-sm font-medium text-slate-300">Quick Health Alerts ({orderedAlerts(quickAlerts).length})</h3>
      {#if orderedAlerts(quickAlerts).length > 0}
        <div class="max-h-[176px] space-y-2 overflow-y-auto pr-1">
          {#each visibleAlerts(orderedAlerts(quickAlerts)) as alert (alert.text)}
            {@const lvl = normalizeAlertLevel(alert.level)}
            <div class={`flex items-start gap-3 rounded-lg px-3 py-2 ${lvl === "critical" ? "border border-red-900/30 bg-red-900/10" : lvl === "warning" ? "border border-amber-900/30 bg-amber-900/10" : "border border-slate-700/40 bg-slate-700/20"}`}>
              <span class={`text-xs ${lvl === "critical" ? "text-red-400" : lvl === "warning" ? "text-amber-400" : "text-slate-300"}`}>{lvl === "critical" ? "!" : lvl === "warning" ? "i" : "*"}</span>
              <span class="flex min-w-0 flex-col">
                <span class={`text-xs font-medium ${lvl === "critical" ? "text-red-200" : lvl === "warning" ? "text-amber-200" : "text-slate-200"}`}>{alert.text}</span>
                {#if alertEnforcementLabel(alert)}
                  <span class="mt-0.5 inline-flex w-fit rounded border px-1.5 py-0.5 text-[9px] uppercase tracking-wide text-slate-300/85" style="border-color: var(--border-subtle);">
                    {alertEnforcementLabel(alert)}
                  </span>
                {/if}
                {#if alert.detail}
                  <span class="text-[10px] text-slate-300/80">{alert.detail}</span>
                {/if}
              </span>
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
    <div
      class="col-span-2 flex flex-col rounded-2xl border p-4 shadow-sm"
      style="background-color: var(--surface-1); border-color: var(--border-subtle); height: clamp(240px, 34vh, 360px);"
    >
      <h3 class="mb-3 text-sm font-medium text-slate-300">Recent Requests</h3>
      <div class="flex-1 overflow-hidden rounded-lg border" style="border-color: var(--border-subtle);" bind:this={recentTableViewport}>
        <table class="w-full table-fixed text-left text-[11px] leading-4">
          <colgroup>
            <col style="width: 24%;" />
            <col style="width: 12%;" />
            <col style="width: 22%;" />
            <col style="width: 12%;" />
            <col style="width: 15%;" />
            <col style="width: 15%;" />
          </colgroup>
          <thead class="bg-slate-900/50 text-slate-400">
            <tr>
              <th class="h-8 whitespace-nowrap px-3 py-2 font-medium">Time</th>
              <th class="h-8 whitespace-nowrap px-3 py-2 text-center font-medium">Status</th>
              <th class="h-8 whitespace-nowrap px-3 py-2 text-center font-medium">Connection/Provider</th>
              <th class="h-8 whitespace-nowrap px-3 py-2 text-center font-medium">Latency</th>
              <th class="h-8 whitespace-nowrap px-3 py-2 text-center font-medium">Tokens In/Out</th>
              <th class="h-8 whitespace-nowrap px-3 py-2 text-center font-medium">Cost</th>
            </tr>
          </thead>
          <tbody>
            {#if recentWindow().length > 0}
              {#each recentRowsForCurrentPage() as req (`${req.time}-${req.provider}-${req.cost}`)}
                <tr class="h-9 border-t hover:bg-white/5" style="border-color: rgba(100,116,139,0.18);">
                  <td class="truncate px-3 py-2 text-slate-300" title={req.request_id || ""}>{formatRequestTime(req.time)}</td>
                  <td class="px-3 py-2 text-center"><span class={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${getStatusColor(req.status)}`}>{req.status.includes("Error") ? "Error" : "Success"}</span></td>
                  <td class="truncate px-3 py-2 text-center text-slate-300" title={requestModelTooltip(req)}>{requestConnectionProvider(req)}</td>
                  <td class="px-3 py-2 text-center text-slate-300">{req.latency || "-"}</td>
                  <td class="px-3 py-2 text-center text-slate-300" title={tokenTotalTooltip(req.tokens)}>{req.tokens || "-"}</td>
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
      <div class="mt-2 flex items-center justify-end text-[11px] text-slate-400">
        <div class="flex items-center gap-2">
          <button type="button" class="rounded-md border px-2 py-1 text-[11px] hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-45" style="border-color: var(--border-subtle);" disabled={!canPrevRecentPage()} onclick={prevRecentPage}>Prev</button>
          <span>Page {recentPage} / {totalRecentPages()}</span>
          <button type="button" class="rounded-md border px-2 py-1 text-[11px] hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-45" style="border-color: var(--border-subtle);" disabled={!canNextRecentPage()} onclick={nextRecentPage}>Next</button>
        </div>
      </div>
    </div>

    <div
      class="col-span-1 flex flex-col rounded-2xl border p-4 shadow-sm"
      style="background-color: var(--surface-1); border-color: var(--border-subtle); height: clamp(240px, 34vh, 360px);"
    >
      <h3 class="mb-3 text-sm font-medium text-slate-300">Top Expensive Requests</h3>
      <div class="flex-1 space-y-0 overflow-hidden" bind:this={topExpensiveViewport}>
        {#if topExpensive.length > 0}
          {#each topExpensive.slice(0, topExpensiveVisibleRows) as item (item.id)}
            <div class="flex items-center justify-between border-b py-2 last:border-0" style="border-color: var(--border-subtle);">
              <div class="min-w-0 pr-2" title={topModelTooltip(item)}>
                <div class="truncate text-xs text-slate-300">{topPrimary(item)}</div>
                <div class="truncate text-[10px] text-slate-500/90">{topSecondary(item)}</div>
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

