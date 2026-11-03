"""Aggregate API v1 routers."""

from fastapi import APIRouter

from app.api.routes import auth, health, plans, projects, rounds, sessions, weaknesses, worker

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(worker.router)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(rounds.router, prefix="/rounds", tags=["rounds"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(weaknesses.router, prefix="/weaknesses", tags=["weaknesses"])
