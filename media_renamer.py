import json
import os
import re
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from config import Config
from logger import Logger


@dataclass
class MediaInfo:
    """媒体信息数据类"""
    title: str
    year: str
    type: str = "unknown"  # movie, tv, unknown
    season: Optional[int] = None
    episode: Optional[int] = None
    resolution: Optional[str] = None

    @property
    def is_movie(self) -> bool:
        return self.type == "movie"

    @property
    def is_tv(self) -> bool:
        return self.type == "tv"


class MediaRenamer:
    """媒体文件重命名工具"""

    def __init__(self, config: Config):
        """初始化媒体重命名器"""
        self.config = config
        self.logger = Logger(config).get_logger()

        # 导入AI库
        if self.config.ai_enabled:
            try:
                import openai
                self.logger.info("AI命名功能已启用")
            except ImportError:
                self.logger.error("缺少OpenAI库，AI功能已禁用")
                self.config.ai_enabled = False

    def process_directory(self, directory_path: str) -> Optional[str]:
        """处理目录"""
        if not os.path.exists(directory_path):
            self.logger.error(f"目录不存在: {directory_path}")
            return None

        dir_name = os.path.basename(directory_path)

        # 排除特定目录名称
        excluded_dirs = ["电影", "电视剧", "动漫", "综艺", "纪录片", "Movies", "TV", "Anime", "Shows"]
        if dir_name in excluded_dirs:
            self.logger.info(f"跳过特定目录: {dir_name}")
            return directory_path

        # 从目录名推断媒体信息
        media_info = self.extract_media_info(dir_name)

        if media_info:
            # 重命名目录
            return self.rename_directory(directory_path, media_info)

        return directory_path

    def process_file(self, file_path: str, directory: str) -> Optional[str]:
        """处理单个文件"""
        if not os.path.exists(file_path):
            self.logger.error(f"文件不存在: {file_path}")
            return None

        # 跳过非媒体文件
        filename = os.path.basename(file_path)
        _, ext = os.path.splitext(filename)
        if ext.lower() not in self.config.media_exts:
            return None

        # 从文件名推断媒体信息
        media_info = self.extract_media_info(filename)

        # 如果无法从文件名获取信息，尝试从目录名获取
        if not media_info:
            dir_name = os.path.basename(directory)
            dir_info = self.extract_media_info(dir_name)

            # 如果从目录获取到了信息，补充文件特定信息（如集数）
            if dir_info:
                # 尝试从文件名提取集数
                episode_num = self.extract_episode_number(filename)
                if episode_num:
                    dir_info.episode = episode_num
                    dir_info.type = "tv"  # 有集数，一定是电视剧
                media_info = dir_info

        # 如果媒体信息有效，重命名文件
        if media_info:
            return self.rename_file(file_path, media_info)

        return file_path

    def extract_media_info(self, name: str) -> Optional[MediaInfo]:
        """从名称中提取媒体信息"""
        # 如果启用了AI，优先使用AI提取
        if self.config.ai_enabled:
            ai_info = self.ai_extract_media_info(name)
            if ai_info:
                return ai_info

        # 自动提取年份
        year_match = re.search(r'(19|20)\d{2}', name)
        year = year_match.group(0) if year_match else None

        # 尝试找出标题
        if year and year_match:
            year_pos = year_match.start()

            # 年份前面的部分可能是标题
            if year_pos > 0:
                title = name[:year_pos].strip()
                title = re.sub(r'[\s\.\-_\[\]\(\)\{\}\<\>《》【】]*$', '', title)
            else:
                # 年份在开头，则后面的内容可能是标题
                title = re.sub(r'^\d{4}[\s\.\-_\[\]\(\)\{\}\<\>《》【】]*', '', name).strip()
        else:
            # 没有年份，整个名称可能是标题（清理常见后缀）
            title = re.sub(r'(1080[pP]|720[pP]|4[kK]|BluRay|WEB-DL).*$', '', name).strip()
            title = re.sub(r'[\s\.\-_\[\]\(\)\{\}\<\>《》【】]*$', '', title)

        # 检测季集信息
        season_match = re.search(r'[Ss](\d{1,2})|第(\d{1,2})季', name)
        season_num = int(season_match.group(1) or season_match.group(2)) if season_match else 1

        episode_num = self.extract_episode_number(name)

        # 清晰度匹配
        resolution_match = re.search(r'(1080[pP]|720[pP]|4[kK]|2160[pP]|UHD)', name)
        resolution = resolution_match.group(1) if resolution_match else None

        # 确定媒体类型
        media_type = "tv" if (season_match or episode_num) else "movie"

        # 创建媒体信息对象
        if title and (year or media_type == "tv"):
            return MediaInfo(
                title=title,
                year=year or "未知",
                type=media_type,
                season=season_num if media_type == "tv" else None,
                episode=episode_num,
                resolution=resolution
            )

        return None

    def extract_episode_number(self, name: str) -> Optional[int]:
        """从文件名提取集数"""
        # 1. 标准格式 E01
        episode_match = re.search(r'[Ee](\d{1,2})|第(\d{1,2})集', name)

        # 2. 方括号等包围的数字 [01]
        if not episode_match:
            episode_match = re.search(r'[\[\(（](\d{1,2})[\]\)）]', name)

        # 3. 季数后跟集数 S01.01
        if not episode_match:
            season_match = re.search(r'[Ss](\d{1,2})', name)
            if season_match:
                season_str = season_match.group(1)
                episode_match = re.search(r'[Ss]' + season_str + r'[\. _-](\d{1,2})', name)

        # 4. 文件名末尾的数字 name.01.mp4
        if not episode_match:
            episode_match = re.search(r'(?<!\d)(\d{2})(?=\.\w+$)', name)

        if episode_match:
            try:
                return int(episode_match.group(1) or episode_match.group(2))
            except:
                pass

        return None

    def ai_extract_media_info(self, name: str) -> Optional[MediaInfo]:
        """使用AI从名称中提取媒体信息"""
        if not self.config.ai_enabled:
            return None

        try:
            from openai import OpenAI

            # 初始化OpenAI客户端
            client = OpenAI(
                base_url=self.config.ai_endpoint,
                api_key=self.config.ai_api_key,
            )

            # 准备提示
            prompt = f"""
            从以下文件名/目录名中提取媒体信息："{name}"

            需要提取以下信息：
            1. 媒体类型（电影/电视剧）
            2. 标题（中文或原始语言）
            3. 年份
            4. 季数（如果是电视剧）
            5. 集数（如果是电视剧）
            6. 分辨率（如1080p、4K等，如果有）

            请返回JSON格式：
            {{
              "type": "movie或tv",
              "title": "标题",
              "year": "年份",
              "season": 季数(仅电视剧),
              "episode": 集数(仅电视剧),
              "resolution": "分辨率"
            }}

            只返回JSON，不要解释。
            """

            # 发送请求
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的媒体文件分析工具，专门从文件名中提取媒体信息。",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.config.ai_model
            )

            # 处理响应
            if not response or not response.choices:
                return None

            message = response.choices[0].message
            if not message or not message.content:
                return None

            content = message.content.strip()

            # 处理可能的Markdown代码块
            content = re.sub(r'```json\s*|\s*```', '', content)

            try:
                # 解析JSON
                ai_info = json.loads(content)
                self.logger.info(f"AI提取的媒体信息: {ai_info}")

                # 转换为MediaInfo对象
                return MediaInfo(
                    title=ai_info.get('title', ''),
                    year=str(ai_info.get('year', '未知')),
                    type=ai_info.get('type', 'unknown'),
                    season=ai_info.get('season'),
                    episode=ai_info.get('episode'),
                    resolution=ai_info.get('resolution')
                )
            except json.JSONDecodeError:
                self.logger.error(f"无法解析AI返回的JSON: {content}")
            except Exception as e:
                self.logger.error(f"处理AI响应时出错: {e}")

        except Exception as e:
            self.logger.error(f"AI提取媒体信息失败: {e}")
            self.logger.error(f"错误详情: {traceback.format_exc()}")

        return None

    def rename_directory(self, directory_path: str, media_info: MediaInfo) -> str:
        """重命名目录"""
        dir_name = os.path.basename(directory_path)

        # 尝试获取AI建议的目录名
        ai_dir_name = None
        if self.config.ai_enabled:
            ai_suggestion = self.get_ai_naming_suggestion(dir_name, media_info, is_directory=True)
            if ai_suggestion:
                ai_dir_name = ai_suggestion
                self.logger.debug(f"使用AI建议的目录名: {ai_dir_name}")

        # 确定新目录名
        if ai_dir_name:
            new_dir_name = ai_dir_name
        else:
            # 标准命名格式
            new_dir_name = f"{media_info.title}（{media_info.year}）"

        # 获取完整路径
        parent_dir = os.path.dirname(directory_path)
        new_path = os.path.join(parent_dir, new_dir_name)

        # 检查是否需要重命名
        if directory_path == new_path or os.path.exists(new_path):
            return directory_path

        # 重命名目录
        try:
            # 添加延迟和重试
            max_retries = 3
            for retry in range(max_retries):
                try:
                    if not os.path.exists(directory_path):
                        time.sleep(1)
                        continue

                    os.rename(directory_path, new_path)
                    self.logger.info(f"已重命名目录: {os.path.basename(directory_path)} -> {new_dir_name}")
                    return new_path
                except Exception as e:
                    if retry < max_retries - 1:
                        time.sleep(1)
                    else:
                        raise

            return directory_path
        except Exception as e:
            self.logger.error(f"重命名目录出错: {e}")
            return directory_path

    def rename_file(self, file_path: str, media_info: MediaInfo) -> str:
        """重命名文件"""
        original_name = os.path.basename(file_path)
        _, ext = os.path.splitext(file_path)

        # 尝试获取AI建议的文件名
        ai_filename = None
        if self.config.ai_enabled:
            ai_suggestion = self.get_ai_naming_suggestion(original_name, media_info, is_directory=False)
            if ai_suggestion and (ai_suggestion.endswith(ext) or '.' in ai_suggestion):
                ai_filename = ai_suggestion
                self.logger.debug(f"使用AI建议的文件名: {ai_filename}")

        # 确定新文件名
        if ai_filename:
            new_filename = ai_filename
        else:
            # 标准命名格式
            resolution_tag = f" - [{media_info.resolution}]" if media_info.resolution else ""

            if media_info.is_movie:
                new_filename = f"{media_info.title}（{media_info.year}）{resolution_tag}{ext}"
            else:  # 电视剧
                if media_info.episode:
                    season_num = str(media_info.season or 1).zfill(2)
                    episode_num = str(media_info.episode).zfill(2)
                    new_filename = f"{media_info.title}（{media_info.year}） - S{season_num}E{episode_num}{resolution_tag}{ext}"
                else:
                    season_num = str(media_info.season or 1).zfill(2)
                    new_filename = f"{media_info.title}（{media_info.year}） - Season {season_num}{resolution_tag}{ext}"

        # 获取完整路径
        directory = os.path.dirname(file_path)
        new_path = os.path.join(directory, new_filename)

        # 检查是否需要重命名
        if file_path == new_path or os.path.exists(new_path):
            return file_path

        # 重命名文件
        try:
            os.rename(file_path, new_path)
            self.logger.info(f"已重命名文件: {os.path.basename(file_path)} -> {new_filename}")
            return new_path
        except Exception as e:
            self.logger.error(f"重命名文件出错: {e}")
            return file_path

    def get_ai_naming_suggestion(self, original_name: str, media_info: MediaInfo, is_directory: bool = False) -> \
    Optional[str]:
        """使用AI获取命名建议"""
        if not self.config.ai_enabled:
            return None

        try:
            from openai import OpenAI

            # 初始化OpenAI客户端
            client = OpenAI(
                base_url=self.config.ai_endpoint,
                api_key=self.config.ai_api_key,
            )

            # 准备提示
            if is_directory:
                prompt = f"""
                将媒体目录重命名为标准格式。

                原目录名: {original_name}
                媒体类型: {media_info.type}
                标题: {media_info.title}
                年份: {media_info.year}

                请将此目录重命名为: "标题（年份）" 格式
                不需要添加其他信息，不要使用代码块

                请直接给出新的目录名:
                """
            else:
                ext = os.path.splitext(original_name)[1]
                prompt = f"""
                将媒体文件重命名为Emby标准格式。

                原文件名: {original_name}
                媒体类型: {media_info.type}
                标题: {media_info.title}
                年份: {media_info.year}
                季数: {media_info.season if media_info.season else '无'}
                集数: {media_info.episode if media_info.episode else '无'}
                分辨率: {media_info.resolution if media_info.resolution else '无'}
                扩展名: {ext}

                电影命名格式: "电影名（年份）- 分辨率.扩展名"
                电视剧命名格式: "剧名（年份） - S季数E集数 - 分辨率.扩展名"

                请直接给出新的文件名:
                """

            # 发送请求
            max_retries = 2
            for retry in range(max_retries):
                response = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的媒体文件命名工具。只返回规范的文件名，不包含其他文字。",
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model=self.config.ai_model
                )

                # 处理响应
                if response and response.choices:
                    message = response.choices[0].message
                    if message and message.content:
                        # 提取内容并移除可能的Markdown代码块和引号
                        content = message.content.strip()
                        content = re.sub(r'```.*\n|\n```|^[\s`"\']*|[\s`"\']*$', '', content)
                        return content

                # 重试前等待
                if retry < max_retries - 1:
                    time.sleep(1)

        except Exception as e:
            self.logger.error(f"获取AI命名建议失败: {e}")

        return None