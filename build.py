from pathlib import Path
import json
import re
import subprocess
import sys


def set_tauri_conf_version(tauri_conf_path: Path, version: str) -> None:
    data = json.loads(tauri_conf_path.read_text(encoding="utf-8"))
    data["version"] = version
    tauri_conf_path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")


def set_cargo_version(cargo_toml_path: Path, version: str) -> None:
    raw = cargo_toml_path.read_text(encoding="utf-8")
    updated, count = re.subn(r'(?m)^version\s*=\s*".*"$', f'version = "{version}"', raw, count=1)
    if count != 1:
        raise RuntimeError("Could not update version in Cargo.toml")
    cargo_toml_path.write_text(updated, encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python build.py <version>")

    version = str(sys.argv[1]).strip()
    if not version:
        raise SystemExit("Version is required")

    root = Path(__file__).resolve().parent
    ui_tauri = root / "ui-tauri"
    tauri_conf = ui_tauri / "src-tauri" / "tauri.conf.json"
    cargo_toml = ui_tauri / "src-tauri" / "Cargo.toml"

    set_tauri_conf_version(tauri_conf, version)
    set_cargo_version(cargo_toml, version)

    subprocess.run(["cargo", "tauri", "build", "--bundles", "nsis,msi"], cwd=ui_tauri, check=True)


if __name__ == "__main__":
    main()
