from fastapi import APIRouter
from app.api.v1.endpoints import auth, questions, practice, drawing, analytics, concepts, admin

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(questions.router)
api_router.include_router(practice.router)
api_router.include_router(drawing.router)
api_router.include_router(analytics.router)
api_router.include_router(concepts.router)
api_router.include_router(admin.router)
