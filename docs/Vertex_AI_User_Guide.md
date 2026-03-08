# Google Cloud Vertex AI -> MCP Synapse -> Local IDE (MCP) User Guide

This guide is for first-time users who want to connect Google Cloud Vertex AI to MCP Synapse and use it from a local IDE MCP client.

Scope:
- Provider: Google Cloud Vertex AI
- Auth path: Service Account JSON key file
- Contract: Vertex AI requires a valid Project ID and a specific Model ID

---

## Table of Contents

1. Prerequisites
2. What You Build
3. Critical Google Cloud Concepts
4. Step 1 - Enable Vertex AI API
5. Step 2 - Create a Service Account
6. Step 3 - Assign Permissions (Roles)
7. Step 4 - Create and Download JSON Key
8. Step 5 - Locate Your Project ID
9. Step 6 - Establish Vertex AI Model Connection
10. Budget and Cost Management
11. Step 7 - Advanced Settings (Region and Endpoint)
12. Step 8 - Test Connection and Add to IDE

---

## 1. Prerequisites

- Active Google Cloud account and project
- Access to Google Cloud Console
- MCP Synapse installed and running locally
- Local IDE/client with MCP support
- Billing enabled for your Google Cloud project (required for API usage)

---

## 2. What You Build

Working chain:

Google Cloud Project -> Service Account (JSON Auth) -> MCP Synapse Connection -> IDE MCP Server -> Live prompt response

---

## 3. Critical Google Cloud Concepts

- **Project ID:** The unique identifier for your GCP project where billing and resources are managed.
- **Service Account:** A "robot user" identity that allows your application to securely access Google Cloud resources.
- **Model ID:** The specific identifier for the Vertex AI model you want to use (e.g., `gemini-2.5-pro`).

---

## 4. Step 1 - Enable Vertex AI API

In Google Cloud Console:

1. Type **Vertex AI API** in the top search bar.
2. Go to the API page and click the **Enable** button.
3. Wait until you see *API Enabled* or *Manage* on the screen to confirm it is active.

---

## 5. Step 2 - Create a Service Account

A service account is required to authenticate your local MCP Synapse instance with Google Cloud.

1. From the left navigation menu, go to **IAM & Admin** > **Service Accounts**.
2. Click the **+ Create Service Account** button at the top.
3. Under details, provide a "Service account name" (e.g., `mcp-synapse-accessor`). The ID will be generated automatically.
4. Click **Create and Continue**.

---

## 6. Step 3 - Assign Permissions (Roles)

This is a critical step; even with a valid key, you will receive errors if you lack the proper permissions.

1. Click the **Select a role** dropdown.
2. Search for **Vertex AI User** and select it.
   *(Note: If you need broader administrative access, you can select "Vertex AI Administrator" instead).*
3. Click the **Done** button to complete the process.

---

## 7. Step 4 - Create and Download JSON Key

Now, you will generate the "password" file used to authenticate this service account.

1. On the Service Accounts list page, click the Email address of the account you just created.
2. Navigate to the **Keys** tab at the top.
3. Click **Add Key** > **Create new key**.
4. Select **JSON** as the key type and click **Create**.
5. A `.json` file will be downloaded to your computer. Move this file to your project's root directory or a secure local folder.

> [!IMPORTANT]
> This JSON file acts as your master password. **Never** share it publicly or commit it to public repositories like GitHub!

---

## 8. Step 5 - Locate Your Project ID

The Project ID field in the MCP Synapse form determines under which project your Google Cloud resources will be billed and managed. You can find this using the following methods:

**Method A: Google Cloud Console Top Bar (Fastest)**
Look at the project selector next to the Google Cloud logo in the top left corner of any console page. You will see your project's Display Name and the Project ID (e.g., `tensile-cogency-483219-q5`). It usually consists of lowercase letters, numbers, and hyphens.

**Method B: Inside the JSON Key File**
Open your downloaded `.json` credential file with a text editor. Look at the top lines for `"project_id": "your-project-id"`. Copy the value inside the quotes.

**Method C: Via Dashboard**
Go to Google Cloud Console > Dashboard. Look at the **Project Info** card on the left side and copy the Project ID value.

> [!IMPORTANT]
> **Match Check:** The value you enter in the "Project ID" field must exactly match the `project_id` value inside the JSON file you provide in the "Credentials Path". Otherwise, you will encounter an "Authentication Error" or "Permission Denied".

---

## 9. Step 6 - Establish Vertex AI Model Connection

To connect Vertex AI models to your MCP Synapse project, you must provide the correct "Model ID".

