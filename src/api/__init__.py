from fastapi import APIRouter
from .v1 import router as v1_router
# from .v2 import router as v2_router  # si tienes más versiones

router = APIRouter()
router.include_router(v1_router, prefix="/v1")