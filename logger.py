import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

from config import Config


class Logger:
    """日志管理类"""
    _instance: Optional['Logger'] = None

    def __new__(cls, config: Optional[Config] = None):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._setup(config)
        elif config:
            cls._instance._setup(config)
        return cls._instance

    def _setup(self, config: Optional[Config] = None) -> None:
        """设置日志记录器"""
        self.logger = logging.getLogger('media_monitor')

        # 清除所有现有处理器
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # 设置日志级别
        log_level = "INFO"
        log_file = "media_monitor.log"

        if config:
            log_level = config.log_level
            log_file = config.log_file

        # 如果日志文件存在，直接删除它
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
            except:
                pass

        level = getattr(logging, log_level)
        self.logger.setLevel(level)

        # 创建文件处理器
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        console_handler = logging.StreamHandler()

        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            '%Y-%m-%d %H:%M:%S'
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        """获取日志记录器实例"""
        return self.logger