import os
import shutil
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.database import engine, Base
from app.seed import seed_database
from app.routes.public import router as public_router
from app.routes.admin import router as admin_router
from app.routes.api import router as api_router

_initialized = False

def init_app_state():
    global _initialized
    if _initialized:
        return
    try:
        # Create tables if not existing
        Base.metadata.create_all(bind=engine)
        # On local development, seed if DB is empty; on Vercel, trendblogo_seed.db is already copied
        seed_database()
        _initialized = True
    except Exception as e:
        print(f"App state init notice: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_app_state()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise AI-Powered Content Automation and Publishing Platform",
    version="2.0.0",
    lifespan=lifespan,
    redirect_slashes=False
)

# Safe mounting of static directories
if settings.UPLOADS_DIR.exists():
    app.mount("/static/uploads", StaticFiles(directory=str(settings.UPLOADS_DIR)), name="uploads")

if settings.STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

# Templates for error pages
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))

# Health check route
@app.get("/health")
def health():
    return {"status": "ok", "platform": "TrendBlogo", "environment": settings.APP_ENV}

# Register Routers
app.include_router(public_router)
app.include_router(admin_router)
app.include_router(api_router)

# Custom 404 and 500 error handlers
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    headers = {
        "X-Debug-Req-Path": str(request.url.path),
        "X-Debug-Scope-Path": str(request.scope.get("path")),
        "X-Debug-Matched-Path": str(request.headers.get("x-matched-path")),
        "X-Debug-All-Headers": str(list(request.headers.keys()))
    }
    return templates.TemplateResponse(
        request=request,
        name="404.html",
        context={
            "request": request,
            "title": "Page Not Found (404) ? TrendBlogo",
            "meta_desc": "The page you are looking for does not exist or has been moved.",
            "base_url": settings.BASE_URL
        },
        status_code=404,
        headers=headers
    )

@app.exception_handler(500)
async def custom_500_handler(request: Request, exc):
    return HTMLResponse(
        """<!DOCTYPE html>
<html lang="en">
<head><title>System Error ? TrendBlogo</title><meta charset="utf-8"></head>
<body style="font-family:system-ui;text-align:center;padding:80px;background:#0F172A;color:#F8FAFC;">
  <h1 style="font-size:32px;color:#F43F5E;">An unexpected error occurred</h1>
  <p style="color:#94A3B8;max-width:500px;margin:20px auto;">The TrendBlogo platform encountered an internal error. Please check system logs in the administrator console.</p>
  <a href="/" style="display:inline-block;padding:12px 24px;background:#4F46E5;color:white;border-radius:8px;text-decoration:none;font-weight:600;">Return Home</a>
</body>
</html>""",
        status_code=500
    )
