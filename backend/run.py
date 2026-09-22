"""
run.py  -  Unified entry-point for the Hybrid Movie Recommendation System.

Usage:
    python run.py [--skip-train] [--skip-eval] [--host HOST] [--port PORT] [--no-frontend]

Steps executed in order:
  1. Validate raw CSV datasets
  2. Train & serialize model artifacts   (skipped with --skip-train)
  3. Offline evaluation (test)            (skipped with --skip-eval)
  4. Launch FastAPI backend + React frontend concurrently
"""
import sys
import argparse
import subprocess
import importlib
import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# VENV BOOTSTRAP
# If we are NOT already running inside the project .venv, find it and
# re-exec this script with the venv Python automatically.
# This lets users type  `python run.py`  regardless of which Python is active.
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent

def _find_venv_python() -> Path | None:
    """Return the .venv Python executable path if it exists."""
    for venv_dir in (".venv", "venv"):
        for python_rel in (
            Path("Scripts") / "python.exe",   # Windows
            Path("bin") / "python",            # Linux / macOS
        ):
            candidate = BASE_DIR / venv_dir / python_rel
            if candidate.exists():
                return candidate
    return None

def _inside_venv() -> bool:
    """True if the current interpreter is already inside any virtual env."""
    return (
        os.environ.get("VIRTUAL_ENV") is not None
        or hasattr(sys, "real_prefix")          # virtualenv
        or (
            hasattr(sys, "base_prefix")
            and sys.base_prefix != sys.prefix   # venv / conda
        )
    )

if not _inside_venv():
    venv_python = _find_venv_python()
    if venv_python:
        print(f"[run.py] Not in a venv — re-launching with: {venv_python}")
        # Re-exec this script with the venv Python, passing all original args
        result = subprocess.run([str(venv_python), __file__] + sys.argv[1:])
        sys.exit(result.returncode)
    else:
        print(
            "[run.py] WARNING: No .venv found and no virtual environment is active.\n"
            "         Install dependencies first:  pip install -r backend/requirements.txt"
        )

# Ensure stdout/stderr use UTF-8 on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ─────────────────────────────────────────────────────────────────────────────
# Ensure the project root is on the Python path
# ─────────────────────────────────────────────────────────────────────────────
sys.path.insert(0, str(BASE_DIR))


def banner(title: str) -> None:
    width = 60
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def run_step(label: str, module_path: str) -> None:
    """
    Import and execute the `main()` function from a backend script module.
    Raises SystemExit on failure so the pipeline stops early.
    """
    banner(label)
    try:
        mod = importlib.import_module(module_path)
        mod.main()
    except Exception as exc:
        print(f"\n[ERROR] {label} failed: {exc}")
        raise SystemExit(1) from exc


def _find_npm() -> str:
    """Return 'npm.cmd' on Windows, 'npm' elsewhere."""
    return "npm.cmd" if sys.platform == "win32" else "npm"


def launch_all(host: str, port: int, with_frontend: bool) -> None:
    """
    Start the FastAPI backend (uvicorn) and optionally the React dev server
    (npm run dev) concurrently. Both are killed cleanly on Ctrl-C.
    BACKEND_PORT is injected into the frontend environment so the Vite proxy
    always routes /api to the correct port.
    """
    banner(f"STARTING SERVICES  ->  backend :{port}" + ("  frontend :5174" if with_frontend else ""))

    backend_cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.app.main:app",
        "--host", host,
        "--port", str(port),
        "--reload",
    ]

    # Environment that carries BACKEND_PORT for the Vite config
    frontend_env = {**os.environ, "BACKEND_PORT": str(port)}
    frontend_dir = BASE_DIR / "frontend"
    frontend_cmd = [_find_npm(), "run", "dev"]

    procs = []
    try:
        print(f"  [backend]  {' '.join(backend_cmd)}")
        procs.append(subprocess.Popen(backend_cmd, cwd=str(BASE_DIR)))

        if with_frontend and frontend_dir.exists():
            print(f"  [frontend] cd frontend && npm run dev  (BACKEND_PORT={port})")
            procs.append(subprocess.Popen(frontend_cmd, cwd=str(frontend_dir), env=frontend_env))

        print()
        # Wait until any process exits (or Ctrl-C)
        for p in procs:
            p.wait()

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Unified run-script: validate -> train -> evaluate -> serve.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--skip-train",
        action="store_true",
        help="Skip dataset validation & model training (use existing artifacts).",
    )
    parser.add_argument(
        "--skip-eval",
        action="store_true",
        help="Skip offline evaluation (evaluate.py).",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address for the FastAPI server.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the FastAPI server.",
    )
    parser.add_argument(
        "--no-frontend",
        action="store_true",
        help="Do not start the React dev server (backend only).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    banner("HYBRID MOVIE RECOMMENDATION SYSTEM  -  FULL PIPELINE")
    print(f"  skip-train   : {args.skip_train}")
    print(f"  skip-eval    : {args.skip_eval}")
    print(f"  backend      : http://{args.host}:{args.port}")
    print(f"  frontend     : {'disabled (--no-frontend)' if args.no_frontend else 'http://localhost:5174'}")

    # ── Step 1 & 2: Validate + Train ─────────────────────────────────────────
    if not args.skip_train:
        run_step("STEP 1/3 — DATA VALIDATION", "backend.scripts.validate_data")
        run_step("STEP 2/3 — MODEL TRAINING",  "backend.scripts.train")
    else:
        banner("STEP 1-2 — SKIPPED (--skip-train)")
        print("  Using existing model artifacts.")

    # ── Step 3: Offline Evaluation ────────────────────────────────────────────
    if not args.skip_eval:
        run_step("STEP 3/3 — OFFLINE EVALUATION (TEST)", "backend.scripts.evaluate")
    else:
        banner("STEP 3/3 — SKIPPED (--skip-eval)")

    # ── Step 4: Launch backend + frontend concurrently ────────────────────────
    launch_all(args.host, args.port, with_frontend=not args.no_frontend)


if __name__ == "__main__":
    main()
