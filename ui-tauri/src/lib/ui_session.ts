export type DataRetention = "1m" | "3m" | "6m" | "unlimited";
export type PortMode = "auto" | "manual";

export type PoliciesSessionState = {
  appliedPersonas: unknown[];
  personaPresets: unknown[];
  selectedPresetId: string;
  presetNameDraft: string;
  personaTextDraft: string;
  contextCachingEnabled: boolean;
  requestDedupEnabled: boolean;
  selectedPersonaId: string;
  selectedTargetId: string;
};

export type ResilienceSessionState = {
  appliedGuards: unknown[];
  interceptorEnabledById: Record<string, boolean>;
  interceptorSettingsById: Record<string, unknown>;
  selectedScopeId: string;
  limitValue: string;
  unit: string;
};

export type UsageSessionState = {
  provider: string;
  dateRange: string;
  sort: string;
};

export type SettingsSessionState = {
  dataRetention: DataRetention;
  portMode: PortMode;
  portMin: string;
  portMax: string;
};

export type UiSessionState = {
  policies: PoliciesSessionState;
  resilience: ResilienceSessionState;
  usage: UsageSessionState;
  settings: SettingsSessionState;
};

function clone<T>(value: T): T {
  if (typeof structuredClone === "function") return structuredClone(value);
  return JSON.parse(JSON.stringify(value)) as T;
}

const DEFAULT_STATE: UiSessionState = {
  policies: {
    appliedPersonas: [],
    personaPresets: [],
    selectedPresetId: "",
    presetNameDraft: "",
    personaTextDraft: "",
    contextCachingEnabled: false,
    requestDedupEnabled: false,
    selectedPersonaId: "default",
    selectedTargetId: "bridge_alpha",
  },
  resilience: {
    appliedGuards: [],
    interceptorEnabledById: {},
    interceptorSettingsById: {},
    selectedScopeId: "all",
    limitValue: "",
    unit: "usd_per_day",
  },
  usage: {
    provider: "all",
    dateRange: "24h",
    sort: "time_desc",
  },
  settings: {
    dataRetention: "3m",
    portMode: "auto",
    portMin: "",
    portMax: "",
  },
};

let state: UiSessionState = clone(DEFAULT_STATE);
type CacheEntry = { at: number; value: unknown };
const responseCache = new Map<string, CacheEntry>();
const inFlight = new Map<string, Promise<unknown>>();
const PERSISTENT_CACHE_PREFIX = "synapse.cache.";
const USAGE_SESSION_STORAGE_KEY = "synapse.session.usage.v1";
const PHASE1_TTL_CACHE_KEY_PREFIX = "opcache::";

export const PHASE1_TTL_CACHE_TTL_MS = 5 * 1000;
export const PHASE1_TTL_CACHE_OPS = ["dashboard.get_state", "usage.recent", "connections.list"] as const;
const OP_CACHE_TRACE_BUFFER_KEY = "__SYNAPSE_OP_CACHE_TRACE__";
const OP_CACHE_TRACE_MAX = 500;

type OpCacheTraceStatus = "HIT" | "MISS" | "INVALIDATE";
type OpCacheTraceEvent = {
  op: string;
  status: OpCacheTraceStatus;
  route: string;
  source: string;
  reason?: string;
  key?: string;
};

function shouldTraceOp(op: string): boolean {
  return (PHASE1_TTL_CACHE_OPS as readonly string[]).includes(String(op || "").trim());
}

function getOpCacheTraceBuffer(): Record<string, unknown>[] | null {
  if (typeof window === "undefined") return null;
  const host = window as unknown as Record<string, unknown>;
  const current = host[OP_CACHE_TRACE_BUFFER_KEY];
  if (Array.isArray(current)) return current as Record<string, unknown>[];
  const next: Record<string, unknown>[] = [];
  host[OP_CACHE_TRACE_BUFFER_KEY] = next;
  return next;
}

let traceInvokePromise: Promise<((command: string, args?: Record<string, unknown>) => Promise<unknown>) | null> | null = null;

async function getTraceInvoke() {
  if (typeof window === "undefined") return null;
  const tauriGlobal = (window as any).__TAURI__ ?? (window as any).__TAURI_INTERNALS__;
  if (!tauriGlobal) return null;
  if (!traceInvokePromise) {
    traceInvokePromise = import("@tauri-apps/api/core")
      .then((mod) => mod.invoke)
      .catch(() => null);
  }
  return traceInvokePromise;
}

