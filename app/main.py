from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app.routes import contribute, products, restaurants, scan, users

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
init_db()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="HalalCheck API",
    version="1.0.0",
    description="Community halal verification API for products, restaurants, and personal tracking.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "halalcheck"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


app.include_router(products.router)
app.include_router(restaurants.router)
app.include_router(users.router)
app.include_router(scan.router)
app.include_router(contribute.router)
app.mount("/web", StaticFiles(directory=WEB_DIR), name="web")
