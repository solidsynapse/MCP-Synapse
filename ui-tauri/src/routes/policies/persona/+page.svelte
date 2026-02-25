<script lang="ts">
  import PolicySelect from "../policy-select.svelte";
  import { getPoliciesSession, patchPoliciesSession } from "$lib/ui_session";

  type PersonaId = "default" | "analyst" | "concise" | "coach" | "strict";
  type TargetId = "bridge_alpha" | "bridge_beta" | "conn_local_a" | "conn_remote_staging";

  type Option<T extends string> = { id: T; label: string };
  type AppliedRow = { id: string; personaId: PersonaId; targetId: TargetId; timestampLabel: string };
  type PersonaPreset = { id: string; name: string; text: string };

  const PERSONAS: Option<PersonaId>[] = [
    { id: "default", label: "Default" },
    { id: "analyst", label: "Analyst" },
    { id: "concise", label: "Concise" },
    { id: "coach", label: "Coach" },
    { id: "strict", label: "Strict" },
  ];

  const TARGETS: Option<TargetId>[] = [
    { id: "bridge_alpha", label: "Bridge Alpha" },
    { id: "bridge_beta", label: "Bridge Beta" },
    { id: "conn_local_a", label: "Connection: Local Runtime A" },
    { id: "conn_remote_staging", label: "Connection: Remote Proxy (Staging)" },
  ];

  const DEFAULT_PRESET_ID = "preset_default";
  const INITIAL_PRESETS: PersonaPreset[] = [
    {
      id: DEFAULT_PRESET_ID,
      name: "Default",
      text: "You are MCP Synapse. Be accurate, neutral, and helpful. If requirements are ambiguous, ask concise clarifying questions. Avoid revealing secrets and avoid provider-specific claims unless explicitly given.",
    },
    {
      id: "preset_analyst",
      name: "Analyst",
      text: "You are an analytical assistant. Explain assumptions, trade-offs, and risks. Prefer structured bullet points. Provide actionable next steps and keep language precise.",
    },
    {
      id: "preset_concise",
      name: "Concise",
      text: "You are a concise assistant. Answer directly, prefer short bullet points, and avoid extra explanation unless asked.",
    },
  ];

  const savedPolicies = getPoliciesSession();
  const savedApplied = savedPolicies.appliedPersonas as AppliedRow[];
  const savedPresets = savedPolicies.personaPresets as PersonaPreset[];
  const initialPresets = Array.isArray(savedPresets) && savedPresets.length > 0 ? savedPresets : INITIAL_PRESETS;
  const initialSelectedPresetId =
    (savedPolicies.selectedPresetId && initialPresets.some((p) => p.id === savedPolicies.selectedPresetId) ? savedPolicies.selectedPresetId : null) ??
    initialPresets[0]?.id ??
    DEFAULT_PRESET_ID;
  const initialPresetForDraft = initialPresets.find((p) => p.id === initialSelectedPresetId) ?? null;

  let selectedPersonaId = $state<PersonaId>("default");
  let selectedTargetId = $state<TargetId>("bridge_alpha");
  let applied = $state<AppliedRow[]>(Array.isArray(savedApplied) ? savedApplied : []);

  let presets = $state<PersonaPreset[]>(initialPresets);
  let selectedPresetId = $state<string>(initialSelectedPresetId);
  let draftPresetId = $state<string>(initialSelectedPresetId);
  let presetNameDraft = $state<string>(savedPolicies.presetNameDraft || initialPresetForDraft?.name || "");
  let personaTextDraft = $state<string>(savedPolicies.personaTextDraft || initialPresetForDraft?.text || "");

  let addPresetOpen = $state(false);
  let newPresetName = $state("");
  let newPresetText = $state("");

  let deleteConfirmOpen = $state(false);

  function formatTimestamp(value: Date) {
    return value.toLocaleString(undefined, {
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

  function applyPersona() {
    const row: AppliedRow = {
      id: `applied_${Math.random().toString(16).slice(2)}_${Date.now()}`,
      personaId: selectedPersonaId,
      targetId: selectedTargetId,
      timestampLabel: formatTimestamp(new Date()),
    };
    applied = [row, ...applied];
  }

  function removeApplied(id: string) {
    applied = applied.filter((r) => r.id !== id);
  }

  const presetOptions = $derived(() => {
    return presets.map((p) => ({ id: p.id, label: p.name }));
  });

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
    deleteConfirmOpen = false;
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
    const id = `preset_${Math.random().toString(16).slice(2)}_${Date.now()}`;
    const next: PersonaPreset = { id, name, text };
    presets = [...presets, next];
    selectedPresetId = id;
    closeAddPreset();
  }

  $effect(() => {
    const id = selectedPresetId;
    if (id === draftPresetId) return;
    const preset = presets.find((p) => p.id === id) ?? null;
    if (!preset) return;
    presetNameDraft = preset.name;
    personaTextDraft = preset.text;
    draftPresetId = id;
  });

  $effect(() => {
    patchPoliciesSession({
      appliedPersonas: applied,
      personaPresets: presets,
      selectedPresetId,
      presetNameDraft,
      personaTextDraft,
    });
  });
</script>

<div class="space-y-4 p-6">
  <div class="flex items-start justify-between gap-4">
    <div class="min-w-0">
      <div class="ui-subtitle">Assign a persona to a bridge/connection (UI-only; ephemeral view state).</div>
    </div>
  </div>

  <div class="ui-card ui-pad-md">
    <div class="ui-title">Applied personas (UI-only)</div>
    <div class="ui-subtitle mt-1">Applies add rows locally; nothing is persisted.</div>

    <div class="mt-3 overflow-hidden rounded-md border" style="border-color: var(--border-subtle);">
      <table class="ui-table text-left text-xs">
        <thead>
          <tr class="border-b" style="border-color: var(--border-subtle);">
            <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Persona</th>
            <th class="px-4 py-3 font-semibold" style="color: var(--text-primary);">Bridge / Connection</th>
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
                <td class="px-4 py-3" style="color: var(--text-primary);">{labelForOption(PERSONAS, row.personaId)}</td>
                <td class="px-4 py-3" style="color: var(--text-muted);">{labelForOption(TARGETS, row.targetId)}</td>
                <td class="px-4 py-3" style="color: var(--text-muted);">{row.timestampLabel}</td>
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
      <div class="ui-subtitle mt-1">Select a persona and a bridge/connection, then apply (UI-only).</div>

      <div class="mt-4 grid gap-3 sm:grid-cols-2">
        <PolicySelect label="Persona" bind:value={selectedPersonaId} options={PERSONAS} />
        <PolicySelect label="Bridge / Connection" bind:value={selectedTargetId} options={TARGETS} />
      </div>

      <div class="mt-4 flex justify-end">
        <button
          type="button"
          class="ui-focus rounded-md border px-5 py-2.5 text-xs font-semibold transition-colors hover:bg-white/5"
          style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary); box-shadow: var(--shadow-1);"
          onclick={applyPersona}
        >
          Apply
        </button>
      </div>
  </div>

  <div class="ui-card ui-pad-md">
    <div class="ui-title">Mini library</div>
    <div class="ui-subtitle mt-1">UI-only presets for persona prompts (not persisted).</div>

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
            class="ui-focus h-9 rounded-md border px-3 text-xs font-semibold transition-colors hover:bg-white/5"
            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary); box-shadow: var(--shadow-1);"
            onclick={saveCurrentPreset}
          >
            Save
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
        <div class="mt-2 text-xs" style="color: var(--text-muted);">UI-only; not persisted.</div>
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
            <div class="ui-subtitle mt-1">UI-only; not persisted.</div>
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
        <div class="ui-subtitle mt-2">UI-only; not persisted.</div>
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
