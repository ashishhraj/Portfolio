from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
import cloudinary, cloudinary.uploader
import os, re

from db.mongo import get_db
from db.chroma import upsert_document, delete_document
from utils.auth_dep import get_current_admin

router = APIRouter()

def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def serialize(doc) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc

# ── Public endpoints ──────────────────────────────────────────────────────────

@router.get("/")
async def list_projects(db=Depends(get_db)):
    docs = await db.projects.find({}).sort("created_at", -1).to_list(100)
    return [serialize(d) for d in docs]

@router.get("/{slug}")
async def get_project(slug: str, db=Depends(get_db)):
    doc = await db.projects.find_one({"slug": slug})
    if not doc:
        raise HTTPException(404, "Project not found")
    return serialize(doc)

# ── Admin endpoints ───────────────────────────────────────────────────────────

class ProjectIn(BaseModel):
    title: str
    description: str
    long_description: Optional[str] = ""
    tech_stack: List[str] = []
    github_url: Optional[str] = ""
    live_url: Optional[str] = ""
    tags: List[str] = []
    featured: bool = False

@router.post("/", dependencies=[Depends(get_current_admin)])
async def create_project(project: ProjectIn, db=Depends(get_db)):
    slug = slugify(project.title)
    existing = await db.projects.find_one({"slug": slug})
    if existing:
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"
    
    doc = {**project.dict(), "slug": slug, "created_at": datetime.utcnow(), "image_url": ""}
    result = await db.projects.insert_one(doc)
    doc_id = str(result.inserted_id)
    
    # Index in ChromaDB
    chroma_text = f"Project: {project.title}. {project.description}. Tech: {', '.join(project.tech_stack)}. Tags: {', '.join(project.tags)}"
    upsert_document(f"project_{doc_id}", chroma_text, {"type": "project", "title": project.title, "slug": slug})
    
    return {"id": doc_id, "slug": slug, "message": "Project created"}

@router.put("/{project_id}", dependencies=[Depends(get_current_admin)])
async def update_project(project_id: str, project: ProjectIn, db=Depends(get_db)):
    result = await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {"$set": {**project.dict(), "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Project not found")
    
    chroma_text = f"Project: {project.title}. {project.description}. Tech: {', '.join(project.tech_stack)}"
    upsert_document(f"project_{project_id}", chroma_text, {"type": "project", "title": project.title})
    return {"message": "Updated"}

@router.delete("/{project_id}", dependencies=[Depends(get_current_admin)])
async def delete_project(project_id: str, db=Depends(get_db)):
    result = await db.projects.delete_one({"_id": ObjectId(project_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Project not found")
    delete_document(f"project_{project_id}")
    return {"message": "Deleted"}

@router.post("/{project_id}/image", dependencies=[Depends(get_current_admin)])
async def upload_image(project_id: str, file: UploadFile = File(...), db=Depends(get_db)):
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET")
    )
    contents = await file.read()
    result = cloudinary.uploader.upload(contents, folder="portfolio/projects")
    image_url = result["secure_url"]
    await db.projects.update_one({"_id": ObjectId(project_id)}, {"$set": {"image_url": image_url}})
    return {"image_url": image_url}
