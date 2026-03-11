# LC-MIN-01 - Legal/Compliance Minimum Pack

Scope: Minimum, user-facing legal/compliance text for the current release. This document does not change runtime behavior.

Companion document: `docs/Final_Roadmap/LC_V10_Comprehensive_Legal_Compliance_Pack.md` (detailed legal/compliance baseline and source register).

## 1) Privacy Notice
We respect user privacy and aim to collect only what is necessary to operate the product. The application runs locally and processes data on the device. If you configure external AI/LLM providers, your prompts and responses are sent to those providers under their own terms and policies.

We do not sell personal data. We do not include advertising trackers. We do not require an account to use the product in the current release.

Budget guard behavior is monitor-only in this release. It provides informational warnings but does not block, throttle, or alter request execution.

## 2) Data Retention / Deletion Policy
Local application data (connections, settings, and usage views) is stored on the device. You control retention by deleting entries or uninstalling the application.

If you export data or logs, those exports become your responsibility to store or delete according to your policies. If you want to remove a connection or usage record, delete it from the UI; this removes it from local storage.

We do not operate a server-side data store for this product in the current release.

## 3) Telemetry + Third-Party Disclosure
Telemetry: The current release does not require external analytics services to function. If you enable any optional telemetry in your environment, it should be limited to operational metrics and must be disclosed in your deployment notes.

Third-party disclosure: When you select a provider (for example, an AI/LLM provider), requests are sent to that provider. Their terms and privacy policies apply to the data you send.

We do not share data with third parties other than the providers you explicitly configure.

## 4) Terms / Disclaimer
This product provides UI and workflow tooling; it does not guarantee the accuracy, completeness, or suitability of model outputs. You are responsible for reviewing outputs and any actions taken based on them.

Budget-related indicators are informational only in this release. They do not enforce limits or prevent execution.

You are responsible for complying with applicable laws and any third-party provider terms.

Operational boundary: This release follows a BYOK + local-only model. Credentials and provider usage authority remain with the user organization.

Forbidden uses:
1) Credential sharing/pooling across unrelated third parties.
2) Running the product as a generic proxy-as-a-service endpoint for external tenants.
3) Claiming the product replaces provider-side legal/compliance obligations.

## 5) Security Contact + Incident Reporting
Security Contact (vulnerability/incident): security@solidsynapse.com
Support Contact (product/user issues): support@solidsynapse.com
Legal Contact (privacy/contracts): legal@solidsynapse.com
Product/Technical Contact (integration): mcp@solidsynapse.com
General Contact (non-support general inquiries): info@solidsynapse.com

Incident reporting process:
1) Report vulnerabilities/incidents through security@solidsynapse.com.
2) Include a clear description, timestamps, and any relevant logs or screenshots.
3) We will acknowledge receipt, triage severity, and provide remediation guidance or fixes.
