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

CRITICAL ACCURACY RULES (do not break these under any circumstance):
- ONLY state facts (certification names, issuers, dates, companies, degrees, skills, etc.) that are EXPLICITLY present in the "RELEVANT CONTEXT" section below.
- NEVER invent, guess, assume, or extrapolate a certification, credential, employer, date, or qualification that is not explicitly written in the context, even if it sounds plausible or common in the industry.
- If the context does not contain the answer to the question, say plainly: "I don't have that information in my records — feel free to reach out via the contact section for details." Do NOT fill the gap with a fabricated answer.
- If the context lists specific certifications, name exactly those and no others. Do not add extra certifications from general knowledge of what certifications exist.
- When unsure whether something is confirmed by the context, err on the side of saying you don't have that information rather than guessing.

Guidelines:
- Be professional, friendly, and concise
- Only answer questions related to the portfolio owner's professional background
- Highlight their strengths in automation, data science, big data analytics, and DevOps where the context supports it
- For technical questions about projects, explain them clearly using only what's in the context
- Encourage visitors to reach out via the contact information provided when you don't have an answer"""

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

        # Pull certifications directly from MongoDB (source of truth) so the
        # model always has the exact, complete, up-to-date list — not just
        # whatever the semantic search happened to retrieve from Chroma.
        cert_docs = await db.certifications.find({}).sort("issue_date", -1).to_list(100)
        if cert_docs:
            cert_lines = [
                f"- {c.get('title')} (Issuer: {c.get('issuer')}, Issued: {c.get('issue_date')})"
                for c in cert_docs
            ]
            context_parts.append(
                "[CERTIFICATIONS - COMPLETE AND AUTHORITATIVE LIST] "
                "This is the full and only list of certifications the portfolio owner holds. "
                "Do not mention any certification not in this list:\n" + "\n".join(cert_lines)
            )
        else:
            context_parts.append(
                "[CERTIFICATIONS] No certifications are currently on record. "
                "If asked about certifications, say none are listed rather than inventing one."
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
            temperature=0.2,
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
