from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pipeline.rag import load_knowledge_base
from app.routes.analyse import router as analyse_router
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: only load text files, no ML models
    print("Loading knowledge base...")
    load_knowledge_base()   # Reads 3 text files into memory — ~10ms
    print("TrackSpendAI ready. RAM usage: minimal.")
    yield
    # No cleanup needed

app = FastAPI(title="TrackSpendAI API", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend URL
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
async def ping():
    return {"status": "ok"}

app.include_router(analyse_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
