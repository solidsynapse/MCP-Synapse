import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


FORBIDDEN = (
    "call_google_vertex_ai",
    "[VERTEX AI GATEWAY]",
)


def test_core_has_no_provider_specific_tool_strings() -> None:
    core_dir = ROOT / "src" / "mcp_server"
    assert core_dir.exists()

    offenders: list[str] = []
    for path in sorted(core_dir.rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for needle in FORBIDDEN:
            if needle in text:
                offenders.append(f"{path}:{needle}")

    assert offenders == []
