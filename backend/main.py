from fastapi import FastAPI
from backend.config import get_settings


# 获取配置实例
settings = get_settings()

# 创建 FastAPI 应用
app = FastAPI(title="数据分析 Agent", debug=settings.debug)


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
