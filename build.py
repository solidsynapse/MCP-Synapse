from pathlib import Path
import subprocess
import sys


def main() -> None:
    root = Path(__file__).resolve().parent
    main_path = root / "src" / "main.py"

    # Use Flet CLI entrypoint; python -m flet fails because flet.__main__ is not present.
    flet_exe = root / "venv" / "Scripts" / "flet.exe"
    cmd = [
        str(flet_exe),
        "pack",
        str(main_path),
        "--name",
        "MCP Router",
        "--add-data",
        "data:data",
    ]
    subprocess.run(cmd, cwd=root, check=True)


if __name__ == "__main__":
    main()
