# LC-V10 - Comprehensive Legal/Compliance Pack (Pre-Release)

Status: Pre-release legal/compliance baseline for V1.0.  
Audience: Product owner, release manager, support, and engineering.  
Legal note: This document is not legal advice; it is an engineering-operational compliance baseline to reduce preventable release risk.

## 1) Product Legal Posture (Current Truth)

- Deployment posture: local-first desktop app, user-configured provider routing.
- Data path posture: prompts/responses are sent to third-party model providers selected by the user.
- Enforcement posture: budget controls are monitor-only in V1.0 (D-031). No budget hard-blocking/throttling claims are allowed.
- Account posture: no mandatory product account is required for core local usage.

Operational consequence:
- We must document clear controller/processor boundaries and avoid any claim that implies platform-managed provider compliance on behalf of the user.

## 2) Regulatory Baseline (EU-Focused, Release-Relevant)

## GDPR (Regulation (EU) 2016/679)

Minimum release controls:
- Lawful-basis disclosure in privacy notice (who processes what, where, why).
- Third-party disclosure for provider calls (Vertex/Azure/OpenAI/Bedrock or other configured providers).
- Data subject request route (support contact and handling path).
- Breach handling process aligned with GDPR incident expectations.
- Cross-border transfer guardrails (adequacy/SCC fallback process).

Minimum product wording requirements:
- No "fully anonymous" guarantee unless technically proven for all flows.
- No "EU-only processing" claim unless enforced and verifiable for all providers and regions.
- No "zero retention everywhere" claim unless contractually and technically guaranteed per provider setup.

## EU AI Act (Regulation (EU) 2024/1689)

Release-safe approach:
- Treat V1.0 as a general-purpose integration/router product with transparency-first positioning.
- Avoid unsupported claims such as "AI Act certified/compliant by default."
- Maintain technical documentation discipline (decisions, evidence, known limits, and operator guidance).
- Preserve human-in-the-loop framing for operational decisions and generated output use.

## NIS2 (Directive (EU) 2022/2555) / Cybersecurity Readiness

Release baseline (pragmatic):
- Document incident intake channel and response process.
- Define logging and forensic minimums for security triage.
- Keep vulnerability disclosure and patch communication process explicit.

## Cyber Resilience Act (Regulation (EU) 2024/2847)

Forward-compat baseline:
- Maintain vulnerability handling workflow and update policy now, even before formal CRA duties fully apply.
- Preserve SBOM/dependency and release-note hygiene to reduce future compliance migration cost.

## 3) Provider and Data-Flow Disclosure Baseline

We must publish a provider disclosure table in product docs/release notes:

- Provider name
- Data sent (prompt, response, metadata)
- Retention posture (what is documented by provider plan/setting)
- Regional control options (if available)
- Customer-side configuration responsibility

Non-negotiable wording:
- "Provider policies and contracts govern provider-side processing."
- "Customer is responsible for provider-region, DPA/SCC, and account-level controls."

## 4) Cross-Border Transfer and Contracting Controls

For EU-facing release operations:
- Prefer adequacy-route providers/regions where feasible.
- If transfer to non-adequate jurisdictions is possible, maintain SCC-based contractual fallback.
- Keep DPA records for each provider account used in production operations.
- Keep a transfer-impact decision note (even if lightweight) as release evidence.

Minimum operational checklist per provider account:
1) DPA status confirmed.
2) Transfer mechanism documented (adequacy or SCC path).
3) Region/data residency setting documented.
4) Retention/training controls documented for the selected plan/settings.

## 5) Claims Policy (Hard Guardrails for Marketing and UI Copy)

Allowed claims (if true in current build):
- Local-first workflow orchestration.
- Monitor-only budget alerts.
- User-managed provider credentials and provider routing.
- Export and local data control features.

Blocked claims (unless proven with contractual + runtime evidence):
- "Guaranteed GDPR compliance."
- "AI Act compliant by default."
- "Zero provider retention for all providers."
- "No cross-border transfer risk."
- "Automatic legal compliance for customer workloads."

