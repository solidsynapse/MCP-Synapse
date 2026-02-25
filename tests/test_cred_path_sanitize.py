def sanitize(p: str) -> str:
    return (p or "").strip().strip('"').strip("'")


def run_tests() -> None:
    cases = {
        '"C:\\path\\key.json"': r"C:\path\key.json",
        "'C:\\path\\key.json'": r"C:\path\key.json",
        r"C:\path\key.json": r"C:\path\key.json",
        ' "C:\\path with spaces\\key.json" ': r"C:\path with spaces\key.json",
        '""': "",
    }

    print("Running credential path sanitization tests...")
    for raw, expected in cases.items():
        result = sanitize(raw)
        print(f"RAW: {raw!r} -> SANITIZED: {result!r}")
        assert result == expected, f"Expected {expected!r}, got {result!r}"

    print("All sanitization tests passed.")


if __name__ == "__main__":
    run_tests()
