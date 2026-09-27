from fastapi import APIRouter

from app.api.ai.router import router as ai_router
from app.api.auth.router import router as auth_router
from app.api.campaigns.router import router as campaigns_router
from app.api.health.router import router as health_router
from app.api.linkedin.router import router as linkedin_router
from app.api.posts.router import router as posts_router
from app.api.schedules.router import router as schedules_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, tags=["authentication"])
api_router.include_router(linkedin_router, tags=["linkedin"])
api_router.include_router(ai_router, tags=["ai"])
api_router.include_router(posts_router, tags=["posts"])
api_router.include_router(campaigns_router, tags=["campaigns"])
api_router.include_router(schedules_router, tags=["schedules"])
