import os
import json
from pathlib import Path

def main():
    """Local-only CI: run pytest suites and summarize.
    - No network calls, no cloud
    - Exits non-zero on failures
    """
    import subprocess
    print("Running unit + integration + e2e tests (local-only)...")
    # prefer coverage if available
    try:
        import importlib
        if importlib.util.find_spec('pytest_cov') is not None:
            code = subprocess.call(["python", "-m", "pytest", "--maxfail=1", "--cov=saraphina", "--cov-report=term-missing", "-q"])  # concise
        else:
            code = subprocess.call(["python", "-m", "pytest", "--maxfail=1", "-q"])  # concise
    except Exception:
        code = subprocess.call(["python", "-m", "pytest", "-q"])  # fallback
    # Optionally run flake8 and mypy if available
    try:
        import shutil
        if shutil.which("ruff"):
            print("Running ruff...")
            subprocess.check_call(["ruff", "check", "."]) 
        elif shutil.which("flake8"):
            print("Running flake8...")
            subprocess.check_call(["flake8", ".", "--max-line-length=120"]) 
        if shutil.which("mypy"):
            print("Running mypy (best-effort)...")
            subprocess.call(["mypy", "saraphina", "--ignore-missing-imports"])  # do not fail build
    except Exception as e:
        print(f"(lint/typecheck skipped: {e})")
    # Summarize simple health after tests
    summary = {
        "status": "passed" if code == 0 else "failed",
    }
    print(json.dumps(summary, indent=2))
    raise SystemExit(code)

if __name__ == "__main__":
    main()
