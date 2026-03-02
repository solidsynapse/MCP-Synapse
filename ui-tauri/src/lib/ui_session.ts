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
