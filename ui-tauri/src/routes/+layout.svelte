<script lang="ts">
  import "../app.css";
  import ShortcutsModal from "$lib/components/ShortcutsModal.svelte";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { onMount } from "svelte";

  type LeafItem = { key: string; label: string; href: string; icon: string };
  type ParentItem = { key: string; label: string; href: string; icon: string; children: LeafItem[] };
  type NavItem = LeafItem | ParentItem;

  const NAV: NavItem[] = [
    { key: "dashboard", label: "Dashboard", href: "/dashboard", icon: "D" },
    { key: "connections", label: "Connections", href: "/connections", icon: "C" },
    {
      key: "usage",
      label: "Usage",
      href: "/usage/summary",
      icon: "U",
      children: [
        { key: "usage-summary", label: "Summary", href: "/usage/summary", icon: "S" },
        { key: "usage-history", label: "History", href: "/usage/history", icon: "H" },
      ],
    },
    {
      key: "policies",
      label: "Policies",
      href: "/policies/persona",
      icon: "P",
      children: [
        { key: "policies-persona", label: "Persona Lite", href: "/policies/persona", icon: "L" },
        { key: "policies-optimizations", label: "Optimizations", href: "/policies/optimizations", icon: "O" },
      ],
    },
    {
      key: "resilience",
      label: "Resilience",
      href: "/resilience/budget",
      icon: "R",
      children: [
        { key: "resilience-budget", label: "Budget Guards", href: "/resilience/budget", icon: "B" },
        { key: "resilience-interceptors", label: "Interceptors", href: "/resilience/interceptors", icon: "I" },
      ],
    },
  ];

  const SETTINGS: LeafItem = { key: "settings", label: "Settings", href: "/settings", icon: "\u2699" };

  function assertNavDepthMax1(items: NavItem[]) {
    for (const item of items) {
      if ("children" in item) {
        for (const child of item.children) {
          if ((child as unknown as { children?: unknown }).children != null) {
            throw new Error("nav_depth_exceeded");
          }
        }
      }
    }
  }
  assertNavDepthMax1(NAV);

  let sidebarCollapsed = $state(false);
  let navOpenByKey = $state<Record<string, boolean>>({ usage: true, policies: true, resilience: true });

  const pathname = $derived($page.url.pathname as string);
  const headerTitle = $derived(() => {
    if (pathname === "/dashboard") return "Dashboard";
    if (pathname === "/connections") return "Connections";
    if (pathname === "/settings") return "Settings";
    if (pathname.startsWith("/usage/")) return "Usage";
    if (pathname.startsWith("/policies/")) return "Policies";
    if (pathname.startsWith("/resilience/")) return "Resilience";
    return "MCP Synapse";
  });

  const COLLAPSED_ICON_PATHS: Record<string, string[]> = {
    dashboard: ["M4 4h7v7H4V4zm9 0h7v7h-7V4zM4 13h7v7H4v-7zm9 0h7v7h-7v-7z"],
    connections: ["M10 13a5 5 0 0 1 0-7l1.5-1.5a5 5 0 1 1 7 7L17 12", "M14 11a5 5 0 0 1 0 7L12.5 19.5a5 5 0 1 1-7-7L7 12"],
    usage: ["M3 19h18", "M6 16V9", "M11 16V5", "M16 16v-7", "M21 16V3"],
    policies: ["M12 3l7 4v6c0 5-3 9-7 11-4-2-7-6-7-11V7l7-4z"],
    resilience: ["M13 2L3 14h7l-1 8 12-14h-7l1-6z"],
    settings: ["M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z", "M19.4 15a7.9 7.9 0 0 0 .1-2l2-1.5-2-3.5-2.3.7a7.6 7.6 0 0 0-1.7-1L15 3h-6l-.5 2.7a7.6 7.6 0 0 0-1.7 1L4.5 6.5l-2 3.5 2 1.5a7.9 7.9 0 0 0 .1 2l-2 1.5 2 3.5 2.3-.7a7.6 7.6 0 0 0 1.7 1L9 21h6l.5-2.7a7.6 7.6 0 0 0 1.7-1l2.3.7 2-3.5-2-1.5z"],
  };

  function isActive(href: string) {
    if (href === "/") return pathname === "/";
    if (pathname === href) return true;
    return pathname.startsWith(href + "/");
  }

  function groupPrefixForHref(href: string) {
    const seg = href.split("/")[1] ?? "";
    return seg ? `/${seg}` : "/";
  }

  function isGroupActive(prefix: string) {
    if (prefix === "/") return pathname === "/";
    if (pathname === prefix) return true;
    return pathname.startsWith(prefix + "/");
  }

  function closeHelp(event: MouseEvent) {
    event.preventDefault();
    const el = event.currentTarget as HTMLElement | null;
    const details = el?.closest("details") as HTMLDetailsElement | null;
    if (details) details.open = false;
  }

  function formatTime(d: Date) {
    return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
  }

  let lastRefresh = $state(formatTime(new Date()));
  let refreshBusy = $state(false);
  let shortcutsOpen = $state(false);

  function triggerRefresh() {
    refreshBusy = true;
    lastRefresh = formatTime(new Date());
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("synapse:global-refresh"));
      window.setTimeout(() => {
        refreshBusy = false;
      }, 900);
    }
  }

  function openShortcuts() {
    shortcutsOpen = true;
  }

  function closeShortcuts() {
    shortcutsOpen = false;
  }

  function isEditableTarget(target: EventTarget | null): boolean {
    const el = target instanceof HTMLElement ? target : null;
    if (!el) return false;
    if (el.closest("input, textarea, select, [contenteditable='true'], [contenteditable=''], [contenteditable]")) return true;
    return false;
  }

  onMount(() => {
    const getHelpDetails = () => document.querySelector("header details") as HTMLDetailsElement | null;

    const onPointerDown = (event: PointerEvent) => {
      const details = getHelpDetails();
      if (!details?.open) return;
      const t = event.target as Node | null;
      if (t && details.contains(t)) return;
      details.open = false;
    };

    const onKeyDown = (event: KeyboardEvent) => {
      const key = String(event.key || "");
      const lower = key.toLowerCase();
      const mod = event.ctrlKey || event.metaKey;
      const typing = isEditableTarget(event.target);
      const currentPath = String(pathname || "");

      if (key === "Escape") {
        if (shortcutsOpen) {
          event.preventDefault();
          closeShortcuts();
          return;
        }
        const escapeEvent = new CustomEvent("synapse:shortcut-escape", { cancelable: true });
        window.dispatchEvent(escapeEvent);
        if (escapeEvent.defaultPrevented) {
          event.preventDefault();
          return;
        }
        const details = getHelpDetails();
        if (!details?.open) return;
        event.preventDefault();
        details.open = false;
        return;
      }

      if (mod && key === "/") {
        event.preventDefault();
        openShortcuts();
        return;
      }

      if (mod && lower === "r" && !typing) {
        event.preventDefault();
        triggerRefresh();
        return;
      }

      if (event.altKey && !mod && !typing) {
        if (lower === "d") {
          event.preventDefault();
          void goto("/dashboard");
          return;
        }
        if (lower === "c") {
          event.preventDefault();
          void goto("/connections");
          return;
        }
        if (lower === "u") {
          event.preventDefault();
          void goto("/usage/summary");
          return;
        }
        if (lower === "p") {
          event.preventDefault();
          void goto("/policies/persona");
          return;
        }
        if (lower === "b") {
          event.preventDefault();
          void goto("/resilience/budget");
          return;
        }
      }

      if (mod && lower === "n" && !typing && currentPath.startsWith("/connections")) {
        const newConnectionEvent = new CustomEvent("synapse:shortcut-new-connection", { cancelable: true });
        window.dispatchEvent(newConnectionEvent);
        if (newConnectionEvent.defaultPrevented) {
          event.preventDefault();
        }
        return;
      }

      if (mod && key === "Enter") {
        const primaryActionEvent = new CustomEvent("synapse:shortcut-primary-action", { cancelable: true });
        window.dispatchEvent(primaryActionEvent);
        if (primaryActionEvent.defaultPrevented) {
          event.preventDefault();
        }
      }
    };

    window.addEventListener("pointerdown", onPointerDown, true);
    window.addEventListener("keydown", onKeyDown, true);
    return () => {
      window.removeEventListener("pointerdown", onPointerDown, true);
      window.removeEventListener("keydown", onKeyDown, true);
    };
  });

  let { children } = $props();
