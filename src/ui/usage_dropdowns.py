from __future__ import annotations


def _coerce_agent_name(value: object) -> str:
    return str(value or "").strip()


def build_usage_bridge_option_specs(
    *,
    config_agents: list[dict] | None,
    usage_rows: list[dict] | None,
    selected_key: str | None,
    test_prefix: str = "_test_",
) -> tuple[list[tuple[str, str]], str]:
    config_names: set[str] = set()
    for agent in config_agents or []:
        name = _coerce_agent_name((agent or {}).get("name"))
        if name:
            config_names.add(name)

    usage_names: set[str] = set()
    for row in usage_rows or []:
        name = _coerce_agent_name((row or {}).get("agent_name"))
        if name:
            usage_names.add(name)

    names: set[str] = set()
    names.update(config_names)
    names.update(usage_names)

    selection = _coerce_agent_name(selected_key) or "All Bridges"
    if selection.endswith(" (test)") and not selection.startswith(test_prefix):
        base = selection[: -len(" (test)")].strip()
        if base:
            selection = f"{test_prefix}{base}"

    if selection != "All Bridges" and selection not in names:
        names.add(selection)

    ordered = sorted(names)
    specs: list[tuple[str, str]] = [("All Bridges", "All Bridges")]
    prefix = _coerce_agent_name(test_prefix)
    for name in ordered:
        text = name
        if prefix and name.startswith(prefix):
            base = name[len(prefix) :].strip()
            if base:
                text = f"{base} (test)"
        specs.append((name, text))

    if selection not in {k for k, _ in specs}:
        selection = "All Bridges"
    return specs, selection
