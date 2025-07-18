"""
Digital Human SDK - Callback Interface
"""
from abc import ABC, abstractmethod
from typing import Optional
from .models import Task, TaskStatus, FrameData, TaskResult


class DigitalHumanCallback(ABC):
    """数字人回调接口 - 第三方需要实现这个接口来接收事件"""
    
    @abstractmethod
    def on_task_status_changed(self, task: Task, old_status: TaskStatus, new_status: TaskStatus):
        """任务状态改变时的回调"""
        pass
    
    @abstractmethod
    def on_frame_ready(self, task: Task, frame_data: FrameData):
        """新帧准备就绪时的回调"""
        pass
    
    @abstractmethod
    def on_idle_frame_ready(self, frame_data: FrameData):
        """IDLE模式帧准备就绪时的回调"""
        pass
    
    @abstractmethod
    def on_task_completed(self, result: TaskResult):
        """任务完成时的回调"""
        pass
    
    @abstractmethod
    def on_error(self, task: Optional[Task], error_message: str):
        """错误发生时的回调"""
        pass
    
    @abstractmethod
    def on_llm_response_chunk(self, task: Task, text_chunk: str):
        """LLM响应文本块时的回调（可选，用于实时显示文本）"""
        pass