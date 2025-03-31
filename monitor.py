import os
import sys
import time
import threading
from typing import Dict, Any, Optional

from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from config import Config
from logger import Logger
from media_renamer import MediaRenamer


class MediaFileHandler(FileSystemEventHandler):
    """媒体文件处理器"""

    def __init__(self, config: Config):
        """初始化处理器"""
        self.config = config
        self.logger = Logger(config).get_logger()
        self.media_renamer = MediaRenamer(config)

        # 使用事件队列延迟处理，避免处理不完整的文件
        self.event_queue: Dict[str, Dict[str, Any]] = {}
        self.queue_lock = threading.Lock()

        # 添加此行：设置running属性
        self.running = True

        # 启动队列处理器
        self.queue_processor = threading.Thread(target=self._process_queue)
        self.queue_processor.daemon = True
        self.queue_processor.start()

    def on_created(self, event):
        """将创建事件加入队列"""
        with self.queue_lock:
            path = os.path.normpath(event.src_path)
            self.event_queue[path] = {
                'type': 'created',
                'is_directory': event.is_directory,
                'timestamp': time.time()
            }

    def _process_queue(self):
        """处理事件队列"""
        while self.running:
            try:
                # 处理队列中的事件
                with self.queue_lock:
                    current_time = time.time()
                    to_process = []

                    # 找出等待时间超过2秒的事件
                    for path, event_info in list(self.event_queue.items()):
                        if current_time - event_info['timestamp'] >= 2.0:
                            to_process.append((path, event_info))
                            del self.event_queue[path]

                # 处理已就绪的事件
                for path, event_info in to_process:
                    if not os.path.exists(path):
                        continue

                    if event_info['is_directory']:
                        self.logger.info(f"处理新目录: {path}")
                        self.media_renamer.process_directory(path)
                    else:
                        self.logger.info(f"处理新文件: {path}")
                        directory = os.path.dirname(path)
                        self.media_renamer.process_file(path, directory)

            except Exception as e:
                self.logger.error(f"处理队列时出错: {e}")

            # 每秒检查一次队列
            time.sleep(1)

    def stop(self):
        """停止队列处理器"""
        self.running = False

        # 等待队列处理完毕
        if self.queue_processor.is_alive():
            self.queue_processor.join(timeout=5)


def start_monitoring(config_path: str = 'config.json'):
    """开始监控目录"""
    # 加载配置
    try:
        config = Config.from_file(config_path)
        config.validate()
    except Exception as e:
        print(f"配置错误: {e}")
        sys.exit(1)

    # 获取日志
    logger = Logger(config).get_logger()
    logger.info("启动媒体文件监控服务")

    # 创建处理器
    event_handler = MediaFileHandler(config)

    # 选择合适的观察器
    if os.name == 'nt':  # Windows
        observer = PollingObserver()
        logger.info("使用PollingObserver (适用于Windows)")
    else:  # Linux/Mac
        try:
            # 尝试使用inotify
            from watchdog.observers.inotify import InotifyObserver
            observer = InotifyObserver()
            logger.info("使用InotifyObserver (适用于Linux)")
        except ImportError:
            # 回退到标准观察器
            observer = Observer()
            logger.info("使用标准Observer")

    # 设置观察器
    observer.schedule(
        event_handler,
        config.monitor_path,
        recursive=config.recursive
    )

    # 启动观察器
    observer.start()
    logger.info(f"开始监控目录: {config.monitor_path} (递归: {config.recursive})")
    logger.info("按 Ctrl+C 停止监控")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("接收到停止信号，正在关闭...")
        event_handler.stop()
        observer.stop()

    observer.join()
    logger.info("监控服务已停止")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Emby媒体文件监控与重命名工具')
    parser.add_argument('-c', '--config', default='config.json',
                        help='配置文件路径 (默认: config.json)')

    args = parser.parse_args()
    start_monitoring(args.config)