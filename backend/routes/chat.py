from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from groq import Groq
import os, logging

from db.mongo import get_db
from db.chroma import query_similar

router = APIRouter()
logger = logging.getLogger(__name__)

_MODEL = "llama-3.3-70b-versatile"

def _get_groq_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are an intelligent AI assistant for a personal portfolio website.
Your job is to answer questions about the portfolio owner professionally and accurately.
You will be provided with relevant context from their resume, projects, and certifications.

Guidelines:
- Be professional, friendly, and concise
- Only answer questions related to the portfolio owner's professional background
- If asked about something not in the context, say you don't have that information
- Highlight their strengths in automation, data science, big data analytics, and DevOps
- For technical questions about projects, explain them clearly
- Encourage visitors to reach out via the contact information provided

The portfolio owner is pursuing PGDM in Big Data Analytics with experience as an Automation Engineer and Data Science Engineer, with skills in dashboards and DevOps."""

class Message(BaseModel):
    role: str   # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []

class ChatResponse(BaseModel):
    reply: str
    sources: List[str] = []

@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest, db=Depends(get_db)):
    try:
        # ── RAG: Query ChromaDB for relevant context ──────────────────────
        relevant_docs = query_similar(req.message, n_results=4)

        context_parts = []
        sources = []

        if relevant_docs and relevant_docs.get("documents") and relevant_docs["documents"][0]:
            for doc, meta in zip(
                relevant_docs["documents"][0],
                relevant_docs["metadatas"][0]
            ):
                context_parts.append(f"[{meta.get('type','').upper()}] {doc}")
                if meta.get("title"):
                    sources.append(meta["title"])

        # Also pull latest resume for extra freshness
        resume_doc = await db.resume.find_one({})
        if resume_doc:
            context_parts.append(
                f"[RESUME] Name: {resume_doc.get('name')}, "
                f"Title: {resume_doc.get('title')}, "
                f"Summary: {resume_doc.get('summary')}, "
                f"Skills: {', '.join(resume_doc.get('skills', []))}"
            )

        context = (
            "\n\n".join(context_parts)
            if context_parts
            else "No specific context available yet. Answer based on general professional info."
        )

        system_with_context = (
            f"{SYSTEM_PROMPT}\n\n"
            f"--- RELEVANT CONTEXT ---\n{context}\n--- END CONTEXT ---"
        )

        # ── Build messages for Groq (OpenAI-compatible format) ────────────
        messages = [{"role": "system", "content": system_with_context}]

        for msg in req.history[-6:]:          # last 6 turns for context window
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": req.message})

        # ── Call Groq ─────────────────────────────────────────────────────
        client = _get_groq_client()
        resp = client.chat.completions.create(
            model=_MODEL,
            messages=messages,
            temperature=0.4,
            max_tokens=800,
        )

        reply = resp.choices[0].message.content
        return ChatResponse(reply=reply, sources=list(set(sources)))

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(500, f"Chat error: {str(e)}")


@router.get("/suggestions")
async def get_suggestions():
    return {
        "suggestions": [
            "What technologies do you work with?",
            "Tell me about your Automation Engineer experience",
            "What projects have you built?",
            "What certifications do you have?",
            "What is your educational background?",
            "What are your Data Science skills?",
            "Tell me about your DevOps experience",
            "How can I contact you?"
        ]
    }
