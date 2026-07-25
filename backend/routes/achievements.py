from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
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
async def list_achievements(db=Depends(get_db)):
    docs = await db.achievements.find({}).sort("date", -1).to_list(100)
    return [serialize(d) for d in docs]

class AchievementIn(BaseModel):
    title: str
    issuer: Optional[str] = ""      # e.g. "College Tech Fest" / "Smart India Hackathon"
    date: Optional[str] = ""        # "2024" or "2024-03"
    description: Optional[str] = ""
    link: Optional[str] = ""        # optional proof/certificate link

@router.post("/", dependencies=[Depends(get_current_admin)])
async def create_achievement(a: AchievementIn, db=Depends(get_db)):
    doc = {**a.dict(), "created_at": datetime.utcnow()}
    result = await db.achievements.insert_one(doc)
    doc_id = str(result.inserted_id)

    chroma_text = f"Academic Achievement: {a.title} ({a.issuer}, {a.date}). {a.description}"
    upsert_document(f"achieve_{doc_id}", chroma_text, {"type": "achievement", "title": a.title})
    return {"id": doc_id, "message": "Achievement added"}

@router.put("/{a_id}", dependencies=[Depends(get_current_admin)])
async def update_achievement(a_id: str, a: AchievementIn, db=Depends(get_db)):
    result = await db.achievements.update_one(
        {"_id": ObjectId(a_id)},
        {"$set": {**a.dict(), "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Achievement not found")

    chroma_text = f"Academic Achievement: {a.title} ({a.issuer}, {a.date}). {a.description}"
    upsert_document(f"achieve_{a_id}", chroma_text, {"type": "achievement", "title": a.title})
    return {"message": "Updated"}

@router.delete("/{a_id}", dependencies=[Depends(get_current_admin)])
async def delete_achievement(a_id: str, db=Depends(get_db)):
    result = await db.achievements.delete_one({"_id": ObjectId(a_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Not found")
    delete_document(f"achieve_{a_id}")
    return {"message": "Deleted"}
