from fastapi import APIRouter


from . import attendance, auth, health, test, timezones

router = APIRouter()
router.include_router(attendance.router, prefix="/attendance")
router.include_router(auth.router, prefix="/auth")
router.include_router(health.router, prefix="/health")
router.include_router(test.router, prefix="/test")
router.include_router(timezones.router, prefix="/timezones")
