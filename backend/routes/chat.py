from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from groq import Groq
import os, logging

from db.mongo import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

_MODEL = "llama-3.3-70b-versatile"


def _get_groq_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))


SYSTEM_PROMPT = """You are an intelligent AI assistant for a personal portfolio website.
Your job is to answer questions about the portfolio owner professionally and accurately.
You will be provided with relevant context from their resume, projects, and certifications.

CRITICAL ACCURACY RULES (do not break these under any circumstance):
- ONLY state facts (certification names, issuers, dates, companies, degrees, achievements, positions, projects, etc.) that are EXPLICITLY present in the "RELEVANT CONTEXT" section below.
- NEVER invent, guess, assume, or extrapolate any detail not explicitly written in the context, even if it sounds plausible or common.
- Each context section states its own total count (e.g. "COMPLETE LIST, 3 total") — when asked "how many" of something, use that exact number and list them if helpful.
- If a context section says "None on record," say so plainly rather than making something up.
- If the context does not contain the answer to the question at all, say plainly: "I don't have that information in my records — feel free to reach out via the contact section for details."

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
        context_parts = []
        sources = []

        # ── Pull ALL portfolio data directly from MongoDB (source of truth) ──
        # The dataset is small, so instead of relying only on Chroma's semantic
        # search (which can miss relevant items, especially for counting /
        # "how many" questions), we give the model the complete, authoritative
        # picture every time. This guarantees accurate, complete answers.

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
                f"[CERTIFICATIONS - COMPLETE LIST, {len(cert_docs)} total] "
                "This is the full and only list of certifications held. "
                "Do not mention any certification not in this list:\n" + "\n".join(cert_lines)
            )
        else:
            context_parts.append("[CERTIFICATIONS] None on record.")

        edu_docs = await db.education.find({}).sort("start_year", -1).to_list(100)
        if edu_docs:
            edu_lines = [
                f"- {e.get('degree')} in {e.get('field')} at {e.get('institution')} "
                f"({e.get('start_year')} - {e.get('end_year') or 'Present'}). "
                f"Grade: {e.get('grade') or 'N/A'}. {e.get('description') or ''}"
                for e in edu_docs
            ]
            context_parts.append(
                f"[EDUCATION - COMPLETE LIST, {len(edu_docs)} total]\n" + "\n".join(edu_lines)
            )
        else:
            context_parts.append("[EDUCATION] None on record.")

        exp_docs = await db.experience.find({}).sort("start_date", -1).to_list(100)
        if exp_docs:
            exp_lines = [
                f"- {e.get('role')} at {e.get('company')} "
                f"({e.get('start_date')} - {e.get('end_date') or 'Present'}). {e.get('description') or ''}"
                for e in exp_docs
            ]
            context_parts.append(
                f"[EXPERIENCE - COMPLETE LIST, {len(exp_docs)} total]\n" + "\n".join(exp_lines)
            )
        else:
            context_parts.append("[EXPERIENCE] None on record.")

        achieve_docs = await db.achievements.find({}).sort("date", -1).to_list(100)
        if achieve_docs:
            achieve_lines = [
                f"- {a.get('title')} ({a.get('issuer') or 'N/A'}, {a.get('date') or 'N/A'}). {a.get('description') or ''}"
                for a in achieve_docs
            ]
            context_parts.append(
                f"[ACADEMIC ACHIEVEMENTS - COMPLETE LIST, {len(achieve_docs)} total] "
                "This is the full and only list of academic achievements. "
                "If asked how many achievements there are, the answer is exactly "
                f"{len(achieve_docs)}:\n" + "\n".join(achieve_lines)
            )
        else:
            context_parts.append("[ACADEMIC ACHIEVEMENTS] None on record.")

        position_docs = await db.positions.find({}).sort("start_date", -1).to_list(100)
        if position_docs:
            position_lines = [
                f"- {p.get('title')} at {p.get('organization')} "
                f"({p.get('start_date')} - {p.get('end_date') or 'Present'}). {p.get('description') or ''}"
                for p in position_docs
            ]
            context_parts.append(
                f"[POSITIONS OF RESPONSIBILITY - COMPLETE LIST, {len(position_docs)} total]\n"
                + "\n".join(position_lines)
            )
        else:
            context_parts.append("[POSITIONS OF RESPONSIBILITY] None on record.")

        project_docs = await db.projects.find({}).sort("created_at", -1).to_list(100)
        if project_docs:
            project_lines = [
                f"- {p.get('title')}: {p.get('description')} (Tech: {', '.join(p.get('tech_stack', []))})"
                for p in project_docs
            ]
            context_parts.append(
                f"[PROJECTS - COMPLETE LIST, {len(project_docs)} total]\n" + "\n".join(project_lines)
            )
        else:
            context_parts.append("[PROJECTS] None on record.")

        context = "\n\n".join(context_parts)

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