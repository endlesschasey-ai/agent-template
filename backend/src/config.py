"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置"""

    # DashScope API 配置
    DASHSCOPE_API_KEY: str
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data.db"
    SQLALCHEMY_ECHO: bool = False

    # CORS 配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # 文件上传配置
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: List[str] = ["image/png", "image/jpeg", "image/jpg"]

    # 日志配置
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()
