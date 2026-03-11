"""ログ管理（日次ローテーション）"""

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def setup_logger(
    name: str,
    log_dir: str = "./logs/",
    log_file: str = "app.log",
    level: str = "INFO",
    log_format: str = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
) -> logging.Logger:
    """名前付きロガーをセットアップする。"""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    file_path = log_path / log_file

    file_handler = TimedRotatingFileHandler(
        str(file_path),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