async function writeTraceRowToFile(row: Record<string, unknown>) {
  const invoke = await getTraceInvoke();
  if (!invoke) return;
  try {
    await invoke("ui_append_frontend_trace_v1", { row });
  } catch {
    // ignore trace sink failures
  }
}

export function uiTraceOpCache(event: OpCacheTraceEvent): void {
  const op = String(event.op || "").trim();
  if (!shouldTraceOp(op)) return;
  const row: Record<string, unknown> = {
    timestamp: new Date().toISOString(),
    op,
    status: event.status,
    route: String(event.route || "").trim() || "unknown",
    source: String(event.source || "").trim() || "unknown",
    reason: String(event.reason || "").trim() || undefined,
    key: String(event.key || "").trim() || undefined,
  };
  const traceBuffer = getOpCacheTraceBuffer();
  if (traceBuffer) {
    traceBuffer.push(row);
    if (traceBuffer.length > OP_CACHE_TRACE_MAX) {
      traceBuffer.splice(0, traceBuffer.length - OP_CACHE_TRACE_MAX);
    }
  }
  if (typeof console !== "undefined" && typeof console.info === "function") {
    console.info("[synapse.opcache]", row);
  }
  if (typeof window !== "undefined") {
    window.dispatchEvent(
      new CustomEvent("synapse:opcache-trace", {
        detail: row,
      }),
    );
  }
  void writeTraceRowToFile(row);
}

function getPersistentStorage(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage ?? null;
  } catch {
    return null;
  }
}

function getPersistentStorageKey(key: string): string {
  return `${PERSISTENT_CACHE_PREFIX}${key}`;
}

function createInitialState(): UiSessionState {
  const next = clone(DEFAULT_STATE);
  const persisted = readUsageSessionFromStorage();
  if (persisted) {
    next.usage = { ...next.usage, ...persisted };
  }
  return next;
}

