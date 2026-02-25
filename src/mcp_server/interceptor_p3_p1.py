from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Optional


_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")


@dataclass(frozen=True)
class RepairResult:
    ok: bool
    raw: str
    value: Any
    repaired: Optional[str]
    changes: list[dict[str, Any]]
    error: Optional[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "raw": self.raw,
            "value": self.value,
            "repaired": self.repaired,
            "changes": self.changes,
            "error": self.error,
        }


def repair_json_syntax(raw: str) -> RepairResult:
    value = _try_parse(raw)
    if value is not None:
        return RepairResult(
            ok=True,
            raw=raw,
            value=value,
            repaired=None,
            changes=[],
            error=None,
        )

    s = raw.strip()
    changes: list[dict[str, Any]] = []
    if s != raw:
        value = _try_parse(s)
        if value is not None:
            changes.append({"op": "trim_whitespace"})
            return RepairResult(
                ok=True,
                raw=raw,
                value=value,
                repaired=s,
                changes=changes,
                error=None,
            )

    extracted, kind = _extract_json_substring(s)
    if extracted is not None:
        changes.append({"op": "extract_json_substring", "kind": kind})
        value = _try_parse(extracted)
        if value is not None:
            return RepairResult(
                ok=True,
                raw=raw,
                value=value,
                repaired=extracted,
                changes=changes,
                error=None,
            )
        s = extracted

    decomma = _remove_trailing_commas(s)
    if decomma != s:
        changes.append({"op": "remove_trailing_commas"})
        value = _try_parse(decomma)
        if value is not None:
            return RepairResult(
                ok=True,
                raw=raw,
                value=value,
                repaired=decomma,
                changes=changes,
                error=None,
            )

    return RepairResult(
        ok=False,
        raw=raw,
        value=None,
        repaired=None,
        changes=changes,
        error="json_decode_error",
    )


def _try_parse(s: str) -> Any | None:
    try:
        return json.loads(s)
    except Exception:
        return None


def _extract_json_substring(s: str) -> tuple[str | None, str | None]:
    obj = _extract_by_brackets(s, "{", "}")
    if obj is not None:
        return obj, "object"
    arr = _extract_by_brackets(s, "[", "]")
    if arr is not None:
        return arr, "array"
    return None, None


def _extract_by_brackets(s: str, open_ch: str, close_ch: str) -> str | None:
    start = s.find(open_ch)
    if start == -1:
        return None
    end = s.rfind(close_ch)
    if end == -1 or end <= start:
        return None
    candidate = s[start : end + 1]
    if candidate == s:
        return None
    return candidate


def _remove_trailing_commas(s: str) -> str:
    while True:
        updated = _TRAILING_COMMA_RE.sub(r"\1", s)
        if updated == s:
            return s
        s = updated
