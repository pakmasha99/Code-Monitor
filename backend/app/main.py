"""
FastAPI application entry point
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.database import get_db
from backend.app.api.users import router as users_router
from backend.app.api.weekly_submissions import router as submissions_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Lab Code Monitoring System",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users_router)
app.include_router(submissions_router)


@app.get("/")
def root():
    return {"app": settings.APP_NAME, "version": "0.1.0", "status": "running"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
