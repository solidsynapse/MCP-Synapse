---
title: Feature Reference
description: Developer-facing reference for the current MCP Synapse product surface in the v0.8.0 Early Access lane.
sidebar:
  label: Feature Reference
  order: 11
---

This page describes the current MCP Synapse product surface for the `v0.8.0` Early Access lane. It is written for developers evaluating what the desktop app exposes today, what each surface is responsible for, and where the current boundaries remain intentionally narrow.

MCP Synapse is a commercial, source-visible product. It is not MIT-licensed, it is not a hosted proxy service, and all runtime execution remains BYOK and local-first.

## Connections

The Connections surface is where you create, edit, start, stop, and delete connections backed by supported providers or the Custom REST API adapter. It also handles provider selection, schema-guided form entry, connection preflight, and MCP config export through the copy-config flow.

This surface does not execute provider logic directly in the UI. Provider behavior, credential resolution, request execution, and REST request handling stay in the backend core, and Bedrock remains Early Access rather than fully runtime-proven.

## Dashboard

The Dashboard surface summarizes recent operational state across the current product path. It exposes KPI cards, a 30-day cost trend, cost breakdown, health alerts, recent requests, and top-expensive requests so the user can see current activity without opening deeper tools first.

The Dashboard is a read-oriented operational view, not a workflow editor. It reflects current backend state and visibility artifacts, but it does not introduce hidden remediation, retry, or routing behavior on its own.

## Usage Summary and History

The Usage surface is the request-level visibility layer. Usage History supports filtering, sorting, pagination, clear-history flow, and CSV export, while pricing state remains explicit through `cost_source` (`ACTUAL`, `ESTIMATED`, or `UNKNOWN`).

This surface reports what the system observed; it does not normalize missing pricing into fake certainty. If pricing data is unavailable for a row, the UI keeps that uncertainty visible instead of silently treating it as exact.

## Policies

The Policies surface currently covers Persona Lite and Optimizations. Persona Lite provides deterministic preset-based system prompt injection, while Optimizations expose persisted toggles for context caching and request deduplication.

This surface is intentionally narrow in the current lane. It does not provide full persona studio, long-term memory, or advanced policy orchestration beyond the persisted controls already exposed in core.

## Resilience

The Resilience surface currently covers Interceptors and Budget Guard. Interceptors expose persisted JSON syntax repair settings, and Budget Guard now supports explicit `monitor`, `block`, and `throttle` behavior across all connections or a selected connection scope.

Resilience behavior remains explicit. The product does not hide fallback, retry, or enforcement logic behind undocumented automation.

## Settings

The Settings surface is the local configuration panel for get, set, persist, validate, reset-style flows, and the notify-only update-check path. It is intended to expose stable local state management without requiring users to edit config files directly.

Settings are saved locally through the application boundary, not by direct user-side file editing through the UI. This keeps the thin-shell boundary intact and avoids turning the UI into a raw config editor.

## Vault

Vault is the local credential storage helper used by the Connections workflow. It supports keyring-backed entry creation, listing, selection, and deletion, including local credential-path references for supported provider setup flows.

Vault is local-only and metadata-first on the current product path. It is not a cloud secret manager, not a team-sharing system, and the UI does not treat vault selection as a raw-secret autofill mechanism.
