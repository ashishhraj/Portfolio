# 🚀 Personal Portfolio Website

A full-stack portfolio with **AI-powered chatbot**, admin panel, and dynamic content management.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, Vanilla JS (single file, zero dependencies) |
| Backend | Python FastAPI |
| Database | MongoDB Atlas |
| Vector Search | ChromaDB (RAG for chatbot) |
| AI Chatbot | Anthropic Claude API |
| File Storage | Cloudinary |
| Hosting | Render (free tier) |

## Features

- **Dynamic Portfolio** — Add/edit/delete projects and certifications via admin panel
- **AI Chatbot** — Trained on your resume, projects, and certifications using RAG
- **Secure Admin** — JWT-based authentication, only you can edit
- **Image Uploads** — Upload project screenshots and certification images
- **PDF Resume** — Upload and serve your resume PDF
- **Professional UI** — Dark, corporate, responsive design

## Quick Start

See [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md) for full step-by-step instructions.

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Fill in your values
uvicorn main:app --reload
```

Then open `frontend/index.html` in your browser.

## Project Structure

```
portfolio/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── requirements.txt     # Python dependencies
│   ├── render.yaml          # Render deployment config
│   ├── .env.example         # Environment variables template
│   ├── db/
│   │   ├── mongo.py         # MongoDB connection
│   │   └── chroma.py        # ChromaDB vector store
│   ├── routes/
│   │   ├── auth.py          # JWT authentication
│   │   ├── projects.py      # Projects CRUD
│   │   ├── certifications.py# Certifications CRUD
│   │   ├── resume.py        # Resume management
│   │   └── chat.py          # AI chatbot (RAG)
│   └── utils/
│       └── auth_dep.py      # Auth dependency
├── frontend/
│   └── index.html           # Complete single-page portfolio
└── docs/
    └── DEPLOYMENT_GUIDE.md  # Step-by-step deployment guide
```
