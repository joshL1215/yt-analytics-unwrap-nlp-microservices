from fastapi import APIRouter
from app.api.handlers import (
    comment_analysis_handler,
    video_analysis_handler
)

router = APIRouter()

# health
@router.get("/health")
def health_check():
    return {"status": "ok"}


# Comment analysis
@router.post("/analyze-comments")
async def analyze_comments(payload: dict):
    return await comment_analysis_handler(payload)


# vid analysis
@router.post("/analyze-video")
def analyze_video(payload: dict):
    return