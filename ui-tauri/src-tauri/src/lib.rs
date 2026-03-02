use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::process::Command;

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

#[tauri::command]
fn dispatch_execute_request_v1(agent_id: String, prompt: String) -> Result<DispatchResult, String> {
    let repo_root = repo_root_from_manifest_dir()?;
    let script = repo_root.join("tools").join("headless_dispatch_v1.py");

    let python = std::env::var("MCP_SYNAPSE_PYTHON").unwrap_or_else(|_| "python".to_string());

    let output = Command::new(python)
        .arg(script)
        .arg("--agent-id")
        .arg(agent_id)
        .arg("--prompt")
        .arg(prompt)
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

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![dispatch_execute_request_v1])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
