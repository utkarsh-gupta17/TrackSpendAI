import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add parent directory to sys.path to allow imports from pipeline folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load env before other imports that use os.getenv
load_dotenv()

from app.services.embeddings import load_models
from pipeline.rag import load_and_chunk_knowledge_base
from app.routes.analyse import router as analyse_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs on startup
    print("Loading embedding models...")
    load_models()
    print("Loading knowledge base...")
    load_and_chunk_knowledge_base()
    print("TrackSpendAI ready.")
    yield
    # Cleanup on shutdown

app = FastAPI(title="TrackSpendAI API", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
async def ping():
    return {"status": "ok"}

app.include_router(analyse_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
