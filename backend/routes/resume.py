from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
import cloudinary, cloudinary.uploader
import os

from db.mongo import get_db
from db.chroma import upsert_document
from utils.auth_dep import get_current_admin

router = APIRouter()

class Experience(BaseModel):
    company: str
    role: str
    start_date: str
    end_date: Optional[str] = "Present"
    description: str
    skills: List[str] = []

class Education(BaseModel):
    institution: str
    degree: str
    field: str
    start_year: int
    end_year: Optional[int] = None

class ResumeIn(BaseModel):
    name: str
    title: str
    summary: str
    email: str
    phone: Optional[str] = ""
    location: Optional[str] = ""
    linkedin: Optional[str] = ""
    github: Optional[str] = ""
    skills: List[str] = []
    experiences: List[Experience] = []
    education: List[Education] = []

@router.get("/")
async def get_resume(db=Depends(get_db)):
    doc = await db.resume.find_one({}, sort=[("updated_at", -1)])
    if not doc:
        raise HTTPException(404, "Resume not found")
    doc["id"] = str(doc.pop("_id"))
    return doc

@router.put("/", dependencies=[Depends(get_current_admin)])
async def update_resume(resume: ResumeIn, db=Depends(get_db)):
    existing = await db.resume.find_one({})
    data = {**resume.dict(), "updated_at": datetime.utcnow()}
    
    if existing:
        await db.resume.update_one({"_id": existing["_id"]}, {"$set": data})
        doc_id = str(existing["_id"])
    else:
        result = await db.resume.insert_one(data)
        doc_id = str(result.inserted_id)
    
    # Index full resume in ChromaDB
    exp_text = " | ".join([f"{e.role} at {e.company}: {e.description}" for e in resume.experiences])
    chroma_text = f"Name: {resume.name}. Title: {resume.title}. Summary: {resume.summary}. Skills: {', '.join(resume.skills)}. Experience: {exp_text}"
    upsert_document("resume_main", chroma_text, {"type": "resume", "name": resume.name, "title": resume.title})
    
    return {"id": doc_id, "message": "Resume updated"}

@router.post("/upload-pdf", dependencies=[Depends(get_current_admin)])
async def upload_resume_pdf(file: UploadFile = File(...), db=Depends(get_db)):
    """Upload a PDF version of the resume."""
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET")
    )
    contents = await file.read()
    result = cloudinary.uploader.upload(contents, folder="portfolio/resume", resource_type="raw")
    pdf_url = result["secure_url"]
    await db.resume.update_one({}, {"$set": {"pdf_url": pdf_url}}, upsert=True)
    return {"pdf_url": pdf_url}
