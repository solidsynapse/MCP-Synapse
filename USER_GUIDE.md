# MCP Router - Google Vertex AI Gateway (Desktop UI)

## Overview

MCP Router is a Windows desktop app that lets you expose Google Vertex AI models as MCP servers. You can:

- Register multiple agents backed by Vertex AI models
- Start/stop MCP servers for each agent
- Copy ready-to-use MCP configuration JSON
- Monitor usage, tokens, and cost over time

> Screenshot Placeholder: Main dashboard with Agent Management tab  
> Screenshot Placeholder: Usage & Analytics tab

---

## Getting Started

### 1. Install Requirements

From the project root:

```bash
py -3.11 -m pip install -r requirements.txt
```

### 2. Run the Desktop App

```bash
py -3.11 src/main.py
```

The main window will open with dark mode enabled.

---

## Agent Management Flow

### Step 1: Add an Agent

1. Click the blue `+` floating button in the bottom-right corner.
2. Fill in the Add Agent dialog:
   - **Agent Name**: Friendly name (e.g., "Gemini 2.0 Flash").
   - **Project ID**: Your GCP project ID.
   - **Location**: Choose from `us-central1`, `europe-west1`, or `asia-northeast1`.
   - **Model ID**: e.g. `gemini-2.0-flash-001`.
   - **Credentials File**: Click "Choose Credentials File" and select your JSON key.
   - **Price Input $/1M**: Optional, for cost estimation.
   - **Price Output $/1M**: Optional, for cost estimation.
   - **Port**: Auto-filled with the next available port (5000–6000).
3. Click **Create Agent**.
4. The agent card appears in the Agent Management tab.

> Screenshot Placeholder: Add Agent dialog

### Step 2: Start the Agent

On the agent card:

1. Click **Start** (▶) to launch the MCP server.
2. The status dot turns green and the status text becomes RUNNING.
3. The server listens on `http://localhost:<port>/sse`.

If anything goes wrong (credentials, port, model access), you’ll see a friendly error dialog instead of a crash.

### Step 3: Copy MCP Config

1. On the running agent card, click **Copy Config**.
2. The MCP JSON is copied to your clipboard.
3. A snackbar shows: `✅ Copied to clipboard!`

The JSON has this exact shape:

```json
{
  "mcpServers": {
    "<name>": {
      "url": "http://localhost:<port>/sse"
    }
  }
}
```

You can paste this into your MCP-enabled IDE config (such as TRAE).

### Step 4: Test the Agent

1. Click **Test** on the agent card.
2. The app sends a `Hi` prompt to Vertex AI using the configured credentials and model.
3. A dialog shows the model response, token counts, and estimated cost.

### Step 5: Stop or Delete the Agent

- **Stop**: Click **Stop** (⏸) to shut down the MCP server and mark it as stopped.
- **Delete**: Click **Delete**, confirm, and the agent is removed from the config and stopped if running.

---

## Usage & Analytics

Switch to the **Usage** tab to see:

- **Total Cost**: Aggregated cost across all logged calls.
- **Total Tokens**: Combined input + output tokens.
- **Active Agents**: Number of agents currently running.

Below the summary cards, a table shows the most recent usage entries:

- Timestamp  
- Agent name  
- Tokens In  
- Tokens Out  
- Cost ($)  

Click the **Refresh** button in the top-right to reload the metrics and table.

> Screenshot Placeholder: Usage summary cards and table

---

## Building a Windows Executable

> NOTE: This section must match SSOT. Source of truth: docs/STATUS.md (Build Gate Status + T0.5 notes).

1) Create and activate a venv (Windows PowerShell):
   - python -m venv .venv
   - .\.venv\Scripts\Activate.ps1

2) Install pinned dependencies:
   - python -m pip install -r requirements.txt

3) Build the executable (Flet pack):
   - flet pack src/main.py --name "MCP Router" --add-data "data:data"

4) Expected output:
   - dist\MCP Router.exe
## Using MCP Config in TRAE

1. Start your desired agent from the Agent Management tab.
2. Click **Copy Config** on that agent card.
3. In TRAE, open the MCP configuration section.
4. Paste the JSON you copied.
5. Save and reload MCP servers in TRAE.

Your Vertex AI-backed MCP server is now available inside your IDE.

---

## Troubleshooting

### No Window Appears

- Ensure you are using Python 3.11:
  - `py -3.11 --version`
- Reinstall dependencies:
  - `py -3.11 -m pip install -r requirements.txt`

### Cannot Start Agent (Port Error)

- Another process may be using the port.
- Edit the agent and choose a different port between 5000 and 6000.

### Credential Errors

- Make sure the JSON file is a valid GCP service account key.
- Required fields: `type`, `project_id`, `private_key`, `client_email`.
- Verify that the service account has access to Vertex AI and the target model.

### Model Not Found / Access Denied

- Check that the model ID (for example `gemini-2.0-flash-001`) is available in your project and region.
- Confirm that Vertex AI generative models are enabled in your GCP project.

### Usage Tab Empty

- The usage database is created automatically as you make calls.
- Once you run tests or use tools through MCP, entries will appear.

### App Crashes or Freezes

- All UI actions are wrapped with error handling.
- If you still see issues:
  - Close the app.
  - Remove `data/config.json` and `data/usage.db` if they are corrupted.
  - Restart the app and recreate agents.

If problems persist, consider running from the console to see Python tracebacks and share them with the maintainer.

