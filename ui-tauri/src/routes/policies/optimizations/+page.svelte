<script lang="ts">
  import { onMount } from "svelte";
  import { uiCacheGet, uiCacheSet, uiRunDeduped } from "$lib/ui_session";

  type BannerKind = "idle" | "info" | "success" | "danger";
  type DispatchError = { code?: string; message?: string };
  type OptimizationsState = {
    context_caching_enabled: boolean;
    request_dedup_enabled: boolean;
  };
  type OptimizationsResponse = {
    ok: boolean;
    status?: string;
    state?: OptimizationsState | null;
    error?: DispatchError | null;
    errors?: string[];
  };

  let contextCachingEnabled = $state(false);
  let requestDedupEnabled = $state(false);
  let saveInFlight = $state(false);
  let bannerKind = $state<BannerKind>("idle");
  let bannerText = $state("");
  let bannerTimer: ReturnType<typeof setTimeout> | null = null;
  const OPTIMIZATIONS_CACHE_KEY = "policies.optimizations.state";
  const OPTIMIZATIONS_CACHE_TTL_MS = 120000;

  function bannerClass(kind: BannerKind) {
    if (kind === "success") return "border-emerald-900/40 bg-emerald-400/10 text-emerald-200";
    if (kind === "danger") return "border-rose-900/40 bg-rose-500/10 text-rose-200";
    if (kind === "info") return "border-slate-700/60 bg-white/5 text-slate-200";
    return "border-slate-800 bg-transparent text-slate-200";
  }

  function setBanner(kind: BannerKind, text: string) {
    if (bannerTimer) {
      clearTimeout(bannerTimer);
      bannerTimer = null;
    }
    bannerKind = kind;
    bannerText = text;
    if (kind !== "idle" && text) {
      bannerTimer = setTimeout(() => {
        bannerKind = "idle";
        bannerText = "";
        bannerTimer = null;
      }, 3200);
    }
  }

  function dismissBanner() {
    if (bannerTimer) {
      clearTimeout(bannerTimer);
      bannerTimer = null;
    }
    bannerKind = "idle";
    bannerText = "";
  }

  function normalizeState(state: OptimizationsState | null | undefined): OptimizationsState {
    return {
      context_caching_enabled: Boolean(state?.context_caching_enabled),
      request_dedup_enabled: Boolean(state?.request_dedup_enabled),
    };
  }

  function applyState(state: OptimizationsState | null | undefined) {
    const normalized = normalizeState(state);
    contextCachingEnabled = normalized.context_caching_enabled;
    requestDedupEnabled = normalized.request_dedup_enabled;
  }

  function currentStatePayload(): OptimizationsState {
    return {
      context_caching_enabled: contextCachingEnabled,
      request_dedup_enabled: requestDedupEnabled,
    };
  }

  async function dispatchInvoke(promptPayload: Record<string, unknown>): Promise<OptimizationsResponse> {
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
      agentId: "policies",
      agent_id: "policies",
      prompt,
    }) as OptimizationsResponse;
  }

  async function loadOptimizationsState() {
    setBanner("idle", "");
    try {
      const result = await uiRunDeduped(OPTIMIZATIONS_CACHE_KEY, async () => await dispatchInvoke({ op: "policies.optimizations.get_state" }));
      if (!result.ok) {
        const code = result.error?.code ? `${result.error.code}: ` : "";
        const msg = result.error?.message || (result.errors || []).join("; ") || "request failed";
        setBanner("danger", `Optimizations load failed: ${code}${msg}`);
        return;
      }
      applyState(result.state);
      uiCacheSet(OPTIMIZATIONS_CACHE_KEY, result.state ?? null);
    } catch (err: any) {
      setBanner("danger", `Optimizations load failed: ${err?.message || String(err)}`);
    }
  }

  async function persistOptimizationsState(successMessage = "") {
    if (saveInFlight) return;
    saveInFlight = true;
    setBanner("idle", "");
    try {
      const result = await dispatchInvoke({ op: "policies.optimizations.set_state", state: currentStatePayload() });
      if (!result.ok) {
        const code = result.error?.code ? `${result.error.code}: ` : "";
        const msg = result.error?.message || (result.errors || []).join("; ") || "request failed";
        setBanner("danger", `Optimizations save failed: ${code}${msg}`);
        return;
      }
      applyState(result.state);
      uiCacheSet(OPTIMIZATIONS_CACHE_KEY, result.state ?? null);
      if (successMessage) {
        setBanner("success", successMessage);
      }
    } catch (err: any) {
      setBanner("danger", `Optimizations save failed: ${err?.message || String(err)}`);
    } finally {
      saveInFlight = false;
    }
  }

  function onToggleContextCaching(event: Event) {
    contextCachingEnabled = (event.currentTarget as HTMLInputElement).checked;
    void persistOptimizationsState("Context caching updated.");
  }

  function onToggleRequestDedup(event: Event) {
    requestDedupEnabled = (event.currentTarget as HTMLInputElement).checked;
    void persistOptimizationsState("Request de-duplication updated.");
  }

  onMount(() => {
    const cached = uiCacheGet<OptimizationsState | null>(OPTIMIZATIONS_CACHE_KEY, OPTIMIZATIONS_CACHE_TTL_MS);
    let refreshDelayMs = 0;
    if (cached) applyState(cached);
    if (cached) refreshDelayMs = 90;
    window.setTimeout(() => {
      void loadOptimizationsState();
    }, refreshDelayMs);
    return () => {
      if (bannerTimer) {
        clearTimeout(bannerTimer);
        bannerTimer = null;
      }
    };
  });
