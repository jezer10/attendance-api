from fastapi import APIRouter
from src.models import HealthResponse
from datetime import datetime

router = APIRouter()


@router.get("", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy", service="attendance-api", timestamp=datetime.now()
    )
