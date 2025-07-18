"""
Digital Human SDK - Data Models
"""
import queue
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class TaskStatus(Enum):
    """任务状态枚举"""
    CREATED = 0
    RUNNING = 1
    FINISHED = 2
    FAILED = 3
    IDLE = 4



class Task:
    """任务类"""
    def __init__(self, task_id: int, question: str):
        self.task_id = task_id
        self.question = question
        self.llm_response_queue = queue.Queue()
        self.llm_virtual_image_queue = queue.Queue()
        self.llm_response_audio_chunk_queue = queue.Queue()
        self.status = TaskStatus.CREATED
        
    def set_status(self, status: TaskStatus):
        """设置任务状态"""
        self.status = status
        
    def start_task(self):
        """开始任务"""
        self.set_status(TaskStatus.RUNNING)
        
    def end_task(self, success: bool = True):
        """结束任务"""
        self.set_status(TaskStatus.FINISHED if success else TaskStatus.FAILED)
        
    def set_idle(self):
        """设置为IDLE状态"""
        self.set_status(TaskStatus.IDLE)


@dataclass
class FrameData:
    """帧数据"""
    image: Optional[object] = None  # numpy array
    audio_chunk: Optional[object] = None  # numpy array
    frame_index: int = 0
    is_idle: bool = False


@dataclass
class TaskResult:
    """任务结果"""
    task_id: int
    success: bool
    error_message: Optional[str] = None
    total_frames: int = 0
    duration: float = 0.0