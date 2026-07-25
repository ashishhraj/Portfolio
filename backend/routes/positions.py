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
async def list_positions(db=Depends(get_db)):
    docs = await db.positions.find({}).sort("start_date", -1).to_list(100)
    return [serialize(d) for d in docs]

class PositionIn(BaseModel):
    title: str                          # e.g. "Class Representative"
    organization: str                   # e.g. "Dept. of Big Data Analytics"
    start_date: str                     # "2023-07"
    end_date: Optional[str] = "Present"
    description: Optional[str] = ""

@router.post("/", dependencies=[Depends(get_current_admin)])
async def create_position(p: PositionIn, db=Depends(get_db)):
    doc = {**p.dict(), "created_at": datetime.utcnow()}
    result = await db.positions.insert_one(doc)
    doc_id = str(result.inserted_id)

    chroma_text = f"Position of Responsibility: {p.title} at {p.organization} ({p.start_date} - {p.end_date}). {p.description}"
    upsert_document(f"position_{doc_id}", chroma_text, {"type": "position", "title": p.title, "organization": p.organization})
    return {"id": doc_id, "message": "Position added"}

@router.put("/{p_id}", dependencies=[Depends(get_current_admin)])
async def update_position(p_id: str, p: PositionIn, db=Depends(get_db)):
    result = await db.positions.update_one(
        {"_id": ObjectId(p_id)},
        {"$set": {**p.dict(), "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Position not found")

    chroma_text = f"Position of Responsibility: {p.title} at {p.organization} ({p.start_date} - {p.end_date}). {p.description}"
    upsert_document(f"position_{p_id}", chroma_text, {"type": "position", "title": p.title, "organization": p.organization})
    return {"message": "Updated"}

@router.delete("/{p_id}", dependencies=[Depends(get_current_admin)])
async def delete_position(p_id: str, db=Depends(get_db)):
    result = await db.positions.delete_one({"_id": ObjectId(p_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Not found")
    delete_document(f"position_{p_id}")
    return {"message": "Deleted"}