## 6) Security and Incident Operations (Minimum Release Standard)

Required before public release:
- Security contact (email or portal) publicly visible.
- Incident severity triage path (P1/P2/P3 or equivalent).
- Internal target timelines (acknowledge, triage, mitigate, communicate).
- Customer-facing incident update template.

Current release contact map:
- Security: security@solidsynapse.com
- Support: support@solidsynapse.com
- Legal/Privacy: legal@solidsynapse.com
- Product/Technical: mcp@solidsynapse.com
- General: info@solidsynapse.com

Minimum incident playbook:
1) Detect and log incident.
2) Classify scope and impact.
3) Isolate affected components.
4) Communicate customer-facing status.
5) Apply fix/workaround and verify.
6) Publish post-incident summary.

## 7) Documentation Pack Required for V1.0

Release bundle must include:
- Privacy Notice (current behavior aligned).
- Terms/Disclaimer (boundary and liability framing).
- Data retention/deletion statement.
- Third-party/provider disclosure.
- Security contact and incident reporting path.
- User guide + known issues + troubleshooting.

Consistency rules:
- Legal and user docs must use identical monitor-only budget language (D-031).
- Cost language must avoid false precision when provider pricing metadata is missing.
- Support boundaries must be explicit (what product supports vs what provider account supports).

## 8) Gap/Risk Register (Current)

Open risk R1 - Provider contract variance:
- Different provider plans can change data handling defaults.
- Mitigation: enforce per-provider account onboarding checklist and evidence capture.

Open risk R2 - Over-claiming in UI/help copy:
- Product text can drift into unsupported legal claims.
- Mitigation: claims guardrail review on release candidate.

Open risk R3 - Cross-border ambiguity:
- Region and transfer mechanics may be unclear to end users.
- Mitigation: provider-region guidance and explicit transfer disclaimer in docs.

Closed risk R4 - Incident channel readiness:
- Reporting channels were defined and published in the legal minimum pack.
- Remaining action is operational monitoring of mailbox responsiveness during RC.

## 9) V1.0 Gate Acceptance for Legal/Docs

GATE-V10-DOCS-LEGAL can be PASS only if:
1) LC-MIN-01 and DOCS-MIN-01 exist and are current-truth aligned.
2) This comprehensive pack is published and referenced in release docs.
3) No blocked claim appears in user-facing copy.
4) Security contact path is explicitly defined before release candidate sign-off.

If any item is missing: keep gate at REVALIDATE.

## 10) Source Register (Primary References)

EU primary law and official guidance:
- GDPR (Regulation (EU) 2016/679): https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng
- EU AI Act (Regulation (EU) 2024/1689): https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng
- NIS2 (Directive (EU) 2022/2555): https://eur-lex.europa.eu/eli/dir/2022/2555/oj/eng
- Cyber Resilience Act (Regulation (EU) 2024/2847): https://eur-lex.europa.eu/eli/reg/2024/2847/oj/eng
- SCC Decision (EU) 2021/914: https://eur-lex.europa.eu/eli/dec_impl/2021/914/oj/eng
- EU adequacy decisions overview: https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/adequacy-decisions_en

Provider/legal documentation (official):
- Google Cloud terms: https://cloud.google.com/terms
- Google Cloud / Vertex AI retention controls: https://cloud.google.com/vertex-ai/generative-ai/docs/learn/data-governance#data-retention
- Azure OpenAI data/privacy: https://learn.microsoft.com/en-us/legal/cognitive-services/openai/data-privacy
- AWS Bedrock data protection: https://docs.aws.amazon.com/bedrock/latest/userguide/data-protection.html
- OpenAI API data controls: https://platform.openai.com/docs/guides/your-data
- OpenAI Business Terms: https://openai.com/policies/business-terms/
- OpenAI DPA: https://openai.com/policies/data-processing-addendum/