</script>

<div class="h-screen overflow-hidden flex flex-col" style="background-color: var(--bg-base); color: var(--text-primary);">
  <div class="flex flex-1 overflow-hidden">
    <aside
      class={`flex h-full flex-col overflow-hidden border-r transition-all duration-200 ease-in-out ${sidebarCollapsed ? "sidebar-collapsed" : "sidebar-expanded"}`}
      style="
        width: {sidebarCollapsed ? '72px' : '260px'}; 
        border-color: var(--border-subtle); 
        background-color: var(--bg-base);
      "
    >
      <div
        class={`flex h-[56px] items-center justify-between border-b ${sidebarCollapsed ? "gap-1 px-2" : "gap-3 px-4"}`}
        style="border-color: var(--border-subtle);"
      >
        <div class={`flex min-w-0 shrink-0 items-center gap-3 ${sidebarCollapsed ? "" : "flex-1"}`}>
          <div 
            class="grid h-8 w-8 shrink-0 place-items-center rounded-md text-sm font-semibold"
            style="background: linear-gradient(135deg, var(--accent-base), #1a7f6c); color: #fff;"
          >
            M
          </div>
          {#if !sidebarCollapsed}
            <div class="min-w-0 truncate text-sm font-semibold tracking-wide">MCP Synapse</div>
          {/if}
        </div>
        <button
          type="button"
          class="grid h-7 w-7 place-items-center rounded-md text-xs hover:bg-white/5 text-slate-400"
          onclick={() => (sidebarCollapsed = !sidebarCollapsed)}
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {#if sidebarCollapsed}
            &gt;
          {:else}
            &lt;
          {/if}
        </button>
      </div>

      {#if sidebarCollapsed}
        <nav class="flex-1 overflow-y-auto overflow-x-hidden px-2 py-3 space-y-1">
          {#each NAV as item (item.key)}
            {@const active = isGroupActive(groupPrefixForHref(item.href))}
            <a
              href={item.href}
              data-sveltekit-preload-data="hover"
              class="collapsed-nav-item flex w-full items-center justify-center rounded-md py-2 transition-colors relative"
              style={active ? "background-color: var(--surface-1); color: #fff;" : "color: var(--text-muted);"}
              aria-label={item.label}
              title={item.label}
            >
              {#if active}
                <div class="absolute left-0 top-1/2 -translate-y-1/2 h-4 w-0.5 rounded-r-full" style="background-color: var(--accent-base);"></div>
              {/if}
              <svg
                viewBox="0 0 24 24"
                width="22"
                height="22"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                {#each COLLAPSED_ICON_PATHS[item.key] ?? ["M12 12h.01"] as d (d)}
                  <path d={d} />
                {/each}
              </svg>
            </a>
          {/each}
        </nav>
      {:else}
        <nav class="flex-1 overflow-hidden px-3 py-4 space-y-1">
          {#each NAV as item (item.key)}
            {#if "children" in item}
              <div class="mb-2">
                <button 
                  type="button"
                  class="flex w-full items-center justify-between px-2 py-1.5 text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:text-slate-300 bg-transparent border-0 p-0"
                  onclick={() => (navOpenByKey = { ...navOpenByKey, [item.key]: !(navOpenByKey[item.key] ?? true) })}
                >
                  <span class="flex min-w-0 items-center gap-2">
                    <svg
                      viewBox="0 0 24 24"
                      width="18"
                      height="18"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.8"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      class="shrink-0 opacity-70"
                    >
                      {#each COLLAPSED_ICON_PATHS[item.key] ?? ["M12 12h.01"] as d (d)}
                        <path d={d} />
                      {/each}
                    </svg>
                    <span class="min-w-0 truncate">{item.label}</span>
                  </span>
                  <span class="text-[10px]">{ (navOpenByKey[item.key] ?? true) ? '-' : '+' }</span>
                </button>

                {#if navOpenByKey[item.key] ?? true}
                  <div class="space-y-0.5">
                    {#each item.children as child (child.key)}
                      {@const active = isActive(child.href)}
                      <a
                        href={child.href}
                        data-sveltekit-preload-data="hover"
                        class="flex items-center rounded-md px-2 py-2 text-sm transition-colors relative group"
                        style={active 
                          ? "background-color: var(--surface-1); color: #fff;" 
                          : "color: var(--text-muted);"}
                      >
                        {#if active}
                          <div class="absolute left-0 top-1/2 -translate-y-1/2 h-4 w-0.5 rounded-r-full" style="background-color: var(--accent-base);"></div>
                        {/if}
                        <span class="truncate">{child.label}</span>
                      </a>
                    {/each}
                  </div>
                {/if}
              </div>
            {:else}
              {@const active = isActive(item.href)}
              <a
                href={item.href}
                data-sveltekit-preload-data="hover"
                class="flex min-w-0 items-center gap-3 rounded-md px-2 py-2 text-sm transition-colors relative group mb-1"
                style={active 
                  ? "background-color: var(--surface-1); color: #fff;" 
                  : "color: var(--text-muted);"}
              >
                {#if active}
                  <div class="absolute left-0 top-1/2 -translate-y-1/2 h-4 w-0.5 rounded-r-full" style="background-color: var(--accent-base);"></div>
                {/if}
                <svg
                  viewBox="0 0 24 24"
                  width="20"
                  height="20"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  class="shrink-0 opacity-70 group-hover:opacity-100"
                >
                  {#each COLLAPSED_ICON_PATHS[item.key] ?? ["M12 12h.01"] as d (d)}
                    <path d={d} />
                  {/each}
                </svg>
                <span class="truncate">{item.label}</span>
              </a>
            {/if}
          {/each}
        </nav>
      {/if}

      <div class="shrink-0 overflow-x-hidden px-3 pb-4">
        <div class="border-t pt-3" style="border-color: var(--border-subtle);">
          <a
            href={SETTINGS.href}
            data-sveltekit-preload-data="hover"
            class={`flex w-full rounded-md text-sm transition-colors relative group ${sidebarCollapsed ? "collapsed-nav-item items-center justify-center px-0 py-2" : "items-center gap-3 px-2 py-2"}`}
            style={isActive(SETTINGS.href) 
              ? "background-color: var(--surface-1); color: #fff;" 
              : "color: var(--text-muted);"}
            title={sidebarCollapsed ? SETTINGS.label : undefined}
            data-testid="settings-bottom"
          >
            {#if isActive(SETTINGS.href)}
              <div class="absolute left-0 top-1/2 -translate-y-1/2 h-4 w-0.5 rounded-r-full" style="background-color: var(--accent-base);"></div>
            {/if}
            {#if sidebarCollapsed}
              <svg
                viewBox="0 0 24 24"
                width="22"
                height="22"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                {#each COLLAPSED_ICON_PATHS.settings as d (d)}
                  <path d={d} />
                {/each}
              </svg>
            {:else}
              <svg
                viewBox="0 0 24 24"
                width="18"
                height="18"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="shrink-0 opacity-70 group-hover:opacity-100"
              >
                {#each COLLAPSED_ICON_PATHS.settings as d (d)}
                  <path d={d} />
                {/each}
              </svg>
              <span class="truncate">{SETTINGS.label}</span>
            {/if}
          </a>
        </div>
      </div>
    </aside>

    <div class="flex min-w-0 flex-1 flex-col overflow-hidden">
      <header 
        class="flex shrink-0 items-center border-b"
        style="height: 56px; border-color: var(--border-subtle); background-color: var(--bg-base);"
      >
        <div class="flex w-full items-center justify-between gap-4 px-6">
          <div class="min-w-0 truncate text-sm font-medium text-slate-400">{headerTitle()}</div>
          <div class="flex items-center gap-3">
            <button
              type="button"
              class="grid h-8 w-8 place-items-center rounded-md border text-slate-300 transition-colors hover:bg-white/5"
              style="border-color: var(--border-subtle);"
              aria-label="Refresh"
              onclick={triggerRefresh}
            >
              <svg
                viewBox="0 0 24 24"
                width="18"
                height="18"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
                class={refreshBusy ? "animate-spin" : ""}
              >
                <path d="M21 12a9 9 0 1 1-2.6-6.4" />
                <path d="M21 3v6h-6" />
              </svg>
            </button>
            <details class="relative group">
              <summary
                class="cursor-pointer list-none rounded-md border px-3 py-1.5 text-xs font-medium transition-colors hover:bg-white/5"
                style="border-color: var(--border-subtle); color: var(--text-primary);"
              >
                Help
              </summary>
              <div
                class="absolute right-0 mt-2 w-40 overflow-hidden rounded-lg border shadow-xl z-50"
                style="background-color: var(--surface-1); border-color: var(--border-subtle);"
              >
                <a href="#docs" class="block w-full px-4 py-2 text-left text-xs hover:bg-white/5 transition-colors text-slate-300 hover:text-white" onclick={closeHelp}>
                  Docs
                </a>
                <a href="#feedback" class="block w-full px-4 py-2 text-left text-xs hover:bg-white/5 transition-colors text-slate-300 hover:text-white" onclick={closeHelp}>
                  Feedback
                </a>
                <a href="#about" class="block w-full px-4 py-2 text-left text-xs hover:bg-white/5 transition-colors text-slate-300 hover:text-white" onclick={closeHelp}>
                  About
                </a>
              </div>
            </details>
          </div>
        </div>
      </header>

      <main class="min-w-0 flex-1 overflow-y-auto">
        {@render children?.()}
      </main>
    </div>
  </div>

  <footer
    class="flex shrink-0 items-center justify-between border-t px-4"
    style="height: 30px; border-color: var(--border-subtle); color: var(--text-muted); font-size: 11px;"
  >
    <div>Solid Synapse (c) 2026</div>
    <div>Last refresh: {lastRefresh}</div>
  </footer>
</div>
<ShortcutsModal open={shortcutsOpen} onClose={closeShortcuts} />

<style>
  .sidebar-collapsed .collapsed-nav-item:focus-visible {
    outline: 2px solid rgba(39, 201, 169, 0.55);
    outline-offset: 2px;
  }
</style>
