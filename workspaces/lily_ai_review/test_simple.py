"""
Test script for the simplified implementation.
"""
import os
import sys
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("test_simple.log")
    ]
)

logger = logging.getLogger("test_simple")

# Import routes
from routes.auth_simple import router as auth_router_simple
from routes.billing_simple import router as billing_router_simple
from routes.billing_webhook_simple import router as billing_webhook_router_simple
from routes.research_paper_simple import router as research_paper_router_simple

# Initialize FastAPI app
app = FastAPI(
    title="Lily AI Research Assistant - Simple Test",
    description="Simple test for the simplified implementation",
    version="0.1.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(auth_router_simple)
app.include_router(billing_router_simple)
app.include_router(billing_webhook_router_simple)
app.include_router(research_paper_router_simple)

# Home page route
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Render the home page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with the home template
    """
    return templates.TemplateResponse("home.html", {"request": request})

if __name__ == "__main__":
    # Run the application
    logger.info("Starting test application on port 8004...")
    uvicorn.run(app, host="0.0.0.0", port=8004)
