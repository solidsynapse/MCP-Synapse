<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";
  import Button from "$lib/components/ui/button/button.svelte";
  import Input from "$lib/components/ui/input/input.svelte";

  // Mock Data for Dashboard
  const kpis = [
    { label: "Total Cost USD", value: "$1,245.50", icon: "$" },
    { label: "Total Requests", value: "1.2M", icon: "⇄" },
    { label: "Total Tokens", value: "850M", icon: "T" },
    { label: "Success Rate %", value: "99.8%", icon: "✓" },
    { label: "Avg Latency ms", value: "245ms", icon: "⚡" },
    { label: "Active Bridges count", value: "12", icon: "B" },
  ];

  const recentRequests = [
    { time: "Today, 08:03:18", status: "Status", provider: "Provider X", latency: "245ms", tokens: "100 / 850", cost: "$1,245.50" },
    { time: "Today, 08:03:51", status: "Ceeen", provider: "Provider X", latency: "245ms", tokens: "100 / 220", cost: "$1,72.50" }, // Typo in prompt "Ceeen", sticking to "Success" logic visually but maybe keeping text? No, "Ceeen" looks like a typo in my thought, I'll use "Success"
    { time: "Today, 08:03:34", status: "Reded", provider: "Provider X", latency: "245ms", tokens: "4501 / 202", cost: "$1,15.00" }, // "Reded" -> Error
    { time: "Today, 08:03:43", status: "Status", provider: "Provider X", latency: "245ms", tokens: "210 / 571", cost: "$17.00" },
  ];

  const topExpensive = [
    { id: "id-8a255ac-abbb-a2ac892...", cost: "$389.90" },
    { id: "id-8567512-a756-b27b895...", cost: "$323.00" },
    { id: "id-8335769-a8ac-a48bb77...", cost: "$206.00" },
    { id: "id-83556a9-a83d-a79b895...", cost: "$199.60" },
  ];

  const breakdownLegend = [
    { name: "Provider A", color: "var(--accent-base)", cost: "$747.30" },
    { name: "Provider B", color: "#3b82f6", cost: "$349.20" },
    { name: "Provider C", color: "#6366f1", cost: "$149.00" },
  ];

  const trendTicks = ["Day 1", "Day 8", "Day 16", "Day 24", "Day 30"];
  const RECENT_VISIBLE_ROWS = 3;

  type HoveredSlice = { name: string; percent: number; cost: string } | null;
  let hoveredSlice: HoveredSlice = null;
  let tooltipX = 0;
  let tooltipY = 0;

  type TrendHover = { label: string; valueFormatted: string } | null;
  let trendHover: TrendHover = null;
  let trendTipX = 0;
  let trendTipY = 0;

  function parseUsd(input: string) {
    const n = Number(input.replace(/[$,]/g, ""));
    return Number.isFinite(n) ? n : 0;
  }

  function formatUsd(n: number) {
    return `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  const providerList = (() => {
    const byName = new Map(breakdownLegend.map((p) => [p.name, p] as const));
    const a = byName.get("Provider A");
    const b = byName.get("Provider B");
    const c = byName.get("Provider C");
    const knownTotal = [a, b, c].reduce((sum, p) => sum + (p ? parseUsd(p.cost) : 0), 0);
    const total = breakdownLegend.reduce((sum, p) => sum + parseUsd(p.cost), 0);
    const othersCost = Math.max(0, total - knownTotal);
    return [
      { name: "Provider A", color: a?.color ?? "var(--accent-base)", cost: a?.cost ?? "$0.00", value: a ? parseUsd(a.cost) : 0 },
      { name: "Provider B", color: b?.color ?? "#3b82f6", cost: b?.cost ?? "$0.00", value: b ? parseUsd(b.cost) : 0 },
      { name: "Provider C", color: c?.color ?? "#6366f1", cost: c?.cost ?? "$0.00", value: c ? parseUsd(c.cost) : 0 },
      { name: "Others", color: "rgba(148, 163, 184, 0.55)", cost: formatUsd(othersCost), value: othersCost },
    ];
  })();

  const donutSegments = (() => {
    const r = 40;
    const circumference = 2 * Math.PI * r;
    const base = [...providerList].sort((a, b) => {
      if (a.name === "Others" && b.name !== "Others") return 1;
      if (b.name === "Others" && a.name !== "Others") return -1;
      return b.value - a.value;
    });

    const total = base.reduce((sum, r) => sum + r.value, 0);
    const rawPercents = base.map((r) => (total > 0 ? (r.value / total) * 100 : 0));
    const roundedPercents: number[] = [];
    for (let i = 0; i < rawPercents.length; i++) {
      if (i === rawPercents.length - 1) {
        const used = roundedPercents.reduce((s, p) => s + p, 0);
        roundedPercents.push(Math.max(0, Math.round(100 - used)));
      } else {
        roundedPercents.push(Math.max(0, Math.round(rawPercents[i] ?? 0)));
      }
    }

    const labels = [];
    let accLen = 0;
    let accPercent = 0;
    for (let i = 0; i < base.length; i++) {
      const seg = base[i]!;
      const percent = roundedPercents[i] ?? 0;
      const len = (circumference * percent) / 100;
      const dashOffset = -accLen;
      const startDeg = -90 + accPercent * 3.6;
      const midDeg = startDeg + percent * 1.8;
      const rad = (midDeg * Math.PI) / 180;

      const rLine1 = r + 1;
      const rLine2 = r + 6;
      const rTextBase = r + 12;

      const x1 = 50 + rLine1 * Math.cos(rad);
      const y1 = 50 + rLine1 * Math.sin(rad);
      const x2Base = 50 + rLine2 * Math.cos(rad);
      const y2Base = 50 + rLine2 * Math.sin(rad);
      const xTextBase = 50 + rTextBase * Math.cos(rad);
      const yTextBase = 50 + rTextBase * Math.sin(rad);

      const textAnchor = Math.abs(xTextBase - 50) < 7 ? "middle" : xTextBase > 50 ? "start" : "end";

      labels.push({
        name: seg.name,
        color: seg.color,
        percent,
        value: seg.value,
        cost: seg.cost,
        len,
        dashOffset,
        x1,
        y1,
        x2: x2Base,
        y2: y2Base,
        xText: xTextBase,
        yText: yTextBase,
        textAnchor,
      });

      accLen += len;
      accPercent += percent;
    }

    labels.sort((a, b) => a.yText - b.yText);
    for (let i = 1; i < labels.length; i++) {
      const prev = labels[i - 1]!;
      const cur = labels[i]!;
      if (Math.abs(cur.yText - prev.yText) < 10) {
        cur.x2 = 50 + (r + 8) * Math.cos(Math.atan2(cur.y2 - 50, cur.x2 - 50));
        cur.y2 = 50 + (r + 8) * Math.sin(Math.atan2(cur.y2 - 50, cur.x2 - 50));
        cur.xText = 50 + (r + 16) * Math.cos(Math.atan2(cur.yText - 50, cur.xText - 50));
        cur.yText = 50 + (r + 16) * Math.sin(Math.atan2(cur.yText - 50, cur.xText - 50));
      }
    }

    return labels;
  })();

  function updateTooltipPos(event: MouseEvent) {
    const x = event.clientX + 12;
    const y = event.clientY + 12;
    tooltipX = Math.min(x, window.innerWidth - 160);
    tooltipY = Math.min(y, window.innerHeight - 96);
  }

  const trendData = [
    { label: "Day 1", valueFormatted: "$98.20" },
    { label: "Day 4", valueFormatted: "$112.35" },
    { label: "Day 7", valueFormatted: "$105.10" },
    { label: "Day 10", valueFormatted: "$134.40" },
    { label: "Day 13", valueFormatted: "$128.00" },
    { label: "Day 16", valueFormatted: "$162.75" },
    { label: "Day 19", valueFormatted: "$149.30" },
    { label: "Day 22", valueFormatted: "$171.90" },
    { label: "Day 25", valueFormatted: "$158.60" },
    { label: "Day 28", valueFormatted: "$189.15" },
    { label: "Day 30", valueFormatted: "$176.25" },
  ];

  function updateTrendHover(event: MouseEvent) {
    const el = event.currentTarget as HTMLElement | null;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const width = Math.max(1, rect.width);
    const mouseX = Math.min(Math.max(0, event.clientX - rect.left), width);
    const idx = Math.min(trendData.length - 1, Math.max(0, Math.round((mouseX / width) * (trendData.length - 1))));
    trendHover = trendData[idx] ?? null;
    const x = event.clientX + 12;
    const y = event.clientY + 12;
    trendTipX = Math.min(x, window.innerWidth - 160);
    trendTipY = Math.min(y, window.innerHeight - 72);
  }

  function getStatusColor(status: string) {
    if (status.includes("Ceeen") || status.includes("Success") || status === "Status") return "text-emerald-400 bg-emerald-400/10"; // Assuming "Status" is success for now or generic
    if (status.includes("Reded") || status.includes("Error") || status === "Failure") return "text-rose-400 bg-rose-400/10";
    return "text-slate-400 bg-slate-400/10";
  }
</script>

<div class="space-y-4 p-5">
  <!-- Row 1: KPIs -->
  <div class="grid grid-cols-6 gap-3">
    {#each kpis as kpi}
      <div 
        class="flex min-w-0 flex-col justify-between rounded-2xl border p-3 shadow-sm transition-all hover:-translate-y-0.5"
        style="
          background-color: var(--surface-1); 
          border-color: var(--border-subtle);
          box-shadow: var(--shadow-1);
          height: 110px;
        "
      >
        <div class="flex min-w-0 items-start justify-between gap-2">
          <div class="min-w-0 text-[11px] font-medium leading-[1.1] text-slate-400">
            {#if kpi.label === "Total Cost USD"}
              <div>Total Cost</div>
              <div>USD</div>
            {:else if kpi.label === "Total Requests"}
              <div>Total</div>
              <div>Requests</div>
            {:else if kpi.label === "Total Tokens"}
              <div>Total</div>
              <div>Tokens</div>
            {:else if kpi.label === "Avg Latency ms"}
              <div>Avg Latency</div>
              <div>ms</div>
            {:else if kpi.label === "Active Bridges count"}
              <div>Active Bridges</div>
              <div>count</div>
            {:else if kpi.label === "Success Rate %"}
              <div>Success Rate</div>
              <div>%</div>
            {:else}
              <div>{kpi.label}</div>
              <div>&nbsp;</div>
            {/if}
          </div>
          <span class="shrink-0 text-xs text-slate-500 opacity-60">
            {#if kpi.label === "Avg Latency ms"}
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <path d="M13 2L3 14h7l-1 8 12-14h-7l1-6z" />
              </svg>
            {:else}
              {kpi.icon}
            {/if}
          </span>
        </div>
        <div class="mt-2 text-xl font-semibold tracking-tight text-white">
          {kpi.value}
        </div>
      </div>
    {/each}
  </div>

  <!-- Row 2: Charts & Alerts -->
  <div class="grid grid-cols-3 gap-4">
    <!-- Cost Trend -->
    <div 
      class="col-span-1 rounded-2xl border p-4 shadow-sm"
      style="background-color: var(--surface-1); border-color: var(--border-subtle); height: 250px;"
    >
      <h3 class="mb-3 text-sm font-medium text-slate-300">Cost Trend (Last 30 Days)</h3>
      <div class="relative w-full" style="height: 172px;" role="img" aria-label="Cost trend chart" on:mousemove={updateTrendHover} on:mouseleave={() => (trendHover = null)}>
        <!-- Placeholder SVG Chart -->
        <svg viewBox="0 0 300 150" class="h-full w-full overflow-visible">
           <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stop-color="var(--accent-base)" stop-opacity="0.2" />
              <stop offset="100%" stop-color="var(--accent-base)" stop-opacity="0" />
            </linearGradient>
          </defs>
          <path 
            d="M0,120 L30,100 L60,110 L90,80 L120,90 L150,50 L180,70 L210,40 L240,60 L270,30 L300,50" 
            fill="none" 
            stroke="var(--accent-base)" 
            stroke-width="2"
            vector-effect="non-scaling-stroke"
          />
          <path 
            d="M0,120 L30,100 L60,110 L90,80 L120,90 L150,50 L180,70 L210,40 L240,60 L270,30 L300,50 V150 H0 Z" 
            fill="url(#gradient)" 
            stroke="none"
          />
        </svg>
      </div>
      <div class="mt-2 flex justify-between pb-2 text-[10px] text-slate-500">
        {#each trendTicks as t (t)}
          <div>{t}</div>
        {/each}
      </div>
    </div>

    <!-- Cost Breakdown -->
    <div 
      class="col-span-1 rounded-2xl border p-4 shadow-sm"
      style="background-color: var(--surface-1); border-color: var(--border-subtle); height: 250px;"
    >
      <h3 class="mb-3 text-sm font-medium text-slate-300">Cost Breakdown by Provider</h3>
      <div class="flex items-center justify-center" style="height: 150px;">
        <!-- Simple Donut Chart SVG -->
        <svg width="128" height="128" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="40" fill="none" stroke="#21262d" stroke-width="12" />
          {#each donutSegments.filter((s) => s.value > 0) as seg (seg.name)}
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke={seg.color}
              stroke-width="12"
              stroke-dasharray={`${seg.len} ${2 * Math.PI * 40}`}
              stroke-dashoffset={seg.dashOffset}
              transform="rotate(-90 50 50)"
              role="img"
              aria-label={seg.name}
              on:mouseenter={() => (hoveredSlice = { name: seg.name, percent: seg.percent, cost: seg.cost })}
              on:mousemove={(e) => updateTooltipPos(e)}
              on:mouseleave={() => (hoveredSlice = null)}
            />
          {/each}
          {#each donutSegments.filter((s) => s.value > 0 && s.percent >= 6) as seg (seg.name + '-leader')}
            <line x1={seg.x1} y1={seg.y1} x2={seg.x2} y2={seg.y2} stroke={seg.color} stroke-width="1" />
            <text x={seg.xText} y={seg.yText} text-anchor={seg.textAnchor} font-size="9" font-weight="600" fill={seg.color}>
              {seg.percent}%
            </text>
          {/each}
        </svg>
      </div>
      <div class="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1">
        {#each providerList as row (row.name)}
          <div class="flex min-w-0 items-center gap-2 text-[11px] text-slate-300">
            <span class="h-2 w-2 shrink-0 rounded-full" style={`background-color: ${row.color};`}></span>
            <span class="min-w-0 overflow-hidden text-ellipsis whitespace-nowrap">{row.name}</span>
          </div>
        {/each}
      </div>
    </div>

    <!-- Quick Health Alerts -->
    <div 
      class="col-span-1 rounded-2xl border p-4 shadow-sm"
      style="background-color: var(--surface-1); border-color: var(--border-subtle); height: 250px;"
    >
      <h3 class="mb-3 text-sm font-medium text-slate-300">Quick Health Alerts</h3>
      <div class="space-y-2">
        <div class="flex items-center gap-3 rounded-lg border border-red-900/30 bg-red-900/10 px-3 py-2">
          <span class="text-xs text-red-400">⚠️</span>
          <span class="text-xs font-medium text-red-200">High Latency on Provider X</span>
        </div>
        <div class="flex items-center gap-3 rounded-lg border border-amber-900/30 bg-amber-900/10 px-3 py-2">
          <span class="text-xs text-amber-400">⚡</span>
          <span class="text-xs font-medium text-amber-200">Budget threshold nearing</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Row 3: Tables -->
  <div class="grid grid-cols-3 gap-4">
    <!-- Recent Requests -->
    <div 
      class="col-span-2 flex flex-col rounded-2xl border p-4 shadow-sm"
      style="background-color: var(--surface-1); border-color: var(--border-subtle); height: 240px;"
    >
      <h3 class="mb-3 text-sm font-medium text-slate-300">Recent Requests</h3>
      <div class="flex-1 overflow-hidden rounded-lg border" style="border-color: var(--border-subtle);">
        <table class="w-full table-fixed text-left text-xs">
          <colgroup>
            <col style="width: clamp(140px, 26%, 190px);" />
            <col style="width: clamp(64px, 10%, 78px);" />
            <col style="width: clamp(110px, 18%, 140px);" />
            <col style="width: clamp(64px, 10%, 78px);" />
            <col style="width: clamp(92px, 16%, 120px);" />
            <col style="width: clamp(72px, 12%, 88px);" />
          </colgroup>
          <thead class="bg-slate-900/50 text-slate-400">
            <tr>
              <th class="px-3 py-2 font-medium whitespace-nowrap overflow-hidden text-ellipsis">Time</th>
              <th class="px-3 py-2 font-medium whitespace-nowrap overflow-hidden text-ellipsis">Status</th>
              <th class="px-3 py-2 font-medium whitespace-nowrap overflow-hidden text-ellipsis">Provider</th>
              <th class="px-3 py-2 font-medium text-right whitespace-nowrap overflow-hidden text-ellipsis">Latency</th>
              <th class="px-3 py-2 font-medium text-right whitespace-nowrap overflow-hidden text-ellipsis">Tokens In/Out</th>
              <th class="px-3 py-2 font-medium text-right whitespace-nowrap overflow-hidden text-ellipsis">Cost</th>
            </tr>
          </thead>
          <tbody class="divide-y" style="divide-color: var(--border-subtle);">
            {#each recentRequests.slice(0, RECENT_VISIBLE_ROWS) as req (req.time)}
              <tr class="group hover:bg-white/5">
                <td class="px-3 py-2 text-slate-300 whitespace-nowrap overflow-hidden text-ellipsis" title={req.time}>{req.time}</td>
                <td class="px-3 py-2">
                  <span class={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${getStatusColor(req.status)} whitespace-nowrap`}>
                    {req.status === "Reded" ? "Error" : "Success"}
                  </span>
                </td>
                <td class="px-3 py-2 text-slate-300 whitespace-nowrap overflow-hidden text-ellipsis">{req.provider}</td>
                <td class="px-3 py-2 text-right text-slate-300 whitespace-nowrap overflow-hidden text-ellipsis">{req.latency}</td>
                <td class="px-3 py-2 text-right text-slate-300 whitespace-nowrap overflow-hidden text-ellipsis">{req.tokens}</td>
                <td class="px-3 py-2 text-right text-slate-300 whitespace-nowrap overflow-hidden text-ellipsis">{req.cost}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
      <div class="mt-2 flex justify-end">
        <div class="flex items-center gap-1">
          <button type="button" class="grid h-7 w-7 place-items-center rounded-md border text-slate-300 hover:bg-white/5" style="border-color: var(--border-subtle);" aria-label="Previous page">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M15 18l-6-6 6-6" />
            </svg>
          </button>
          <button type="button" class="grid h-7 w-7 place-items-center rounded-md border text-slate-300 hover:bg-white/5" style="border-color: var(--border-subtle);" aria-label="Next page">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 18l6-6-6-6" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Top Expensive Requests -->
    <div 
      class="col-span-1 flex flex-col rounded-2xl border p-4 shadow-sm"
      style="background-color: var(--surface-1); border-color: var(--border-subtle); height: 240px;"
    >
      <h3 class="mb-3 text-sm font-medium text-slate-300">Top Expensive Requests</h3>
      <div class="flex-1 space-y-0 overflow-hidden">
        {#each topExpensive as item}
          <div class="flex items-center justify-between border-b py-2 last:border-0 hover:bg-white/5 px-2 -mx-2 rounded transition-colors" style="border-color: var(--border-subtle);">
            <div class="truncate text-xs text-slate-400 font-mono w-40">{item.id}</div>
            <div class="text-xs font-medium text-slate-200">{item.cost}</div>
          </div>
        {/each}
      </div>
    </div>
  </div>
</div>

{#if hoveredSlice}
  <div
    class="fixed pointer-events-none z-50 rounded-md border px-3 py-2 text-xs shadow-lg"
    style="
      left: {tooltipX}px;
      top: {tooltipY}px;
      background-color: var(--surface-1);
      border-color: var(--border-subtle);
      color: var(--text-primary);
    "
  >
    <div class="font-medium">{hoveredSlice.name}</div>
    <div style="color: var(--text-muted);">{hoveredSlice.percent}%</div>
    <div>{hoveredSlice.cost}</div>
  </div>
{/if}

{#if trendHover}
  <div
    class="fixed pointer-events-none z-50 rounded-md border px-3 py-2 text-xs shadow-lg"
    style="
      left: {trendTipX}px;
      top: {trendTipY}px;
      background-color: var(--surface-1);
      border-color: var(--border-subtle);
      color: var(--text-primary);
    "
  >
    <div class="font-medium">{trendHover.label}</div>
    <div style="color: var(--text-muted);">{trendHover.valueFormatted}</div>
  </div>
{/if}
