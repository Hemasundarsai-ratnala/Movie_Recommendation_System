import sys
from pathlib import Path

# Add project root to sys.path so 'backend' package resolves properly on Vercel
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app
from backend.app.services.recommender import engine

# Ensure model artifacts are loaded even if the serverless runtime skips ASGI lifespan events
@app.middleware("http")
async def ensure_engine_loaded(request, call_next):
    if not engine.is_loaded:
        engine.load_artifacts()
    response = await call_next(request)
    return response
