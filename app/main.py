from fastapi import FastAPI
from app.database import init_db

app = FastAPI(title="MD Tracker")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def dashboard():
    return {"status": "ok", "message": "MD Tracker - Phase 1 complete"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)
