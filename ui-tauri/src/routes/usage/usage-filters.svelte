<script lang="ts">
  import { onMount } from "svelte";

  type ProviderId = "all" | "openai" | "azure_openai" | "vertex" | "bedrock" | "huggingface" | "ollama";
  type DateRangeId = "all" | "1h" | "4h" | "24h" | "7d" | "30d";
  type SortId = "time_desc" | "time_asc" | "cost_desc" | "latency_desc";

  const PROVIDERS: { id: ProviderId; label: string }[] = [
    { id: "all", label: "All" },
    { id: "openai", label: "OpenAI" },
    { id: "azure_openai", label: "Azure OpenAI" },
    { id: "vertex", label: "Vertex AI" },
    { id: "bedrock", label: "Bedrock" },
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
    { id: "cost_desc", label: "Cost (high→low)" },
    { id: "latency_desc", label: "Latency (high→low)" },
  ];

  let { provider = $bindable("all"), dateRange = $bindable("24h"), sort = $bindable("time_desc") } = $props();

  type MenuKey = "provider" | "dateRange" | "sort";
  let rootEl = $state<HTMLElement | null>(null);
  let openMenu = $state<MenuKey | null>(null);

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

<div class="ui-card ui-pad-md flex flex-wrap items-center gap-3" bind:this={rootEl}>
  <div class="ui-title">Filters</div>
  <div class="flex flex-wrap items-center gap-3">
    <div class="relative">
      <button type="button" class={triggerClass} style={triggerStyle} aria-expanded={openMenu === "provider"} onclick={() => toggleMenu("provider")}>
        <span class="text-xs" style="color: var(--text-muted);">Provider</span>
        <span class="truncate">{labelForProvider(provider)}</span>
        <span class="text-[10px]" style="color: var(--text-muted);">▾</span>
      </button>
      {#if openMenu === "provider"}
        <div class="absolute left-0 z-10 mt-2 w-[240px] overflow-hidden border" style={menuStyle}>
          {#each PROVIDERS as p (p.id)}
            <button
              type="button"
              class="block w-full px-3 py-2 text-left text-xs transition-colors hover:bg-white/5"
              style={p.id === provider ? "color: var(--text-primary);" : "color: var(--text-muted);"}
              onclick={() => {
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
      <button type="button" class={triggerClass} style={triggerStyle} aria-expanded={openMenu === "dateRange"} onclick={() => toggleMenu("dateRange")}>
        <span class="text-xs" style="color: var(--text-muted);">Date range</span>
        <span class="truncate">{labelForDateRange(dateRange)}</span>
        <span class="text-[10px]" style="color: var(--text-muted);">▾</span>
      </button>
      {#if openMenu === "dateRange"}
        <div class="absolute left-0 z-10 mt-2 w-[240px] overflow-hidden border" style={menuStyle}>
          {#each DATE_RANGES as r (r.id)}
            <button
              type="button"
              class="block w-full px-3 py-2 text-left text-xs transition-colors hover:bg-white/5"
              style={r.id === dateRange ? "color: var(--text-primary);" : "color: var(--text-muted);"}
              onclick={() => {
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

    <div class="relative">
      <button type="button" class={triggerClass} style={triggerStyle} aria-expanded={openMenu === "sort"} onclick={() => toggleMenu("sort")}>
        <span class="text-xs" style="color: var(--text-muted);">Sort</span>
        <span class="truncate">{labelForSort(sort)}</span>
        <span class="text-[10px]" style="color: var(--text-muted);">▾</span>
      </button>
      {#if openMenu === "sort"}
        <div class="absolute left-0 z-10 mt-2 w-[260px] overflow-hidden border" style={menuStyle}>
          {#each SORTS as s (s.id)}
            <button
              type="button"
              class="block w-full px-3 py-2 text-left text-xs transition-colors hover:bg-white/5"
              style={s.id === sort ? "color: var(--text-primary);" : "color: var(--text-muted);"}
              onclick={() => {
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
