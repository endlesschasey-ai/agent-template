"""Logging configuration."""
import logging
import sys
from ..config import settings


def setup_logging():
    """配置全局日志"""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def get_logger(name: str) -> logging.Logger:
    """获取 logger 实例"""
    return logging.getLogger(name)


# 应用启动时初始化日志
setup_logging()
