use crate::DispatchResult;
use serde_json::{json, Value};
use std::io::{BufRead, BufReader, Write};
#[cfg(windows)]
use std::os::windows::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{mpsc, Mutex, OnceLock};
use std::time::Duration;

#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x08000000;
const WORKER_FLAG_ENV: &str = "MCP_SYNAPSE_PERSISTENT_WORKER_V1";
const WORKER_TIMEOUT_ENV: &str = "MCP_SYNAPSE_PERSISTENT_WORKER_TIMEOUT_MS";
const WORKER_TIMEOUT_DEFAULT_MS: u64 = 8000;
const WORKER_ALLOWED_OPS: [&str; 10] = [
    "dashboard.get_state",
    "usage.recent",
    "connections.list",
    "connections.copy_config",
    "connections.schema_hint",
    "settings.get_state",
    "policies.persona.get_state",
    "policies.optimizations.get_state",
    "resilience.budget.get_state",
    "resilience.interceptors.get_state",
];

static NEXT_REQUEST_ID: AtomicU64 = AtomicU64::new(1);
static WORKER_STATE: OnceLock<Mutex<Option<WorkerHandle>>> = OnceLock::new();

#[derive(Clone)]
struct WorkerHandle {
    req_tx: mpsc::Sender<WorkerRequest>,
    pid: u32,
}

struct WorkerRequest {
    line: String,
    resp_tx: mpsc::Sender<Result<String, String>>,
}

enum WorkerError {
    Timeout,
    Other(String),
}

fn state() -> &'static Mutex<Option<WorkerHandle>> {
    WORKER_STATE.get_or_init(|| Mutex::new(None))
}

fn worker_enabled() -> bool {
    match std::env::var(WORKER_FLAG_ENV) {
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

fn worker_timeout_ms() -> u64 {
    match std::env::var(WORKER_TIMEOUT_ENV) {
        Ok(raw) => raw
            .trim()
            .parse::<u64>()
            .ok()
            .filter(|v| *v >= 100)
            .unwrap_or(WORKER_TIMEOUT_DEFAULT_MS),
        Err(_) => WORKER_TIMEOUT_DEFAULT_MS,
    }
}

fn prompt_op(prompt: &str) -> Option<String> {
    let parsed = serde_json::from_str::<Value>(prompt).ok()?;
    let obj = parsed.as_object()?;
    let op = obj.get("op")?.as_str()?.trim();
    if op.is_empty() {
        return None;
    }
    Some(op.to_string())
}

fn op_allowed(op: &str) -> bool {
    WORKER_ALLOWED_OPS.contains(&op)
}

pub fn should_attempt_worker(prompt: &str) -> bool {
    if !worker_enabled() {
        return false;
    }
    match prompt_op(prompt) {
        Some(op) => op_allowed(&op),
        None => false,
    }
}

pub fn effective_worker_flag() -> bool {
    worker_enabled()
}

pub fn prewarm_worker(repo_root: &Path, python: &str) -> Result<(), String> {
    if !worker_enabled() {
        return Ok(());
    }
    let _ = ensure_worker(repo_root, python)?;
    Ok(())
}

pub fn prompt_op_for_observability(prompt: &str) -> Option<String> {
    prompt_op(prompt)
}

pub fn is_worker_whitelist_op(op: &str) -> bool {
    op_allowed(op)
}

pub fn classify_worker_startup_health(error: &str) -> &'static str {
    let err = error.trim();
    if err.starts_with("worker_spawn_failed")
        || err.starts_with("worker_stdin_unavailable")
        || err.starts_with("worker_stdout_unavailable")
        || err.starts_with("worker_thread_spawn_failed")
        || err.starts_with("worker_state_lock_failed")
    {
        return "startup_failed";
    }
    if err == "worker_timeout" {
        return "running_timeout";
    }
    if err.starts_with("worker_response_json_failed")
        || err.starts_with("worker_returned_error")
        || err.starts_with("worker_missing_payload")
        || err.starts_with("worker_payload_parse_failed")
    {
        return "running_invalid_response";
    }
    if err.starts_with("worker_send_failed")
        || err.starts_with("worker_write_failed")
        || err.starts_with("worker_read_failed")
        || err == "worker_eof"
        || err == "worker_response_disconnected"
    {
        return "running_io_failed";
    }
    "running_unknown_error"
}

fn terminate_pid(pid: u32) {
    #[cfg(windows)]
    {
        let _ = Command::new("taskkill")
            .arg("/PID")
            .arg(pid.to_string())
            .arg("/T")
            .arg("/F")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();
    }
    #[cfg(not(windows))]
    {
        let _ = Command::new("kill")
            .arg("-TERM")
            .arg(pid.to_string())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();
    }
}

fn invalidate_worker(kill: bool) {
    let mut guard = match state().lock() {
        Ok(value) => value,
        Err(_) => return,
    };
    let old = guard.take();
    drop(guard);
    if kill {
        if let Some(handle) = old {
            terminate_pid(handle.pid);
        }
    }
}

fn worker_script_path(repo_root: &Path) -> PathBuf {
    repo_root.join("tools").join("dispatch_worker_v1.py")
}

fn spawn_worker(repo_root: &Path, python: &str) -> Result<WorkerHandle, String> {
    let script = worker_script_path(repo_root);
    let mut command = Command::new(python);
    command
        .arg("-u")
        .arg(script)
        .current_dir(repo_root)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null());
    #[cfg(windows)]
    command.creation_flags(CREATE_NO_WINDOW);
    let mut child = command
        .spawn()
        .map_err(|e| format!("worker_spawn_failed: {e}"))?;
    let pid = child.id();
    let stdin = child
        .stdin
        .take()
        .ok_or_else(|| "worker_stdin_unavailable".to_string())?;
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| "worker_stdout_unavailable".to_string())?;
    let (req_tx, req_rx) = mpsc::channel::<WorkerRequest>();
    std::thread::Builder::new()
        .name("synapse-worker-io".to_string())
        .spawn(move || {
            let mut child_stdin = stdin;
            let mut child_stdout = BufReader::new(stdout);
            while let Ok(req) = req_rx.recv() {
                let mut write_ok = child_stdin.write_all(req.line.as_bytes());
                if write_ok.is_ok() {
                    write_ok = child_stdin.write_all(b"\n");
                }
                if write_ok.is_ok() {
                    write_ok = child_stdin.flush();
                }
                if let Err(e) = write_ok {
                    let _ = req.resp_tx.send(Err(format!("worker_write_failed: {e}")));
                    break;
                }
                let mut line = String::new();
                match child_stdout.read_line(&mut line) {
                    Ok(0) => {
                        let _ = req.resp_tx.send(Err("worker_eof".to_string()));
                        break;
                    }
                    Ok(_) => {
                        let value = line.trim_end_matches(&['\r', '\n'][..]).to_string();
                        let _ = req.resp_tx.send(Ok(value));
                    }
                    Err(e) => {
                        let _ = req.resp_tx.send(Err(format!("worker_read_failed: {e}")));
                        break;
                    }
                }
            }
            let _ = child.kill();
            let _ = child.wait();
        })
        .map_err(|e| format!("worker_thread_spawn_failed: {e}"))?;
    Ok(WorkerHandle { req_tx, pid })
}

