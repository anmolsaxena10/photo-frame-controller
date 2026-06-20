from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

def create_app(state_manager) -> FastAPI:
    app = FastAPI(
        title="Photo Frame API",
        version="1.0.0",
        docs_url="/api/docs"
    )

    # We will mount static files and add routers later in the implementation.
    web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "web")
    os.makedirs(web_dir, exist_ok=True)
    
    # Create a dummy index.html if it doesn't exist so StaticFiles doesn't crash
    if not os.path.exists(os.path.join(web_dir, "index.html")):
        with open(os.path.join(web_dir, "index.html"), "w") as f:
            f.write("<h1>Photo Frame Server Starting...</h1>")
            
    app.mount("/", StaticFiles(directory=web_dir, html=True))

    @app.get("/api/health")
    def health():
        return {"status": "ok", "mode": state_manager.current_mode.value}

    return app
