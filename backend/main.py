from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import get_settings
from backend.database import engine, Base
from backend.routers import upload, charts, chat


# 获取配置实例
settings = get_settings()

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建 FastAPI 应用
app = FastAPI(title="数据分析 Agent", debug=settings.debug)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(upload.router)
app.include_router(charts.router)
app.include_router(chat.router)


# 定义一个测试接口
@app.get("/")
def read_root():
    return {
        "message": "Hello! 数据分析 Agent 启动成功！",
        "debug": settings.debug,
        "upload_dir": settings.upload_dir
    }


@app.get("/settings")
def read_settings():
    return {
        "LLM_api_key": bool(settings.llm_api_key != "your_api_key_here"),  # 检查LLM_api_key是否为空
        "database_url": settings.database_url,
        "upload_dir": settings.upload_dir,
        "max_file_size": settings.max_file_size,
        "allowed_origins": settings.allowed_origins
    }
