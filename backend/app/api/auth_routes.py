from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.auth import check_credentials, create_token

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/auth/login")
async def login(payload: LoginRequest):
    if not check_credentials(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_token(payload.username)
    return {"token": token}