fn ensure_worker(repo_root: &Path, python: &str) -> Result<WorkerHandle, String> {
    let mut guard = state()
        .lock()
        .map_err(|_| "worker_state_lock_failed".to_string())?;
    if let Some(existing) = guard.as_ref() {
        return Ok(existing.clone());
    }
    let created = spawn_worker(repo_root, python)?;
    *guard = Some(created.clone());
    Ok(created)
}

fn build_worker_line(agent_id: &str, prompt: &str) -> Result<String, String> {
    let prompt_value = serde_json::from_str::<Value>(prompt)
        .map_err(|e| format!("worker_prompt_parse_failed: {e}"))?;
    if !prompt_value.is_object() {
        return Err("worker_prompt_must_be_object".to_string());
    }
    let request_id = NEXT_REQUEST_ID.fetch_add(1, Ordering::Relaxed);
    serde_json::to_string(&json!({
        "id": request_id,
        "agent_id": agent_id,
        "prompt": prompt_value
    }))
    .map_err(|e| format!("worker_request_json_failed: {e}"))
}

fn dispatch_once(handle: &WorkerHandle, agent_id: &str, prompt: &str, timeout_ms: u64) -> Result<String, WorkerError> {
    let line = build_worker_line(agent_id, prompt).map_err(WorkerError::Other)?;
    let (resp_tx, resp_rx) = mpsc::channel::<Result<String, String>>();
    handle
        .req_tx
        .send(WorkerRequest { line, resp_tx })
        .map_err(|e| WorkerError::Other(format!("worker_send_failed: {e}")))?;
    match resp_rx.recv_timeout(Duration::from_millis(timeout_ms)) {
        Ok(Ok(value)) => Ok(value),
        Ok(Err(e)) => Err(WorkerError::Other(e)),
        Err(mpsc::RecvTimeoutError::Timeout) => Err(WorkerError::Timeout),
        Err(mpsc::RecvTimeoutError::Disconnected) => {
            Err(WorkerError::Other("worker_response_disconnected".to_string()))
        }
    }
}

fn parse_worker_response(raw: &str) -> Result<DispatchResult, String> {
    let parsed: Value =
        serde_json::from_str(raw).map_err(|e| format!("worker_response_json_failed: {e}"))?;
    let is_ok = parsed.get("ok").and_then(Value::as_bool).unwrap_or(false);
    if !is_ok {
        let code = parsed
            .get("error")
            .and_then(|e| e.get("code"))
            .and_then(Value::as_str)
            .unwrap_or("worker_error");
        let message = parsed
            .get("error")
            .and_then(|e| e.get("message"))
            .and_then(Value::as_str)
            .unwrap_or("worker returned error");
        return Err(format!("worker_returned_error: {code}: {message}"));
    }
    let payload = parsed
        .get("payload")
        .ok_or_else(|| "worker_missing_payload".to_string())?;
    serde_json::from_value::<DispatchResult>(payload.clone())
        .map_err(|e| format!("worker_payload_parse_failed: {e}"))
}

pub fn dispatch_via_worker(agent_id: &str, prompt: &str, repo_root: &Path, python: &str) -> Result<DispatchResult, String> {
    let timeout_ms = worker_timeout_ms();
    let handle = ensure_worker(repo_root, python)?;
    match dispatch_once(&handle, agent_id, prompt, timeout_ms) {
        Ok(raw) => match parse_worker_response(&raw) {
            Ok(result) => Ok(result),
            Err(e) => {
                invalidate_worker(true);
                Err(e)
            }
        },
        Err(WorkerError::Timeout) => {
            invalidate_worker(true);
            Err("worker_timeout".to_string())
        }
        Err(WorkerError::Other(e)) => {
            invalidate_worker(true);
            Err(e)
        }
    }
}
