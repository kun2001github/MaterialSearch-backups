import datetime
import logging
import os
import threading
from pathlib import Path
from watchdog.events import FileSystemEventHandler

from app.config import (
    ASSETS_PATH,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    SKIP_PATH,
    IGNORE_STRINGS,
)
from app.models.database import (
    delete_image_by_path,
    delete_video_by_path,
    get_image_count,
    get_video_count,
    get_video_frame_count,
)
from app.models.models import DatabaseSession
from app.services.process_assets import process_images, process_video
from app.services.utils import get_file_hash


logger = logging.getLogger(__name__)


class FileWatchEventHandler(FileSystemEventHandler):
    """
    文件监控事件处理器
    """

    def __init__(self, file_watcher):
        super().__init__()
        self.file_watcher = file_watcher

    def on_created(self, event):
        """文件创建事件"""
        if event.is_directory:
            return

        file_path = event.src_path
        logger.info(f"触发创建事件: {file_path}, 是目录: {event.is_directory}")

        if not self.file_watcher.should_watch(file_path):
            logger.info(f"文件不在监控范围内，跳过创建: {file_path}")
            return

        logger.info(f"检测到新文件，添加到处理队列: {file_path}")
        self.file_watcher.add_to_queue(file_path, 'created')

    def on_modified(self, event):
        """文件修改事件"""
        if event.is_directory:
            return

        file_path = event.src_path
        logger.info(f"触发修改事件: {file_path}, 是目录: {event.is_directory}")

        if not self.file_watcher.should_watch(file_path):
            logger.info(f"文件不在监控范围内，跳过修改: {file_path}")
            return

        logger.info(f"检测到文件修改，添加到处理队列: {file_path}")
        self.file_watcher.add_to_queue(file_path, 'modified')

    def on_moved(self, event):
        """文件移动事件"""
        if event.is_directory:
            return

        file_path = event.dest_path
        old_path = event.src_path
        logger.info(f"触发移动事件: {old_path} -> {file_path}, 是目录: {event.is_directory}")

        # 如果旧路径在监控范围内，删除旧记录
        if self.file_watcher.should_watch(old_path):
            logger.info(f"移动的旧文件在监控范围内，删除旧记录: {old_path}")
            self.file_watcher.remove_from_database(old_path)
        else:
            logger.info(f"移动的旧文件不在监控范围内，跳过删除: {old_path}")

        # 如果新路径在监控范围内，添加新文件
        if self.file_watcher.should_watch(file_path):
            logger.info(f"移动的新文件在监控范围内，添加到队列: {file_path}")
            self.file_watcher.add_to_queue(file_path, 'created')
        else:
            logger.info(f"移动的新文件不在监控范围内，跳过添加: {file_path}")

    def on_deleted(self, event):
        """文件删除事件"""
        if event.is_directory:
            return

        file_path = event.src_path
        logger.info(f"触发删除事件: {file_path}, 是目录: {event.is_directory}")

        if not self.file_watcher.should_watch(file_path):
            logger.info(f"文件不在监控范围内，跳过删除: {file_path}")
            return

        logger.info(f"检测到文件删除，准备从数据库删除: {file_path}")
        self.file_watcher.remove_from_database(file_path)


