import sys

def main() -> int:
    """
    PUBLIC_INTERFACE
    Perform a lightweight import check to validate that the FastAPI app and
    dependencies load correctly without starting the server.
    Returns 0 if success, non-zero otherwise.
    """
    try:
        from src.api.main import app  # noqa: F401
        print("Import OK: src.api.main.app")
        return 0
    except Exception as e:
        print(f"Import failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
