"""FastAPI 应用入口"""
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import init_db, get_db
from app.services.auth_service import AuthService
from app.routers import auth_router, chat_router, knowledge_base_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("[启动] RAG 知识库问答系统启动中...")

    # 初始化数据库
    init_db()
    print("[启动] 数据库初始化完成")

    # 初始化管理员账号
    db = next(get_db())
    try:
        AuthService.init_admin(db)
    finally:
        db.close()

    yield

    # 关闭时执行
    print("[关闭] 系统已关闭")


app = FastAPI(
    title="LangChain RAG 知识库问答系统",
    description="基于 LangChain + 阿里云百炼的电商知识库问答系统",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {str(exc)}" if settings.DASHSCOPE_API_KEY else "服务器内部错误"},
    )


# 注册路由
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(knowledge_base_router)


# 健康检查
@app.get("/health", tags=["系统"])
def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "llm_provider": "阿里云百炼",
        "llm_model": settings.LLM_MODEL_NAME,
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
    }


# 根路径
@app.get("/", tags=["系统"])
def root():
    return {
        "message": "欢迎使用 LangChain RAG 知识库问答系统",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )