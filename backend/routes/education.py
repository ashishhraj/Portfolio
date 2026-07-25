from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

from db.mongo import get_db
from db.chroma import upsert_document, delete_document
from utils.auth_dep import get_current_admin

router = APIRouter()

def serialize(doc) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc

@router.get("/")
async def list_education(db=Depends(get_db)):
    docs = await db.education.find({}).sort("start_year", -1).to_list(100)
    return [serialize(d) for d in docs]

class EducationIn(BaseModel):
    institution: str
    degree: str
    field: str
    start_year: int
    end_year: Optional[int] = None      # blank = currently pursuing
    grade: Optional[str] = ""           # e.g. "8.7 CGPA" or "85%"
    description: Optional[str] = ""
    tags: List[str] = []                # e.g. relevant coursework, honors

@router.post("/", dependencies=[Depends(get_current_admin)])
async def create_education(edu: EducationIn, db=Depends(get_db)):
    doc = {**edu.dict(), "created_at": datetime.utcnow()}
    result = await db.education.insert_one(doc)
    doc_id = str(result.inserted_id)

    chroma_text = f"Education: {edu.degree} in {edu.field} at {edu.institution} ({edu.start_year} - {edu.end_year or 'Present'}). Grade: {edu.grade}. {edu.description}. Tags: {', '.join(edu.tags)}"
    upsert_document(f"edu_{doc_id}", chroma_text, {"type": "education", "institution": edu.institution, "degree": edu.degree})
    return {"id": doc_id, "message": "Education added"}

@router.put("/{edu_id}", dependencies=[Depends(get_current_admin)])
async def update_education(edu_id: str, edu: EducationIn, db=Depends(get_db)):
    result = await db.education.update_one(
        {"_id": ObjectId(edu_id)},
        {"$set": {**edu.dict(), "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Education entry not found")

    chroma_text = f"Education: {edu.degree} in {edu.field} at {edu.institution} ({edu.start_year} - {edu.end_year or 'Present'}). Grade: {edu.grade}. {edu.description}. Tags: {', '.join(edu.tags)}"
    upsert_document(f"edu_{edu_id}", chroma_text, {"type": "education", "institution": edu.institution, "degree": edu.degree})
    return {"message": "Updated"}

@router.delete("/{edu_id}", dependencies=[Depends(get_current_admin)])
async def delete_education(edu_id: str, db=Depends(get_db)):
    result = await db.education.delete_one({"_id": ObjectId(edu_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Not found")
    delete_document(f"edu_{edu_id}")
    return {"message": "Deleted"}
