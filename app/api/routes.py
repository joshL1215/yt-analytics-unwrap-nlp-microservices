from fastapi import APIRouter
from api.handlers import (
    health_check_handler,
    comment_analysis_handler,
    video_analysis_handler
)

router = APIRouter()

# health
@router.get("/health")
def health_check():
    return {"status": "ok"}


# Comment analysis
@router.post("/analyze-comment")
async def analyze_comment(payload: dict):
    return await comment_analysis_handler(payload)


# vid analysis
@router.post("/analyze-video")
def analyze_video(payload: dict):
    return