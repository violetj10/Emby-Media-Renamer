import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class Config:
    """配置数据类"""
    monitor_path: str
    media_exts: List[str]
    recursive: bool = True
    log_level: str = "INFO"
    log_file: str = "media_monitor.log"
    ai_enabled: bool = False
    ai_api_key: str = ""
    ai_endpoint: str = ""
    ai_model: str = "gpt-4o"

    @classmethod
    def from_file(cls, config_path: str = 'config.json') -> 'Config':
        """从配置文件加载配置"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        return cls(**config_data)

    def validate(self) -> None:
        """验证配置是否有效"""
        # 检查监控路径
        if not self.monitor_path or not os.path.isdir(self.monitor_path):
            raise ValueError(f"无效的监控目录: {self.monitor_path}")

        # 检查AI设置
        if self.ai_enabled and (not self.ai_api_key or not self.ai_endpoint):
            raise ValueError("AI功能已启用但缺少API密钥或端点URL")

        # 确保路径是绝对路径
        self.monitor_path = os.path.abspath(self.monitor_path)