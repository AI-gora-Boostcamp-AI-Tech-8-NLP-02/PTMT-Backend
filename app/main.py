"""PTMT Backend - FastAPI Application Entry Point

논문 기반 커리큘럼 생성 서비스 백엔드
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.schemas.common import ApiResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """애플리케이션 생명주기 관리
    
    TODO: 실제 구현 시
    - DB 연결 초기화
    - Redis 연결 (캐싱용)
    - 백그라운드 워커 시작
    """
    # Startup
    print(f"🚀 Starting {settings.APP_NAME} API Server...")
    print(f"📍 Environment: {settings.APP_ENV}")
    print(f"🔗 CORS Origins: {settings.cors_origins_list}")
    
    # TODO: DB 연결
    # await database.connect()
    
    yield
    
    # Shutdown
    print(f"👋 Shutting down {settings.APP_NAME} API Server...")
    
    # TODO: DB 연결 해제
    # await database.disconnect()


# FastAPI 앱 생성
app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="PTMT(페튜와 매튜) - 논문 기반 커리큘럼 생성 서비스 API",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)


# ===========================================
# CORS 설정
# ===========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===========================================
# 전역 예외 처리
# ===========================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """전역 예외 처리
    
    TODO: 로깅 추가
    """
    # 개발 환경에서는 상세 에러 메시지
    if settings.DEBUG:
        detail = str(exc)
    else:
        detail = "서버 내부 오류가 발생했습니다."
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiResponse.fail(
            code="INTERNAL_SERVER_ERROR",
            message=detail,
        ).model_dump(),
    )


# ===========================================
# 라우터 등록
# ===========================================

# API v1 라우터 등록 (prefix: /api)
app.include_router(api_router, prefix="/api")


# ===========================================
# 헬스체크 엔드포인트
# ===========================================

@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """헬스체크 - 서버 상태 확인"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "environment": settings.APP_ENV,
    }


@app.get("/", tags=["root"])
async def root() -> dict:
    """루트 엔드포인트"""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs": "/docs",
        "health": "/health",
    }


# ===========================================
# 개발용 실행
# ===========================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
