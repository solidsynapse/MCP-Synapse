<script lang="ts">
  import { onMount } from "svelte";

  type ProviderId = "all" | "openai" | "azure_openai" | "vertex" | "bedrock" | "huggingface" | "ollama";
  type DateRangeId = "all" | "1h" | "4h" | "24h" | "7d" | "30d";
  type SortId = "time_desc" | "time_asc" | "cost_desc" | "latency_desc";
  type TokenRangeId = "all" | "0_100" | "101_1000" | "1001_10000" | "10001_plus";
  type ModelOption = { id: string; label: string };

  const PROVIDERS: { id: ProviderId; label: string }[] = [
    { id: "all", label: "All" },
    { id: "openai", label: "OpenAI" },
    { id: "azure_openai", label: "Azure OpenAI" },
    { id: "vertex", label: "Vertex AI" },
    { id: "huggingface", label: "Hugging Face" },
    { id: "ollama", label: "Ollama" },
  ];

  const DATE_RANGES: { id: DateRangeId; label: string }[] = [
    { id: "all", label: "All time" },
    { id: "1h", label: "Last 1h" },
    { id: "4h", label: "Last 4h" },
    { id: "24h", label: "Last 24h" },
    { id: "7d", label: "Last 7d" },
    { id: "30d", label: "Last 30d" },
  ];

  const SORTS: { id: SortId; label: string }[] = [
    { id: "time_desc", label: "Time (newest)" },
    { id: "time_asc", label: "Time (oldest)" },
    { id: "cost_desc", label: "Cost (high->low)" },
    { id: "latency_desc", label: "Latency (high->low)" },
  ];

  const TOKEN_RANGES: { id: TokenRangeId; label: string }[] = [
    { id: "all", label: "All" },
    { id: "0_100", label: "0-100" },
    { id: "101_1000", label: "101-1,000" },
    { id: "1001_10000", label: "1,001-10,000" },
    { id: "10001_plus", label: "10,001+" },
  ];

  let {
    provider = $bindable("all"),
    dateRange = $bindable("24h"),
    sort = $bindable("time_desc"),
    showHistoryExtras = false,
    modelIdFilter = $bindable("all"),
    modelOptions = [],
    totalTokensRange = $bindable("all"),
  }: {
    provider?: ProviderId;
    dateRange?: DateRangeId;
    sort?: SortId;
    showHistoryExtras?: boolean;
    modelIdFilter?: string;
    modelOptions?: ModelOption[];
    totalTokensRange?: TokenRangeId;
  } = $props();

  type MenuKey = "provider" | "dateRange" | "modelId" | "totalTokensRange" | "sort";
  let rootEl = $state<HTMLElement | null>(null);
  let openMenu = $state<MenuKey | null>(null);
  let helperOpen = $state(false);

  function closeMenus() {
    openMenu = null;
  }

  function toggleMenu(key: MenuKey) {
    openMenu = openMenu === key ? null : key;
  }

  function labelForProvider(id: string) {
    return PROVIDERS.find((p) => p.id === id)?.label ?? id;
  }

  function labelForDateRange(id: string) {
    return DATE_RANGES.find((r) => r.id === id)?.label ?? id;
  }

  function labelForSort(id: string) {
    return SORTS.find((s) => s.id === id)?.label ?? id;
  }

  function labelForModel(id: string) {
    return modelOptions.find((o) => o.id === id)?.label ?? id;
  }

  function labelForTokenRange(id: string) {
    return TOKEN_RANGES.find((r) => r.id === id)?.label ?? id;
  }

  onMount(() => {
    const onPointerDown = (event: PointerEvent) => {
      const t = event.target as Node | null;
      if (openMenu == null) return;
      if (t && rootEl?.contains(t)) return;
      closeMenus();
    };

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      closeMenus();
    };

    window.addEventListener("pointerdown", onPointerDown, true);
    window.addEventListener("keydown", onKeyDown, true);
    return () => {
      window.removeEventListener("pointerdown", onPointerDown, true);
      window.removeEventListener("keydown", onKeyDown, true);
    };
  });

  const triggerClass = "ui-focus flex h-9 items-center justify-between gap-2 rounded-md border px-3 text-xs";
  const triggerStyle = "border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);";
  const menuStyle =
    "border-color: var(--border-subtle); background-color: var(--surface-2); border-radius: var(--radius-card); box-shadow: var(--shadow-2);";
</script>

