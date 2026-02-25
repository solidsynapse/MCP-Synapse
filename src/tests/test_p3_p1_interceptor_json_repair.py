import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.mcp_server.interceptor_p3_p1 import repair_json_syntax


def test_p3_p1_valid_json_no_repair() -> None:
    raw = '{"a": 1, "b": [true, null, "x"]}'
    result = repair_json_syntax(raw)
    assert result.ok is True
    assert result.value == {"a": 1, "b": [True, None, "x"]}
    assert result.repaired is None
    assert result.changes == []
    assert result.error is None


def test_p3_p1_embedded_json_extracts_object() -> None:
    raw = "Here you go:\n{\"a\": 1}\nThanks"
    result = repair_json_syntax(raw)
    assert result.ok is True
    assert result.value == {"a": 1}
    assert result.repaired == "{\"a\": 1}"
    assert result.changes == [{"op": "extract_json_substring", "kind": "object"}]
    assert result.error is None


def test_p3_p1_trailing_comma_repaired_object() -> None:
    raw = "{\"a\": 1,}"
    result = repair_json_syntax(raw)
    assert result.ok is True
    assert result.value == {"a": 1}
    assert result.repaired == "{\"a\": 1}"
    assert result.changes == [{"op": "remove_trailing_commas"}]
    assert result.error is None


def test_p3_p1_trailing_comma_repaired_array() -> None:
    raw = "[1,2,]"
    result = repair_json_syntax(raw)
    assert result.ok is True
    assert result.value == [1, 2]
    assert result.repaired == "[1,2]"
    assert result.changes == [{"op": "remove_trailing_commas"}]
    assert result.error is None


def test_p3_p1_disallowed_single_quotes_fails() -> None:
    raw = "{'a': 1}"
    result = repair_json_syntax(raw)
    assert result.ok is False
    assert result.value is None
    assert result.repaired is None
    assert result.error is not None


def test_p3_p1_determinism_same_input_same_output() -> None:
    raw = "junk {\"a\": 1,}\n"
    r1 = repair_json_syntax(raw)
    r2 = repair_json_syntax(raw)
    assert r1.to_dict() == r2.to_dict()
