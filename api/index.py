import sys
import threading
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

# Add project root to sys.path so 'backend' package resolves properly on Vercel
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app as fastapi_app
from backend.app.services.recommender import engine

_load_lock = threading.Lock()

def ensure_engine():
    """Thread-safe engine artifact loader for serverless cold starts."""
    if not engine.is_loaded:
        with _load_lock:
            if not engine.is_loaded:
                engine.load_artifacts()

# Eager warm-up during module initialization
try:
    ensure_engine()
except Exception:
    pass

class VercelServerlessApp:
    """
    ASGI wrapper that handles Vercel Serverless Function routing quirks:
    1. Normalizes paths when internal rewrites map /api/* to /api/index.py
    2. Restores original request URI from x-forwarded-uri / x-matched-path / query params
    3. Guarantees model artifact loading on cold starts
    """
    def __init__(self, inner_app):
        self.inner_app = inner_app

    def __getattr__(self, name):
        return getattr(self.inner_app, name)

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            ensure_engine()

            raw_path = scope.get("path", "")
            # Detect rewritten destination paths
            if raw_path in ("/api/index.py", "/index.py", "api/index.py") or raw_path.startswith("/api/index.py/"):
                headers = dict(
                    (k.decode("latin1").lower(), v.decode("latin1"))
                    for k, v in scope.get("headers", [])
                )

                if raw_path.startswith("/api/index.py/"):
                    scope["path"] = raw_path[len("/api/index.py"):]
                elif "x-forwarded-uri" in headers:
                    parsed = urlsplit(headers["x-forwarded-uri"])
                    scope["path"] = parsed.path
                    if parsed.query and not scope.get("query_string"):
                        scope["query_string"] = parsed.query.encode("latin1")
                elif "x-matched-path" in headers:
                    scope["path"] = headers["x-matched-path"]
                elif "x-invoke-path" in headers:
                    scope["path"] = headers["x-invoke-path"]
                else:
                    # Parse path parameter if passed via query string
                    qs = parse_qs(scope.get("query_string", b"").decode("latin1"))
                    if "path" in qs and qs["path"]:
                        subpath = qs["path"][0].lstrip("/")
                        scope["path"] = f"/api/{subpath}" if not subpath.startswith("api/") else f"/{subpath}"

        await self.inner_app(scope, receive, send)

# Export app instance for Vercel Python runtime
app = VercelServerlessApp(fastapi_app)
