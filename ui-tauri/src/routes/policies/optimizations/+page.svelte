<script lang="ts">
  import { getPoliciesSession, patchPoliciesSession } from "$lib/ui_session";

  const session = getPoliciesSession();
  let contextCachingEnabled = $state(session.contextCachingEnabled);
  let requestDedupEnabled = $state(session.requestDedupEnabled);

  $effect(() => {
    patchPoliciesSession({
      contextCachingEnabled,
      requestDedupEnabled
    });
  });
</script>

<div class="space-y-4 p-6">
  <div class="flex items-start justify-between gap-4">
    <div class="min-w-0">
      <div class="ui-subtitle">Placeholder optimization toggles (UI-only; not wired).</div>
    </div>
  </div>

  <div class="grid gap-3 lg:grid-cols-2">
    <div class="ui-card ui-pad-md">
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <div class="ui-title">Context caching (FinOps)</div>
          <div class="ui-subtitle mt-1">Reduce repeated request assembly costs (placeholder).</div>
        </div>
        <label class="flex items-center gap-2 text-xs" style="color: var(--text-primary);">
          <input
            type="checkbox"
            class="ui-focus h-4 w-4 rounded border"
            style="border-color: var(--border-subtle); background-color: var(--surface-2);"
            bind:checked={contextCachingEnabled}
          />
          <span>{contextCachingEnabled ? "Enabled" : "Disabled"}</span>
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
          <div class="ui-subtitle mt-1">Coalesce identical requests in a short window (placeholder).</div>
        </div>
        <label class="flex items-center gap-2 text-xs" style="color: var(--text-primary);">
          <input
            type="checkbox"
            class="ui-focus h-4 w-4 rounded border"
            style="border-color: var(--border-subtle); background-color: var(--surface-2);"
            bind:checked={requestDedupEnabled}
          />
          <span>{requestDedupEnabled ? "Enabled" : "Disabled"}</span>
        </label>
      </div>

      <div class="mt-3 text-xs" style="color: var(--text-muted);">
        When enabled, identical requests may be collapsed into a single in-flight execution to reduce load.
      </div>
    </div>
  </div>
</div>