<div class="ui-card ui-pad-md relative z-20 overflow-visible" bind:this={rootEl}>
  <div class="flex items-center gap-3">
    <div class="flex shrink-0 items-center gap-2">
      <div class="ui-title">Filters</div>
      <button
        type="button"
        class="ui-focus inline-flex h-5 w-5 items-center justify-center rounded-full border text-[11px] font-semibold transition-colors hover:bg-white/5"
        style="border-color: var(--border-subtle); color: var(--text-muted);"
        aria-label="Toggle filters helper"
        aria-expanded={helperOpen}
        on:click={() => (helperOpen = !helperOpen)}
      >
        ?
      </button>
    </div>
    <div class="ml-auto flex min-w-0 flex-1 items-center justify-end gap-2 whitespace-nowrap overflow-visible">
    <div class="relative">
      <button type="button" class={`${triggerClass} w-[122px]`} style={triggerStyle} aria-expanded={openMenu === "provider"} on:click={() => toggleMenu("provider")}>
        <span class="text-xs" style="color: var(--text-muted);">Provider</span>
        <span class="truncate">{labelForProvider(provider)}</span>
        <span class="text-[10px]" style="color: var(--text-muted);">v</span>
      </button>
      {#if openMenu === "provider"}
        <div class="absolute left-0 z-40 mt-2 max-h-[260px] w-[240px] overflow-y-auto border" style={menuStyle}>
          {#each PROVIDERS as p (p.id)}
            <button
              type="button"
              class="block w-full px-3 py-2 text-left text-xs transition-colors hover:bg-white/5"
              style={p.id === provider ? "color: var(--text-primary);" : "color: var(--text-muted);"}
              on:click={() => {
                provider = p.id;
                closeMenus();
              }}
            >
              {p.label}
            </button>
          {/each}
        </div>
      {/if}
    </div>

    <div class="relative">
      <button type="button" class={`${triggerClass} w-[132px]`} style={triggerStyle} aria-expanded={openMenu === "dateRange"} on:click={() => toggleMenu("dateRange")}>
        <span class="text-xs" style="color: var(--text-muted);">Date range</span>
        <span class="truncate">{labelForDateRange(dateRange)}</span>
        <span class="text-[10px]" style="color: var(--text-muted);">v</span>
      </button>
      {#if openMenu === "dateRange"}
        <div class="absolute left-0 z-40 mt-2 max-h-[260px] w-[240px] overflow-y-auto border" style={menuStyle}>
          {#each DATE_RANGES as r (r.id)}
            <button
              type="button"
              class="block w-full px-3 py-2 text-left text-xs transition-colors hover:bg-white/5"
              style={r.id === dateRange ? "color: var(--text-primary);" : "color: var(--text-muted);"}
              on:click={() => {
                dateRange = r.id;
                closeMenus();
              }}
            >
              {r.label}
            </button>
          {/each}
        </div>
      {/if}
    </div>

    {#if showHistoryExtras}
      <div class="relative">
        <button type="button" class={`${triggerClass} w-[152px]`} style={triggerStyle} aria-expanded={openMenu === "modelId"} on:click={() => toggleMenu("modelId")}>
          <span class="text-xs" style="color: var(--text-muted);">Model ID</span>
          <span class="truncate">{labelForModel(modelIdFilter)}</span>
          <span class="text-[10px]" style="color: var(--text-muted);">v</span>
        </button>
        {#if openMenu === "modelId"}
          <div class="absolute left-0 z-40 mt-2 max-h-[260px] w-[300px] overflow-y-auto border" style={menuStyle}>
            {#each modelOptions as opt (opt.id)}
              <button
                type="button"
                class="block w-full px-3 py-2 text-left text-xs transition-colors hover:bg-white/5"
                style={opt.id === modelIdFilter ? "color: var(--text-primary);" : "color: var(--text-muted);"}
                on:click={() => {
                  modelIdFilter = opt.id;
                  closeMenus();
                }}
              >
                {opt.label}
              </button>
            {/each}
          </div>
        {/if}
      </div>

      <div class="relative">
        <button type="button" class={`${triggerClass} w-[152px]`} style={triggerStyle} aria-expanded={openMenu === "totalTokensRange"} on:click={() => toggleMenu("totalTokensRange")}>
          <span class="text-xs" style="color: var(--text-muted);">Tokens Range</span>
          <span class="truncate">{labelForTokenRange(totalTokensRange)}</span>
          <span class="text-[10px]" style="color: var(--text-muted);">v</span>
        </button>
        {#if openMenu === "totalTokensRange"}
          <div class="absolute left-0 z-40 mt-2 max-h-[260px] w-[230px] overflow-y-auto border" style={menuStyle}>
            {#each TOKEN_RANGES as r (r.id)}
              <button
                type="button"
                class="block w-full px-3 py-2 text-left text-xs transition-colors hover:bg-white/5"
                style={r.id === totalTokensRange ? "color: var(--text-primary);" : "color: var(--text-muted);"}
                on:click={() => {
                  totalTokensRange = r.id;
                  closeMenus();
                }}
              >
                {r.label}
              </button>
            {/each}
          </div>
        {/if}
      </div>
    {/if}

    <div class="relative">
      <button type="button" class={`${triggerClass} w-[152px]`} style={triggerStyle} aria-expanded={openMenu === "sort"} on:click={() => toggleMenu("sort")}>
        <span class="text-xs" style="color: var(--text-muted);">Sort</span>
        <span class="truncate">{labelForSort(sort)}</span>
        <span class="text-[10px]" style="color: var(--text-muted);">v</span>
      </button>
      {#if openMenu === "sort"}
        <div class="absolute left-0 z-40 mt-2 max-h-[260px] w-[260px] overflow-y-auto border" style={menuStyle}>
          {#each SORTS as s (s.id)}
            <button
              type="button"
              class="block w-full px-3 py-2 text-left text-xs transition-colors hover:bg-white/5"
              style={s.id === sort ? "color: var(--text-primary);" : "color: var(--text-muted);"}
              on:click={() => {
                sort = s.id;
                closeMenus();
              }}
            >
              {s.label}
            </button>
          {/each}
        </div>
      {/if}
    </div>
    </div>
  </div>
  {#if helperOpen}
    <div class="mt-2 text-[11px]" style="color: var(--text-muted);">
      Filters affect visible rows. On History, the same filters are also used for CSV export.
    </div>
  {/if}
</div>

