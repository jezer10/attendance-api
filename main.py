import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.info("Starting attendance API...")
    logging.info(f"Base URL: {settings.base_url}")
    logging.info(f"Company ID: {settings.company_id}")
    yield
    # Shutdown
    logging.info("Shutting down attendance API...")


app = FastAPI(
    title="Attendance Management API",
    description="API for managing employee attendance",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1", tags=["attendance"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Attendance Management API", "version": "1.0.0", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host="0.0.0.0", port=settings.port, reload=True, log_level="info"
    )
