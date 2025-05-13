"""
API routes package.
"""
from fastapi import APIRouter
from app.api.routes import tasks, agents, workspaces, discussions, ui

# Create API router
api_router = APIRouter()

# Include routers
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(discussions.router, prefix="/discussions", tags=["discussions"])
api_router.include_router(ui.router, tags=["ui"])

__all__ = ["api_router"]
