from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os


def create_app(state_manager) -> FastAPI:
    app = FastAPI(
        title="Photo Frame API",
        version="1.0.0",
        docs_url="/api/docs"
    )

    app.state.state_manager = state_manager

    from app.server.routes import system, photos, settings, wifi
    app.include_router(system.router, prefix="/api/system", tags=["System"])
    app.include_router(photos.router, prefix="/api/photos", tags=["Photos"])
    app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
    app.include_router(wifi.router, prefix="/api/wifi", tags=["WiFi"])

    web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "web")
    os.makedirs(web_dir, exist_ok=True)

    # Create a dummy index.html if it doesn't exist so FileResponse doesn't crash
    if not os.path.exists(os.path.join(web_dir, "index.html")):
        with open(os.path.join(web_dir, "index.html"), "w") as f:
            f.write("<h1>Photo Frame Server Starting...</h1>")

    # Mount static assets (css, js, assets)
    for subdir in ["css", "js", "assets"]:
        subpath = os.path.join(web_dir, subdir)
        if os.path.exists(subpath):
            app.mount(f"/{subdir}", StaticFiles(directory=subpath), name=subdir)

    @app.get("/")
    async def serve_root(request: Request):
        """Serve setup page in AP mode, main UI when configured."""
        sm = request.app.state.state_manager
        if sm.current_mode.value in ("first_boot", "ap_setup"):
            setup_path = os.path.join(web_dir, "setup.html")
            if os.path.exists(setup_path):
                return FileResponse(setup_path, media_type="text/html")

        index_path = os.path.join(web_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path, media_type="text/html")
        return {"message": "Photo Frame Server"}

    @app.get("/api/health")
    def health():
        return {"status": "ok", "mode": state_manager.current_mode.value}

    return app
