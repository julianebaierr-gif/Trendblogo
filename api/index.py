import sys
import os
import traceback
from pathlib import Path

# Add the project root to sys.path so that 'app' module can be found
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Explicitly set Vercel environment flag
os.environ["VERCEL"] = "1"

_import_error = None
try:
    from app.main import app as base_app

    class VercelPathMiddleware:
        def __init__(self, inner_app):
            self.inner_app = inner_app

        async def __call__(self, scope, receive, send):
            if scope["type"] == "http":
                headers = dict(scope.get("headers", []))
                matched_path = (
                    headers.get(b"x-matched-path")
                    or headers.get(b"x-forwarded-uri")
                    or headers.get(b"x-invoke-path")
                )
                if matched_path:
                    path_str = matched_path.decode("latin1", errors="replace")
                    if "?" in path_str:
                        path_str = path_str.split("?")[0]
                    for prefix in ("/api/index.py", "/api/index"):
                        if path_str.startswith(prefix):
                            path_str = path_str[len(prefix):]
                    if not path_str or not path_str.startswith("/"):
                        path_str = "/" + path_str
                    scope["path"] = path_str
                else:
                    path_str = scope.get("path", "/")
                    for prefix in ("/api/index.py", "/api/index"):
                        if path_str.startswith(prefix):
                            path_str = path_str[len(prefix):]
                    if not path_str or not path_str.startswith("/"):
                        path_str = "/" + path_str
                    scope["path"] = path_str

            await self.inner_app(scope, receive, send)

    app = VercelPathMiddleware(base_app)

except Exception as e:
    _import_error = traceback.format_exc()
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    app = FastAPI(title="TrendBlogo Diagnostic Bootloader")
    
    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def catch_all_diag(path_name: str = ""):
        return HTMLResponse(
            f"""<!DOCTYPE html>
<html>
<head><title>TrendBlogo Deployment Diagnostic</title></head>
<body style="font-family:monospace;background:#18181b;color:#f43f5e;padding:30px;">
  <h2 style="color:#fbbf24;">Serverless Function Boot Diagnostic</h2>
  <p style="color:#e4e4e7;">An unhandled exception occurred during application startup:</p>
  <pre style="background:#09090b;padding:20px;border-radius:8px;border:1px solid #27272a;overflow:auto;color:#38bdf8;">{_import_error}</pre>
</body>
</html>""",
            status_code=500
        )
