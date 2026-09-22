import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.config import settings
from backend.app.logging_config import logger
from backend.app.services.recommender import engine

from backend.app.api.health import router as health_router
from backend.app.api.movies import router as movies_router
from backend.app.api.recommendations import router as recs_router
from backend.app.api.insights import router as insights_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Hybrid Movie Recommendation System backend...")
    success = engine.load_artifacts()
    if not success:
        logger.warning("Artifact loading failed at startup. Run `python backend/scripts/train.py` to generate model files.")
    yield
    logger.info("Shutting down backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production Hybrid Movie Recommendation Engine combining TF-IDF Content Filtering, Centered Cosine Collaborative Filtering, RapidFuzz Title Aliasing, and Bayesian Weighted Ranking.",
    lifespan=lifespan,
    redirect_slashes=False,
)

# CORS Middleware - permits localhost and Vercel domains (*.vercel.app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|.*\.vercel\.app)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers preventing traceback leakage
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again or check server logs."},
    )

# Routers - mounted under /api as primary endpoints
app.include_router(health_router, prefix="/api")
app.include_router(movies_router, prefix="/api")
app.include_router(recs_router, prefix="/api")
app.include_router(insights_router, prefix="/api")

# Routers - also mounted at root for proxies/rewrites that strip the /api prefix
app.include_router(health_router)
app.include_router(movies_router)
app.include_router(recs_router)
app.include_router(insights_router)

@app.get("/")
@app.get("/api")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs_url": "/docs",
        "health_check": "/api/health",
    }
