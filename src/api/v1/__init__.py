from fastapi import APIRouter


from . import  attendance, auth, health

router = APIRouter()
router.include_router(attendance.router, prefix="/attendance")
router.include_router(auth.router, prefix="/auth")
router.include_router(health.router, prefix="/health")