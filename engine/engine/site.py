"""Serve the demo website and fixture API from one process and origin."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from .api import app as fixture_api


UI_DIST = Path(__file__).resolve().parents[2] / "ui" / "dist"
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    if not (UI_DIST / "index.html").is_file():
        raise HTTPException(503, "Website build missing")
    return {"status": "ready"}


app.mount("/api", fixture_api)


@app.get("/{path:path}")
def website(path: str):
    root = UI_DIST.resolve()
    asset = (root / path).resolve()
    if asset.is_relative_to(root) and asset.is_file():
        return FileResponse(asset)
    if "." in Path(path).name:
        raise HTTPException(404, "Asset not found")
    index = root / "index.html"
    if not index.is_file():
        raise HTTPException(503, "Website build missing")
    return FileResponse(index)
