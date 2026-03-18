mod worker_dispatch;

use serde::{Deserialize, Serialize};
use serde_json::json;
use std::fs::{create_dir_all, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use tauri::Manager;
#[cfg(windows)]
use std::os::windows::process::CommandExt;
#[cfg(windows)]
use std::sync::OnceLock;

static STOP_ALL_CONNECTIONS_ONCE: AtomicBool = AtomicBool::new(false);
#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x08000000;
#[cfg(windows)]
const SINGLE_INSTANCE_MUTEX_NAME: &str = "Local\\MCP_SYNAPSE_SINGLE_INSTANCE_V1";
#[cfg(windows)]
const MAIN_WINDOW_TITLE: &str = "MCP Synapse";
#[cfg(windows)]
const ERROR_ALREADY_EXISTS: u32 = 183;
#[cfg(windows)]
const SW_SHOW: i32 = 5;
#[cfg(windows)]
const SW_RESTORE: i32 = 9;
const WORKER_DECISION_LOG_FILE: &str = "runtime_worker_decision.jsonl";
const LIFECYCLE_LOG_FILE: &str = "runtime_lifecycle.jsonl";
const DISPATCH_ENTRY_NAME: &str = "dispatch_execute_request_v1";
const CLOSE_BUDGET_ENV: &str = "MCP_SYNAPSE_CLOSE_BUDGET_MS";
const CLOSE_BUDGET_DEFAULT_MS: u64 = 2000;
const INTERNAL_DEBUG_OBS_ENV: &str = "MCP_SYNAPSE_INTERNAL_DEBUG_OBS";
#[cfg(windows)]
static SINGLE_INSTANCE_MUTEX_HANDLE: OnceLock<usize> = OnceLock::new();

const DESKTOP_UX_HARDENING_JS: &str = r#"
(() => {
  if (window.__MCP_SYNAPSE_DESKTOP_HARDENED__) return;
  window.__MCP_SYNAPSE_DESKTOP_HARDENED__ = true;

  const isEditableTarget = (target) => {
    if (!target || typeof target.closest !== 'function') return false;
    return !!target.closest('input, textarea, [contenteditable="true"], [contenteditable=""]');
  };

  window.addEventListener('contextmenu', (event) => {
    if (isEditableTarget(event.target)) return;
    event.preventDefault();
  }, true);

  window.addEventListener('keydown', (event) => {
    const key = (event.key || '').toLowerCase();
    if ((event.ctrlKey || event.metaKey) && key === 'p') {
      event.preventDefault();
      event.stopPropagation();
    }
  }, true);

  window.print = () => {};
})();
"#;

#[cfg(windows)]
type WinHandle = *mut std::ffi::c_void;

#[cfg(windows)]
#[link(name = "kernel32")]
extern "system" {
    fn CreateMutexW(
        lp_mutex_attributes: *mut std::ffi::c_void,
        b_initial_owner: i32,
        lp_name: *const u16,
    ) -> WinHandle;
    fn GetLastError() -> u32;
}

#[cfg(windows)]
#[link(name = "user32")]
extern "system" {
    fn FindWindowW(lp_class_name: *const u16, lp_window_name: *const u16) -> WinHandle;
    fn IsIconic(hwnd: WinHandle) -> i32;
    fn ShowWindow(hwnd: WinHandle, n_cmd_show: i32) -> i32;
    fn SetForegroundWindow(hwnd: WinHandle) -> i32;
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DispatchError {
    pub code: String,
    pub message: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DispatchResult {
    pub ok: bool,
    pub status: String,
    pub text: Option<String>,
    pub result: Option<serde_json::Value>,
    pub state: Option<serde_json::Value>,
    pub error: Option<DispatchError>,
    pub errors: Option<Vec<String>>,
    pub warnings: Option<Vec<String>>,
    pub schema_hint: Option<serde_json::Value>,
    pub data: Option<serde_json::Value>,
    pub normalized_payload: Option<serde_json::Value>,
    pub config_text: Option<String>,
    pub dry_run_trace: Option<serde_json::Value>,
    pub connections: Option<Vec<serde_json::Value>>,
}

fn unix_ms_now() -> u128 {
    match SystemTime::now().duration_since(UNIX_EPOCH) {
        Ok(duration) => duration.as_millis(),
        Err(_) => 0,
    }
}

fn append_jsonl(path: PathBuf, mut row: serde_json::Value) -> Result<bool, String> {
    if let serde_json::Value::Object(ref mut map) = row {
        if !map.contains_key("server_ts_unix_ms") {
            map.insert(
                "server_ts_unix_ms".to_string(),
                serde_json::Value::Number(serde_json::Number::from(unix_ms_now() as u64)),
            );
        }
    }
    if let Some(parent) = path.parent() {
        create_dir_all(parent).map_err(|e| format!("trace_mkdir_failed: {e}"))?;
    }
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path)
        .map_err(|e| format!("trace_open_failed: {e}"))?;
    let line = serde_json::to_string(&row).map_err(|e| format!("trace_json_failed: {e}"))?;
    file.write_all(line.as_bytes())
        .map_err(|e| format!("trace_write_failed: {e}"))?;
    file.write_all(b"\n")
        .map_err(|e| format!("trace_newline_failed: {e}"))?;
    Ok(true)
}

fn close_budget_ms() -> u64 {
    match std::env::var(CLOSE_BUDGET_ENV) {
        Ok(raw) => raw
            .trim()
            .parse::<u64>()
            .ok()
            .filter(|v| *v >= 2000)
            .unwrap_or(CLOSE_BUDGET_DEFAULT_MS),
        Err(_) => CLOSE_BUDGET_DEFAULT_MS,
    }
}

fn internal_debug_observability_enabled() -> bool {
    match std::env::var(INTERNAL_DEBUG_OBS_ENV) {
        Ok(value) => {
            let normalized = value
                .trim()
                .trim_matches('"')
                .trim_matches('\'')
                .trim()
                .to_ascii_lowercase();
            if matches!(normalized.as_str(), "1" | "true" | "yes" | "on") {
                return true;
            }
            normalized
                .parse::<i64>()
                .ok()
                .map(|v| v > 0)
                .unwrap_or(false)
        }
        Err(_) => false,
    }
}

fn append_lifecycle_log(repo_root: &PathBuf, event: &str, extra: serde_json::Value) {
    let exe_path = std::env::current_exe()
        .ok()
        .map(|p| p.to_string_lossy().to_string())
        .unwrap_or_else(|| "unknown".to_string());
    let build_marker = option_env!("MCP_SYNAPSE_BUILD_MARKER").unwrap_or(env!("CARGO_PKG_VERSION"));
    let mut row = json!({
        "timestamp_unix_ms": unix_ms_now() as u64,
        "event": event,
        "pid": std::process::id(),
        "exe_path": exe_path,
        "build_marker": build_marker,
    });
    if let (Some(row_obj), Some(extra_obj)) = (row.as_object_mut(), extra.as_object()) {
        for (k, v) in extra_obj {
            row_obj.insert(k.clone(), v.clone());
        }
    }
    let out_file = repo_root
        .join("data")
        .join("observability")
        .join(LIFECYCLE_LOG_FILE);
    let _ = append_jsonl(out_file, row);
}

fn repo_root_from_manifest_dir() -> Result<PathBuf, String> {
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let ui_root = manifest_dir
        .parent()
        .ok_or_else(|| "invalid_manifest_dir".to_string())?;
    let repo_root = ui_root
        .parent()
        .ok_or_else(|| "invalid_repo_root".to_string())?;
    Ok(repo_root.to_path_buf())
}

fn dispatch_execute_request_legacy(
    repo_root: &PathBuf,
    python: &str,
    agent_id: &str,
    prompt: &str,
) -> Result<DispatchResult, String> {
    let script = repo_root.join("tools").join("headless_dispatch_v1.py");
    let mut command = Command::new(python);
    command
        .arg(script)
        .arg("--agent-id")
        .arg(agent_id)
        .arg("--prompt")
        .arg(prompt);
    #[cfg(windows)]
    command.creation_flags(CREATE_NO_WINDOW);
    let output = command
        .output()
        .map_err(|e| format!("dispatch_spawn_failed: {e}"))?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    if stdout.trim().is_empty() {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        return Err(format!(
            "dispatch_empty_stdout: exit_code={:?} stderr={}",
            output.status.code(),
            stderr.trim()
        ));
    }

    let parsed: DispatchResult =
        serde_json::from_str(&stdout).map_err(|e| format!("dispatch_invalid_json: {e}"))?;
    Ok(parsed)
}

fn log_text(raw: &str, max_chars: usize) -> String {
    let mut compact = raw.replace('\r', " ");
    compact = compact.replace('\n', " ");
    let mut out = String::new();
    for (idx, ch) in compact.chars().enumerate() {
        if idx >= max_chars {
            out.push_str("...");
            break;
        }
        out.push(ch);
    }
    out
}

fn append_worker_decision_log(
    repo_root: &PathBuf,
    op: &str,
    flag_effective: bool,
    whitelist_eligible: bool,
    worker_startup_health: &str,
    worker_result_or_fallback_reason: &str,
    trace_source: Option<&str>,
) {
    if !internal_debug_observability_enabled() {
        return;
    }
    let exe_path = std::env::current_exe()
        .ok()
        .map(|p| p.to_string_lossy().to_string())
        .unwrap_or_else(|| "unknown".to_string());
    let build_marker = option_env!("MCP_SYNAPSE_BUILD_MARKER").unwrap_or(env!("CARGO_PKG_VERSION"));
    let out_file = repo_root
        .join("data")
        .join("observability")
        .join(WORKER_DECISION_LOG_FILE);
    let row = json!({
        "timestamp_unix_ms": unix_ms_now() as u64,
        "op": op,
        "flag_effective": flag_effective,
        "whitelist_eligible": whitelist_eligible,
        "worker_startup_health": worker_startup_health,
        "worker_result_or_fallback_reason": worker_result_or_fallback_reason,
        "pid": std::process::id(),
        "exe_path": exe_path,
        "dispatch_entry": DISPATCH_ENTRY_NAME,
        "build_marker": build_marker,
        "trace_source": trace_source,
    });
    let _ = append_jsonl(out_file, row);
}

fn append_worker_stage_log(repo_root: &PathBuf, op: &str, trace_source: Option<&str>, stage: &str) {
    if !internal_debug_observability_enabled() {
        return;
    }
    let exe_path = std::env::current_exe()
        .ok()
        .map(|p| p.to_string_lossy().to_string())
        .unwrap_or_else(|| "unknown".to_string());
    let build_marker = option_env!("MCP_SYNAPSE_BUILD_MARKER").unwrap_or(env!("CARGO_PKG_VERSION"));
    let out_file = repo_root
        .join("data")
        .join("observability")
        .join(WORKER_DECISION_LOG_FILE);
    let row = json!({
        "timestamp_unix_ms": unix_ms_now() as u64,
        "op": op,
        "stage": stage,
        "pid": std::process::id(),
        "exe_path": exe_path,
        "dispatch_entry": DISPATCH_ENTRY_NAME,
        "build_marker": build_marker,
        "trace_source": trace_source,
    });
    let _ = append_jsonl(out_file, row);
}

fn should_force_decision_log_for_op(op: &str) -> bool {
    matches!(op, "connections.copy_config" | "connections.schema_hint")
}

fn prompt_trace_source_for_observability(prompt: &str) -> Option<String> {
    let parsed = serde_json::from_str::<serde_json::Value>(prompt).ok()?;
    let obj = parsed.as_object()?;
    let raw = obj.get("_trace_source")?.as_str()?.trim();
    match raw {
        "details_open"
        | "copy_button"
        | "copy_debug"
        | "edit_open"
        | "new_provider_select" => Some(raw.to_string()),
        _ => None,
    }
}

#[tauri::command]
fn dispatch_execute_request_v1(agent_id: String, prompt: String) -> Result<DispatchResult, String> {
    let repo_root = repo_root_from_manifest_dir()?;
    let python = std::env::var("MCP_SYNAPSE_PYTHON").unwrap_or_else(|_| "python".to_string());
    let prompt_op = worker_dispatch::prompt_op_for_observability(&prompt);
    let trace_source = prompt_trace_source_for_observability(&prompt);
    let flag_effective = worker_dispatch::effective_worker_flag();
    let whitelist_eligible = prompt_op
        .as_deref()
        .map(worker_dispatch::is_worker_whitelist_op)
        .unwrap_or(false);
    let force_log_for_op = prompt_op
        .as_deref()
        .map(should_force_decision_log_for_op)
        .unwrap_or(false);
    if force_log_for_op {
        if let Some(op) = prompt_op.as_deref() {
            append_worker_stage_log(&repo_root, op, trace_source.as_deref(), "entry");
        }
    }
    let should_attempt_worker = worker_dispatch::should_attempt_worker(&prompt);
    let mut worker_startup_health = "not_attempted".to_string();
    let mut worker_result_or_fallback_reason = if flag_effective {
        "fallback:not_whitelisted_or_prompt_unparseable".to_string()
    } else {
        "fallback:flag_off".to_string()
    };

    if should_attempt_worker {
        match worker_dispatch::dispatch_via_worker(&agent_id, &prompt, &repo_root, &python) {
            Ok(result) => {
                worker_startup_health = "healthy".to_string();
                worker_result_or_fallback_reason = "worker_success".to_string();
                if let Some(op) = prompt_op.as_deref() {
                    if force_log_for_op {
                        append_worker_stage_log(
                            &repo_root,
                            op,
                            trace_source.as_deref(),
                            "worker_success",
                        );
                    }
                    append_worker_decision_log(
                        &repo_root,
                        op,
                        flag_effective,
                        whitelist_eligible,
                        &worker_startup_health,
                        &worker_result_or_fallback_reason,
                        trace_source.as_deref(),
                    );
                }
                return Ok(result);
            }
            Err(err) => {
                worker_startup_health =
                    worker_dispatch::classify_worker_startup_health(&err).to_string();
                worker_result_or_fallback_reason = format!("fallback:{}", log_text(&err, 220));
            }
        }
    }

    if force_log_for_op {
        if let Some(op) = prompt_op.as_deref() {
            append_worker_stage_log(&repo_root, op, trace_source.as_deref(), "legacy_before");
        }
    }
    let legacy_result = dispatch_execute_request_legacy(&repo_root, &python, &agent_id, &prompt);
    if whitelist_eligible || force_log_for_op {
        if let Some(op) = prompt_op.as_deref() {
            let worker_outcome = match &legacy_result {
                Ok(_) => worker_result_or_fallback_reason.clone(),
                Err(err) => format!(
                    "{}|legacy_error:{}",
                    worker_result_or_fallback_reason,
                    log_text(err, 220)
                ),
            };
            append_worker_decision_log(
                &repo_root,
                op,
                flag_effective,
                whitelist_eligible,
                &worker_startup_health,
                &worker_outcome,
                trace_source.as_deref(),
            );
        }
    }
    legacy_result
}

#[tauri::command]
fn ui_append_frontend_trace_v1(row: serde_json::Value) -> Result<bool, String> {
    if !internal_debug_observability_enabled() {
        return Ok(false);
    }
    let repo_root = repo_root_from_manifest_dir()?;
    let out_file = repo_root
        .join("data")
        .join("observability")
        .join("frontend_opcache_trace.jsonl");
    append_jsonl(out_file, row)
}

fn best_effort_stop_all_connections_with_budget(repo_root: &PathBuf) -> serde_json::Value {
    let start = Instant::now();
    let budget_ms = close_budget_ms();
    let script = repo_root.join("tools").join("headless_dispatch_v1.py");
    let python = std::env::var("MCP_SYNAPSE_PYTHON").unwrap_or_else(|_| "python".to_string());
    let prompt = r#"{"op":"connections.stop_all"}"#;
    let mut command = Command::new(python);
    command
        .arg(script)
        .arg("--agent-id")
        .arg("connections")
        .arg("--prompt")
        .arg(prompt)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null());
    #[cfg(windows)]
    command.creation_flags(CREATE_NO_WINDOW);

    let mut child = match command.spawn() {
        Ok(value) => value,
        Err(err) => {
            return json!({
                "status": "spawn_failed",
                "shutdown_scope": "stop_all",
                "cleanup_scope": "none",
                "child_process_wait": "not_started",
                "close_to_exit_ms_estimate": start.elapsed().as_millis() as u64,
                "close_budget_ms": budget_ms,
                "error": log_text(&err.to_string(), 180),
            });
        }
    };

    loop {
        match child.try_wait() {
            Ok(Some(status)) => {
                return json!({
                    "status": "completed",
                    "shutdown_scope": "stop_all",
                    "cleanup_scope": "none",
                    "child_process_wait": "bounded",
                    "close_to_exit_ms_estimate": start.elapsed().as_millis() as u64,
                    "close_budget_ms": budget_ms,
                    "exit_code": status.code(),
                });
            }
            Ok(None) => {
                if start.elapsed().as_millis() as u64 >= budget_ms {
                    let _ = child.kill();
                    let _ = child.wait();
                    return json!({
                        "status": "timeout_killed_fail_open",
                        "shutdown_scope": "stop_all",
                        "cleanup_scope": "none",
                        "child_process_wait": "bounded",
                        "close_to_exit_ms_estimate": start.elapsed().as_millis() as u64,
                        "close_budget_ms": budget_ms,
                    });
                }
                std::thread::sleep(Duration::from_millis(25));
            }
            Err(err) => {
                let _ = child.kill();
                let _ = child.wait();
                return json!({
                    "status": "wait_error_fail_open",
                    "shutdown_scope": "stop_all",
                    "cleanup_scope": "none",
                    "child_process_wait": "bounded",
                    "close_to_exit_ms_estimate": start.elapsed().as_millis() as u64,
                    "close_budget_ms": budget_ms,
                    "error": log_text(&err.to_string(), 180),
                });
            }
        }
    }
}

fn best_effort_reset_connection_runtime_state_on_startup(repo_root: &PathBuf) -> serde_json::Value {
    let start = Instant::now();
    let script = repo_root.join("tools").join("headless_dispatch_v1.py");
    let python = std::env::var("MCP_SYNAPSE_PYTHON").unwrap_or_else(|_| "python".to_string());
    let prompt = r#"{"op":"connections.reset_runtime_state"}"#;
    let mut command = Command::new(python);
    command
        .arg(script)
        .arg("--agent-id")
        .arg("connections")
        .arg("--prompt")
        .arg(prompt)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null());
    #[cfg(windows)]
    command.creation_flags(CREATE_NO_WINDOW);

    let mut child = match command.spawn() {
        Ok(value) => value,
        Err(err) => {
            return json!({
                "status": "spawn_failed",
                "scope": "startup_reset_runtime_state",
                "elapsed_ms": start.elapsed().as_millis() as u64,
                "error": log_text(&err.to_string(), 180),
            });
        }
    };

    let budget_ms = 2000_u64;
    loop {
        match child.try_wait() {
            Ok(Some(status)) => {
                return json!({
                    "status": "completed",
                    "scope": "startup_reset_runtime_state",
                    "elapsed_ms": start.elapsed().as_millis() as u64,
                    "exit_code": status.code(),
                });
            }
            Ok(None) => {
                if start.elapsed().as_millis() as u64 >= budget_ms {
                    let _ = child.kill();
                    let _ = child.wait();
                    return json!({
                        "status": "timeout_killed_fail_open",
                        "scope": "startup_reset_runtime_state",
                        "elapsed_ms": start.elapsed().as_millis() as u64,
                        "budget_ms": budget_ms,
                    });
                }
                std::thread::sleep(Duration::from_millis(25));
            }
            Err(err) => {
                let _ = child.kill();
                let _ = child.wait();
                return json!({
                    "status": "wait_error_fail_open",
                    "scope": "startup_reset_runtime_state",
                    "elapsed_ms": start.elapsed().as_millis() as u64,
                    "budget_ms": budget_ms,
                    "error": log_text(&err.to_string(), 180),
                });
            }
        }
    }
}

