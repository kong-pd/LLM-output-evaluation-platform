from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.database import init_db
from app.routers import datasets, annotations

app = FastAPI(title="LLM Eval Platform", version="0.3.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])
app.include_router(datasets.router)
app.include_router(annotations.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}