class FileWatcher:
    """
    文件监控器
    实时监控文件变化并自动处理
    """

    def __init__(self, scanner):
        self.scanner = scanner
        self.observer = None
        self.file_queue = {}  # {file_path: event_type}
        self.queue_lock = threading.Lock()
        self.processing = False
        self.batch_timer = None
        self.batch_delay = 2.0  # 批量处理延迟（秒），避免频繁处理

        # 处理跳过路径
        self.skip_paths = [Path(i) for i in SKIP_PATH if i]
        self.ignore_keywords = [i for i in IGNORE_STRINGS if i]
        self.extensions = IMAGE_EXTENSIONS + VIDEO_EXTENSIONS

        logger.info("文件监控器初始化完成")

    def should_watch(self, path):
        """
        判断文件是否需要监控
        """
        if type(path) == str:
            path_str = path
            path = Path(path)
        else:
            path_str = str(path)

        # 检查后缀
        file_ext = path.suffix.lower() if path.suffix else ""
        if file_ext not in self.extensions:
            logger.debug(f"跳过文件（后缀不匹配）: {path_str}, 后缀: {file_ext}")
            return False

        # 检查跳过路径
        skip = any((path.is_relative_to(p) for p in self.skip_paths))
        if skip:
            logger.debug(f"跳过文件（在跳过路径中）: {path_str}")
            return False

        # 检查忽略关键词
        ignore = any((keyword in path_str.lower() for keyword in self.ignore_keywords))
        if ignore:
            logger.debug(f"跳过文件（包含忽略关键词）: {path_str}")
            return False

        # 检查是否在监控路径中
        paths = [Path(i) for i in ASSETS_PATH if i]
        in_assets = any((path.is_relative_to(p) for p in paths))
        if not in_assets:
            logger.debug(f"跳过文件（不在监控路径中）: {path_str}")
            return False

        return True

    def add_to_queue(self, file_path, event_type):
        """
        添加文件到处理队列
        """
        with self.queue_lock:
            self.file_queue[file_path] = event_type
            logger.debug(f"添加文件到队列: {file_path} ({event_type})")

        # 重置批量处理计时器
        if self.batch_timer:
            self.batch_timer.cancel()
        self.batch_timer = threading.Timer(self.batch_delay, self.process_queue)
        self.batch_timer.start()

    def remove_from_database(self, file_path):
        """
        从数据库中删除文件记录
        """
        with DatabaseSession() as session:
            try:
                if file_path.lower().endswith(IMAGE_EXTENSIONS):
                    delete_image_by_path(session, file_path)
                    logger.info(f"从数据库删除图片: {file_path}")
                    self.scanner.total_images = get_image_count(session)
                elif file_path.lower().endswith(VIDEO_EXTENSIONS):
                    delete_video_by_path(session, file_path)
                    logger.info(f"从数据库删除视频: {file_path}")
                    self.scanner.total_videos = get_video_count(session)
                    self.scanner.total_video_frames = get_video_frame_count(session)
            except Exception as e:
                logger.error(f"删除数据库记录失败: {file_path}, 错误: {e}")

    def process_queue(self):
        """
        批量处理队列中的文件
        """
        with self.queue_lock:
            if not self.file_queue:
                return

            files_to_process = self.file_queue.copy()
            self.file_queue.clear()

        if not files_to_process:
            return

        logger.info(f"开始处理 {len(files_to_process)} 个文件变化")
        self.processing = True

        try:
            with DatabaseSession() as session:
                for file_path, event_type in files_to_process.items():
                    if not os.path.exists(file_path):
                        logger.debug(f"文件不存在，跳过: {file_path}")
                        continue

                    try:
                        if file_path.lower().endswith(IMAGE_EXTENSIONS):
                            self.process_image(session, file_path)
                        elif file_path.lower().endswith(VIDEO_EXTENSIONS):
                            self.process_video(session, file_path)
                    except Exception as e:
                        logger.error(f"处理文件失败: {file_path}, 错误: {e}")
        except Exception as e:
            logger.error(f"批量处理文件时发生错误: {e}")
        finally:
            self.processing = False
            logger.info("文件变化处理完成")

    def process_image(self, session, file_path):
        """
        处理图片文件
        """
        modify_time = os.path.getmtime(file_path)
        checksum = None

        try:
            modify_time = datetime.datetime.fromtimestamp(modify_time)
        except Exception as e:
            logger.warning(f"文件修改日期转换失败: {file_path}, 错误: {e}")
            modify_time = datetime.datetime.now()
            checksum = get_file_hash(file_path)

        # 如果checksum为None，则使用空字符串
        if checksum is None:
            checksum = ""

        # 使用批量处理
        path_list, features_list = process_images([file_path])
        if not path_list or features_list is None:
            return

        for path, features in zip(path_list, features_list):
            features = features.tobytes()
            from app.models.database import add_image
            add_image(session, path, modify_time, checksum, features)
            logger.info(f"添加/更新图片到数据库: {path}")

        self.scanner.total_images = get_image_count(session)

    def process_video(self, session, file_path):
        """
        处理视频文件
        """
        modify_time = os.path.getmtime(file_path)
        checksum = None

        try:
            modify_time = datetime.datetime.fromtimestamp(modify_time)
        except Exception as e:
            logger.warning(f"文件修改日期转换失败: {file_path}, 错误: {e}")
            modify_time = datetime.datetime.now()
            checksum = get_file_hash(file_path)

        # 如果checksum为None，则使用空字符串
        if checksum is None:
            checksum = ""

        from app.models.database import add_video
        add_video(session, file_path, modify_time, checksum, process_video(file_path))
        logger.info(f"添加/更新视频到数据库: {file_path}")

        self.scanner.total_videos = get_video_count(session)
        self.scanner.total_video_frames = get_video_frame_count(session)

    def start(self):
        """
        启动文件监控
        """
        from watchdog.observers import Observer

        if self.observer and self.observer.is_alive():
            logger.warning("文件监控已经在运行")
            return

        logger.info(f"准备启动文件监控，监控路径: {ASSETS_PATH}")

        self.observer = Observer()
        event_handler = FileWatchEventHandler(self)

        # 为每个监控路径添加观察者
        paths_to_watch = []
        for path in ASSETS_PATH:
            if os.path.exists(path):
                paths_to_watch.append(path)
                try:
                    self.observer.schedule(event_handler, path, recursive=True)
                    logger.info(f"成功添加监控目录: {path}")
                except Exception as e:
                    logger.error(f"添加监控目录失败: {path}, 错误: {e}")
            else:
                logger.warning(f"监控路径不存在: {path}")

        if not paths_to_watch:
            logger.error("没有可监控的路径，监控器未启动")
            return

        try:
            self.observer.start()
            logger.info(f"文件监控已成功启动，正在监控 {len(paths_to_watch)} 个目录")
            logger.info(f"监控状态: alive={self.observer.is_alive()}, event_handler={event_handler}")
        except Exception as e:
            logger.error(f"启动文件监控失败: {e}")
            self.observer = None
            raise

    def stop(self):
        """
        停止文件监控
        """
        if self.batch_timer:
            self.batch_timer.cancel()
            self.batch_timer = None

        if self.observer:
            # 处理剩余队列中的文件
            self.process_queue()

            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("文件监控已停止")

    def is_running(self):
        """
        检查文件监控是否在运行
        """
        return self.observer is not None and self.observer.is_alive()
