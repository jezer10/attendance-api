import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import router as api_router
from src.core.config import settings
import uvicorn
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.info("Starting attendance API on port %s", settings.port)
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
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Attendance Management API", "version": "1.0.0", "docs": "/docs"}


if __name__ == "__main__":
    reload = settings.env == "development"
    host = settings.host  # valor por defecto si no existe
    port = int(os.getenv("PORT", settings.port))  # uvicorn requiere entero
    uvicorn.run("main:app", host=host, port=port, reload=reload)
