"""
Main application module for the Autonomous Agent System.
"""
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.db.base import init_db
from app.api.routes import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("autonomous-agent-system")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Create startup event
@app.on_event("startup")
async def startup_event():
    """
    Initialize application on startup.
    """
    logger.info("Starting up application")

    # Initialize database
    await init_db()

    # Create agent workspaces directory if it doesn't exist
    os.makedirs(settings.AGENT_WORKSPACE_ROOT, exist_ok=True)

    logger.info("Application startup complete")

# Create shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up on application shutdown.
    """
    logger.info("Shutting down application")

# Create root endpoint
@app.get("/")
async def root():
    """
    Root endpoint.
    """
    return {
        "message": "Welcome to the Autonomous Agent System API",
        "docs_url": f"/docs",
        "openapi_url": f"{settings.API_V1_STR}/openapi.json",
    }

# Run the application
if __name__ == "__main__":
    import uvicorn

    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8001))

    # Run the application
    uvicorn.run("app.new_main:app", host="0.0.0.0", port=port, reload=True)