**Finding the Model ID:**
1. Go to **Vertex AI > Model Garden** in the Google Cloud Console.
2. Select the model card you want to use.
3. Click **View on Model Garden**.
4. Scroll down to the **Model Details** table on the Overview tab.
5. Copy the technical name from the **Model Name** row (e.g., `gemini-2.5-pro` or `gemini-2.0-flash-001`).
6. Paste this ID into the **Model ID** field in the MCP Synapse interface.

> [!TIP]
> **Short ID vs. Full Path:** Usually, short IDs like `gemini-2.5-pro` are sufficient. If you encounter connection errors, you can copy the Full Path located at the top right of the model page (starts with `publishers/google/models/...`).

**Which Model Should I Choose?**
To see the full list of currently available models and their API IDs, visit the official [Vertex AI Models Page](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models). 
Copy the exact version name, paste it into the Model ID box, and click **Preflight / Test**. The system performs a targeted dry probe for the model and returns explicit status classes (`Preflight OK`, `NOT_FOUND_OR_NO_ACCESS (404)`, `PERMISSION (403)`, `QUOTA`, or `PROBE_FAILED`).

> [!CAUTION]
> **About API 404 Errors:** If you receive a "404 Not Found" error during the Preflight test despite entering the correct Model ID, this does not mean your settings are wrong. Google does not instantly grant API access to all projects for some new or "Preview" models (e.g., `gemini-3.1-pro-preview`). In such cases, switch to a stable, widely available model like `gemini-2.5-pro` or `gemini-2.0-flash-001`.

---

## 10. Budget and Cost Management

Understanding how costs are calculated when selecting models on Vertex AI prevents unexpected billing surprises.

> [!WARNING]
> **Important Budget Note:** Google Cloud's $300 free credit for new accounts applies to Gemini, Llama, and Gemma models, as well as standard infrastructure services. However, Partner models like Claude and GLM 5 are usually billed directly and independently of this credit.

| Model Category | Example Models | Billing Method | Covered by $300 Credit? |
| :--- | :--- | :--- | :--- |
| **Google Built-in** | Gemini 1.5 Pro / Flash | Pay-per-use (Tokens) | Yes |
| **Partner (MaaS)** | Claude 3.5, GLM 5 | Pay-per-use (Tokens) | No (Usually) |
| **Open Source (Self-Hosted)** | Llama 3, Falcon | Infrastructure (GPU/CPU) | Yes |

**Key Details to Watch:**

**A. Google's Native Models**
* **Credit Usage:** Costs incurred from calling Gemini models are deducted from your available $300 credit.
* **Free Tier:** You have free usage allowances within specific limits (e.g., monthly limits for online predictions).

**B. Partner Models (MaaS - Model-as-a-Service)**
* **Direct Billing:** Because payments go to partners (Anthropic, Zhipu, etc.), using these models generally requires upgrading your account to a "Paid" status.
* **Error Messages:** If no credit card is linked or your account is in Free-tier, you may receive a `Free-tier accounts cannot access this model` error.

**C. Open Source Models (Compute-based)**
* **Compute Power Payment:** When you deploy models like Llama to a custom Endpoint, you pay for the GPU/CPU compute time powering the model, not the model itself. This compute cost is covered by the $300 credit.

---

## 11. Step 7 - Advanced Settings (Region and Endpoint)

These fields at the bottom of the form determine the technical routing of your connection. If you don't have specific networking needs, it is highly recommended to use the defaults.

* **Location:** * *Default:* `us-central1`
    * *Description:* The physical region where your Vertex AI resources are hosted. Keep it as `us-central1` unless your organization requires otherwise, as it is the most stable and feature-rich region for GCP.
* **Endpoint / Base URL:**
    * *Default:* Leave empty
    * *Description:* Used to override standard Google endpoints. Leave this blank unless you are using a custom Proxy, Private Service Connect, or specific API gateway. The application will automatically select the optimal routing.

---

## 12. Step 8 - Test Connection and Add to IDE

Once the form is filled out, follow these steps to verify your settings and integrate the connection into your local IDE:

1.  **Preflight (Dry-Run):** Click the **Preflight** button at the bottom of the form. This performs a targeted validation of your JSON path, Project ID, and model access on Google Cloud.
2.  **Confirm and Create:** Once you receive a green **Preflight OK** message, click **Create Connection** to save.
3.  **Copy Configuration:** In the Connections list, click the **Copy** icon next to your newly created connection. This copies the specific MCP configuration snippet to your clipboard.
4.  **IDE Integration:** Open the MCP settings page in your local IDE (Cursor, VS Code, etc.). Paste the copied snippet into the Manual Entry section and save.

> [!CHECK]
> **Stage 1 PASS!** Every query you make through your local IDE will now be routed to Vertex AI via Synapse, allowing you to seamlessly track your usage and costs in real-time.
