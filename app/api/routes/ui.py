"""
UI routes.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os

router = APIRouter()

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get the static directory
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), "app", "static")

@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """
    Get the agent dashboard UI.
    """
    return FileResponse(os.path.join(static_dir, "agent_dashboard.html"))

@router.get("/dashboard.js")
async def get_dashboard_js(request: Request):
    """
    Get the agent dashboard JavaScript.
    """
    return FileResponse(os.path.join(static_dir, "agent_dashboard.js"))
