<script lang="ts">
  import { onMount } from "svelte";

  type Opt = { id: string; label: string };

  let { label, options, value = $bindable("") } = $props<{ label: string; options: Opt[]; value: string }>();

  let rootEl = $state<HTMLElement | null>(null);
  let open = $state(false);

  function close() {
    open = false;
  }

  function toggle() {
    open = !open;
  }

  function labelFor(id: string) {
    return options.find((o: Opt) => o.id === id)?.label ?? id;
  }

  onMount(() => {
    const onPointerDown = (event: PointerEvent) => {
      if (!open) return;
      const t = event.target as Node | null;
      if (t && rootEl?.contains(t)) return;
      close();
    };

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      close();
    };

    window.addEventListener("pointerdown", onPointerDown, true);
    window.addEventListener("keydown", onKeyDown, true);
    return () => {
      window.removeEventListener("pointerdown", onPointerDown, true);
      window.removeEventListener("keydown", onKeyDown, true);
    };
  });

  const triggerClass = "ui-focus flex h-9 w-full items-center justify-between gap-2 rounded-md border px-3 text-xs";
  const triggerStyle = "border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);";
  const menuStyle =
    "border-color: var(--border-subtle); background-color: var(--surface-2); border-radius: var(--radius-card); box-shadow: var(--shadow-2);";
</script>

<div class="relative" bind:this={rootEl}>
  <div class="ui-subtitle">{label}</div>
  <button type="button" class={triggerClass} style={triggerStyle} aria-expanded={open} onclick={toggle}>
    <span class="truncate">{labelFor(value)}</span>
    <span class="text-[10px]" style="color: var(--text-muted);">▾</span>
  </button>

  {#if open}
    <div class="absolute left-0 z-10 mt-2 w-full overflow-hidden border" style={menuStyle}>
      {#each options as opt (opt.id)}
        <button
          type="button"
          class="block w-full px-3 py-2 text-left text-xs transition-colors hover:bg-white/5"
          style={opt.id === value ? "color: var(--text-primary);" : "color: var(--text-muted);"}
          onclick={() => {
            value = opt.id;
            close();
          }}
        >
          {opt.label}
        </button>
      {/each}
    </div>
  {/if}
</div>
