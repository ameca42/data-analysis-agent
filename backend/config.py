from pydantic_settings import BaseSettings
from typing import Any, Dict, List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """
    应用配置类
    从.env文件加载环境变量并提供配置项
    """

    # ===== API Keys =====
    llm_api_key: str
    llm_base_url: str
    llm_model_name: str

    # ===== Database =====
    database_url: str = "sqlite:///./data.db"

    # ===== App Settings =====
    debug: bool = False
    upload_dir: str = "./backend/uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB

    # ===== CORS =====
    allowed_origins: List[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置实例的缓存函数
    使用lru_cache装饰器缓存配置实例,提高性能
    """
    return Settings()
