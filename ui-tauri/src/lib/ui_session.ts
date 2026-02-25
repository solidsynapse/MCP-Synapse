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
};

export type ResilienceSessionState = {
  appliedGuards: unknown[];
  interceptorEnabledById: Record<string, boolean>;
  interceptorSettingsById: Record<string, unknown>;
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
  },
  resilience: {
    appliedGuards: [],
    interceptorEnabledById: {},
    interceptorSettingsById: {},
  },
  settings: {
    dataRetention: "3m",
    portMode: "auto",
    portMin: "",
    portMax: "",
  },
};

let state: UiSessionState = clone(DEFAULT_STATE);

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

export function getSettingsSession(): SettingsSessionState {
  return state.settings;
}

export function patchSettingsSession(patch: Partial<SettingsSessionState>) {
  state = { ...state, settings: { ...state.settings, ...patch } };
}
