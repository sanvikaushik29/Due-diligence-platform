
from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.api.auth_routes import router as auth_router
from app.db import init_db

app = FastAPI(title="Due Diligence Platform")

allowed = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
origins = [o.strip() for o in allowed.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

@app.get("/")
async def health():
    return {"status": "ok"}

app.include_router(auth_router, prefix="/api")
app.include_router(router, prefix="/api")
