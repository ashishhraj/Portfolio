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
async def list_experience(db=Depends(get_db)):
    docs = await db.experience.find({}).sort("start_date", -1).to_list(100)
    return [serialize(d) for d in docs]

class ExperienceIn(BaseModel):
    company: str
    role: str
    start_date: str
    end_date: Optional[str] = "Present"
    description: Optional[str] = ""
    skills: List[str] = []

@router.post("/", dependencies=[Depends(get_current_admin)])
async def create_experience(exp: ExperienceIn, db=Depends(get_db)):
    doc = {**exp.dict(), "created_at": datetime.utcnow()}
    result = await db.experience.insert_one(doc)
    doc_id = str(result.inserted_id)

    chroma_text = f"Experience: {exp.role} at {exp.company} ({exp.start_date} - {exp.end_date}). {exp.description}. Skills: {', '.join(exp.skills)}"
    upsert_document(f"exp_{doc_id}", chroma_text, {"type": "experience", "company": exp.company, "role": exp.role})
    return {"id": doc_id, "message": "Experience added"}

@router.put("/{exp_id}", dependencies=[Depends(get_current_admin)])
async def update_experience(exp_id: str, exp: ExperienceIn, db=Depends(get_db)):
    result = await db.experience.update_one(
        {"_id": ObjectId(exp_id)},
        {"$set": {**exp.dict(), "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Experience not found")

    chroma_text = f"Experience: {exp.role} at {exp.company} ({exp.start_date} - {exp.end_date}). {exp.description}. Skills: {', '.join(exp.skills)}"
    upsert_document(f"exp_{exp_id}", chroma_text, {"type": "experience", "company": exp.company, "role": exp.role})
    return {"message": "Updated"}

@router.delete("/{exp_id}", dependencies=[Depends(get_current_admin)])
async def delete_experience(exp_id: str, db=Depends(get_db)):
    result = await db.experience.delete_one({"_id": ObjectId(exp_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Not found")
    delete_document(f"exp_{exp_id}")
    return {"message": "Deleted"}
