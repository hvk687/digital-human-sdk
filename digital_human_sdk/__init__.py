"""
Digital Human SDK - 实时数字人合成SDK
"""
from .core import DigitalHumanEngine
from .models import Task, TaskStatus, FrameData, TaskResult
from .callbacks import DigitalHumanCallback
from .config import DigitalHumanConfig, Config
from .llm import LLMChatClient
from .tts import CosyVoiceClient
from .threads import DigitalHumanSynthesisThread, AudioPlayerThread

__version__ = "1.0.0"
__author__ = "Digital Human Team"
__description__ = "实时数字人合成SDK - 支持语音合成、唇形同步和视频生成"

__all__ = [
    # 核心组件
    "DigitalHumanEngine",
    
    # 数据模型和配置 - 统一使用DigitalHumanConfig
    "Task", "TaskStatus", "DigitalHumanConfig", "FrameData", "TaskResult",
    
    # 向后兼容
    "Config",  # Config现在是DigitalHumanConfig的别名
    
    # 回调接口
    "DigitalHumanCallback",
    
    # 子模块
    "LLMChatClient",
    "CosyVoiceClient", 
    "DigitalHumanSynthesisThread",
    "AudioPlayerThread"
]