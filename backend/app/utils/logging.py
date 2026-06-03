"""Loguru 日志配置"""
import os
import sys

from loguru import logger

from app.settings import BASE_DIR, settings

LOG_DIR = os.path.join(BASE_DIR, "logs")
_initialized = False

_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def setup_logger() -> None:
    """配置日志系统（幂等，可安全重复调用）"""
    global _initialized
    if _initialized:
        return

    os.makedirs(LOG_DIR, exist_ok=True)
    logger.remove()

    level = "DEBUG" if settings.debug else "INFO"

    logger.add(
        sys.stdout,
        colorize=True,
        format=_CONSOLE_FORMAT,
        level=level,
    )

    logger.add(
        os.path.join(LOG_DIR, "app.log"),
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        serialize=True,
        level="INFO",
    )

    logger.add(
        os.path.join(LOG_DIR, "error.log"),
        rotation="100 MB",
        retention="30 days",
        compression="zip",
        level="ERROR",
        backtrace=True,
        diagnose=settings.debug,
    )

    _initialized = True
    logger.info("日志系统初始化完成 env={}", settings.app_env)