function readUsageSessionFromStorage(): Partial<UsageSessionState> | null {
  const storage = getPersistentStorage();
  if (!storage) return null;
  try {
    const raw = storage.getItem(USAGE_SESSION_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<UsageSessionState> | null;
    if (!parsed || typeof parsed !== "object") return null;
    const next: Partial<UsageSessionState> = {};
    if (typeof parsed.provider === "string") next.provider = parsed.provider;
    if (typeof parsed.dateRange === "string") next.dateRange = parsed.dateRange;
    if (typeof parsed.sort === "string") next.sort = parsed.sort;
    if (Object.keys(next).length === 0) return null;
    return next;
  } catch {
    return null;
  }
}

function persistUsageSessionToStorage(usage: UsageSessionState): void {
  const storage = getPersistentStorage();
  if (!storage) return;
  try {
    storage.setItem(USAGE_SESSION_STORAGE_KEY, JSON.stringify(usage));
  } catch {
    // ignore storage write failures
  }
}

state = createInitialState();

export function resetUiSession() {
  state = clone(DEFAULT_STATE);
}

export function getUiSession(): UiSessionState {
  return state;
}

export function getPoliciesSession(): PoliciesSessionState {
  return state.policies;
}

export function patchPoliciesSession(patch: Partial<PoliciesSessionState>) {
  state = { ...state, policies: { ...state.policies, ...patch } };
}

export function getResilienceSession(): ResilienceSessionState {
  return state.resilience;
}

export function patchResilienceSession(patch: Partial<ResilienceSessionState>) {
  state = { ...state, resilience: { ...state.resilience, ...patch } };
}

export function getUsageSession(): UsageSessionState {
  return state.usage;
}

export function patchUsageSession(patch: Partial<UsageSessionState>) {
  state = { ...state, usage: { ...state.usage, ...patch } };
  persistUsageSessionToStorage(state.usage);
}

export function getSettingsSession(): SettingsSessionState {
  return state.settings;
}

export function patchSettingsSession(patch: Partial<SettingsSessionState>) {
  state = { ...state, settings: { ...state.settings, ...patch } };
}

export function uiCacheGet<T>(key: string, maxAgeMs = 0): T | null {
  const entry = responseCache.get(key);
  if (!entry) return null;
  if (maxAgeMs > 0 && Date.now() - entry.at > maxAgeMs) {
    responseCache.delete(key);
    return null;
  }
  return clone(entry.value as T);
}

export function uiCacheSet<T>(key: string, value: T) {
  responseCache.set(key, { at: Date.now(), value: clone(value) });
}

export function uiPersistentCacheGet<T>(key: string, maxAgeMs: number): T | null {
  const storage = getPersistentStorage();
  if (!storage) return null;
  const storageKey = getPersistentStorageKey(key);
  try {
    const raw = storage.getItem(storageKey);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { at?: number; value?: T };
    if (!parsed || typeof parsed !== "object") {
      storage.removeItem(storageKey);
      return null;
    }
    if (typeof parsed.at !== "number") {
      storage.removeItem(storageKey);
      return null;
    }
    if (maxAgeMs > 0 && Date.now() - parsed.at > maxAgeMs) {
      storage.removeItem(storageKey);
      return null;
    }
    return clone(parsed.value as T);
  } catch {
    try {
      storage.removeItem(storageKey);
    } catch {
      // ignore storage cleanup failures
    }
    return null;
  }
}

export function uiPersistentCacheSet<T>(key: string, value: T): void {
  const storage = getPersistentStorage();
  if (!storage) return;
  const storageKey = getPersistentStorageKey(key);
  try {
    storage.setItem(storageKey, JSON.stringify({ at: Date.now(), value: clone(value) }));
  } catch {
    // ignore storage write failures
  }
}

export function uiRunDeduped<T>(key: string, run: () => Promise<T>): Promise<T> {
  const existing = inFlight.get(key);
  if (existing) return existing as Promise<T>;
  const pending = run().finally(() => {
    if (inFlight.get(key) === pending) inFlight.delete(key);
  });
  inFlight.set(key, pending as Promise<unknown>);
  return pending;
}

function normalizeCachePart(value: unknown): unknown {
  if (value === null) return null;
  const valueType = typeof value;
  if (valueType === "string" || valueType === "number" || valueType === "boolean") return value;
  if (Array.isArray(value)) return value.map((item) => normalizeCachePart(item));
  if (valueType === "object") {
    const src = value as Record<string, unknown>;
    const dst: Record<string, unknown> = {};
    const keys = Object.keys(src).sort((a, b) => a.localeCompare(b));
    for (const key of keys) {
      dst[key] = normalizeCachePart(src[key]);
    }
    return dst;
  }
  return String(value);
}

function stableCachePart(value: unknown): string {
  return JSON.stringify(normalizeCachePart(value));
}

export function uiBuildOpCacheKey(
  op: string,
  promptPayload: Record<string, unknown>,
  activeFilters: Record<string, unknown> = {},
): string {
  const normalizedOp = String(op || "").trim();
  return `${PHASE1_TTL_CACHE_KEY_PREFIX}${normalizedOp}|payload=${stableCachePart(promptPayload)}|filters=${stableCachePart(activeFilters)}`;
}

export function uiInvalidateOpCaches(
  ops: readonly string[],
  meta: { reason?: string; route?: string; source?: string } = {},
): void {
  if (!Array.isArray(ops) || ops.length === 0) return;
  for (const op of ops) {
    uiTraceOpCache({
      op: String(op || "").trim(),
      status: "INVALIDATE",
      route: String(meta.route || "").trim() || "unknown",
      source: String(meta.source || "").trim() || "unknown",
      reason: String(meta.reason || "").trim() || "cache_invalidate",
    });
  }
  const prefixes = ops
    .map((op) => `${PHASE1_TTL_CACHE_KEY_PREFIX}${String(op || "").trim()}|`)
    .filter((prefix) => prefix.length > PHASE1_TTL_CACHE_KEY_PREFIX.length);
  if (prefixes.length === 0) return;

  const shouldDelete = (key: string): boolean => prefixes.some((prefix) => key.startsWith(prefix));

  for (const key of Array.from(responseCache.keys())) {
    if (shouldDelete(key)) responseCache.delete(key);
  }
  for (const key of Array.from(inFlight.keys())) {
    if (shouldDelete(key)) inFlight.delete(key);
  }

  const storage = getPersistentStorage();
  if (!storage) return;
  const storagePrefixes = prefixes.map((prefix) => `${PERSISTENT_CACHE_PREFIX}${prefix}`);
  const keysToRemove: string[] = [];
  for (let i = 0; i < storage.length; i += 1) {
    const storageKey = storage.key(i);
    if (!storageKey) continue;
    if (storagePrefixes.some((prefix) => storageKey.startsWith(prefix))) {
      keysToRemove.push(storageKey);
    }
  }
  for (const key of keysToRemove) {
    try {
      storage.removeItem(key);
    } catch {
      // ignore storage cleanup failures
    }
  }
}
