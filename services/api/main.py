"""
Main FastAPI Application for SiteSense.
Binds all service routers, mounts static frontend and media storage,
and enforces standard error shape.
"""

from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from services.core.config import get_settings
from services.core.init_db import init_database
from services.api.routes import (
    auth, sites, inspections, jobs, media,
    chat, review, reports, dashboard, rules,
    tickets, zones, policies, audit
)

settings = get_settings()

app = FastAPI(
    title="SiteSense Multimodal Operations Intelligence API",
    description="Unified API Gateway connecting Computer Vision, Gen AI, and Agentic Orchestration.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Global Error Handling Conventions
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        error_payload = detail
    else:
        error_payload = {
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(detail),
                "detail": None
            }
        }
    return JSONResponse(status_code=exc.status_code, content=error_payload)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters or payload shape.",
                "detail": str(exc.errors())
            }
        }
    )

# 3. Mount Static Storage, Data & Frontend
storage_path = Path(settings.STORAGE_DIR)
storage_path.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(storage_path)), name="storage")

data_path = Path("data")
if data_path.exists():
    app.mount("/data", StaticFiles(directory="data"), name="data")

frontend_dir = Path("frontend")
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend_root():
        """Serves the Single Page Application UI."""
        return FileResponse("frontend/index.html")

# 4. Startup Event: Ensure database is initialized
@app.on_event("startup")
def on_startup():
    settings.ensure_directories()
    init_database()

# 5. Mount Service Routers
app.include_router(auth.router)
app.include_router(sites.router)
app.include_router(inspections.router)
app.include_router(jobs.router)
app.include_router(media.router)
app.include_router(chat.router)
app.include_router(review.router)
app.include_router(reports.router)
app.include_router(dashboard.router)
app.include_router(rules.router)
app.include_router(tickets.router)
app.include_router(zones.router)
app.include_router(policies.router)
app.include_router(audit.router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify API readiness."""
    return {"status": "healthy", "platform": "SiteSense", "version": "1.0.0"}
