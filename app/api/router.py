"""API Router - 모든 라우터 통합"""

from fastapi import APIRouter

from app.api.routes import auth, curriculums, papers, users

api_router = APIRouter()

# 라우터 등록
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(papers.router)
api_router.include_router(curriculums.router)

