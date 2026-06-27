from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import os, jwt, bcrypt
from datetime import datetime, timedelta

router = APIRouter()

SECRET_KEY  = os.getenv("JWT_SECRET", "your-super-secret-key-change-this")
ALGORITHM   = "HS256"
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@portfolio.com")
ADMIN_PASS  = os.getenv("ADMIN_PASSWORD", "admin123")  # Change in .env

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

def create_token(data: dict, expires_hours: int = 24):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=expires_hours)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    if req.email != ADMIN_EMAIL or req.password != ADMIN_PASS:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"sub": req.email, "role": "admin"})
    return TokenResponse(access_token=token)

@router.get("/verify")
async def verify(token: str):
    payload = verify_token(token)
    return {"valid": True, "email": payload.get("sub")}
