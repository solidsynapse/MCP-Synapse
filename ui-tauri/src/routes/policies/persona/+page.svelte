<script lang="ts">
  import { onMount } from "svelte";
  import PolicySelect from "../policy-select.svelte";
  import { uiCacheGet, uiCacheSet, uiRunDeduped } from "$lib/ui_session";

  type Option<T extends string> = { id: T; label: string };
  type AppliedRow = { id: string; personaId: string; targetId: string; appliedAt: string };
  type PersonaPreset = { id: string; name: string; text: string };
  type BannerKind = "idle" | "info" | "success" | "danger";
  type DispatchError = { code?: string; message?: string };
  type ConnectionItem = {
    id?: string;
    connection_name?: string;
    status?: string;
    port?: number;
  };
  type PersonaState = {
    selected_persona_id: string;
    selected_target_id: string;
    applied_rows: Array<{ id: string; persona_id: string; target_id: string; applied_at: string }>;
    presets: PersonaPreset[];
    selected_preset_id: string;
  };
  type DispatchResponse = {
    ok: boolean;
    status?: string;
    state?: PersonaState | null;
    connections?: ConnectionItem[];
    error?: DispatchError | null;
    errors?: string[];
  };

  const LEGACY_PERSONAS: Option<string>[] = [
    { id: "default", label: "Default" },
    { id: "analyst", label: "Analyst" },
    { id: "concise", label: "Concise" },
    { id: "coach", label: "Coach" },
    { id: "strict", label: "Strict" },
  ];

  const LEGACY_TARGET_IDS = new Set(["bridge_alpha", "bridge_beta", "conn_local_a", "conn_remote_staging"]);

  const DEFAULT_PRESET_ID = "preset_default";
  const BUILTIN_PRESETS: PersonaPreset[] = [
    {
      id: DEFAULT_PRESET_ID,
      name: "Default",
      text: "You are MCP Synapse. Be accurate, neutral, and helpful. If requirements are ambiguous, ask concise clarifying questions. Avoid revealing secrets and avoid provider-specific claims unless explicitly given.",
    },
    {
      id: "preset_production_operator",
      name: "Production Operator",
      text: "You are a production-focused MCP operations assistant. Prioritize reliability, deterministic behavior, and low-risk execution. Start with the smallest safe scope and confirm assumptions before taking action. Prefer explicit checks over inference. For runtime, config, or data changes, state preconditions, expected outcome, and rollback path. Never claim success without observable evidence. If results are ambiguous, return REVALIDATE with exact missing proof. Avoid broad audits unless requested. Keep outputs concise and ordered by operational impact.",
    },
    {
      id: "preset_debug_investigator",
      name: "Debug Investigator",
      text: "You are a debugging investigator for UI, wiring, and runtime issues. Reproduce in narrow scope, isolate failing surface, and map symptom to trigger to probable source. Prefer deterministic probes with exact file paths and expected versus observed behavior. Distinguish static confidence from runtime-confirmed evidence. If runtime proof is missing, return REVALIDATE. Propose the smallest patch that resolves the issue without redesign. Call out regression risk and side effects explicitly. Keep language concrete and action-oriented.",
    },
    {
      id: "preset_cost_usage_analyst",
      name: "Cost & Usage Analyst",
      text: "You are a cost and usage analysis assistant for multi-provider LLM systems. Separate measured values from estimates. If cost is inferred, state assumptions and confidence clearly. Highlight variance drivers such as provider pricing model, token accounting differences, retries, streaming behavior, and caching effects. Present concise findings suitable for release planning. Prioritize transparency and trust: reproducible formulas, clear attribution by provider and model, and practical drift alerts. Avoid overpromising precision where provider metadata is incomplete.",
    },
    {
      id: "preset_security_compliance_guard",
      name: "Security & Compliance Guard",
      text: "You are a security-first assistant for local and BYOK AI tooling. Enforce least-privilege, secret hygiene, and auditability. Treat credentials and sensitive paths as high-risk inputs. Recommend secure defaults, explicit error handling, and non-leaky UX messages. Do not make unsupported legal or compliance claims. For sensitive flows provide threat surface, abuse path, mitigation, and residual risk. Prefer incremental hardening over disruptive redesign. If risk closure is uncertain, return BLOCKER or REVALIDATE with exact missing verification.",
    },
  ];
  const BUILTIN_PRESET_IDS = new Set(BUILTIN_PRESETS.map((p) => p.id));
  const INITIAL_PRESETS: PersonaPreset[] = BUILTIN_PRESETS;

  let selectedPersonaId = $state<string>(DEFAULT_PRESET_ID);
  let selectedTargetId = $state<string>("");
  let targetOptions = $state<Option<string>[]>([]);
  let applied = $state<AppliedRow[]>([]);

  let presets = $state<PersonaPreset[]>(INITIAL_PRESETS);
  let selectedPresetId = $state<string>(DEFAULT_PRESET_ID);
  let draftPresetId = $state<string>(DEFAULT_PRESET_ID);
  let presetNameDraft = $state<string>(INITIAL_PRESETS[0]?.name || "");
  let personaTextDraft = $state<string>(INITIAL_PRESETS[0]?.text || "");

  let addPresetOpen = $state(false);
  let newPresetName = $state("");
  let newPresetText = $state("");

  let deleteConfirmOpen = $state(false);
  let bannerKind = $state<BannerKind>("idle");
  let bannerText = $state("");
  let bannerTimer: ReturnType<typeof setTimeout> | null = null;
  let saveInFlight = $state(false);
  let hydrated = $state(false);
  let persistArmed = $state(false);
  const PERSONA_STATE_CACHE_KEY = "policies.persona.state";
  const PERSONA_TARGETS_CACHE_KEY = "policies.persona.targets";
  const PERSONA_CACHE_TTL_MS = 120000;

  function formatTimestamp(value: string | Date) {
    const d = value instanceof Date ? value : new Date(value);
    return d.toLocaleString(undefined, {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  }

  function labelForOption<T extends string>(options: Option<T>[], id: T) {
    return options.find((o) => o.id === id)?.label ?? id;
  }

  function normalizeLabelPart(value: unknown, fallback: string) {
    const text = String(value || "").trim();
    return text || fallback;
  }

  function createPresetId(name: string) {
    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
    return `preset_${slug || "custom"}_${Date.now().toString(36)}`;
  }

  function createLocalAppliedRowId() {
    return `applied_local_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
  }

  function ensureTargetOptionExists(optionsIn: Option<string>[], targetId: string) {
    const cleanTargetId = String(targetId || "").trim();
    if (!cleanTargetId) return optionsIn;
    if (LEGACY_TARGET_IDS.has(cleanTargetId)) return optionsIn;
    if (optionsIn.some((o) => o.id === cleanTargetId)) return optionsIn;
    return [...optionsIn, { id: cleanTargetId, label: `Connection: ${cleanTargetId}` }];
  }

  function personaLabelForId(personaId: string) {
    const fromPreset = presets.find((p) => p.id === personaId)?.name;
    if (fromPreset) return fromPreset;
    return labelForOption(LEGACY_PERSONAS, personaId);
  }

  function targetLabelForId(targetId: string) {
    const fromTargets = targetOptions.find((o) => o.id === targetId)?.label;
    if (fromTargets) return fromTargets;
    return `Connection: ${targetId}`;
  }

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

  function canApplyPersona() {
    const hasPersona = String(selectedPersonaId || "").trim().length > 0;
    const hasTarget = String(selectedTargetId || "").trim().length > 0;
    return hasPersona && hasTarget && !saveInFlight;
  }

  function normalizeState(state: PersonaState | null | undefined) {
    const presetsIn = Array.isArray(state?.presets) ? state!.presets : [];
    const sanitizedIncoming = presetsIn
      .filter((p) => p && typeof p.id === "string" && typeof p.name === "string")
      .map((p) => ({
        id: String(p.id || "").trim(),
        name: String(p.name || "").trim(),
        text: typeof p.text === "string" ? p.text : "",
      }))
      .filter((p) => p.id.length > 0 && p.name.length > 0);
    const presetById = new Map<string, PersonaPreset>();
    for (const preset of sanitizedIncoming) {
      if (!presetById.has(preset.id)) presetById.set(preset.id, preset);
    }
    for (const builtin of BUILTIN_PRESETS) {
      if (!presetById.has(builtin.id)) presetById.set(builtin.id, builtin);
    }
    const normalizedPresets: PersonaPreset[] = [];
    for (const builtin of BUILTIN_PRESETS) {
      const existing = presetById.get(builtin.id);
      if (existing) normalizedPresets.push(existing);
    }
    for (const preset of sanitizedIncoming) {
      if (!BUILTIN_PRESET_IDS.has(preset.id)) normalizedPresets.push(preset);
    }
    const selectedPreset = String(state?.selected_preset_id || normalizedPresets[0]?.id || DEFAULT_PRESET_ID);
    const appliedRowsIn = Array.isArray(state?.applied_rows) ? state!.applied_rows : [];
    const normalizedApplied: AppliedRow[] = appliedRowsIn
      .filter((r) => r && typeof r.persona_id === "string" && typeof r.target_id === "string")
      .map((r) => ({
        id: String(r.id || ""),
        personaId: String(r.persona_id || ""),
        targetId: String(r.target_id || ""),
        appliedAt: String(r.applied_at || ""),
      }));
    return {
      selectedPersonaId: (() => {
        const candidate = String(
          state?.selected_persona_id || state?.selected_preset_id || normalizedPresets[0]?.id || DEFAULT_PRESET_ID,
        ).trim();
        if (normalizedPresets.some((p) => p.id === candidate)) return candidate;
        return String(normalizedPresets[0]?.id || DEFAULT_PRESET_ID);
      })(),
      selectedTargetId: String(state?.selected_target_id || "").trim(),
      presets: normalizedPresets,
      selectedPresetId: selectedPreset,
      applied: normalizedApplied,
    };
  }

  function currentStatePayload(): PersonaState {
    return {
      selected_persona_id: selectedPersonaId,
      selected_target_id: selectedTargetId,
      applied_rows: applied.map((row) => ({
        id: row.id,
        persona_id: row.personaId,
        target_id: row.targetId,
        applied_at: row.appliedAt,
      })),
      presets: presets.map((p) => ({ id: p.id, name: p.name, text: p.text })),
      selected_preset_id: selectedPresetId,
    };
  }

  function applyHydratedState(state: PersonaState | null | undefined) {
    const next = normalizeState(state);
    selectedPersonaId = next.selectedPersonaId;
    selectedTargetId = next.selectedTargetId;
    targetOptions = ensureTargetOptionExists(targetOptions, next.selectedTargetId);
    presets = next.presets;
    selectedPresetId = next.selectedPresetId;
    draftPresetId = next.selectedPresetId;
    const selected = next.presets.find((p) => p.id === next.selectedPresetId) ?? next.presets[0] ?? null;
    presetNameDraft = selected?.name || "";
    personaTextDraft = selected?.text || "";
    applied = next.applied;
    hydrated = true;
    persistArmed = false;
  }

  async function dispatchInvoke(promptPayload: Record<string, unknown>): Promise<DispatchResponse> {
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
    }) as DispatchResponse;
  }

  async function loadConnectionTargets() {
    try {
      const result = await uiRunDeduped(PERSONA_TARGETS_CACHE_KEY, async () => await dispatchInvoke({ op: "connections.list" }));
      if (!result.ok) {
        targetOptions = ensureTargetOptionExists(targetOptions, selectedTargetId);
        return;
      }
      const rows = Array.isArray(result.connections) ? result.connections : [];
      const mapped: Option<string>[] = rows
        .filter((row) => row && typeof row.id === "string" && String(row.id).trim().length > 0)
        .map((row) => {
          const id = String(row.id || "").trim();
          const name = normalizeLabelPart(row.connection_name, id);
          const status = normalizeLabelPart(row.status, "unknown");
          const portText = Number.isFinite(Number(row.port)) ? `:${Number(row.port)}` : "";
          return { id, label: `${name} (${status}${portText})` };
        });
      const normalizedTargets = mapped;
      if (normalizedTargets.length > 0) {
        if (!selectedTargetId || !normalizedTargets.some((o) => o.id === selectedTargetId)) {
          selectedTargetId = normalizedTargets[0].id;
        }
        targetOptions = normalizedTargets;
      } else {
        targetOptions = ensureTargetOptionExists([], selectedTargetId);
      }
      uiCacheSet(PERSONA_TARGETS_CACHE_KEY, targetOptions);
    } catch {
      targetOptions = ensureTargetOptionExists(targetOptions, selectedTargetId);
    }
  }

  async function loadPersonaState() {
    setBanner("idle", "");
    try {
      const result = await uiRunDeduped(PERSONA_STATE_CACHE_KEY, async () => await dispatchInvoke({ op: "policies.persona.get_state" }));
      if (!result.ok) {
        const code = result.error?.code ? `${result.error.code}: ` : "";
        const msg = result.error?.message || (result.errors || []).join("; ") || "request failed";
        setBanner("danger", `Persona load failed: ${code}${msg}`);
        return;
      }
      applyHydratedState(result.state);
      uiCacheSet(PERSONA_STATE_CACHE_KEY, result.state ?? null);
    } catch (err: any) {
      setBanner("danger", `Persona load failed: ${err?.message || String(err)}`);
    }
  }

  async function persistPersonaState(successMessage = "") {
    if (saveInFlight) return;
    saveInFlight = true;
    setBanner("idle", "");
    try {
      const result = await dispatchInvoke({ op: "policies.persona.set_state", state: currentStatePayload() });
      if (!result.ok) {
        const code = result.error?.code ? `${result.error.code}: ` : "";
        const msg = result.error?.message || (result.errors || []).join("; ") || "request failed";
        setBanner("danger", `Persona save failed: ${code}${msg}`);
        return;
      }
      applyHydratedState(result.state);
      await loadConnectionTargets();
      if (successMessage) {
        setBanner("success", successMessage);
      }
    } catch (err: any) {
      setBanner("danger", `Persona save failed: ${err?.message || String(err)}`);
    } finally {
      saveInFlight = false;
    }
  }

  function applyPersona() {
    const row: AppliedRow = {
      id: createLocalAppliedRowId(),
      personaId: selectedPersonaId,
      targetId: selectedTargetId,
      appliedAt: new Date().toISOString(),
    };
    applied = [row, ...applied];
    void persistPersonaState("Persona applied.");
  }

  function removeApplied(id: string) {
    applied = applied.filter((r) => r.id !== id);
    void persistPersonaState("Persona entry removed.");
  }

  const presetOptions = $derived(() => {
    return presets.map((p) => ({ id: p.id, label: p.name }));
  });
  const applyPersonaOptions = $derived(() => {
    return presets.map((p) => ({ id: p.id, label: p.name }));
  });
  const savePresetDisabled = $derived(() => !selectedPresetId || !presetNameDraft.trim());

  const deleteDisabled = $derived(() => selectedPresetId === DEFAULT_PRESET_ID || presets.length <= 1);

  function openAddPreset() {
    addPresetOpen = true;
    newPresetName = "";
    newPresetText = "";
  }

  function saveCurrentPreset() {
    const id = selectedPresetId;
    if (!id) return;
    const name = presetNameDraft.trim();
    if (!name) return;
    presets = presets.map((p) => (p.id === id ? { ...p, name, text: personaTextDraft } : p));
    persistArmed = true;
    void persistPersonaState("Preset saved.");
  }

  function openDeleteConfirm() {
    if (deleteDisabled()) return;
    deleteConfirmOpen = true;
  }

  function closeDeleteConfirm() {
    deleteConfirmOpen = false;
  }

  function confirmDeletePreset() {
    if (deleteDisabled()) return;
    const id = selectedPresetId;
    const remaining = presets.filter((p) => p.id !== id);
    presets = remaining;
    selectedPresetId = remaining[0]?.id ?? DEFAULT_PRESET_ID;
    if (selectedPersonaId === id) {
      selectedPersonaId = remaining[0]?.id ?? DEFAULT_PRESET_ID;
    }
    deleteConfirmOpen = false;
    persistArmed = true;
    void persistPersonaState("Preset deleted.");
  }

  function closeAddPreset() {
    addPresetOpen = false;
    newPresetName = "";
    newPresetText = "";
  }

  function saveNewPreset() {
    const name = newPresetName.trim();
    const text = newPresetText.trim();
    if (!name || !text) return;
    const id = createPresetId(name);
    const next: PersonaPreset = { id, name, text };
    presets = [...presets, next];
    selectedPresetId = id;
    selectedPersonaId = id;
    closeAddPreset();
    persistArmed = true;
    void persistPersonaState("Preset added.");
  }

  $effect(() => {
    const id = selectedPresetId;
    if (id === draftPresetId) return;
    const preset = presets.find((p) => p.id === id) ?? null;
    if (!preset) return;
    selectedPersonaId = id;
    presetNameDraft = preset.name;
    personaTextDraft = preset.text;
    draftPresetId = id;
  });

  $effect(() => {
    if (!hydrated || !persistArmed) return;
    void persistPersonaState();
    persistArmed = false;
  });

  let prevSelectedPersonaId = $state(selectedPersonaId);
  let prevSelectedTargetId = $state(selectedTargetId);
  let prevSelectedPresetId = $state(selectedPresetId);
  $effect(() => {
    if (!hydrated) return;
    if (
      selectedPersonaId !== prevSelectedPersonaId ||
      selectedTargetId !== prevSelectedTargetId ||
      selectedPresetId !== prevSelectedPresetId
    ) {
      prevSelectedPersonaId = selectedPersonaId;
      prevSelectedTargetId = selectedTargetId;
      prevSelectedPresetId = selectedPresetId;
      persistArmed = true;
    }
  });

  onMount(() => {
    const onShortcutEscape = (event: Event) => {
      if (addPresetOpen) {
        closeAddPreset();
        event.preventDefault();
        return;
      }
      if (deleteConfirmOpen) {
        closeDeleteConfirm();
        event.preventDefault();
      }
    };
    window.addEventListener("synapse:shortcut-escape", onShortcutEscape as EventListener);

    const cachedState = uiCacheGet<PersonaState | null>(PERSONA_STATE_CACHE_KEY, PERSONA_CACHE_TTL_MS);
    let refreshDelayMs = 0;
    if (cachedState) applyHydratedState(cachedState);
    if (cachedState) refreshDelayMs = 90;
    const cachedTargets = uiCacheGet<Option<string>[]>(PERSONA_TARGETS_CACHE_KEY, PERSONA_CACHE_TTL_MS);
    const sanitizedCachedTargets = (cachedTargets || []).filter((o) => {
      const id = String(o?.id || "").trim();
      return id.length > 0 && !LEGACY_TARGET_IDS.has(id);
    });
    if (sanitizedCachedTargets.length > 0) {
      targetOptions = ensureTargetOptionExists(sanitizedCachedTargets, selectedTargetId);
      refreshDelayMs = 90;
    }
    window.setTimeout(() => {
      void Promise.all([loadPersonaState(), loadConnectionTargets()]);
    }, refreshDelayMs);
    return () => {
      window.removeEventListener("synapse:shortcut-escape", onShortcutEscape as EventListener);
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
      <div class="ui-subtitle">Assign a persona to a connection.</div>
    </div>
  </div>

  <div class="ui-card ui-pad-md">
    <div class="ui-title">Applied personas</div>
    <div class="ui-subtitle mt-1">Applied personas are persisted.</div>

    <div class="mt-3 overflow-hidden rounded-md border" style="border-color: var(--border-subtle);">
      <table class="ui-table text-left text-xs">
        <thead>
          <tr class="border-b" style="border-color: var(--border-subtle);">
            <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Persona</th>
            <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Connection</th>
            <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Applied at</th>
            <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Action</th>
          </tr>
        </thead>
        <tbody>
          {#if applied.length === 0}
            <tr class="border-b" style="border-color: var(--border-subtle);">
              <td class="px-4 py-4" colspan="3" style="color: var(--text-muted);">No applied personas yet.</td>
              <td class="px-4 py-4 text-center" style="color: var(--text-muted);">—</td>
            </tr>
          {:else}
            {#each applied as row (row.id)}
              <tr class="border-b ui-row-hover" style="border-color: var(--border-subtle);">
                <td class="px-4 py-3" style="color: var(--text-primary);">{personaLabelForId(row.personaId)}</td>
                <td class="px-4 py-3" style="color: var(--text-muted);">{targetLabelForId(row.targetId)}</td>
                <td class="px-4 py-3" style="color: var(--text-muted);">{formatTimestamp(row.appliedAt)}</td>
                <td class="px-4 py-3">
                  <button
                    type="button"
                    class="ui-focus rounded-md border px-3 py-2 text-xs font-semibold transition-colors hover:bg-white/5"
                    style="border-color: var(--border-subtle); background-color: transparent; color: var(--text-primary);"
                    onclick={() => removeApplied(row.id)}
                  >
                    Remove
                  </button>
                </td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
  </div>

  <div class="ui-card ui-pad-md">
      <div class="ui-title">Apply persona</div>
      <div class="ui-subtitle mt-1">Select a persona and a connection, then apply.</div>

      <div class="mt-4 grid gap-3 sm:grid-cols-2">
        <PolicySelect label="Persona" bind:value={selectedPersonaId} options={applyPersonaOptions()} />
        <PolicySelect label="Connection" bind:value={selectedTargetId} options={targetOptions} />
      </div>

      <div class="mt-4 flex justify-end">
        <button
          type="button"
          class="ui-focus rounded-md border px-5 py-2.5 text-xs font-semibold transition-colors hover:bg-white/5"
          style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary); box-shadow: var(--shadow-1);"
          disabled={!canApplyPersona()}
          onclick={applyPersona}
        >
          Apply
        </button>
      </div>
  </div>

  <div class="ui-card ui-pad-md">
    <div class="ui-title">Mini library</div>
    <div class="ui-subtitle mt-1">Presets for persona prompts.</div>

    <div class="mt-4 grid gap-3">
      <div class="flex items-end gap-3">
        <div class="w-1/2">
          <PolicySelect label="Preset" bind:value={selectedPresetId} options={presetOptions()} />
        </div>
        <div class="flex w-1/2 justify-end gap-2">
          <button
            type="button"
            class="ui-focus h-9 rounded-md border px-3 text-xs font-medium transition-colors hover:bg-white/5"
            style="border-color: var(--border-subtle); background-color: transparent; color: var(--text-primary);"
            onclick={openAddPreset}
          >
            Add new
          </button>
          <button
            type="button"
            class="ui-focus h-9 rounded-md border px-3 text-xs font-semibold transition-colors hover:bg-white/5 disabled:opacity-60"
            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary); box-shadow: var(--shadow-1);"
            disabled={savePresetDisabled()}
            onclick={saveCurrentPreset}
          >
            Save preset
          </button>
          <button
            type="button"
            class="ui-focus h-9 rounded-md border px-3 text-xs font-semibold transition-colors hover:bg-white/5 disabled:opacity-60"
            style="border-color: var(--border-subtle); background-color: transparent; color: var(--text-primary);"
            disabled={deleteDisabled()}
            onclick={openDeleteConfirm}
          >
            Delete
          </button>
        </div>
      </div>
      <label class="flex items-center gap-3">
        <span class="ui-subtitle w-28">Preset name</span>
        <input
          class="ui-focus h-9 flex-1 rounded-md border px-3 text-xs"
          style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
          value={presetNameDraft}
          oninput={(e) => (presetNameDraft = (e.currentTarget as HTMLInputElement).value)}
        />
      </label>
      <div>
        <div class="ui-subtitle">Persona text</div>
        <textarea
          class="ui-focus mt-2 w-full rounded-md border px-3 py-2 text-xs leading-5"
          style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary); min-height: 140px;"
          value={personaTextDraft}
          oninput={(e) => (personaTextDraft = (e.currentTarget as HTMLTextAreaElement).value)}
        ></textarea>
        <div class="mt-2 text-xs" style="color: var(--text-muted);">Saved to local policy state.</div>
      </div>
    </div>
  </div>
</div>

{#if addPresetOpen}
  <div class="fixed inset-0 z-50">
    <button
      type="button"
      class="absolute inset-0 h-full w-full"
      style="background-color: rgba(0, 0, 0, 0.55);"
      aria-label="Close add preset modal"
      onclick={closeAddPreset}
    ></button>
    <div class="absolute left-1/2 top-1/2 w-[720px] max-w-[calc(100vw-40px)] -translate-x-1/2 -translate-y-1/2">
      <div class="ui-card ui-pad-lg" style="background-color: var(--surface-1);">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <div class="ui-title">Add preset</div>
            <div class="ui-subtitle mt-1">Saved after you click Save.</div>
          </div>
          <button
            type="button"
            class="ui-focus rounded-md border px-3 py-2 text-xs font-medium transition-colors hover:bg-white/5"
            style="border-color: var(--border-subtle); color: var(--text-primary); background-color: transparent;"
            onclick={closeAddPreset}
          >
            Close
          </button>
        </div>

        <div class="mt-4 grid gap-3">
          <div>
            <div class="ui-subtitle">Preset name</div>
            <input
              class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
              style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
              value={newPresetName}
              oninput={(e) => (newPresetName = (e.currentTarget as HTMLInputElement).value)}
              placeholder="e.g., Security Reviewer"
            />
          </div>
          <div>
            <div class="ui-subtitle">Persona text</div>
            <textarea
              class="ui-focus mt-2 w-full rounded-md border px-3 py-2 text-xs leading-5"
              style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary); min-height: 180px;"
              value={newPresetText}
              oninput={(e) => (newPresetText = (e.currentTarget as HTMLTextAreaElement).value)}
              placeholder="Paste or write a persona prompt..."
            ></textarea>
          </div>
        </div>

        <div class="mt-4 flex justify-end gap-2">
          <button
            type="button"
            class="ui-focus h-9 rounded-md border px-3 text-xs font-medium transition-colors hover:bg-white/5"
            style="border-color: var(--border-subtle); background-color: transparent; color: var(--text-primary);"
            onclick={closeAddPreset}
          >
            Cancel
          </button>
          <button
            type="button"
            class="ui-focus h-9 rounded-md border px-3 text-xs font-semibold transition-colors hover:bg-white/5 disabled:opacity-60"
            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary); box-shadow: var(--shadow-1);"
            disabled={!newPresetName.trim() || !newPresetText.trim()}
            onclick={saveNewPreset}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

{#if deleteConfirmOpen}
  {@const selected = presets.find((p) => p.id === selectedPresetId) ?? null}
  <div class="fixed inset-0 z-50">
    <button
      type="button"
      class="absolute inset-0 h-full w-full"
      style="background-color: rgba(0, 0, 0, 0.55);"
      aria-label="Close delete preset confirmation"
      onclick={closeDeleteConfirm}
    ></button>
    <div class="absolute left-1/2 top-1/2 w-[560px] max-w-[calc(100vw-40px)] -translate-x-1/2 -translate-y-1/2">
      <div class="ui-card ui-pad-lg" style="background-color: var(--surface-1);">
        <div class="ui-title">Delete preset</div>
        <div class="ui-subtitle mt-2">Removes preset from persisted policy state.</div>
        <div class="mt-3 rounded-md border border-rose-900/40 bg-rose-500/10 p-3 text-xs text-rose-200">
          {#if selected}
            <div class="font-medium truncate">{selected.name}</div>
          {:else}
            <div class="font-medium">Not found.</div>
          {/if}
        </div>
        <div class="mt-4 flex justify-end gap-2">
          <button
            type="button"
            class="ui-focus h-9 rounded-md border px-3 text-xs font-medium transition-colors hover:bg-white/5"
            style="border-color: var(--border-subtle); background-color: transparent; color: var(--text-primary);"
            onclick={closeDeleteConfirm}
          >
            Cancel
          </button>
          <button
            type="button"
            class="ui-focus h-9 rounded-md border px-3 text-xs font-semibold transition-colors hover:bg-rose-500/15 disabled:opacity-60"
            style="border-color: rgba(159, 18, 57, 0.6); background-color: rgba(244, 63, 94, 0.10); color: rgb(254, 202, 202);"
            disabled={deleteDisabled()}
            onclick={confirmDeletePreset}
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}
