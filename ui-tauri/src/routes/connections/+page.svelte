<script lang="ts">
  import { onMount } from "svelte";

  import { invoke } from "@tauri-apps/api/core";

  type Connection = {
    id: string;
    name: string;
    status: "running" | "stopped";
    providerId: ProviderId;
    modelId: string;
    location: "local" | "lan" | "remote";
    endpoint: string;
    credentialsPath?: string;
    updatedAtLabel: string;
    tags: string[];
    configText: string;
  };

  type ProviderId = "openai" | "azure_openai" | "vertex" | "bedrock" | "huggingface" | "ollama";

  // STUB: local mock connections for UI replication only (NO WIRING).
  const STUB_CONNECTIONS: Connection[] = [
    {
      id: "conn_local_runtime_a",
      name: "Local Runtime A",
      status: "running",
      providerId: "ollama",
      modelId: "model-alpha",
      location: "local",
      endpoint: "LOCALHOST_11434",
      updatedAtLabel: "Today, 09:14:02",
      tags: ["local", "llm"],
      configText: JSON.stringify({ connection_name: "Local Runtime A", provider_id: "ollama", model_id: "model-alpha", endpoint: "LOCALHOST_11434" }, null, 2),
    },
    {
      id: "conn_lan_runtime_b",
      name: "LAN Runtime B",
      status: "stopped",
      providerId: "ollama",
      modelId: "model-beta",
      location: "lan",
      endpoint: "LAN_HOST_1234",
      updatedAtLabel: "Yesterday, 18:42:10",
      tags: ["lan"],
      configText: JSON.stringify({ connection_name: "LAN Runtime B", provider_id: "ollama", model_id: "model-beta", endpoint: "LAN_HOST_1234" }, null, 2),
    },
    {
      id: "conn_remote_proxy",
      name: "Remote Proxy (Staging)",
      status: "running",
      providerId: "openai",
      modelId: "model-gamma",
      location: "remote",
      endpoint: "STAGING_ENDPOINT",
      updatedAtLabel: "Today, 08:03:18",
      tags: ["remote", "staging"],
      configText: JSON.stringify({ connection_name: "Remote Proxy (Staging)", provider_id: "openai", model_id: "model-gamma", endpoint: "STAGING_ENDPOINT" }, null, 2),
    },
    {
      id: "conn_local_dev",
      name: "Local Dev Runtime",
      status: "stopped",
      providerId: "ollama",
      modelId: "mock:model",
      location: "local",
      endpoint: "DEV_RUNTIME_5055",
      updatedAtLabel: "Today, 07:55:41",
      tags: ["local", "dev"],
      configText: JSON.stringify({ connection_name: "Local Dev Runtime", provider_id: "ollama", model_id: "mock:model", endpoint: "DEV_RUNTIME_5055" }, null, 2),
    },
  ];

  let connections = $state<Connection[]>([]);
  let pageStatus = $state<"idle" | "loading" | "ready" | "error">("idle");
  let busyById = $state<Record<string, boolean>>({});

  let query = $state("");
  let statusFilter = $state<"all" | "running" | "stopped">("all");

  type BannerKind = "idle" | "info" | "success" | "danger";
  let bannerKind = $state<BannerKind>("idle");
  let bannerText = $state("");

  let detailsOpen = $state(false);
  let detailsId = $state<string | null>(null);

  let deleteConfirmOpen = $state(false);
  let deleteConfirmId = $state<string | null>(null);

  let newWizardOpen = $state(false);
  type ProviderOption = { id: ProviderId; label: string };
  const PROVIDERS: ProviderOption[] = [
    { id: "openai", label: "OpenAI" },
    { id: "azure_openai", label: "Azure OpenAI" },
    { id: "vertex", label: "Vertex AI" },
    { id: "bedrock", label: "Bedrock" },
    { id: "huggingface", label: "Hugging Face" },
    { id: "ollama", label: "Ollama" },
  ];

  let newWizardProvider = $state<ProviderId | null>(null);
  let providerQuery = $state("");
  let providerMenuOpen = $state(false);
  let newWizardName = $state("");
  let newWizardValues = $state<Record<string, string>>({});
  let nextStubId = $state(1);

  const providerOptions = $derived(() => {
    const q = providerQuery.trim().toLowerCase();
    if (!q) return PROVIDERS;
    return PROVIDERS.filter((p) => p.label.toLowerCase().includes(q) || p.id.toLowerCase().includes(q));
  });

  function providerLabel(id: ProviderId | null) {
    if (!id) return "";
    return PROVIDERS.find((p) => p.id === id)?.label ?? id;
  }

  function openProviderPicker() {
    providerMenuOpen = true;
  }

  function closeProviderPicker() {
    providerMenuOpen = false;
  }

  function selectProvider(id: ProviderId) {
    newWizardProvider = id;
    providerQuery = providerLabel(id);
    providerMenuOpen = false;
  }

  const filtered = $derived(() => {
    const q = query.trim().toLowerCase();
    return connections
      .filter((c) => (statusFilter === "all" ? true : c.status === statusFilter))
      .filter((c) => {
        if (!q) return true;
        const hay = `${c.name} ${c.modelId} ${c.endpoint} ${c.location} ${c.tags.join(" ")}`.toLowerCase();
        return hay.includes(q);
      });
  });

  const stats = $derived(() => {
    const total = connections.length;
    const running = connections.filter((c) => c.status === "running").length;
    const stopped = total - running;
    return { total, running, stopped };
  });

  function badgeClassForStatus(status: Connection["status"]) {
    if (status === "running") return "text-emerald-200 bg-emerald-400/10";
    return "text-slate-300 bg-white/5";
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

  async function simulateRefresh() {
    pageStatus = "loading";
    setBanner("idle", "");
    connections = STUB_CONNECTIONS;
    pageStatus = "ready";
  }

  async function toggleConnection(connectionId: string) {
    busyById = { ...busyById, [connectionId]: true };
    setBanner("idle", "");
    let nextStatus: Connection["status"] | null = null;
    connections = connections.map((c) => {
      if (c.id !== connectionId) return c;
      nextStatus = c.status === "running" ? "stopped" : "running";
      return { ...c, status: nextStatus };
    });
    if (nextStatus === "running") setBanner("success", "Started (stub).");
    if (nextStatus === "stopped") setBanner("danger", "Stopped (stub).");
    busyById = { ...busyById, [connectionId]: false };
  }

  async function testConnection(connectionId: string) {
    busyById = { ...busyById, [connectionId]: true };
    setBanner("idle", "");
    try {
      const prompt = JSON.stringify({ dry_run: true });
      const result = await invoke("dispatch_execute_request_v1", {
        agentId: connectionId,
        prompt: prompt,
      }) as { ok: boolean; status: string; text?: string; dry_run_data?: any; error?: { message: string } };

      if (result.ok && result.dry_run_data) {
        const data = result.dry_run_data;
        setBanner("success", `Dry-run OK: ${data.provider}/${data.model_id} (ID: ${data.request_id})`);
      } else {
        setBanner("danger", `Dry-run failed: ${result.error?.message || result.status}`);
      }
    } catch (err: any) {
      setBanner("danger", `Dispatch error: ${err.message || String(err)}`);
    } finally {
      busyById = { ...busyById, [connectionId]: false };
    }
  }

  async function copyConnectionConfig(connectionId: string) {
    busyById = { ...busyById, [connectionId]: true };
    setBanner("idle", "");

    const c = connections.find((x) => x.id === connectionId);
    const text = c?.configText ?? "";
    if (!text) {
      setBanner("danger", "No config available (stub).");
      busyById = { ...busyById, [connectionId]: false };
      return;
    }

    try {
      await navigator.clipboard.writeText(text);
      setBanner("success", "Config copied (stub).");
    } catch {
      const el = document.createElement("textarea");
      el.value = text;
      el.style.position = "fixed";
      el.style.left = "-9999px";
      document.body.appendChild(el);
      el.focus();
      el.select();
      document.execCommand("copy");
      document.body.removeChild(el);
      setBanner("success", "Config copied (stub).");
    } finally {
      busyById = { ...busyById, [connectionId]: false };
    }
  }

  function resetFilters() {
    query = "";
    statusFilter = "all";
  }

  function openDetails(connectionId: string) {
    detailsId = connectionId;
    detailsOpen = true;
  }

  function closeDetails() {
    detailsOpen = false;
    detailsId = null;
  }

  function openDeleteConfirm(connectionId: string) {
    deleteConfirmId = connectionId;
    deleteConfirmOpen = true;
  }

  function closeDeleteConfirm() {
    deleteConfirmOpen = false;
    deleteConfirmId = null;
  }

  async function confirmDelete() {
    const id = deleteConfirmId;
    if (!id) return;
    closeDeleteConfirm();
    busyById = { ...busyById, [id]: true };
    setBanner("idle", "");
    connections = connections.filter((c) => c.id !== id);
    busyById = { ...busyById, [id]: false };
    setBanner("danger", "Deleted (stub).");
    if (detailsId === id) closeDetails();
  }

  function openNewWizard() {
    newWizardOpen = true;
    newWizardProvider = null;
    providerQuery = "";
    providerMenuOpen = false;
    newWizardName = "";
    newWizardValues = {};
  }

  function closeNewWizard() {
    newWizardOpen = false;
  }

  function updateWizardField(fieldKey: string, value: string) {
    newWizardValues = { ...newWizardValues, [fieldKey]: value };
  }

  async function submitNewConnection() {
    const providerId = newWizardProvider;
    if (!providerId) {
      setBanner("danger", "Choose a provider (stub).");
      return;
    }

    const connectionName = (newWizardName ?? "").trim();
    const modelId = (newWizardValues.model_id ?? "").trim();
    const endpoint = (newWizardValues.endpoint ?? "").trim();
    const credentialsPath = (newWizardValues.credentials_path ?? "").trim();

    if (!connectionName || !modelId) {
      setBanner("danger", "Provide connection name and model ID (stub).");
      return;
    }

    const id = `conn_stub_${nextStubId}`;
    nextStubId += 1;

    const config: Record<string, unknown> = { connection_name: connectionName, provider_id: providerId, model_id: modelId };
    if (endpoint) config.endpoint = endpoint;
    if (credentialsPath) config.credentials_path = credentialsPath;

    const row: Connection = {
      id,
      name: connectionName,
      status: "stopped",
      providerId: providerId,
      modelId,
      location: "remote",
      endpoint: endpoint || "",
      credentialsPath: credentialsPath || undefined,
      updatedAtLabel: "Just now",
      tags: [providerId, "stub"],
      configText: JSON.stringify(config, null, 2),
    };

    busyById = { ...busyById, [id]: true };
    setBanner("idle", "");
    connections = [row, ...connections];
    busyById = { ...busyById, [id]: false };
    closeNewWizard();
    setBanner("success", "Created connection (stub).");
  }

  onMount(() => {
    simulateRefresh();
  });
</script>

<div class="space-y-4 p-6">
  <div class="flex items-start justify-between gap-4">
    <div class="min-w-0">
      <div class="ui-subtitle mt-1">Manage runtimes and configs (UI only; stubbed data).</div>
    </div>
    <div class="flex shrink-0 items-center gap-2">
      <button
        type="button"
        class="ui-focus rounded-md border px-5 py-2.5 text-sm font-semibold transition-colors"
        style="
          border-color: rgba(39, 201, 169, 0.55);
          background: radial-gradient(140% 140% at 30% 0%, rgba(39, 201, 169, 0.25) 0%, rgba(39, 201, 169, 0.06) 55%, transparent 100%);
          color: var(--text-primary);
          box-shadow: var(--shadow-1);
        "
        onclick={openNewWizard}
      >
        + New Connection
      </button>
    </div>
  </div>

  <div class={`ui-card ui-pad-sm border ${bannerClass(bannerKind)}`} style="height: 40px;">
    <div class="flex h-full items-center justify-between gap-3">
      <div class="min-w-0">
        {#if bannerText}
          <div class="truncate text-xs font-medium">{bannerText}</div>
        {:else}
          <div class="truncate text-xs" style="color: var(--text-muted);"> </div>
        {/if}
      </div>
      <div class="shrink-0 text-[10px]" style="color: var(--text-muted);">UI-only</div>
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-[minmax(0,2fr),minmax(0,3fr)] gap-3">
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <div class="ui-card ui-pad-md">
        <div class="ui-subtitle">Total</div>
        <div class="mt-2 text-xl font-semibold tracking-tight">{stats().total}</div>
      </div>
      <div class="ui-card ui-card--glow ui-pad-md">
        <div class="ui-subtitle">Running</div>
        <div class="mt-2 text-xl font-semibold tracking-tight">{stats().running}</div>
      </div>
      <div
        class="ui-card ui-pad-md"
        style="background-image: radial-gradient(120% 120% at 30% 0%, rgba(244, 63, 94, 0.12) 0%, transparent 55%);"
      >
        <div class="ui-subtitle">Stopped</div>
        <div class="mt-2 text-xl font-semibold tracking-tight">{stats().stopped}</div>
      </div>
    </div>

    <div class="ui-card ui-pad-md">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex min-w-0 items-center gap-2">
          <div class="ui-title">Filters</div>
          <div class="ui-pill text-slate-300 bg-white/5">{filtered().length} shown</div>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <label class="sr-only" for="connections-query">Search</label>
          <input
            id="connections-query"
            class="ui-focus h-9 w-[240px] min-w-[180px] flex-1 rounded-md border px-3 text-xs"
            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
            placeholder="Search…"
            bind:value={query}
          />
          <label class="sr-only" for="connections-status">Status</label>
          <select
            id="connections-status"
            class="ui-focus h-9 rounded-md border px-3 text-xs"
            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
            bind:value={statusFilter}
          >
            <option value="all">All</option>
            <option value="running">Running</option>
            <option value="stopped">Stopped</option>
          </select>
          <button
            type="button"
            class="ui-focus h-9 rounded-md border px-3 text-xs font-medium transition-colors hover:bg-white/5"
            style="border-color: var(--border-subtle); color: var(--text-primary); background-color: transparent;"
            onclick={resetFilters}
          >
            Reset filters
          </button>
        </div>
      </div>
    </div>
  </div>

  <div class="ui-card ui-pad-md">
    <div class="flex items-center justify-between gap-3">
      <div class="ui-title">Connection list</div>
      <div class="ui-subtitle">Click a row to view details (modal).</div>
    </div>

    <div class="mt-3 overflow-hidden rounded-lg border" style="border-color: var(--border-subtle);">
      <table class="ui-table table-fixed text-left text-xs">
        <colgroup>
          <col style="width: clamp(160px, 28%, 260px);" />
          <col style="width: clamp(90px, 12%, 110px);" />
          <col style="width: clamp(240px, 38%, 420px);" />
          <col style="width: clamp(180px, 24%, 300px);" />
        </colgroup>
        <thead style="background-color: rgba(240, 246, 252, 0.04); color: var(--text-muted);">
          <tr>
            <th class="px-3 py-2 font-medium whitespace-nowrap overflow-hidden text-ellipsis">Name</th>
            <th class="px-3 py-2 font-medium whitespace-nowrap overflow-hidden text-ellipsis">Status</th>
            <th class="px-3 py-2 font-medium whitespace-nowrap overflow-hidden text-ellipsis">Target</th>
            <th class="px-3 py-2 font-medium text-right whitespace-nowrap overflow-hidden text-ellipsis">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y" style="divide-color: var(--border-subtle);">
          {#if pageStatus === "loading"}
            {#each Array.from({ length: 4 }) as _, i (i)}
              <tr>
                <td class="px-3 py-3">
                  <div class="h-3 w-40 rounded bg-white/10 animate-pulse"></div>
                </td>
                <td class="px-3 py-3">
                  <div class="h-5 w-20 rounded-full bg-white/10 animate-pulse"></div>
                </td>
                <td class="px-3 py-3">
                  <div class="h-3 w-72 rounded bg-white/10 animate-pulse"></div>
                </td>
                <td class="px-3 py-3">
                  <div class="ml-auto h-7 w-40 rounded bg-white/10 animate-pulse"></div>
                </td>
              </tr>
            {/each}
          {:else if pageStatus === "ready" && filtered().length === 0}
            <tr>
              <td class="px-3 py-6" colspan="4">
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <div class="ui-title">No connections found</div>
                    <div class="ui-subtitle mt-1">Adjust filters or create a new connection.</div>
                  </div>
                  <button
                    type="button"
                    class="ui-focus rounded-md border px-3 py-2 text-xs font-medium transition-colors hover:bg-white/5"
                    style="border-color: var(--border-subtle); color: var(--text-primary); background-color: transparent;"
                    onclick={resetFilters}
                  >
                    Reset filters
                  </button>
                </div>
              </td>
            </tr>
          {:else if pageStatus === "ready"}
            {#each filtered() as c (c.id)}
              <tr
                class="ui-row-hover cursor-pointer"
                onclick={() => openDetails(c.id)}
              >
                <td class="px-3 py-3">
                  <div class="flex min-w-0 items-center gap-2">
                    <div class="min-w-0">
                      <div class="truncate font-medium" style="color: var(--text-primary);">{c.name}</div>
                      <div class="truncate ui-subtitle mt-0.5">{c.modelId} • {c.location}</div>
                    </div>
                  </div>
                </td>
                <td class="px-3 py-3">
                  <span class={`ui-pill ${badgeClassForStatus(c.status)}`}>{c.status === "running" ? "Running" : "Stopped"}</span>
                </td>
                <td class="px-3 py-3">
                  <div class="truncate" style="color: var(--text-primary);">{c.endpoint || "—"}</div>
                  <div class="ui-subtitle mt-0.5">Updated: {c.updatedAtLabel}</div>
                </td>
                <td class="px-3 py-3">
                  <div class="flex items-center justify-end gap-1.5">
                    <button
                      type="button"
                      class={`ui-focus h-7 rounded-md border px-2 text-[11px] font-medium transition-colors ${
                        c.status === "running"
                          ? "border-rose-900/50 bg-rose-500/10 text-rose-200 hover:bg-rose-500/15"
                          : "border-emerald-900/50 bg-emerald-400/10 text-emerald-200 hover:bg-emerald-400/15"
                      }`}
                      disabled={busyById[c.id] === true}
                      onclick={(e) => {
                        e.stopPropagation();
                        toggleConnection(c.id);
                      }}
                    >
                      {c.status === "running" ? "Stop" : "Start"}
                    </button>
                    <button
                      type="button"
                      class="ui-focus h-7 rounded-md border border-slate-700/60 bg-white/5 px-2 text-[11px] font-medium text-slate-200 transition-colors hover:bg-white/10"
                      disabled={busyById[c.id] === true}
                      onclick={(e) => {
                        e.stopPropagation();
                        testConnection(c.id);
                      }}
                    >
                      Test
                    </button>
                    <button
                      type="button"
                      class="ui-focus h-7 rounded-md border border-slate-700/60 bg-white/5 px-2 text-[11px] font-medium text-slate-200 transition-colors hover:bg-white/10"
                      disabled={busyById[c.id] === true}
                      onclick={(e) => {
                        e.stopPropagation();
                        copyConnectionConfig(c.id);
                      }}
                    >
                      Copy <span class="hidden xl:inline">Config</span>
                    </button>
                    <button
                      type="button"
                      class="ui-focus h-7 rounded-md border border-rose-900/60 bg-rose-500/10 px-2 text-[11px] font-medium text-rose-200 transition-colors hover:bg-rose-500/15"
                      disabled={busyById[c.id] === true}
                      onclick={(e) => {
                        e.stopPropagation();
                        openDeleteConfirm(c.id);
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            {/each}
          {:else if pageStatus === "error"}
            <tr>
              <td class="px-3 py-6 ui-subtitle" colspan="4">Failed to load (stubbed).</td>
            </tr>
          {/if}
        </tbody>
      </table>
    </div>
  </div>
</div>

{#if detailsOpen}
  {@const selected = detailsId ? connections.find((c) => c.id === detailsId) ?? null : null}
  <div class="fixed inset-0 z-50">
    <button
      type="button"
      class="absolute inset-0 h-full w-full"
      style="background-color: rgba(0, 0, 0, 0.55);"
      aria-label="Close details"
      onclick={closeDetails}
    ></button>
    <div class="absolute left-1/2 top-1/2 w-[720px] max-w-[calc(100vw-40px)] -translate-x-1/2 -translate-y-1/2">
      <div class="ui-card ui-pad-lg" style="background-color: var(--surface-1);">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <div class="ui-title">Details</div>
            {#if selected}
              <div class="mt-1 truncate text-sm font-medium" style="color: var(--text-primary);">{selected.name}</div>
              <div class="ui-subtitle mt-1">{selected.modelId} • {selected.location}</div>
            {:else}
              <div class="ui-subtitle mt-1">Not found.</div>
            {/if}
          </div>
          <button
            type="button"
            class="ui-focus rounded-md border px-3 py-2 text-xs font-medium transition-colors hover:bg-white/5"
            style="border-color: var(--border-subtle); color: var(--text-primary); background-color: transparent;"
            onclick={closeDetails}
          >
            Close
          </button>
        </div>

        {#if selected}
          <div class="mt-4 grid grid-cols-2 gap-3">
            <div class="ui-card ui-pad-md" style="background-color: var(--surface-2);">
              <div class="ui-subtitle">Endpoint</div>
              <div class="mt-1 truncate text-xs" style="color: var(--text-primary);">{selected.endpoint || "—"}</div>
            </div>
            <div class="ui-card ui-pad-md" style="background-color: var(--surface-2);">
              <div class="ui-subtitle">Tags</div>
              <div class="mt-2 flex flex-wrap gap-2">
                {#each selected.tags as t (t)}
                  <span class="ui-pill text-slate-300 bg-white/5">{t}</span>
                {/each}
              </div>
            </div>
          </div>
          <div class="mt-3 ui-card ui-pad-md" style="background-color: var(--surface-2);">
            <div class="ui-subtitle">Config (stub)</div>
            <pre
              class="mt-2 overflow-auto rounded-md border p-3 text-[11px] leading-4"
              style="border-color: var(--border-subtle); background-color: rgba(0,0,0,0.12); color: var(--text-primary); max-height: 260px;"
            >{selected.configText}</pre>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

{#if deleteConfirmOpen}
  {@const toDelete = deleteConfirmId ? connections.find((c) => c.id === deleteConfirmId) ?? null : null}
  <div class="fixed inset-0 z-50">
    <button
      type="button"
      class="absolute inset-0 h-full w-full"
      style="background-color: rgba(0, 0, 0, 0.55);"
      aria-label="Close delete confirmation"
      onclick={closeDeleteConfirm}
    ></button>
    <div class="absolute left-1/2 top-1/2 w-[560px] max-w-[calc(100vw-40px)] -translate-x-1/2 -translate-y-1/2">
      <div class="ui-card ui-pad-lg" style="background-color: var(--surface-1);">
        <div class="ui-title">Delete connection</div>
        <div class="ui-subtitle mt-2">
          This is UI-only. The connection will be removed from the local list for this session.
        </div>
        <div class="mt-3 rounded-md border border-rose-900/40 bg-rose-500/10 p-3 text-xs text-rose-200">
          {#if toDelete}
            <div class="font-medium truncate">{toDelete.name}</div>
            <div class="mt-1 truncate" style="color: rgba(255,255,255,0.75);">{toDelete.endpoint}</div>
          {:else}
            <div class="font-medium">Not found.</div>
          {/if}
        </div>
        <div class="mt-4 flex justify-end gap-2">
          <button
            type="button"
            class="ui-focus h-9 rounded-md border border-slate-700/60 bg-white/5 px-3 text-xs font-medium text-slate-200 transition-colors hover:bg-white/10"
            onclick={closeDeleteConfirm}
          >
            Cancel
          </button>
          <button
            type="button"
            class="ui-focus h-9 rounded-md border border-rose-900/60 bg-rose-500/10 px-3 text-xs font-semibold text-rose-200 transition-colors hover:bg-rose-500/15"
            onclick={confirmDelete}
          >
            Delete (stub)
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

{#if newWizardOpen}
  {@const providerId = newWizardProvider}
  <div class="fixed inset-0 z-50">
    <button
      type="button"
      class="absolute inset-0 h-full w-full"
      style="background-color: rgba(0, 0, 0, 0.55);"
      aria-label="Close new connection wizard"
      onclick={closeNewWizard}
    ></button>
    <div class="absolute left-1/2 top-1/2 w-[780px] max-w-[calc(100vw-40px)] -translate-x-1/2 -translate-y-1/2">
      <div class="ui-card ui-pad-lg" style="background-color: var(--surface-1);">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <div class="ui-title">New Connection</div>
            <div class="ui-subtitle mt-1">Wizard is stubbed; submit updates local list only.</div>
          </div>
          <button
            type="button"
            class="ui-focus rounded-md border px-3 py-2 text-xs font-medium transition-colors hover:bg-white/5"
            style="border-color: var(--border-subtle); color: var(--text-primary); background-color: transparent;"
            onclick={closeNewWizard}
          >
            Close
          </button>
        </div>

        <div class="mt-4">
          <div class="ui-card ui-pad-md" style="background-color: var(--surface-2);">
            <label class="ui-subtitle" for="provider-combobox">Provider</label>
            <div class="relative mt-2">
              <input
                id="provider-combobox"
                class="ui-focus h-9 w-full rounded-md border px-3 text-xs"
                style="border-color: var(--border-subtle); background-color: rgba(0,0,0,0.12); color: var(--text-primary);"
                placeholder="Search and select..."
                value={providerQuery}
                onfocus={() => openProviderPicker()}
                onblur={() => setTimeout(() => closeProviderPicker(), 0)}
                oninput={(e) => {
                  providerQuery = (e.currentTarget as HTMLInputElement).value;
                  newWizardProvider = null;
                  openProviderPicker();
                }}
                onkeydown={(e) => {
                  if (e.key === "Escape") closeProviderPicker();
                }}
                aria-expanded={providerMenuOpen}
                aria-controls="provider-menu"
              />

              {#if providerMenuOpen}
                <div
                  id="provider-menu"
                  class="absolute left-0 right-0 z-10 mt-2 overflow-hidden rounded-md border"
                  style="border-color: var(--border-subtle); background-color: var(--surface-2); box-shadow: var(--shadow-2);"
                >
                  {#if providerOptions().length === 0}
                    <div class="px-3 py-2 text-xs" style="color: var(--text-muted);">No matches</div>
                  {:else}
                    {#each providerOptions() as p (p.id)}
                      <button
                        type="button"
                        class="ui-focus block w-full px-3 py-2 text-left text-xs transition-colors hover:bg-white/5"
                        style="color: var(--text-primary); background-color: transparent;"
                        onclick={() => selectProvider(p.id)}
                      >
                        <div class="font-medium">{p.label}</div>
                        <div class="mt-0.5 text-[10px]" style="color: var(--text-muted);">{p.id}</div>
                      </button>
                    {/each}
                  {/if}
                </div>
              {/if}
            </div>
          </div>

          <div class="mt-3 ui-card ui-pad-md min-h-[260px]" style="background-color: var(--surface-2);">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="ui-subtitle" for="new-name">Connection name</label>
                <input
                  id="new-name"
                  class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
                  style="border-color: var(--border-subtle); background-color: rgba(0,0,0,0.12); color: var(--text-primary);"
                  placeholder="Example: Synapse Agent"
                  bind:value={newWizardName}
                />
              </div>
              <div>
                <label class="ui-subtitle" for="new-model">Model ID</label>
                <input
                  id="new-model"
                  class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
                  style="border-color: var(--border-subtle); background-color: rgba(0,0,0,0.12); color: var(--text-primary);"
                  placeholder="Example: gpt-4o-mini"
                  value={newWizardValues.model_id || ""}
                  oninput={(e) => updateWizardField("model_id", (e.currentTarget as HTMLInputElement).value)}
                />
              </div>
            </div>

            <div class="mt-3 grid grid-cols-2 gap-3">
              <div>
                <label class="ui-subtitle" for="new-endpoint">Endpoint / Base URL (optional)</label>
                <input
                  id="new-endpoint"
                  class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
                  style="border-color: var(--border-subtle); background-color: rgba(0,0,0,0.12); color: var(--text-primary);"
                  placeholder="api.example.invalid"
                  value={newWizardValues.endpoint || ""}
                  oninput={(e) => updateWizardField("endpoint", (e.currentTarget as HTMLInputElement).value)}
                />
              </div>
              <div>
                <label class="ui-subtitle" for="new-creds">Credentials path (optional)</label>
                <input
                  id="new-creds"
                  class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
                  style="border-color: var(--border-subtle); background-color: rgba(0,0,0,0.12); color: var(--text-primary);"
                  placeholder="C:\\path\\to\\credentials.json"
                  value={newWizardValues.credentials_path || ""}
                  oninput={(e) => updateWizardField("credentials_path", (e.currentTarget as HTMLInputElement).value)}
                />
              </div>
            </div>

            <div class="mt-3">
              <div class="ui-subtitle">Selected provider</div>
              <div class="mt-1 truncate text-xs font-medium" style="color: var(--text-primary);">{providerId ? providerLabel(providerId) : "—"}</div>
              <div class="mt-0.5 truncate text-[10px]" style="color: var(--text-muted);">{providerId || ""}</div>
            </div>

            <details class="mt-3 rounded-md border border-slate-700/60 bg-white/5 p-3">
              <summary class="cursor-pointer text-xs font-medium" style="color: var(--text-primary);">Advanced (optional)</summary>
              <div class="mt-3">
                <div class="ui-subtitle">Provider-specific options (stub)</div>
                <textarea
                  class="ui-focus mt-2 w-full rounded-md border p-3 text-[11px] leading-4"
                  style="border-color: var(--border-subtle); background-color: rgba(0,0,0,0.12); color: var(--text-primary); height: 96px; resize: none;"
                  placeholder="Stub JSON (not saved yet)"
                  value={newWizardValues.advanced_stub || ""}
                  oninput={(e) => updateWizardField("advanced_stub", (e.currentTarget as HTMLTextAreaElement).value)}
                ></textarea>
              </div>
            </details>
          </div>

          <div class="mt-4 flex justify-end gap-2">
            <button
              type="button"
              class="ui-focus h-9 rounded-md border border-slate-700/60 bg-white/5 px-3 text-xs font-medium text-slate-200 transition-colors hover:bg-white/10"
              onclick={closeNewWizard}
            >
              Cancel
            </button>
            <button
              type="button"
              class="ui-focus h-9 rounded-md border px-4 text-xs font-semibold transition-colors"
              style={providerId && newWizardName.trim() && (newWizardValues.model_id || "").trim()
                ? "border-color: rgba(39, 201, 169, 0.55); background-color: rgba(39, 201, 169, 0.10); color: var(--text-primary);"
                : "border-color: var(--border-subtle); background-color: rgba(255,255,255,0.04); color: var(--text-muted);"}
              disabled={!(providerId && newWizardName.trim() && (newWizardValues.model_id || "").trim())}
              onclick={submitNewConnection}
            >
              Create (stub)
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}