</script>

<div class="space-y-4 p-6">
  {#if bannerText}
    <div class={`rounded-md border px-3 py-2 text-xs ${bannerClass(bannerKind)}`}>
      <div class="flex items-center justify-between gap-2">
        <div class="min-w-0 truncate">{bannerText}</div>
        <button type="button" class="shrink-0 rounded border px-1.5 py-0.5 text-[10px] hover:bg-white/10" style="border-color: var(--border-subtle);" onclick={dismissBanner}>x</button>
      </div>
    </div>
  {/if}
  <div class="flex items-start justify-between gap-4">
    <div class="min-w-0">
      <div class="ui-subtitle">Configure persisted optimization toggles.</div>
      <div class="mt-1 text-[11px]" style="color: var(--text-muted);">Toggle effects are applied to new requests after state is saved.</div>
    </div>
  </div>

  <div class="grid gap-3 lg:grid-cols-2">
    <div class="ui-card ui-pad-md">
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <div class="ui-title">Context caching</div>
          <div class="ui-subtitle mt-1">Reduce repeated request assembly costs.</div>
        </div>
        <label class="flex items-center gap-2 text-xs" style="color: var(--text-primary);">
          <input
            type="checkbox"
            class="ui-focus h-4 w-4 rounded border"
            style="border-color: var(--border-subtle); background-color: var(--surface-2);"
            checked={contextCachingEnabled}
            disabled={saveInFlight}
            onchange={onToggleContextCaching}
          />
          <span>{contextCachingEnabled ? "On" : "Off"}</span>
        </label>
      </div>

      <div class="mt-3 text-xs" style="color: var(--text-muted);">
        When enabled, the system may reuse stable assembly results for identical prompts/personas to reduce compute and cost.
      </div>
    </div>

    <div class="ui-card ui-pad-md">
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <div class="ui-title">Request de-duplication</div>
          <div class="ui-subtitle mt-1">Coalesce identical requests in a short window.</div>
        </div>
        <label class="flex items-center gap-2 text-xs" style="color: var(--text-primary);">
          <input
            type="checkbox"
            class="ui-focus h-4 w-4 rounded border"
            style="border-color: var(--border-subtle); background-color: var(--surface-2);"
            checked={requestDedupEnabled}
            disabled={saveInFlight}
            onchange={onToggleRequestDedup}
          />
          <span>{requestDedupEnabled ? "On" : "Off"}</span>
        </label>
      </div>

      <div class="mt-3 text-xs" style="color: var(--text-muted);">
        When enabled, identical requests may be collapsed into a single in-flight execution to reduce load.
      </div>
    </div>
  </div>
</div>
