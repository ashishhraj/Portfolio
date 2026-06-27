from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os, jwt, logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from routes import projects, certifications, resume, chat, auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    from db.mongo import init_mongo
    from db.chroma import init_chroma
    await init_mongo()
    init_chroma()
    logger.info("✅ Databases initialized")
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title="Portfolio API",
    description="Personal Portfolio API with AI Chatbot",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,           prefix="/api/auth",         tags=["Auth"])
app.include_router(projects.router,       prefix="/api/projects",     tags=["Projects"])
app.include_router(certifications.router, prefix="/api/certifications",tags=["Certifications"])
app.include_router(resume.router,         prefix="/api/resume",       tags=["Resume"])
app.include_router(chat.router,           prefix="/api/chat",         tags=["Chat"])

@app.get("/")
async def root():
    return {"message": "Portfolio API is running 🚀", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
