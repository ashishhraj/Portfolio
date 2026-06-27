from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from bson import ObjectId
import cloudinary, cloudinary.uploader
import os

from db.mongo import get_db
from db.chroma import upsert_document, delete_document
from utils.auth_dep import get_current_admin

router = APIRouter()

def serialize(doc) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc

@router.get("/")
async def list_certifications(db=Depends(get_db)):
    docs = await db.certifications.find({}).sort("issue_date", -1).to_list(100)
    return [serialize(d) for d in docs]

class CertIn(BaseModel):
    title: str
    issuer: str
    issue_date: str          # "YYYY-MM"
    expiry_date: Optional[str] = None
    credential_url: Optional[str] = ""
    credential_id: Optional[str] = ""
    skills: list[str] = []

@router.post("/", dependencies=[Depends(get_current_admin)])
async def create_cert(cert: CertIn, db=Depends(get_db)):
    doc = {**cert.dict(), "created_at": datetime.utcnow(), "image_url": ""}
    result = await db.certifications.insert_one(doc)
    doc_id = str(result.inserted_id)
    
    chroma_text = f"Certification: {cert.title} from {cert.issuer}. Skills: {', '.join(cert.skills)}. Issued: {cert.issue_date}"
    upsert_document(f"cert_{doc_id}", chroma_text, {"type": "certification", "title": cert.title, "issuer": cert.issuer})
    return {"id": doc_id, "message": "Certification added"}

@router.put("/{cert_id}", dependencies=[Depends(get_current_admin)])
async def update_cert(cert_id: str, cert: CertIn, db=Depends(get_db)):
    result = await db.certifications.update_one(
        {"_id": ObjectId(cert_id)},
        {"$set": {**cert.dict(), "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Certification not found")
    chroma_text = f"Certification: {cert.title} from {cert.issuer}. Skills: {', '.join(cert.skills)}"
    upsert_document(f"cert_{cert_id}", chroma_text, {"type": "certification", "title": cert.title})
    return {"message": "Updated"}

@router.delete("/{cert_id}", dependencies=[Depends(get_current_admin)])
async def delete_cert(cert_id: str, db=Depends(get_db)):
    result = await db.certifications.delete_one({"_id": ObjectId(cert_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Not found")
    delete_document(f"cert_{cert_id}")
    return {"message": "Deleted"}

@router.post("/{cert_id}/image", dependencies=[Depends(get_current_admin)])
async def upload_cert_image(cert_id: str, file: UploadFile = File(...), db=Depends(get_db)):
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET")
    )
    contents = await file.read()
    result = cloudinary.uploader.upload(contents, folder="portfolio/certs")
    image_url = result["secure_url"]
    await db.certifications.update_one({"_id": ObjectId(cert_id)}, {"$set": {"image_url": image_url}})
    return {"image_url": image_url}