#[cfg(windows)]
fn to_wide_null(value: &str) -> Vec<u16> {
    value.encode_utf16().chain(std::iter::once(0)).collect()
}

#[cfg(windows)]
fn focus_existing_main_window() {
    let window_title = to_wide_null(MAIN_WINDOW_TITLE);
    for _ in 0..12 {
        let hwnd = unsafe { FindWindowW(std::ptr::null(), window_title.as_ptr()) };
        if !hwnd.is_null() {
            unsafe {
                if IsIconic(hwnd) != 0 {
                    let _ = ShowWindow(hwnd, SW_RESTORE);
                } else {
                    let _ = ShowWindow(hwnd, SW_SHOW);
                }
                let _ = SetForegroundWindow(hwnd);
            }
            return;
        }
        std::thread::sleep(Duration::from_millis(120));
    }
}

#[cfg(windows)]
fn should_exit_for_existing_instance() -> bool {
    let mutex_name = to_wide_null(SINGLE_INSTANCE_MUTEX_NAME);
    let handle = unsafe { CreateMutexW(std::ptr::null_mut(), 0, mutex_name.as_ptr()) };
    if handle.is_null() {
        return false;
    }

    let last_error = unsafe { GetLastError() };
    if last_error == ERROR_ALREADY_EXISTS {
        focus_existing_main_window();
        return true;
    }

    let _ = SINGLE_INSTANCE_MUTEX_HANDLE.set(handle as usize);
    false
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    #[cfg(windows)]
    if should_exit_for_existing_instance() {
        return;
    }

    let startup_t0 = Instant::now();
    let repo_root_for_lifecycle = repo_root_from_manifest_dir().ok();
    if let Some(repo_root) = repo_root_for_lifecycle.as_ref() {
        append_lifecycle_log(
            repo_root,
            "startup_boot",
            json!({
                "phase": "critical_before_ready",
            }),
        );
    }

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .setup(move |app| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.eval(DESKTOP_UX_HARDENING_JS);
            }
            if let Some(repo_root) = repo_root_for_lifecycle.as_ref() {
                append_lifecycle_log(
                    repo_root,
                    "startup_runtime_reset_begin",
                    json!({
                        "phase": "critical_before_ready",
                    }),
                );
                let reset_outcome = best_effort_reset_connection_runtime_state_on_startup(repo_root);
                append_lifecycle_log(repo_root, "startup_runtime_reset_end", reset_outcome);
                append_lifecycle_log(
                    repo_root,
                    "startup_ready",
                    json!({
                        "phase": "critical_before_ready",
                        "startup_ready_ms": startup_t0.elapsed().as_millis() as u64,
                    }),
                );

                let repo_root_bg = repo_root.clone();
                std::thread::spawn(move || {
                    let deferred_t0 = Instant::now();
                    append_lifecycle_log(
                        &repo_root_bg,
                        "startup_deferred_begin",
                        json!({
                            "phase": "defer_after_ready",
                            "task": "worker_prewarm",
                        }),
                    );
                    let python =
                        std::env::var("MCP_SYNAPSE_PYTHON").unwrap_or_else(|_| "python".to_string());
                    let status = if worker_dispatch::effective_worker_flag() {
                        match worker_dispatch::prewarm_worker(&repo_root_bg, &python) {
                            Ok(_) => "ok".to_string(),
                            Err(err) => format!("error:{}", log_text(&err, 180)),
                        }
                    } else {
                        "skipped_flag_off".to_string()
                    };
                    append_lifecycle_log(
                        &repo_root_bg,
                        "startup_deferred_done",
                        json!({
                            "phase": "defer_after_ready",
                            "task": "worker_prewarm",
                            "status": status,
                            "defer_after_ready_ms": deferred_t0.elapsed().as_millis() as u64,
                        }),
                    );
                });
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            dispatch_execute_request_v1,
            ui_append_frontend_trace_v1
        ])
        .on_window_event(|_window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                if !STOP_ALL_CONNECTIONS_ONCE.swap(true, Ordering::SeqCst) {
                    if let Ok(repo_root) = repo_root_from_manifest_dir() {
                        append_lifecycle_log(
                            &repo_root,
                            "shutdown_begin",
                            json!({
                                "phase": "close_requested",
                                "close_budget_ms": close_budget_ms(),
                            }),
                        );
                        let outcome = best_effort_stop_all_connections_with_budget(&repo_root);
                        append_lifecycle_log(&repo_root, "shutdown_end", outcome);
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
