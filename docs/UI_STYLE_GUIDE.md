# Dashboard Design Language (UI Primitives)

This document captures the reusable design language used on the Dashboard UI, expressed as token usage and neutral CSS primitives. It is intended for consistent UI construction without introducing new styling systems or hardcoded colors.

## Token Usage

Use existing CSS variables from ui-tauri/src/app.css as the single source of truth for color, radii, spacing, and shadows.

- Background and surfaces: --bg-base, --surface-1, --surface-2
- Borders: --border-subtle
- Text: --text-primary, --text-muted
- Accent: --accent-base, --accent-dim, --accent-glow
- Radii: --radius-card, --radius-btn, --radius-badge
- Spacing: --space-1 … --space-5
- Shadows: --shadow-1, --shadow-2

## Token Canonical List

Canonical tokens to use in new code:

- --bg-base
- --surface-1
- --surface-2
- --border-subtle
- --text-primary
- --text-muted
- --accent-base
- --accent-glow
- --radius-card
- --radius-badge
- --shadow-1
- --space-1
- --space-3
- --space-4

Do not use legacy alias tokens in new code. They exist only for compatibility.

## Primitive Classes

These classes are defined in ui-tauri/src/app.css and are intentionally minimal so they do not change existing visuals unless applied.

- ui-card: Standard surface panel (background, border, radius, shadow).
- card: Alias for ui-card.
- ui-card--glow: Optional subtle accent glow overlay for premium emphasis.
- ui-pad-sm / ui-pad-md / ui-pad-lg: Spacing presets using token spacing.
- ui-title: Standard section/title typography helper.
- ui-subtitle: Muted subtitle/helper typography.
- ui-table: Base table shell (width, collapse).
- table-container: Alias for ui-table.
- ui-row-hover: Hover surface for clickable rows.
- table-row: Alias hover behavior for ui-row-hover.
- ui-pill: Base status chip styling (neutral; color can be applied via existing utility patterns).
- ui-focus: Accent focus ring for keyboard focus.

## Composition Rules

- Use ui-card for KPI tiles and dashboard panels.
- Use ui-title/ui-subtitle for panel headings and secondary labels.
- Use ui-table for tables and lists that need consistent column structure.
- Apply ui-row-hover to rows that are interactive; do not add hover effects to static rows.
- Apply ui-focus to interactive controls where focus visibility is needed.

## Interaction Rules

- Hover tooltips should be lightweight and non-layout-shifting (fixed position, pointer-events-none).
- Modals and popovers should not introduce global scrollbars; contain overflow within the component boundary.
- Prefer deterministic layouts (explicit widths/min-widths) for dense tables at constrained viewports.

## Do Not

- Do not hardcode colors when a token exists; use the CSS variables above.
- Do not introduce new radii/shadow values; use --radius-* and --shadow-*.
- Do not add new global CSS rules that change existing layout or typography.
- Do not rely on inline styles unless they are necessary for dynamic values; prefer primitives when reusable.

## Copy/Paste Snippets

Card:

```html
<div class="ui-card">
  ...
</div>
```

Card (alias):

```html
<div class="card">
  ...
</div>
```

Table container + row hover:

```html
<table class="ui-table">
  <tr class="ui-row-hover">
    ...
  </tr>
</table>
```

Aliases:

```html
<table class="table-container">
  <tr class="table-row">
    ...
  </tr>
</table>
```
