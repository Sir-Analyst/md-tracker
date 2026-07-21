from pathlib import Path

import os
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.config import HOST, PORT, STATIC_DIR, TEMPLATES_DIR
from app.database import (
    add_file,
    delete_file,
    get_file,
    get_file_stats,
    get_global_stats,
    get_steps,
    init_db,
    list_files,
    toggle_step_cascade,
    touch_file,
    upsert_steps,
)
from app.parser import parse_file

app = FastAPI(title="MD Tracker")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    files = list_files()
    stats = get_global_stats()
    return templates.TemplateResponse(request, "dashboard.html", {
        "files": files,
        "stats": stats,
    })


@app.get("/view/{file_id}", response_class=HTMLResponse)
def viewer(request: Request, file_id: int):
    file = get_file(file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    touch_file(file_id)
    steps = get_steps(file_id)
    stats = get_file_stats(file_id)
    content = ""
    try:
        content = Path(file["path"]).read_text(encoding="utf-8", errors="replace")
    except Exception:
        pass
    return templates.TemplateResponse(request, "viewer.html", {
        "file": file,
        "steps": steps,
        "stats": stats,
        "content": content,
    })


class AddFileRequest(BaseModel):
    path: str


@app.post("/api/files")
def api_add_file(req: AddFileRequest):
    p = Path(req.path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    if p.suffix.lower() not in (".md", ".markdown", ".txt"):
        raise HTTPException(status_code=400, detail="Not a markdown file")

    parsed = parse_file(str(p))
    if "error" in parsed:
        raise HTTPException(status_code=400, detail=parsed["error"])

    file = add_file(name=parsed["name"], path=parsed["path"])
    if not file:
        raise HTTPException(status_code=500, detail="Failed to add file")

    upsert_steps(file["id"], parsed["steps"])
    return file


@app.get("/api/files")
def api_list_files():
    return list_files()


@app.delete("/api/files/{file_id}")
def api_delete_file(file_id: int):
    if not delete_file(file_id):
        raise HTTPException(status_code=404, detail="File not found")
    return {"ok": True}


@app.get("/api/files/{file_id}/steps")
def api_get_steps(file_id: int):
    file = get_file(file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    steps = get_steps(file_id)
    stats = get_file_stats(file_id)
    return {"file": file, "steps": steps, "stats": stats}


class ToggleRequest(BaseModel):
    completed: bool | None = None


@app.patch("/api/steps/{step_id}")
def api_toggle_step(step_id: int, req: ToggleRequest | None = None):
    result = toggle_step_cascade(step_id)
    if not result:
        raise HTTPException(status_code=404, detail="Step not found")
    return {"changed": result}


@app.get("/api/stats")
def api_stats():
    return get_global_stats()


@app.post("/api/files/{file_id}/rescan")
def api_rescan_file(file_id: int):
    file = get_file(file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    parsed = parse_file(file["path"])
    if "error" in parsed:
        raise HTTPException(status_code=400, detail=parsed["error"])
    upsert_steps(file_id, parsed["steps"])
    steps = get_steps(file_id)
    stats = get_file_stats(file_id)
    return {"steps": steps, "stats": stats}


@app.get("/api/browse")
def api_browse(path: str = ""):
    if not path:
        home_desktop = Path.home() / "Desktop"
        if home_desktop.exists():
            path = str(home_desktop)
        elif Path(r"C:\Desktop").exists():
            path = r"C:\Desktop"
        else:
            path = str(Path.home())
    p = Path(path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Directory not found")
    if not p.is_dir():
        p = p.parent

    items = []
    try:
        entries = sorted(os.scandir(str(p)), key=lambda e: (not e.is_dir(), e.name.lower()))
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    for entry in entries:
        if entry.name.startswith("."):
            continue
        items.append({
            "name": entry.name,
            "path": entry.path,
            "is_dir": entry.is_dir(),
        })

    parent = str(p.parent) if str(p.parent) != str(p) else None
    return {"current": str(p), "parent": parent, "items": items}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
