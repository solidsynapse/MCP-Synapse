<script lang="ts">
  import { onMount } from "svelte";
  import {
    PHASE1_TTL_CACHE_OPS,
    PHASE1_TTL_CACHE_TTL_MS,
    uiBuildOpCacheKey,
    uiCacheGet,
    uiCacheSet,
    uiInvalidateOpCaches,
    uiRunDeduped,
    uiTraceOpCache,
  } from "$lib/ui_session";

  type Connection = {
    id: string;
    name: string;
    status: "running" | "stopped";
    providerId: ProviderId;
    modelId: string;
    location: "local" | "lan" | "remote";
    endpoint: string;
    credentialsPath?: string;
    options?: Record<string, string>;
    updatedAtLabel: string;
    tags: string[];
    configText: string;
  };

  type ProviderId = string;

  type ConnectionRecord = {
    id: string;
    connection_name: string;
    status?: string;
    provider_id: string;
    model_id: string;
    endpoint?: string;
    credentials_path?: string;
    options?: Record<string, unknown>;
  };

  type DispatchError = { code?: string; message: string; details?: unknown };
  type CanonicalErrorDetail = {
    code: string;
    provider?: string;
    model_id?: string;
    request_id?: string;
    reason: string;
    raw?: string;
  };

  type SchemaHintField = {
    id: string;
    label: string;
    required: boolean;
    kind: string;
    options?: Array<{ value: string; label: string }>;
    placeholder?: string;
    help?: string;
    section?: string;
  };

  type SchemaHint = {
    fields: SchemaHintField[];
    suggested_defaults?: Record<string, string>;
    defaults?: Record<string, string>;
    notes?: string[];
  };

  type DryRunTrace = {
    request_id: string;
    connection_id: string;
    connection_name: string;
    provider_id: string;
    model_id: string;
    preflight_result: {
      ok: boolean;
      errors_count: number;
      warnings_count: number;
    };
    canonical_config_hash: string;
    simulated_steps: string[];
    dry_run_result: string;
  };

  type ConnectionsResponse = {
    ok: boolean;
    status: string;
    text?: string | null;
    error?: DispatchError | null;
    errors?: string[];
    warnings?: string[];
    normalized_payload?: ConnectionRecord;
    connections?: ConnectionRecord[];
    config_text?: string | null;
    dry_run_trace?: DryRunTrace;
    schema_hint?: SchemaHint;
    data?: {
      fields?: SchemaHintField[];
      defaults?: Record<string, string>;
      notes?: string[];
      warnings?: string[];
      entries?: VaultEntry[];
      path?: string;
      id?: string;
      type?: string;
      mode?: string;
      source_name?: string;
      managed_path_present?: boolean;
    } | null;
  };

  type VaultEntry = {
    id: string;
    name: string;
    type: string;
    created_at?: string;
  };

  type DetailsConfigTab = "cursor" | "vscode" | "raw";

  let connections = $state<Connection[]>([]);
  let pageStatus = $state<"idle" | "loading" | "ready" | "error">("idle");
  const CONNECTIONS_OP = "connections.list";
  const CONNECTIONS_COPY_CONFIG_OP = "connections.copy_config";
  const CONNECTIONS_SCHEMA_HINT_OP = "connections.schema_hint";
  const CONNECTIONS_INTERACTION_TTL_MS = 5000;
  let busyById = $state<Record<string, boolean>>({});

  let query = $state("");
  let statusFilter = $state<"all" | "running" | "stopped">("all");

  type BannerKind = "idle" | "info" | "success" | "danger";
  let bannerKind = $state<BannerKind>("idle");
  let bannerText = $state("");
  let bannerDebugDetail = $state("");
  let bannerTimer: ReturnType<typeof setTimeout> | null = null;

  let detailsOpen = $state(false);
  let detailsId = $state<string | null>(null);
  let detailsConfigTab = $state<DetailsConfigTab>("cursor");

  let deleteConfirmOpen = $state(false);
  let deleteConfirmId = $state<string | null>(null);

  let newWizardOpen = $state(false);
  let wizardMode = $state<"create" | "edit">("create");
  let editingConnectionId = $state<string | null>(null);
  let vaultEntries = $state<VaultEntry[]>([]);
  let vaultStatus = $state<"idle" | "loading" | "ready" | "error">("idle");
  let vaultNoticeKind = $state<BannerKind>("idle");
  let vaultNoticeText = $state("");
  let vaultPickerOpen = $state(false);
  let vaultTargetFieldId = $state<string | null>(null);
  let vaultName = $state("");
  let vaultSecret = $state("");
  let vaultBusy = $state(false);
  let vaultDeleteBusyId = $state<string | null>(null);
  let helperOpenId = $state<string | null>(null);
  type ProviderOption = {
    id: ProviderId;
    label: string;
    category: "llm" | "rest";
    earlyAccess?: boolean;
    infoNote?: string;
  };
  const PROVIDERS: ProviderOption[] = [
    { id: "openai", label: "OpenAI", category: "llm" },
    { id: "azure_openai", label: "Azure OpenAI", category: "llm" },
    { id: "anthropic", label: "Anthropic", category: "llm" },
    { id: "groq", label: "Groq", category: "llm" },
    { id: "gemini", label: "Gemini", category: "llm" },
    { id: "openrouter", label: "OpenRouter", category: "llm" },
    { id: "deepseek", label: "DeepSeek", category: "llm" },
    { id: "xai", label: "xAI (Grok)", category: "llm" },
    { id: "vertex", label: "Vertex AI", category: "llm" },
    {
      id: "bedrock",
      label: "Amazon Bedrock",
      category: "llm",
      earlyAccess: true,
      infoNote: "Coded but not runtime-tested by the development team. Use at your own risk.",
    },
    { id: "huggingface", label: "Hugging Face", category: "llm" },
    { id: "ollama", label: "Ollama", category: "llm" },
    { id: "rest_api", label: "Custom REST API", category: "rest" },
  ];

  let newWizardProvider = $state<ProviderId | null>(null);
  let providerQuery = $state("");
  let providerMenuOpen = $state(false);
  let providerPickerEl = $state<HTMLDivElement | null>(null);
  let newWizardName = $state("");
  let newWizardValues = $state<Record<string, string>>({});
  let newWizardSchemaHint = $state<SchemaHint | null>(null);
  let newWizardSchemaStatus = $state<"idle" | "loading" | "ready" | "error">("idle");
  let newWizardNoticeKind = $state<BannerKind>("idle");
  let newWizardNoticeText = $state("");
  let newWizardDebugDetail = $state("");
  let schemaHintRequestSeq = 0;
  let schemaHintLoadingProviderId = "";
  const copyConfigInFlight = new Map<string, Promise<string>>();
  const DETAILS_CONFIG_TABS: Array<{ id: DetailsConfigTab; label: string }> = [
    { id: "cursor", label: "Cursor / Windsurf" },
    { id: "vscode", label: "VS Code" },
    { id: "raw", label: "Other / Raw" },
  ];
  function formatErrors(errors: string[] | undefined) {
    if (!errors || errors.length === 0) return "Unknown error.";
    return errors.join("; ");
  }

  function firstErrorReason(errors: string[] | undefined) {
    if (!errors || errors.length === 0) return "Unknown error.";
    const first = String(errors[0] || "").trim();
    if (!first) return "Unknown error.";
    return first;
  }

  function buildCanonicalErrorDetail(result: ConnectionsResponse): CanonicalErrorDetail {
    const reason = firstErrorReason(result.errors);
    const provider = String(result.normalized_payload?.provider_id || "").trim();
    const modelId = String(result.normalized_payload?.model_id || "").trim();
    const requestId = "";
    const code = String(result.error?.code || "invalid_request").trim() || "invalid_request";
    return {
      code,
      provider: provider || undefined,
      model_id: modelId || undefined,
      request_id: requestId || undefined,
      reason,
    };
  }

  function canonicalErrorDetailText(detail: CanonicalErrorDetail | null) {
    if (!detail) return "";
    const parts: string[] = [];
    parts.push(`code=${detail.code}`);
    if (detail.provider) parts.push(`provider=${detail.provider}`);
    if (detail.model_id) parts.push(`model_id=${detail.model_id}`);
    if (detail.request_id) parts.push(`request_id=${detail.request_id}`);
    return parts.join(" ");
  }

  function formatSchemaHintError(error: DispatchError | null | undefined) {
    const code = String(error?.code || "schema_hint_failed").trim();
    const message = String(error?.message || "Schema hint request failed.").trim();
    return `${code}: ${message}`;
  }

  function safeParseConfigText(text: string) {
    try {
      return JSON.parse(text) as Record<string, unknown>;
    } catch {
      return null;
    }
  }

  function formatConfigText(value: unknown) {
    return JSON.stringify(value, null, 2);
  }

  function buildCursorConfigText(rawText: string) {
    const parsed = safeParseConfigText(rawText);
    if (!parsed || typeof parsed !== "object" || !parsed.mcpServers) return rawText;
    return formatConfigText(parsed);
  }

  function buildVsCodeConfigText(rawText: string) {
    const parsed = safeParseConfigText(rawText);
    const rawServers = parsed?.mcpServers;
    if (!rawServers || typeof rawServers !== "object") return rawText;

    const servers: Record<string, { type: string; url: string }> = {};
    for (const [name, value] of Object.entries(rawServers)) {
      if (!value || typeof value !== "object") continue;
      const entry = value as Record<string, unknown>;
      const url = String(entry.url || "").trim();
      if (!url) continue;
      const type = String(entry.type || "sse").trim() || "sse";
      servers[name] = { type, url };
    }
    return formatConfigText({ servers });
  }

  function getDetailsConfigText(rawText: string, tab: DetailsConfigTab) {
    if (tab === "vscode") return buildVsCodeConfigText(rawText);
    if (tab === "cursor") return buildCursorConfigText(rawText);
    return rawText;
  }

  function getDetailsCopyLabel(tab: DetailsConfigTab) {
    if (tab === "vscode") return "VS Code";
    if (tab === "cursor") return "Cursor / Windsurf";
    return "Raw";
  }

  function formatWarnings(warnings: string[] | undefined) {
    if (!warnings || warnings.length === 0) return "";
    return warnings.join("; ");
  }

  function formatDryRunTrace(trace: DryRunTrace) {
    const preflight = trace.preflight_result;
    const preflightLabel = `${preflight.ok ? "ok" : "fail"}(${preflight.errors_count}e/${preflight.warnings_count}w)`;
    return `Preflight passed (offline dry-run). Connection: ${trace.connection_name} - Provider: ${trace.provider_id} - Model: ${trace.model_id} - Preflight: ${preflightLabel}`;
  }

  function normalizeSchemaCandidate(candidate: any): SchemaHint | null {
    if (!candidate || !Array.isArray(candidate.fields)) return null;
    return {
      fields: candidate.fields,
      suggested_defaults: candidate.suggested_defaults ?? candidate.defaults ?? {},
      notes: candidate.notes ?? [],
    };
  }

  function normalizeSchemaHint(result: ConnectionsResponse): SchemaHint | null {
    const fromData = normalizeSchemaCandidate(result?.data);
    if (fromData) return fromData;

    const fromSchemaHint = normalizeSchemaCandidate(result?.schema_hint);
    if (fromSchemaHint) return fromSchemaHint;

    const fromNestedDataSchemaHint = normalizeSchemaCandidate((result as any)?.data?.schema_hint);
    if (fromNestedDataSchemaHint) return fromNestedDataSchemaHint;

    const text = typeof result?.text === "string" ? result.text.trim() : "";
    if (!text) return null;
    try {
      const parsed = JSON.parse(text);
      return (
        normalizeSchemaCandidate(parsed?.data) ??
        normalizeSchemaCandidate(parsed?.schema_hint) ??
        normalizeSchemaCandidate(parsed?.data?.schema_hint) ??
        normalizeSchemaCandidate(parsed)
      );
    } catch {
      return null;
    }
  }

  function toUiConnections(list: ConnectionRecord[]) {
    return list.map((connection) => ({
      id: connection.id,
      name: connection.connection_name,
      status: connection.status === "running" ? "running" : "stopped",
      providerId: connection.provider_id,
      modelId: connection.model_id,
      location: "remote",
      endpoint: connection.endpoint ?? "",
      credentialsPath: connection.credentials_path,
      options: Object.fromEntries(
        Object.entries(connection.options ?? {}).map(([k, v]) => [String(k), String(v ?? "")])
      ),
      updatedAtLabel: "Persisted",
      tags: [connection.provider_id],
      configText: "",
    })) as Connection[];
  }

  const providerOptions = $derived(() => PROVIDERS);
  let providerHighlightIndex = $state<number>(-1);

  function providerLabel(id: ProviderId | null) {
    if (!id) return "";
    return PROVIDERS.find((p) => p.id === id)?.label ?? id;
  }

  function providerOptionById(id: ProviderId | null) {
    if (!id) return null;
    return PROVIDERS.find((p) => p.id === id) ?? null;
  }

  function providerCategoryLabel(category: ProviderOption["category"]) {
    return category === "rest" ? "REST Sources" : "Language Models";
  }

  function openProviderPicker() {
    providerMenuOpen = true;
    const selectedIndex = providerOptions().findIndex((p) => p.id === newWizardProvider);
    providerHighlightIndex = selectedIndex >= 0 ? selectedIndex : 0;
  }

  function closeProviderPicker() {
    providerMenuOpen = false;
    providerHighlightIndex = -1;
  }

  function toggleProviderPicker() {
    if (providerMenuOpen) {
      closeProviderPicker();
      return;
    }
    openProviderPicker();
  }

  function handleProviderPointerDown(event: PointerEvent) {
    event.preventDefault();
    event.stopPropagation();
    toggleProviderPicker();
  }

  function handleProviderFocusOut(event: FocusEvent) {
    const next = event.relatedTarget as Node | null;
    if (next && providerPickerEl?.contains(next)) return;
    closeProviderPicker();
  }

  async function selectProvider(id: ProviderId) {
    const sameProvider = id === newWizardProvider;
    newWizardProvider = id;
    providerQuery = providerLabel(id);
    providerMenuOpen = false;
    providerHighlightIndex = -1;
    if (sameProvider && newWizardSchemaStatus === "ready" && newWizardSchemaHint) return;
    await loadNewWizardSchemaHint(id, "new_provider_select");
  }

  function setNewWizardNotice(kind: BannerKind, text: string, debugDetail = "") {
    newWizardNoticeKind = kind;
    newWizardNoticeText = text;
    newWizardDebugDetail = debugDetail;
    setBanner(kind, text, debugDetail);
  }

  function clearNewWizardNotice() {
    newWizardNoticeKind = "idle";
    newWizardNoticeText = "";
    newWizardDebugDetail = "";
  }

  function setVaultNotice(kind: BannerKind, text: string) {
    vaultNoticeKind = kind;
    vaultNoticeText = text;
  }

  function clearVaultNotice() {
    vaultNoticeKind = "idle";
    vaultNoticeText = "";
  }

  function inferVaultEntryType() {
    const fieldId = String(vaultTargetFieldId || "").trim().toLowerCase();
    if (fieldId === "credentials_path" || fieldId.endsWith("_path") || fieldId.includes("credential")) {
      return "credentials_path";
    }
    if (fieldId === "api_key" || fieldId.includes("api_key") || fieldId.includes("token") || fieldId.includes("secret")) {
      return "api_key";
    }
    return "api_key";
  }

  function isLocalBridgeEndpoint(value: string) {
    const v = String(value || "").trim();
    return /^https?:\/\/(?:127\.0\.0\.1|localhost):\d+\/sse$/i.test(v);
  }

  function helperCopy(fieldId: string) {
    const id = String(fieldId || "").trim().toLowerCase();
    if (id === "model_id") {
      return "Use the exact provider model ID. Placeholder examples show a valid format.";
    }
    if (id === "credential_source") {
      return "File mode uses Credentials path. Manual mode uses AWS keys. API Key mode uses Bedrock bearer token.";
    }
    if (id === "endpoint") {
      if (newWizardProvider === "ollama") {
        return "Ollama base URL. Local default is http://127.0.0.1:11434.";
      }
      if (newWizardProvider === "huggingface") {
        return "HF OpenAI-compatible base URL. Leave blank to use default (https://router.huggingface.co/v1).";
      }
      return "Leave empty to use core defaults. Set only if your provider requires a custom base URL.";
    }
    if (id === "credentials_path") {
      if (newWizardProvider === "huggingface") {
        return "Path (or vault:// reference) for your HF access token. Use Browse or Vault.";
      }
      return "Local credentials file path. Use Browse or Vault to fill this value.";
    }
    if (id === "hf_enable_network") {
      return "Safety rail for live calls. Keep Disabled unless you explicitly want outbound HF requests.";
    }
    if (id === "aws_access_key_id" || id === "aws_secret_access_key" || id === "aws_session_token") {
      return "Bedrock manual credentials fields. Session token is optional for temporary credentials.";
    }
    if (id === "bedrock_api_key") {
      return "Bedrock API bearer token (ABSK...). Required when Credential source is API Key.";
    }
    return "";
  }

  function fieldHelpText(field: SchemaHintField): string {
    const rawHelp = String(field.help ?? "").trim();
    if (!rawHelp) return "";
    const fieldId = String(field.id || "").trim().toLowerCase();
    if (fieldId === "credentials_path") {
      return rawHelp.replace(/^optional\s+/i, "");
    }
    return rawHelp;
  }

  function toggleHelper(fieldId: string) {
    const id = String(fieldId || "").trim();
    helperOpenId = helperOpenId === id ? null : id;
  }

  function isVaultCredentialsPathType() {
    return inferVaultEntryType() === "credentials_path";
  }

  async function triggerVaultCredentialsBrowse() {
    clearVaultNotice();
    try {
      const result = await dispatchInvoke({ op: "vault.pick_credentials_path" });
      const selected = result.ok ? String(result.data?.path ?? "").trim() : "";
      if (selected) {
        vaultSecret = selected;
        return;
      }
      if (!result.ok) {
        setVaultNotice("danger", result.error?.message || "File picker unavailable.");
      }
      return;
    } catch {
      // Fallback below keeps compatibility if picker dispatch is unavailable at runtime.
    }

    const el = document.getElementById("vault-credentials-file") as HTMLInputElement | null;
    el?.click();
  }

  function onVaultCredentialsFileSelected(event: Event) {
    const input = event.currentTarget as HTMLInputElement | null;
    const file = input?.files?.[0];
    if (!file) return;
    const tauriPath = String((file as any).path ?? "").trim();
    if (tauriPath) {
      vaultSecret = tauriPath;
    } else {
      setVaultNotice("danger", "Native file path unavailable. Please use the Tauri file picker.");
    }
    if (input) input.value = "";
  }

  function validateCredentialsPathValue(pathValue: string): string | null {
    const value = String(pathValue || "").trim();
    if (!value) return null;
    if (value.toLowerCase().startsWith("vault://")) return null;
    const unquoted = value.replace(/^['"]+|['"]+$/g, "");
    const hasSeparator = unquoted.includes("\\") || unquoted.includes("/") || unquoted.includes(":");
    if (!hasSeparator) {
      return "Credentials path looks invalid. Use Browse to select a file path.";
    }
    return null;
  }

  async function loadVaultEntries() {
    vaultStatus = "loading";
    clearVaultNotice();
    try {
      const result = await dispatchInvoke({ op: "vault.list" });
      const entries = result.ok ? (result.data?.entries ?? []) : [];
      vaultEntries = Array.isArray(entries) ? entries : [];
      if (result.ok) {
        vaultStatus = "ready";
        return;
      }
      vaultStatus = "error";
      setVaultNotice("danger", result.error?.message || "Vault list failed");
    } catch (err: any) {
      vaultStatus = "error";
      setVaultNotice("danger", err?.message || "Vault list failed");
    }
  }

  async function openVaultPicker(fieldId: string) {
    vaultTargetFieldId = fieldId;
    vaultPickerOpen = true;
    await loadVaultEntries();
  }

  function closeVaultPicker() {
    vaultPickerOpen = false;
    vaultTargetFieldId = null;
    vaultName = "";
    vaultSecret = "";
    vaultBusy = false;
    vaultDeleteBusyId = null;
    clearVaultNotice();
  }

  async function createVaultEntry() {
    if (vaultBusy) return;
    const name = vaultName.trim();
    const type = inferVaultEntryType();
    const secret = vaultSecret;
    if (!name || !secret) {
      setVaultNotice("danger", "Name and secret are required.");
      return;
    }
    if (type === "credentials_path") {
      const validationMessage = validateCredentialsPathValue(secret);
      if (validationMessage) {
        setVaultNotice("danger", validationMessage);
        return;
      }
    }
    if (!type) {
      setVaultNotice("danger", "Vault type resolution failed.");
      return;
    }
    vaultBusy = true;
    try {
      const importMode = type === "credentials_path" ? "credentials_file" : "plain";
      const result = await dispatchInvoke({ op: "vault.create", entry: { name, type, secret, import_mode: importMode } });
      if (result.ok) {
        vaultName = "";
        vaultSecret = "";
        await loadVaultEntries();
        setVaultNotice("success", "Vault entry saved.");
      } else {
        setVaultNotice("danger", result.error?.message || "Vault save failed");
      }
    } catch (err: any) {
      setVaultNotice("danger", err?.message || "Vault save failed");
    } finally {
      vaultBusy = false;
    }
  }

  async function useVaultEntry(entry: VaultEntry) {
    if (vaultBusy || !vaultTargetFieldId) return;
    const entryId = String(entry.id || "").trim();
    const entryName = String(entry.name || "").trim() || "Selected vault entry";
    if (vaultTargetFieldId === "credentials_path") {
      updateWizardField(vaultTargetFieldId, `vault://${entryId}`);
      closeVaultPicker();
      return;
    }
    vaultBusy = true;
    try {
      const result = await dispatchInvoke({ op: "vault.read", entry_id: entryId });
      if (result.ok) {
        const entryType = String(result.data?.type || entry.type || "").trim();
        const mode = String(result.data?.mode || "").trim();
        const sourceName = String(result.data?.source_name || "").trim();
        const details = [entryType, mode, sourceName].filter((value) => value.length > 0).join(" / ");
        const suffix = details ? ` (${details})` : "";
        setVaultNotice(
          "info",
          `${entryName}${suffix} is metadata-only. Raw secret autofill is disabled; enter the value manually.`,
        );
        return;
      }
      setVaultNotice("danger", result.error?.message || "Vault read failed");
    } catch (err: any) {
      setVaultNotice("danger", err?.message || "Vault read failed");
    } finally {
      vaultBusy = false;
    }
  }

  async function deleteVaultEntry(entryId: string) {
    if (vaultBusy) return;
    vaultDeleteBusyId = entryId;
    try {
      const result = await dispatchInvoke({ op: "vault.delete", entry_id: entryId });
      if (result.ok) {
        await loadVaultEntries();
        setVaultNotice("success", "Vault entry deleted.");
      } else {
        setVaultNotice("danger", result.error?.message || "Vault delete failed");
      }
    } catch (err: any) {
      setVaultNotice("danger", err?.message || "Vault delete failed");
    } finally {
      vaultDeleteBusyId = null;
    }
  }

  async function loadNewWizardSchemaHint(providerId: ProviderId, source: "edit_open" | "new_provider_select") {
    const providerKey = String(providerId || "").trim().toLowerCase();
    if (!providerKey) return;
    if (schemaHintLoadingProviderId === providerKey) {
      return;
    }
    const requestSeq = ++schemaHintRequestSeq;
    schemaHintLoadingProviderId = providerKey;
    newWizardSchemaStatus = "loading";
    newWizardSchemaHint = null;
    clearNewWizardNotice();
    const cacheKey = uiBuildOpCacheKey(
      CONNECTIONS_SCHEMA_HINT_OP,
      { op: CONNECTIONS_SCHEMA_HINT_OP, provider_id: providerId },
      { route: "/connections", flow: "new_wizard" },
    );
    try {
      const cached = uiCacheGet<SchemaHint>(cacheKey, CONNECTIONS_INTERACTION_TTL_MS);
      uiTraceOpCache({
        op: CONNECTIONS_SCHEMA_HINT_OP,
        status: cached ? "HIT" : "MISS",
        route: "/connections",
        source,
        reason: "interaction_ttl_lookup",
        key: cacheKey,
      });
      if (cached) {
        if (requestSeq !== schemaHintRequestSeq) return;
        newWizardSchemaHint = cached;
        newWizardSchemaStatus = "ready";
        const defaults = cached.suggested_defaults ?? {};
        const next = { ...newWizardValues };
        for (const [k, v] of Object.entries(defaults)) {
          const existing = String(next[k] ?? "").trim();
          if (!existing) next[k] = String(v ?? "");
        }
        newWizardValues = next;
        clearNewWizardNotice();
        return;
      }

      const result = await uiRunDeduped(
        cacheKey,
        async () =>
          await dispatchInvoke({
            op: CONNECTIONS_SCHEMA_HINT_OP,
            provider_id: providerId,
            _trace_source: source,
          }),
      );
      if (requestSeq !== schemaHintRequestSeq) return;
      const normalized = normalizeSchemaHint(result);
      if (!result.ok && result.error?.code === "desktop_required") {
        newWizardSchemaStatus = "idle";
        newWizardSchemaHint = null;
        setNewWizardNotice("info", "Desktop app required for schema hints. Showing fallback fields.");
        return;
      }
      const hint = normalized;
      if (result.ok) {
        if (hint) {
          newWizardSchemaHint = hint;
          newWizardSchemaStatus = "ready";
          uiCacheSet(cacheKey, hint);
          const defaults = hint.suggested_defaults ?? {};
          const next = { ...newWizardValues };
          for (const [k, v] of Object.entries(defaults)) {
            const existing = String(next[k] ?? "").trim();
            if (!existing) next[k] = String(v ?? "");
          }
          newWizardValues = next;
        } else {
          newWizardSchemaStatus = "idle";
        }
        clearNewWizardNotice();
        return;
      }
      newWizardSchemaStatus = "error";
      setNewWizardNotice("danger", `Schema hint failed: ${formatSchemaHintError(result.error)}`);
    } catch (err: any) {
      newWizardSchemaStatus = "error";
      setNewWizardNotice("danger", `Schema hint failed: ${err?.message || String(err)}`);
    } finally {
      if (schemaHintLoadingProviderId === providerKey) {
        schemaHintLoadingProviderId = "";
      }
    }
  }

  const newWizardFields = $derived(() => newWizardSchemaHint?.fields ?? []);
  const newWizardNameField = $derived(() => newWizardFields().find((f) => f.id === "connection_name") ?? null);

  const newWizardGlobalRequiredFields = $derived(() => {
    const commonFields = newWizardFields().filter((f) => (f.section || "common") === "common");
    return commonFields.slice(0, 2);
  });

  const newWizardProviderFields = $derived(() => {
    const globalIds = new Set(newWizardGlobalRequiredFields().map((f) => String(f.id || "").trim()));
    return newWizardFields().filter((f) => !globalIds.has(String(f.id || "").trim()));
  });

  const fallbackWizardCommonFields: SchemaHintField[] = [
    {
      id: "model_id",
      label: "Model ID",
      required: true,
      kind: "text",
      placeholder: "",
      help: "Model identifier for the selected provider.",
      section: "common",
    },
  ];

  const fallbackWizardAdvancedFields: SchemaHintField[] = [
    {
      id: "endpoint",
      label: "Endpoint / Base URL",
      required: false,
      kind: "text",
      placeholder: "Optional override",
      help: "Optional provider endpoint override. Leave blank to use core defaults.",
      section: "advanced",
    },
    {
      id: "credentials_path",
      label: "Credentials path",
      required: false,
      kind: "text",
      placeholder: "C:\\path\\to\\credentials.json",
      help: "Path to a local credentials file used by the core runtime.",
      section: "advanced",
    },
  ];

  const effectiveNewWizardCommonFields = $derived(() => {
    return newWizardFields().length > 0 ? newWizardGlobalRequiredFields() : fallbackWizardCommonFields;
  });

  const effectiveNewWizardProviderFields = $derived(() => {
    return newWizardFields().length > 0 ? newWizardProviderFields() : fallbackWizardAdvancedFields;
  });

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

  function setBanner(kind: BannerKind, text: string, debugDetail = "") {
    if (bannerTimer) {
      clearTimeout(bannerTimer);
      bannerTimer = null;
    }
    bannerKind = kind;
    bannerText = text;
    bannerDebugDetail = debugDetail;
    if (kind !== "idle" && text) {
      bannerTimer = setTimeout(() => {
        bannerKind = "idle";
        bannerText = "";
        bannerDebugDetail = "";
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
    bannerDebugDetail = "";
  }

  async function dispatchInvoke(promptPayload: Record<string, unknown>): Promise<ConnectionsResponse> {
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
      agentId: "connections",
      agent_id: "connections",
      prompt,
    }) as ConnectionsResponse;
  }

  function connectionsActiveFilters() {
    return {
      query: String(query || "").trim().toLowerCase(),
      status: statusFilter,
    };
  }

  function connectionsCacheKey() {
    return uiBuildOpCacheKey(CONNECTIONS_OP, { op: CONNECTIONS_OP }, connectionsActiveFilters());
  }

  async function refreshConnections(forceRefresh = false, source = "connections.refresh") {
    if (pageStatus === "idle" && connections.length === 0) {
      pageStatus = "loading";
    }
    setBanner("idle", "");
    const cacheKey = connectionsCacheKey();
    if (forceRefresh) {
      uiInvalidateOpCaches(PHASE1_TTL_CACHE_OPS, {
        reason: "global_refresh_event",
        source,
        route: "/connections",
      });
    }
    try {
      const cached = uiCacheGet<Connection[]>(cacheKey, PHASE1_TTL_CACHE_TTL_MS);
      uiTraceOpCache({
        op: CONNECTIONS_OP,
        status: cached ? "HIT" : "MISS",
        route: "/connections",
        source,
        reason: "ttl_lookup",
        key: cacheKey,
      });
      if (cached) {
        connections = cached;
        pageStatus = "ready";
        return;
      }
      const result = await uiRunDeduped(cacheKey, async () => await dispatchInvoke({ op: CONNECTIONS_OP }));

      if (result.ok) {
        const next = toUiConnections(result.connections ?? []);
        connections = next;
        uiCacheSet(cacheKey, next);
        pageStatus = "ready";
        return;
      }

      pageStatus = "error";
      const detail = buildCanonicalErrorDetail(result);
      setBanner("danger", `Failed to load connections: ${detail.reason}`, canonicalErrorDetailText(detail));
    } catch (err: any) {
      pageStatus = "error";
      setBanner("danger", `Failed to load connections: ${err?.message || String(err)}`);
    }
  }

  async function toggleConnection(connectionId: string) {
    busyById = { ...busyById, [connectionId]: true };
    setBanner("idle", "");
    try {
      const current = connections.find((connection) => connection.id === connectionId);
      const op = current?.status === "running" ? "connections.stop" : "connections.start";
      const result = await dispatchInvoke({ op, connection_id: connectionId });
      if (result.ok) {
        uiInvalidateOpCaches(PHASE1_TTL_CACHE_OPS, {
          reason: op === "connections.stop" ? "connections.stop_success" : "connections.start_success",
          source: "connections.toggle",
          route: "/connections",
        });
        await refreshConnections(false, "connections.toggle.after_success");
        setBanner("success", op === "connections.stop" ? "Connection stopped." : "Connection started.");
      } else {
        const detail = buildCanonicalErrorDetail(result);
        setBanner("danger", `${op === "connections.stop" ? "Stop" : "Start"} failed: ${detail.reason}`, canonicalErrorDetailText(detail));
      }
    } catch (err: any) {
      setBanner("danger", `Start/stop failed: ${err?.message || String(err)}`);
    } finally {
      busyById = { ...busyById, [connectionId]: false };
    }
  }

  async function testConnection(connectionId: string) {
    busyById = { ...busyById, [connectionId]: true };
    setBanner("idle", "");
    try {
      const result = await dispatchInvoke({ op: "connections.dry_run", connection_id: connectionId });
      if (result.ok && result.dry_run_trace) {
        setBanner("info", formatDryRunTrace(result.dry_run_trace));
      } else {
        const detail = buildCanonicalErrorDetail(result);
        setBanner("danger", `Dry-run failed: ${detail.reason}`, canonicalErrorDetailText(detail));
      }
    } catch (err: any) {
      setBanner("danger", `Dry-run failed: ${err?.message || String(err)}`);
    } finally {
      busyById = { ...busyById, [connectionId]: false };
    }
  }

  async function copyConnectionConfig(connectionId: string) {
    if (busyById[connectionId] === true) return;
    busyById = { ...busyById, [connectionId]: true };
    setBanner("idle", "");

    const text = await fetchConnectionConfig(connectionId, false, "copy_button");
    if (!text) return;

    try {
      await navigator.clipboard.writeText(text);
      setBanner("success", "MCP config copied to clipboard.");
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
      setBanner("success", "MCP config copied to clipboard.");
    } finally {
      busyById = { ...busyById, [connectionId]: false };
    }
  }

  async function copyDetailsConfig(connection: Connection, tab: DetailsConfigTab) {
    if (busyById[connection.id] === true) return;
    busyById = { ...busyById, [connection.id]: true };
    setBanner("idle", "");

    let rawText = connection.configText || "";
    if (!rawText) {
      rawText = await fetchConnectionConfig(connection.id, false, "details_open");
      if (rawText) {
        connections = connections.map((item) => (item.id === connection.id ? { ...item, configText: rawText } : item));
      }
    }
    if (!rawText) {
      busyById = { ...busyById, [connection.id]: false };
      return;
    }

    const text = getDetailsConfigText(rawText, tab);
    try {
      await navigator.clipboard.writeText(text);
      setBanner("success", `${getDetailsCopyLabel(tab)} config copied to clipboard.`);
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
      setBanner("success", `${getDetailsCopyLabel(tab)} config copied to clipboard.`);
    } finally {
      busyById = { ...busyById, [connection.id]: false };
    }
  }

  function resetFilters() {
    query = "";
    statusFilter = "all";
  }

  async function openDetails(connectionId: string) {
    detailsId = connectionId;
    detailsOpen = true;
    detailsConfigTab = "cursor";
    const existing = connections.find((connection) => connection.id === connectionId);
    if (existing?.configText) return;
    const text = await fetchConnectionConfig(connectionId, false, "details_open");
    if (text) {
      connections = connections.map((connection) =>
        connection.id === connectionId ? { ...connection, configText: text } : connection
      );
    }
  }

  function closeDetails() {
    detailsOpen = false;
    detailsId = null;
    detailsConfigTab = "cursor";
  }

  function openDeleteConfirm(connectionId: string) {
    deleteConfirmId = connectionId;
    deleteConfirmOpen = true;
  }

  function closeDeleteConfirm() {
    deleteConfirmOpen = false;
    deleteConfirmId = null;
  }

  async function fetchConnectionConfig(
    connectionId: string,
    verbose: boolean,
    source: "details_open" | "copy_button" | "copy_debug",
  ) {
    const inFlightKey = `${String(connectionId || "").trim()}|${verbose ? "1" : "0"}`;
    const inFlight = copyConfigInFlight.get(inFlightKey);
    if (inFlight) {
      return await inFlight;
    }

    const cacheKey = uiBuildOpCacheKey(
      CONNECTIONS_COPY_CONFIG_OP,
      { op: CONNECTIONS_COPY_CONFIG_OP, connection_id: connectionId, verbose },
      { route: "/connections", flow: "details_copy" },
    );
    const cached = uiCacheGet<string>(cacheKey, CONNECTIONS_INTERACTION_TTL_MS);
    uiTraceOpCache({
      op: CONNECTIONS_COPY_CONFIG_OP,
      status: cached ? "HIT" : "MISS",
      route: "/connections",
      source,
      reason: "interaction_ttl_lookup",
      key: cacheKey,
    });
    if (cached) return cached;
    const request = (async () => {
      try {
        const result = await uiRunDeduped(
          cacheKey,
          async () =>
            await dispatchInvoke({
              op: CONNECTIONS_COPY_CONFIG_OP,
              connection_id: connectionId,
              verbose,
              _trace_source: source,
            }),
        );
        if (result.ok && result.config_text) {
          uiCacheSet(cacheKey, result.config_text);
          return result.config_text;
        }
        const detail = buildCanonicalErrorDetail(result);
        setBanner("danger", `Copy Config failed: ${detail.reason}`, canonicalErrorDetailText(detail));
      } catch (err: any) {
        setBanner("danger", `Copy Config failed: ${err?.message || String(err)}`);
      }
      return "";
    })();

    copyConfigInFlight.set(inFlightKey, request);
    try {
      return await request;
    } finally {
      if (copyConfigInFlight.get(inFlightKey) === request) {
        copyConfigInFlight.delete(inFlightKey);
      }
    }
  }

  async function confirmDelete() {
    const id = deleteConfirmId;
    if (!id) return;
    closeDeleteConfirm();
    busyById = { ...busyById, [id]: true };
    setBanner("idle", "");
    try {
      const result = await dispatchInvoke({ op: "connections.delete", connection_id: id });
      if (result.ok) {
        uiInvalidateOpCaches(PHASE1_TTL_CACHE_OPS, {
          reason: "connections.delete_success",
          source: "connections.delete",
          route: "/connections",
        });
        await refreshConnections(false, "connections.delete.after_success");
        setBanner("success", "Connection deleted.");
      } else {
        const detail = buildCanonicalErrorDetail(result);
        setBanner("danger", `Delete failed: ${detail.reason}`, canonicalErrorDetailText(detail));
      }
    } catch (err: any) {
      setBanner("danger", `Delete failed: ${err?.message || String(err)}`);
    } finally {
      busyById = { ...busyById, [id]: false };
    }
  }

  function openNewWizard() {
    wizardMode = "create";
    editingConnectionId = null;
    newWizardOpen = true;
    helperOpenId = null;
    newWizardProvider = null;
    providerQuery = "";
    providerMenuOpen = false;
    newWizardName = "";
    newWizardValues = {};
    newWizardSchemaHint = null;
    newWizardSchemaStatus = "idle";
    clearNewWizardNotice();
  }

  function closeNewWizard() {
    newWizardOpen = false;
    wizardMode = "create";
    editingConnectionId = null;
    helperOpenId = null;
  }

  function updateWizardField(fieldKey: string, value: string) {
    newWizardValues = { ...newWizardValues, [fieldKey]: value };
  }

  function isCredentialsField(fieldId: string) {
    return String(fieldId || "").trim() === "credentials_path";
  }

  async function triggerCredentialsBrowse(fieldId: string, inputId: string) {
    try {
      const result = await dispatchInvoke({ op: "vault.pick_credentials_path" });
      const selected = String(result.data?.path ?? "").trim();
      if (result.ok && selected) {
        updateWizardField(fieldId, selected);
        return;
      }
    } catch {
      // Fall back to native file input below.
    }
    const el = document.getElementById(inputId) as HTMLInputElement | null;
    el?.click();
  }

  function onCredentialsFileSelected(fieldId: string, event: Event) {
    const input = event.currentTarget as HTMLInputElement | null;
    const file = input?.files?.[0];
    if (!file) return;
    const tauriPath = String((file as any).path ?? "").trim();
    if (tauriPath) {
      updateWizardField(fieldId, tauriPath);
    }
    if (input) input.value = "";
  }

  function fieldKind(field: SchemaHintField) {
    const kind = String(field.kind ?? "").trim().toLowerCase();
    return kind || "text";
  }

  function inputTypeForField(field: SchemaHintField) {
    return fieldKind(field) === "password" ? "password" : "text";
  }

  function fieldOptions(field: SchemaHintField) {
    const options = Array.isArray(field.options) ? field.options : [];
    return options
      .map((opt) => ({
        value: String(opt?.value ?? "").trim(),
        label: String(opt?.label ?? "").trim(),
      }))
      .filter((opt) => opt.value.length > 0);
  }

  function activeBedrockCredentialSource() {
    const provider = String(newWizardProvider ?? "").trim().toLowerCase();
    if (provider !== "bedrock") return "";
    const raw = String(newWizardValues.credential_source ?? "").trim().toLowerCase();
    if (raw === "manual") return "manual";
    if (raw === "api_key") return "api_key";
    return "file";
  }

  function activeRestAuthType() {
    const provider = String(newWizardProvider ?? "").trim().toLowerCase();
    if (provider !== "rest_api") return "";
    const raw = String(newWizardValues.auth_type ?? "none").trim().toLowerCase();
    if (raw === "api_key_header") return "api_key_header";
    if (raw === "bearer") return "bearer";
    if (raw === "basic") return "basic";
    return "none";
  }

  function isWizardFieldVisible(fieldId: string) {
    const id = String(fieldId || "").trim().toLowerCase();
    const source = activeBedrockCredentialSource();
    if (source) {
      if (id === "credentials_path") return source === "file";
      if (id === "aws_access_key_id" || id === "aws_secret_access_key" || id === "aws_session_token") {
        return source === "manual";
      }
      if (id === "bedrock_api_key") return source === "api_key";
      return true;
    }
    const restAuthType = activeRestAuthType();
    if (restAuthType) {
      if (id === "credentials_path") return restAuthType !== "none";
      return true;
    }
    return true;
  }

  function fieldLabel(field: SchemaHintField) {
    return String(field.label ?? field.id ?? "").trim() || String(field.id ?? "");
  }

  function inputAutocompleteForField(fieldId: string) {
    const id = String(fieldId || "").trim().toLowerCase();
    if (id === "credentials_path" || id === "aws_secret_access_key" || id === "aws_session_token" || id === "bedrock_api_key") {
      return "new-password";
    }
    return "off";
  }

  function modelPlaceholderForProvider(providerId: ProviderId | null): string {
    const id = String(providerId || "").trim().toLowerCase();
    if (id === "anthropic") return "Example: claude-3-5-sonnet-20241022";
    if (id === "groq") return "Example: llama-3.3-70b-versatile";
    if (id === "gemini") return "Example: gemini-1.5-flash";
    if (id === "openrouter") return "Example: openai/gpt-4o-mini";
    if (id === "deepseek") return "Example: deepseek-chat";
    if (id === "xai") return "Example: grok-3";
    if (id === "vertex") return "Example: gemini-2.0-flash-001";
    if (id === "azure_openai") return "Example: gpt-4o-mini-deploy";
    if (id === "openai") return "Example: gpt-4o-mini";
    if (id === "bedrock") return "Example: anthropic.claude-3-5-sonnet";
    if (id === "huggingface") return "Example: meta-llama/Llama-3.1-8B-Instruct";
    if (id === "ollama") return "Example: llama3.1";
    if (id === "rest_api") return "Hidden for REST adapter";
    return "Example: gpt-4o-mini";
  }

  function fieldPlaceholder(field: SchemaHintField) {
    const id = String(field.id || "").trim();
    if (id === "model_id") return modelPlaceholderForProvider(newWizardProvider);
    return String(field.placeholder || "");
  }

  const SSOT_GATE_TEXT = "Not wired in this phase (SSOT gate).";
  const COPY_CONFIG_TEXT = "Copy MCP config (canonical).";
  const TEST_OFFLINE_ONLY_TEXT = "Offline only (deterministic dry-run).";

  function buildNewWizardConnectionPayload() {
    const providerId = String(newWizardProvider ?? "").trim();
    const connectionName = String(newWizardName ?? "").trim();
    const payload: Record<string, string> = {
      connection_name: connectionName,
      provider_id: providerId,
    };

    const fields = newWizardFields();
    if (fields.length > 0) {
      for (const f of fields) {
        const id = String(f.id || "").trim();
        if (!id || id === "connection_name" || id === "provider_id") continue;
        if (!isWizardFieldVisible(id)) continue;
        const value = String(newWizardValues[id] ?? "").trim();
        if (!value) continue;
        payload[id] = value;
      }
      if (providerId === "bedrock") {
        const sourceRaw = String(newWizardValues.credential_source ?? payload.credential_source ?? "file").trim().toLowerCase();
        payload.credential_source = sourceRaw === "manual" ? "manual" : sourceRaw === "api_key" ? "api_key" : "file";
        if (payload.credential_source === "manual") {
          delete payload.credentials_path;
          delete payload.bedrock_api_key;
        } else if (payload.credential_source === "api_key") {
          delete payload.credentials_path;
          delete payload.aws_access_key_id;
          delete payload.aws_secret_access_key;
          delete payload.aws_session_token;
        } else {
          delete payload.aws_access_key_id;
          delete payload.aws_secret_access_key;
          delete payload.aws_session_token;
          delete payload.bedrock_api_key;
        }
      } else if (providerId === "azure_openai") {
        const deploymentName = String(payload.model_id ?? "").trim();
        if (deploymentName) {
          payload.deployment_name = deploymentName;
        }
      } else if (providerId === "ollama") {
        const ollamaBaseUrl = String(payload.endpoint ?? "").trim();
        if (ollamaBaseUrl) {
          payload.ollama_base_url = ollamaBaseUrl;
        }
      } else if (providerId === "huggingface") {
        const hfEndpoint = String(payload.endpoint ?? "").trim();
        if (hfEndpoint) {
          payload.hf_endpoint = hfEndpoint;
        }
      }
      return payload;
    }

    const modelId = String(newWizardValues.model_id ?? "").trim();
    if (modelId) payload.model_id = modelId;
    const endpoint = String(newWizardValues.endpoint ?? "").trim();
    if (endpoint) payload.endpoint = endpoint;
    const credentialsPath = String(newWizardValues.credentials_path ?? "").trim();
    if (credentialsPath) payload.credentials_path = credentialsPath;
    return payload;
  }

  async function preflightConnection() {
    busyById = { ...busyById, preflight: true };
    setBanner("idle", "");
    try {
      const connection = buildNewWizardConnectionPayload();
      const credentialsPath = String(connection.credentials_path ?? "").trim();
      const validationMessage = validateCredentialsPathValue(credentialsPath);
      if (validationMessage) {
        setNewWizardNotice("danger", validationMessage);
        return;
      }
      const result = await dispatchInvoke({
        op: "connections.preflight",
        connection,
      });

      if (result.ok) {
        const warningText = formatWarnings(result.warnings);
        if (warningText) {
          setNewWizardNotice("info", `Preflight warnings: ${warningText}`);
        } else {
          setNewWizardNotice("success", "Preflight OK.");
        }
        return;
      }

      const detail = buildCanonicalErrorDetail(result);
      setNewWizardNotice("danger", `Preflight failed: ${detail.reason}`, canonicalErrorDetailText(detail));
    } catch (err: any) {
      setNewWizardNotice("danger", `Preflight failed: ${err?.message || String(err)}`);
    } finally {
      busyById = { ...busyById, preflight: false };
    }
  }

  async function submitNewConnection() {
    busyById = { ...busyById, new: true };
    setBanner("idle", "");
    try {
      const connection = buildNewWizardConnectionPayload();
      const credentialsPath = String(connection.credentials_path ?? "").trim();
      const validationMessage = validateCredentialsPathValue(credentialsPath);
      if (validationMessage) {
        setNewWizardNotice("danger", validationMessage);
        return;
      }
      const op = wizardMode === "edit" ? "connections.update" : "connections.create";
      const payload: Record<string, unknown> = { op, connection };
      if (wizardMode === "edit" && editingConnectionId) {
        payload.connection_id = editingConnectionId;
      }
      const result = await dispatchInvoke(payload);

      if (result.ok) {
        uiInvalidateOpCaches(PHASE1_TTL_CACHE_OPS, {
          reason: wizardMode === "edit" ? "connections.update_success" : "connections.create_success",
          source: "connections.submit",
          route: "/connections",
        });
        connections = toUiConnections(result.connections ?? []);
        pageStatus = "ready";
        closeNewWizard();
        const warningText = formatWarnings(result.warnings);
        if (warningText) {
          setBanner("info", `${wizardMode === "edit" ? "Updated" : "Created"} with warnings: ${warningText}`);
        } else {
          setBanner("success", wizardMode === "edit" ? "Connection updated." : "Created connection.");
        }
        return;
      }

      const detail = buildCanonicalErrorDetail(result);
      setNewWizardNotice("danger", `${wizardMode === "edit" ? "Update" : "Create"} failed: ${detail.reason}`, canonicalErrorDetailText(detail));
    } catch (err: any) {
      setNewWizardNotice("danger", `${wizardMode === "edit" ? "Update" : "Create"} failed: ${err?.message || String(err)}`);
    } finally {
      busyById = { ...busyById, new: false };
    }
  }

  async function openEditWizard(connectionId: string) {
    const target = connections.find((connection) => connection.id === connectionId);
    if (!target) {
      setBanner("danger", "Edit failed: connection not found.");
      return;
    }

    wizardMode = "edit";
    editingConnectionId = connectionId;
    newWizardOpen = true;
    helperOpenId = null;
    newWizardProvider = target.providerId;
    providerQuery = providerLabel(target.providerId);
    providerMenuOpen = false;
    newWizardName = target.name;
    newWizardValues = {
      model_id: target.modelId,
      endpoint: target.endpoint || "",
      credentials_path: target.credentialsPath || "",
      ...(target.options ?? {}),
    };
    if (target.providerId === "azure_openai") {
      const mappedEndpoint = String((target.options ?? {})["azure_endpoint"] ?? "").trim();
      if (!mappedEndpoint && target.endpoint && !isLocalBridgeEndpoint(target.endpoint)) {
        newWizardValues = { ...newWizardValues, azure_endpoint: target.endpoint };
      }
      const mappedDeployment = String((target.options ?? {})["deployment_name"] ?? "").trim();
      if (mappedDeployment) {
        newWizardValues = { ...newWizardValues, model_id: mappedDeployment };
      }
    } else if (target.providerId === "groq") {
      const mappedBaseUrl = String((target.options ?? {})["groq_base_url"] ?? "").trim();
      const runtimeEndpoint = String(target.endpoint ?? "").trim();
      const endpointForForm =
        mappedBaseUrl || (!isLocalBridgeEndpoint(runtimeEndpoint) ? runtimeEndpoint : "");
      newWizardValues = { ...newWizardValues, endpoint: endpointForForm, groq_base_url: endpointForForm };
    } else if (target.providerId === "ollama") {
      const mappedBaseUrl = String((target.options ?? {})["ollama_base_url"] ?? "").trim();
      const runtimeEndpoint = String(target.endpoint ?? "").trim();
      const endpointForForm =
        mappedBaseUrl || (!isLocalBridgeEndpoint(runtimeEndpoint) ? runtimeEndpoint : "") || "http://127.0.0.1:11434";
      newWizardValues = { ...newWizardValues, endpoint: endpointForForm, ollama_base_url: endpointForForm };
    } else if (target.providerId === "huggingface") {
      const mappedBaseUrl = String((target.options ?? {})["hf_endpoint"] ?? "").trim();
      const runtimeEndpoint = String(target.endpoint ?? "").trim();
      const endpointForForm =
        mappedBaseUrl || (!isLocalBridgeEndpoint(runtimeEndpoint) ? runtimeEndpoint : "") || "https://router.huggingface.co/v1";
      const rawGate = String((target.options ?? {})["hf_enable_network"] ?? "").trim().toLowerCase();
      const gateForForm = rawGate === "true" || rawGate === "1" || rawGate === "yes" || rawGate === "on" ? "true" : "false";
      newWizardValues = {
        ...newWizardValues,
        endpoint: endpointForForm,
        hf_endpoint: endpointForForm,
        hf_enable_network: gateForForm,
      };
    }
    clearNewWizardNotice();
    await loadNewWizardSchemaHint(target.providerId, "edit_open");
  }

  onMount(() => {
    const onGlobalRefresh = () => {
      void refreshConnections(true, "connections.global_refresh_event");
    };
    const onShortcutNewConnection = (event: Event) => {
      openNewWizard();
      event.preventDefault();
    };
    const onShortcutPrimaryAction = (event: Event) => {
      if (!newWizardOpen || busyById.new) return;
      void submitNewConnection();
      event.preventDefault();
    };
    const onShortcutEscape = (event: Event) => {
      if (vaultPickerOpen) {
        closeVaultPicker();
        event.preventDefault();
        return;
      }
      if (deleteConfirmOpen) {
        closeDeleteConfirm();
        event.preventDefault();
        return;
      }
      if (detailsOpen) {
        closeDetails();
        event.preventDefault();
        return;
      }
      if (newWizardOpen) {
        closeNewWizard();
        event.preventDefault();
      }
    };
    window.addEventListener("synapse:global-refresh", onGlobalRefresh as EventListener);
    window.addEventListener("synapse:shortcut-new-connection", onShortcutNewConnection as EventListener);
    window.addEventListener("synapse:shortcut-primary-action", onShortcutPrimaryAction as EventListener);
    window.addEventListener("synapse:shortcut-escape", onShortcutEscape as EventListener);

    const bootstrapKey = connectionsCacheKey();
    const cached = uiCacheGet<Connection[]>(bootstrapKey, PHASE1_TTL_CACHE_TTL_MS);
    uiTraceOpCache({
      op: CONNECTIONS_OP,
      status: cached ? "HIT" : "MISS",
      route: "/connections",
      source: "connections.on_mount.bootstrap",
      reason: "ttl_lookup",
      key: bootstrapKey,
    });
    if (cached) {
      connections = cached;
      pageStatus = "ready";
      window.setTimeout(() => {
        void refreshConnections(false, "connections.on_mount.warm_followup");
      }, 90);
    } else {
      void refreshConnections(false, "connections.on_mount.initial_load");
    }
    return () => {
      window.removeEventListener("synapse:global-refresh", onGlobalRefresh as EventListener);
      window.removeEventListener("synapse:shortcut-new-connection", onShortcutNewConnection as EventListener);
      window.removeEventListener("synapse:shortcut-primary-action", onShortcutPrimaryAction as EventListener);
      window.removeEventListener("synapse:shortcut-escape", onShortcutEscape as EventListener);
      if (bannerTimer) {
        clearTimeout(bannerTimer);
        bannerTimer = null;
      }
    };
  });
</script>

<div class="space-y-4 p-6">
  <div class="flex items-start justify-between gap-4">
    <div class="min-w-0">
      <div class="ui-subtitle mt-1">Create and manage MCP connections.</div>
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
          {#if bannerDebugDetail}
            <details class="mt-1 text-[10px]">
              <summary class="cursor-pointer" style="color: var(--text-muted);">Details</summary>
              <div class="mt-1 break-all font-mono" style="color: var(--text-muted);">{bannerDebugDetail}</div>
            </details>
          {/if}
        {:else}
          <div class="truncate text-xs" style="color: var(--text-muted);"> </div>
        {/if}
      </div>
      {#if bannerText}
        <button
          type="button"
          class="shrink-0 rounded border px-1.5 py-0.5 text-[10px] hover:bg-white/10"
          style="border-color: var(--border-subtle);"
          aria-label="Dismiss notification"
          onclick={dismissBanner}
        >
          x
        </button>
      {/if}
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-[minmax(0,2fr),minmax(0,3fr)] gap-3">
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <div class="ui-card ui-pad-md">
        <div class="ui-subtitle">Total</div>
        <div class="mt-2 text-2xl font-semibold tracking-tight tabular-nums text-right">{stats().total}</div>
      </div>
      <div class="ui-card ui-card--glow ui-pad-md">
        <div class="ui-subtitle">Running</div>
        <div class="mt-2 text-2xl font-semibold tracking-tight tabular-nums text-right">{stats().running}</div>
      </div>
      <div
        class="ui-card ui-pad-md"
        style="background-image: radial-gradient(120% 120% at 30% 0%, rgba(244, 63, 94, 0.12) 0%, transparent 55%);"
      >
        <div class="ui-subtitle" style="color: rgb(254, 202, 202);">Stopped</div>
        <div class="mt-2 text-2xl font-semibold tracking-tight tabular-nums text-right" style="color: rgb(254, 202, 202);">{stats().stopped}</div>
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
            placeholder="Search..."
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
      <div class="ui-subtitle">Use row actions or open details from the row affordance.</div>
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
                class="group ui-row-hover cursor-pointer"
                onclick={() => openDetails(c.id)}
              >
                <td class="px-3 py-3">
                  <div class="flex min-w-0 items-center gap-2">
                    <div class="min-w-0">
                      <div class="truncate font-medium" style="color: var(--text-primary);">{c.name}</div>
                      <div class="truncate ui-subtitle mt-0.5">{c.modelId} - {c.location}</div>
                    </div>
                    <span class="ml-auto hidden shrink-0 items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] text-slate-300/85 transition-opacity group-hover:inline-flex" style="border-color: var(--border-subtle);">
                      <svg viewBox="0 0 24 24" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                        <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                      </svg>
                      <span>View details</span>
                    </span>
                  </div>
                </td>
                <td class="px-3 py-3">
                  <span class={`ui-pill ${badgeClassForStatus(c.status)}`}>{c.status === "running" ? "Running" : "Stopped"}</span>
                </td>
                <td class="px-3 py-3">
                  <div class="truncate" style="color: var(--text-primary);">{c.endpoint || "Not set"}</div>
                  <div class="ui-subtitle mt-0.5">{c.updatedAtLabel}</div>
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
                      title={c.status === "running" ? "Stop connection" : "Start connection"}
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
                      title={TEST_OFFLINE_ONLY_TEXT}
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
                      title={COPY_CONFIG_TEXT}
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
                      class="ui-focus h-7 rounded-md border border-slate-700/60 bg-white/5 px-2 text-[11px] font-medium text-slate-200 transition-colors hover:bg-white/10"
                      title="Edit connection"
                      disabled={busyById[c.id] === true}
                      onclick={(e) => {
                        e.stopPropagation();
                        void openEditWizard(c.id);
                      }}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      class="ui-focus h-7 rounded-md border border-rose-900/60 bg-rose-500/10 px-2 text-[11px] font-medium text-rose-200 transition-colors hover:bg-rose-500/15"
                      title="Delete connection"
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
              <td class="px-3 py-6 ui-subtitle" colspan="4">Failed to load.</td>
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
              <div class="ui-subtitle mt-1">{selected.modelId} - {selected.location}</div>
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
              <div class="mt-1 truncate text-xs" style="color: var(--text-primary);">{selected.endpoint || "Not set"}</div>
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
            <div class="ui-subtitle">Config</div>
            <div class="mt-3 flex flex-wrap gap-2">
              {#each DETAILS_CONFIG_TABS as tab (tab.id)}
                <button
                  type="button"
                  class="ui-focus rounded-md border px-3 py-2 text-xs font-medium transition-colors"
                  style={`border-color: ${detailsConfigTab === tab.id ? "var(--accent-base)" : "var(--border-subtle)"}; background-color: ${detailsConfigTab === tab.id ? "var(--accent-dim)" : "transparent"}; color: ${detailsConfigTab === tab.id ? "var(--text-primary)" : "var(--text-muted)"};`}
                  onclick={() => (detailsConfigTab = tab.id)}
                >
                  {tab.label}
                </button>
              {/each}
            </div>
            <pre
              class="mt-2 overflow-auto rounded-md border p-3 text-[11px] leading-4"
              style="border-color: var(--border-subtle); background-color: rgba(0,0,0,0.12); color: var(--text-primary); max-height: 260px;"
            >{getDetailsConfigText(selected.configText || "", detailsConfigTab)}</pre>
            <div class="mt-3 flex justify-end">
              <button
                type="button"
                class="ui-focus h-9 rounded-md border px-3 text-xs font-semibold transition-colors hover:bg-white/5"
                style="border-color: var(--border-subtle); background-color: transparent; color: var(--text-primary);"
                disabled={busyById[selected.id] === true}
                onclick={() => copyDetailsConfig(selected, detailsConfigTab)}
              >
                Copy {DETAILS_CONFIG_TABS.find((tab) => tab.id === detailsConfigTab)?.label ?? "Config"}
              </button>
            </div>
          </div>
        {/if}
    </div>
  </div>
  </div>
{/if}

<style>
  select {
    color-scheme: dark;
  }
</style>

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
          This will permanently delete the selected connection.
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
            Delete
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
    <div class="absolute left-1/2 top-1/2 w-[780px] max-w-[calc(100vw-40px)] max-h-[calc(100vh-40px)] -translate-x-1/2 -translate-y-1/2">
      <div class="ui-card ui-pad-lg flex max-h-[calc(100vh-40px)] flex-col" style="background-color: var(--surface-1);">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <div class="ui-title">{wizardMode === "edit" ? "Edit Connection" : "New Connection"}</div>
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

        <div class={`mt-4 rounded-md border p-3 text-xs ${bannerClass(newWizardNoticeKind)}`}>
          {#if newWizardNoticeText}
            <div class="font-medium">{newWizardNoticeText}</div>
            {#if newWizardDebugDetail}
              <details class="mt-2 text-[10px]">
                <summary class="cursor-pointer" style="color: var(--text-muted);">Details</summary>
                <div class="mt-1 break-all font-mono" style="color: var(--text-muted);">{newWizardDebugDetail}</div>
              </details>
            {/if}
          {:else if newWizardSchemaHint?.notes?.length}
            <div style="color: var(--text-muted);">{newWizardSchemaHint.notes.join(" ")}</div>
          {:else}
            <div style="color: var(--text-muted);"> </div>
          {/if}
        </div>

        <div class="mt-4 flex-1 overflow-y-auto pr-1">
          <div>
            <div class="ui-card ui-pad-md" style="background-color: var(--surface-2);">
              <label class="ui-subtitle" for="provider-combobox">Provider</label>
              <div class="relative mt-2" bind:this={providerPickerEl} onfocusout={handleProviderFocusOut}>
                <input
                  id="provider-combobox"
                  class="ui-focus h-9 w-full rounded-md border px-3 text-xs"
                  style="border-color: var(--border-subtle); background-color: rgba(0,0,0,0.12); color: var(--text-primary);"
                  placeholder="Select provider..."
                  value={providerQuery}
                  readonly
                  autocomplete="off"
                  autocapitalize="off"
                  autocorrect="off"
                  spellcheck={false}
                  onfocus={() => openProviderPicker()}
                  onpointerdown={handleProviderPointerDown}
                  onkeydown={(e) => {
                    const options = providerOptions();
                    const max = options.length - 1;
                    if (e.key === "Escape") {
                      e.preventDefault();
                      closeProviderPicker();
                      return;
                    }
                    if (e.key === "ArrowDown") {
                      e.preventDefault();
                      if (!providerMenuOpen) {
                        openProviderPicker();
                        return;
                      }
                      providerHighlightIndex = Math.min(max, providerHighlightIndex + 1);
                      return;
                    }
                    if (e.key === "ArrowUp") {
                      e.preventDefault();
                      if (!providerMenuOpen) {
                        openProviderPicker();
                        return;
                      }
                      providerHighlightIndex = Math.max(0, providerHighlightIndex - 1);
                      return;
                    }
                    if (e.key === "Enter") {
                      e.preventDefault();
                      if (!providerMenuOpen) return;
                      if (providerHighlightIndex < 0 || providerHighlightIndex > max) return;
                      selectProvider(options[providerHighlightIndex].id);
                      return;
                    }
                    if (e.key === "Backspace" || e.key === "Delete" || e.key.length === 1) {
                      e.preventDefault();
                    }
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
                    {#each providerOptions() as p, idx (p.id)}
                      {#if idx === 0 || providerOptions()[idx - 1]?.category !== p.category}
                        <div
                          class="px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.14em]"
                          style="color: var(--text-muted); background-color: rgba(255,255,255,0.03);"
                        >
                          {providerCategoryLabel(p.category)}
                        </div>
                      {/if}
                      <button
                        type="button"
                        class={`ui-focus block w-full px-3 py-2 text-left text-xs transition-colors ${
                          idx === providerHighlightIndex ? "bg-white/10" : "hover:bg-white/5"
                        }`}
                        style="color: var(--text-primary); background-color: transparent;"
                        onpointerdown={(e) => {
                          e.preventDefault();
                          selectProvider(p.id);
                        }}
                      >
                        <div class="flex items-center justify-between gap-3">
                          <div class="font-medium">{p.label}</div>
                          {#if p.earlyAccess}
                            <span
                              class="ui-pill shrink-0 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em]"
                              style="background-color: rgba(245, 158, 11, 0.14); color: rgb(251, 191, 36); border: 1px solid rgba(245, 158, 11, 0.32);"
                            >
                              Early Access
                            </span>
                          {/if}
                        </div>
                      </button>
                    {/each}
                  </div>
                {/if}
              </div>
            </div>
          </div>

          <div class="mt-3 ui-card ui-pad-md min-h-[260px]" style="background-color: var(--surface-2);">
            <div>
              <label class="ui-subtitle" for="new-name">
                {newWizardNameField()?.label ?? "Connection name"}{newWizardNameField()?.required ? " *" : ""}
              </label>
              <input
                id="new-name"
                class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
                style="border-color: var(--border-subtle); background-color: rgba(0,0,0,0.12); color: var(--text-primary);"
                placeholder={newWizardNameField()?.placeholder ?? "Example: Synapse Agent"}
                autocomplete="off"
                autocapitalize="off"
                spellcheck="false"
                bind:value={newWizardName}
              />
              {#if newWizardNameField()?.help}
                <div class="mt-1 text-[11px]" style="color: var(--text-muted);">{newWizardNameField()?.help}</div>
              {/if}
            </div>

            <div class="mt-3 grid gap-3 sm:grid-cols-2">
              {#each effectiveNewWizardCommonFields() as field (field.id)}
                {#if field.id !== "connection_name" && isWizardFieldVisible(field.id)}
                  <div>
                    <div class="flex items-center justify-between gap-2">
                      <label class="ui-subtitle" for={`new-${field.id}`}>
                        {fieldLabel(field)}{field.required ? " *" : ""}
                      </label>
                      {#if helperCopy(field.id)}
                        <button
                          type="button"
                          class="ui-focus rounded-full border px-2 py-0.5 text-[10px] font-semibold"
                          style="border-color: var(--border-subtle); color: var(--text-muted);"
                          aria-expanded={helperOpenId === field.id}
                          onclick={() => toggleHelper(field.id)}
                        >
                          ?
                        </button>
                      {/if}
                    </div>
                    {#if helperOpenId === field.id}
                      <div class="mt-1 rounded-md border px-2 py-1 text-[11px]" style="border-color: var(--border-subtle); color: var(--text-muted);">
                        {helperCopy(field.id)}
                      </div>
                    {/if}
                    {#if fieldKind(field) === "multiline"}
                      <textarea
                        id={`new-${field.id}`}
                        class="ui-focus mt-2 w-full rounded-md border p-3 text-[11px] leading-4"
                        style="border-color: var(--border-subtle); background-color: rgba(0,0,0,0.12); color: var(--text-primary); height: 96px; resize: none;"
                        value={newWizardValues[field.id] || ""}
                        oninput={(e) => updateWizardField(field.id, (e.currentTarget as HTMLTextAreaElement).value)}
                      ></textarea>
                    {:else if fieldKind(field) === "select"}
                      <select
                        id={`new-${field.id}`}
                        class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
                        style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
                        value={newWizardValues[field.id] || ""}
                        onchange={(e) => updateWizardField(field.id, (e.currentTarget as HTMLSelectElement).value)}
                      >
                        {#each fieldOptions(field) as option (option.value)}
                          <option value={option.value}>{option.label}</option>
                        {/each}
                      </select>
                    {:else}
                      {#if isCredentialsField(field.id)}
                        <div class="mt-2 flex items-center gap-2">
                          <input
                            id={`new-${field.id}`}
                            class="ui-focus h-9 w-full rounded-md border px-3 text-xs"
                            style="border-color: var(--border-subtle); background-color: rgba(0,0,0,0.12); color: var(--text-primary);"
                            placeholder={fieldPlaceholder(field)}
                            autocomplete={inputAutocompleteForField(field.id)}
                            autocapitalize="off"
                            spellcheck="false"
                            value={newWizardValues[field.id] || ""}
                            oninput={(e) => updateWizardField(field.id, (e.currentTarget as HTMLInputElement).value)}
                          />
                          <button
                            type="button"
                            class="ui-focus h-9 shrink-0 rounded-md border px-3 text-xs font-medium transition-colors hover:bg-white/5"
                            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
                            onclick={() => triggerCredentialsBrowse(field.id, `new-${field.id}-file`)}
                          >
                            Browse
                          </button>
                          <button
                            type="button"
                            class="ui-focus h-9 shrink-0 rounded-md border px-3 text-xs font-medium transition-colors hover:bg-white/5"
                            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
                            onclick={() => openVaultPicker(field.id)}
                          >
                            Vault
                          </button>
                          <input
                            id={`new-${field.id}-file`}
                            type="file"
                            class="hidden"
                            onchange={(e) => onCredentialsFileSelected(field.id, e)}
                          />
                        </div>
                      {:else}
                        <input
                          id={`new-${field.id}`}
                          type={inputTypeForField(field)}
                          class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
                          style="border-color: var(--border-subtle); background-color: rgba(0,0,0,0.12); color: var(--text-primary);"
                          placeholder={fieldPlaceholder(field)}
                          autocomplete={inputAutocompleteForField(field.id)}
                          autocapitalize="off"
                          spellcheck="false"
                          value={newWizardValues[field.id] || ""}
                          oninput={(e) => updateWizardField(field.id, (e.currentTarget as HTMLInputElement).value)}
                        />
                      {/if}
                    {/if}
                    {#if fieldHelpText(field)}
                      <div class="mt-1 text-[11px]" style="color: var(--text-muted);">{fieldHelpText(field)}</div>
                    {/if}
                  </div>
                {/if}
              {/each}
            </div>

            <div class="mt-3">
              <div class="ui-subtitle">Selected provider</div>
              <div class="mt-1 flex items-center gap-2 text-xs font-medium" style="color: var(--text-primary);">
                <span class="truncate">{providerId ? providerLabel(providerId) : "-"}</span>
                {#if providerOptionById(providerId)?.earlyAccess}
                  <span
                    class="ui-pill shrink-0 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em]"
                    style="background-color: rgba(245, 158, 11, 0.14); color: rgb(251, 191, 36); border: 1px solid rgba(245, 158, 11, 0.32);"
                  >
                    Early Access
                  </span>
                {/if}
              </div>
              {#if providerOptionById(providerId)?.infoNote}
                <div
                  class="mt-2 rounded-md border px-3 py-2 text-[11px] leading-4"
                  style="border-color: rgba(245, 158, 11, 0.32); background-color: rgba(245, 158, 11, 0.08); color: rgb(253, 230, 138);"
                >
                  {providerOptionById(providerId)?.infoNote}
                </div>
              {/if}
            </div>

            <div class="mt-3 rounded-md border border-slate-700/60 bg-white/5 p-3">
              <div class="text-xs font-medium" style="color: var(--text-primary);">Provider fields</div>
              <div class="mt-3">
                {#if effectiveNewWizardProviderFields().length === 0}
                  <div class="text-xs" style="color: var(--text-muted);">No provider fields.</div>
                {:else}
                  <div class="grid gap-3 sm:grid-cols-2">
                    {#each effectiveNewWizardProviderFields() as field (field.id)}
                      {#if isWizardFieldVisible(field.id)}
                      <div>
                        <div class="flex items-center justify-between gap-2">
                          <label class="ui-subtitle" for={`new-${field.id}`}>
                            {fieldLabel(field)}{field.required ? " *" : ""}
                          </label>
                          {#if helperCopy(field.id)}
                            <button
                              type="button"
                              class="ui-focus rounded-full border px-2 py-0.5 text-[10px] font-semibold"
                              style="border-color: var(--border-subtle); color: var(--text-muted);"
                              aria-expanded={helperOpenId === field.id}
                              onclick={() => toggleHelper(field.id)}
                            >
                              ?
                            </button>
                          {/if}
                        </div>
                        {#if helperOpenId === field.id}
                          <div class="mt-1 rounded-md border px-2 py-1 text-[11px]" style="border-color: var(--border-subtle); color: var(--text-muted);">
                            {helperCopy(field.id)}
                          </div>
                        {/if}
                    {#if fieldKind(field) === "multiline"}
                      <textarea
                            id={`new-${field.id}`}
                            class="ui-focus mt-2 w-full rounded-md border p-3 text-[11px] leading-4"
                            style="border-color: var(--border-subtle); background-color: rgba(0,0,0,0.12); color: var(--text-primary); height: 96px; resize: none;"
                            value={newWizardValues[field.id] || ""}
                            oninput={(e) => updateWizardField(field.id, (e.currentTarget as HTMLTextAreaElement).value)}
                          ></textarea>
                        {:else if fieldKind(field) === "select"}
                          <select
                            id={`new-${field.id}`}
                            class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
                            style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
                            value={newWizardValues[field.id] || ""}
                            onchange={(e) => updateWizardField(field.id, (e.currentTarget as HTMLSelectElement).value)}
                          >
                            {#each fieldOptions(field) as option (option.value)}
                              <option value={option.value}>{option.label}</option>
                            {/each}
                          </select>
                        {:else}
                          {#if isCredentialsField(field.id)}
                            <div class="mt-2 flex items-center gap-2">
                              <input
                                id={`new-${field.id}`}
                                class="ui-focus h-9 w-full rounded-md border px-3 text-xs"
                                style="border-color: var(--border-subtle); background-color: rgba(0,0,0,0.12); color: var(--text-primary);"
                                placeholder={fieldPlaceholder(field)}
                                autocomplete={inputAutocompleteForField(field.id)}
                                autocapitalize="off"
                                spellcheck="false"
                                value={newWizardValues[field.id] || ""}
                                oninput={(e) => updateWizardField(field.id, (e.currentTarget as HTMLInputElement).value)}
                              />
                              <button
                                type="button"
                                class="ui-focus h-9 shrink-0 rounded-md border px-3 text-xs font-medium transition-colors hover:bg-white/5"
                                style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
                                onclick={() => triggerCredentialsBrowse(field.id, `new-${field.id}-file`)}
                              >
                                Browse
                              </button>
                              <button
                                type="button"
                                class="ui-focus h-9 shrink-0 rounded-md border px-3 text-xs font-medium transition-colors hover:bg-white/5"
                                style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
                                onclick={() => openVaultPicker(field.id)}
                              >
                                Vault
                              </button>
                              <input
                                id={`new-${field.id}-file`}
                                type="file"
                                class="hidden"
                                onchange={(e) => onCredentialsFileSelected(field.id, e)}
                              />
                            </div>
                          {:else}
                            <input
                              id={`new-${field.id}`}
                              type={inputTypeForField(field)}
                              class="ui-focus mt-2 h-9 w-full rounded-md border px-3 text-xs"
                              style="border-color: var(--border-subtle); background-color: rgba(0,0,0,0.12); color: var(--text-primary);"
                              placeholder={fieldPlaceholder(field)}
                              autocomplete={inputAutocompleteForField(field.id)}
                              autocapitalize="off"
                              spellcheck="false"
                              value={newWizardValues[field.id] || ""}
                              oninput={(e) => updateWizardField(field.id, (e.currentTarget as HTMLInputElement).value)}
                            />
                          {/if}
                        {/if}
                        {#if fieldHelpText(field)}
                          <div class="mt-1 text-[11px]" style="color: var(--text-muted);">{fieldHelpText(field)}</div>
                        {/if}
                      </div>
                      {/if}
                    {/each}
                  </div>
                {/if}
              </div>
            </div>
          </div>
        </div>

        {#if vaultPickerOpen}
          <div class="fixed inset-0 z-50">
            <button
              type="button"
              class="absolute inset-0 h-full w-full"
              style="background-color: rgba(0, 0, 0, 0.55);"
              aria-label="Close vault picker"
              onclick={closeVaultPicker}
            ></button>
            <div class="absolute left-1/2 top-1/2 w-[640px] max-w-[calc(100vw-40px)] -translate-x-1/2 -translate-y-1/2">
              <div class="ui-card ui-pad-md" style="background-color: var(--surface-1);">
                <div class="flex items-start justify-between gap-3">
                  <div class="ui-title text-base">Vault</div>
                  <button
                    type="button"
                    class="ui-focus rounded-md border px-3 py-2 text-xs font-medium transition-colors hover:bg-white/5"
                    style="border-color: var(--border-subtle); color: var(--text-primary); background-color: transparent;"
                    onclick={closeVaultPicker}
                  >
                    Close
                  </button>
                </div>

                <div class={`mt-3 rounded-md border p-2 text-xs ${bannerClass(vaultNoticeKind)}`}>
                  {#if vaultNoticeText}
                    <div class="font-medium">{vaultNoticeText}</div>
                  {:else}
                    <div style="color: var(--text-muted);"> </div>
                  {/if}
                </div>

                <div class="mt-3 grid gap-2">
                  <input
                    class="ui-focus h-9 w-full rounded-md border px-3 text-xs"
                    style="border-color: var(--border-subtle); background-color: rgba(0,0,0,0.12); color: var(--text-primary);"
                    placeholder="Vault entry name"
                    autocomplete="off"
                    autocapitalize="off"
                    spellcheck="false"
                    bind:value={vaultName}
                  />
                  <div class="flex items-center gap-2">
                    <input
                      class="ui-focus h-9 w-full rounded-md border px-3 text-xs"
                      style="border-color: var(--border-subtle); background-color: rgba(0,0,0,0.12); color: var(--text-primary);"
                      placeholder={isVaultCredentialsPathType() ? "Credentials path" : "Secret"}
                      autocomplete="new-password"
                      autocapitalize="off"
                      spellcheck="false"
                      type={isVaultCredentialsPathType() ? "text" : "password"}
                      bind:value={vaultSecret}
                    />
                    {#if isVaultCredentialsPathType()}
                      <button
                        type="button"
                        class="ui-focus h-9 shrink-0 rounded-md border px-3 text-xs font-medium transition-colors hover:bg-white/5"
                        style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
                        onclick={triggerVaultCredentialsBrowse}
                      >
                        Browse
                      </button>
                      <input
                        id="vault-credentials-file"
                        type="file"
                        class="hidden"
                        onchange={(e) => onVaultCredentialsFileSelected(e)}
                      />
                    {/if}
                  </div>
                  <div class="flex justify-end">
                    <button
                      type="button"
                      class="ui-focus h-9 rounded-md border px-3 text-xs font-medium transition-colors hover:bg-white/5"
                      style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
                      disabled={vaultBusy}
                      onclick={createVaultEntry}
                    >
                      Save to Vault
                    </button>
                  </div>
                </div>

                <div class="mt-3">
                  {#if vaultStatus === "loading"}
                    <div class="text-xs text-slate-500">Loading vault entries...</div>
                  {:else if vaultEntries.length === 0}
                    <div class="text-xs text-slate-500">No vault entries.</div>
                  {:else}
                    <div class="space-y-2">
                      {#each vaultEntries as entry (entry.id)}
                        <div class="flex items-center justify-between gap-3 rounded-md border px-3 py-2" style="border-color: var(--border-subtle);">
                          <div class="min-w-0">
                            <div class="truncate text-xs font-medium" style="color: var(--text-primary);">{entry.name}</div>
                            <div class="truncate text-[10px] text-slate-500/90">{entry.type}</div>
                          </div>
                          <div class="flex items-center gap-2">
                            <button
                              type="button"
                              class="ui-focus h-8 rounded-md border px-2 text-[11px] font-medium transition-colors hover:bg-white/5"
                              style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
                              disabled={vaultBusy}
                              onclick={() => useVaultEntry(entry)}
                            >
                              Use
                            </button>
                            <button
                              type="button"
                              class="ui-focus h-8 rounded-md border px-2 text-[11px] font-medium transition-colors hover:bg-white/5"
                              style="border-color: var(--border-subtle); background-color: var(--surface-2); color: var(--text-primary);"
                              disabled={vaultDeleteBusyId === entry.id}
                              onclick={() => deleteVaultEntry(entry.id)}
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      {/each}
                    </div>
                  {/if}
                </div>
              </div>
            </div>
          </div>
        {/if}

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
              class="ui-focus h-9 rounded-md border border-slate-700/60 bg-white/5 px-3 text-xs font-medium text-slate-200 transition-colors hover:bg-white/10"
              disabled={busyById.preflight === true}
              onclick={preflightConnection}
            >
              Preflight
            </button>
            <button
              type="button"
              class="ui-focus h-9 rounded-md border px-4 text-xs font-semibold transition-colors"
              style="border-color: rgba(39, 201, 169, 0.55); background-color: rgba(39, 201, 169, 0.10); color: var(--text-primary);"
              disabled={busyById.new === true}
              onclick={submitNewConnection}
            >
              {wizardMode === "edit" ? "Save Changes" : "Create Connection"}
            </button>
          </div>
        </div>
      </div>
    </div>
{/if}
