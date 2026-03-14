from pathlib import Path

p = Path("dummy.json")
p.write_text('{"dummy": true}\n', encoding="utf-8")  # NO BOM
b = p.read_bytes()

print("has_BOM_utf8:", b.startswith(b"\xef\xbb\xbf"))
print("head_bytes:", b[:8])
print("content:", p.read_text(encoding="utf-8"))
