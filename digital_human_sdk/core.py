"""
Digital Human SDK - Core Engine
"""
import threading
import time
import os
import cv2
import numpy as np
from typing import Optional, List
from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSignal

from .models import Task, TaskStatus, FrameData, TaskResult
from .callbacks import DigitalHumanCallback

# 导入SDK内部模块
from .llm.llm_chat_client import LLMChatClient
from .threads.digital_human_synthesis_thread import DigitalHumanSynthesisThread
from .threads.audio_player_thread import AudioPlayerThread
from .video.video_model import VideoModel
from .config.config import Config


class DigitalHumanEngine(QObject):
    """数字人引擎 - SDK的核心类"""
    
    # Qt信号（用于线程间通信）
    frame_ready = pyqtSignal(object, object)  # task, frame_data
    idle_frame_ready = pyqtSignal(object)     # frame_data
    task_status_changed = pyqtSignal(object, object, object)  # task, old_status, new_status
    
    def __init__(self, config: Config, callback: DigitalHumanCallback):
        super().__init__()
        self.config = config
        self.callback = callback
        
        # 初始化组件
        self._init_components()
        
        # 状态管理
        self.current_task: Optional[Task] = None
        self.task_counter = 0
        self.is_idle = True
        self.idle_frame_index = 0
        
        # 添加任务提交锁，防止快速点击导致多个任务同时提交
        self._submitting_task = False
        
        # 线程管理
        self.digital_human_thread: Optional[DigitalHumanSynthesisThread] = None
        self.audio_player_thread: Optional[AudioPlayerThread] = None
        self.frame_timer: Optional[QTimer] = None
        self.idle_timer: Optional[QTimer] = None
        self.queue_check_timer: Optional[QTimer] = None
        
        # 连接信号
        self._connect_signals()
        
        # 启动IDLE模式
        self.start_idle_mode()
    
    def _init_components(self):
        """初始化各个组件"""
        try:
            # 初始化LLM客户端
            self.llm_client = LLMChatClient(
                server_url=self.config.llm_server_url,
                n=self.config.llm_response_chunk_size
            )
            
            # 初始化视频模型
            self.video_model = VideoModel(config=self.config)
            
            print("数字人引擎初始化成功")
        except Exception as e:
            error_msg = f"数字人引擎初始化失败: {str(e)}"
            print(error_msg)
            self.callback.on_error(None, error_msg)

    def _connect_signals(self):
        """连接Qt信号到回调函数"""
        self.frame_ready.connect(self._on_frame_ready)
        self.idle_frame_ready.connect(self._on_idle_frame_ready)
        self.task_status_changed.connect(self._on_task_status_changed)
    
    def submit_question(self, question: str) -> bool:
        """提交问题给数字人处理"""
        if not question.strip():
            return False
        
        # 防止快速点击：检查是否正在提交任务
        if self._submitting_task:
            print("正在提交任务中，请稍候...")
            return False
            
        # 检查是否可以接收新任务
        if self.current_task and self.current_task.status not in (
            TaskStatus.FINISHED, TaskStatus.FAILED, TaskStatus.IDLE
        ):
            print(f"当前任务状态 {self.current_task.status} 不允许提交新任务")
            return False

        # 设置提交锁，防止重复提交
        self._submitting_task = True
        
        try:
            # 创建新任务
            self.task_counter += 1
            task = Task(self.task_counter, question)
            
            # 提交给LLM客户端
            if not self.llm_client.receive_task(task):
                print("LLM客户端拒绝了任务")
                return False
            
            # 重要：使用LLM客户端的任务对象，确保引用一致
            old_status = self.current_task.status if self.current_task else None
            self.current_task = self.llm_client.current_task
            
            # 重置帧计数器（每个新任务重新开始计数）
            self._frame_counter = 0
            
            # 发出状态变更信号
            self.task_status_changed.emit(self.current_task, old_status, TaskStatus.RUNNING)
            
            # 启动处理线程
            self._start_task_processing(self.current_task)
            
            print(f"任务 {self.current_task.task_id} 提交成功")
            return True
            
        except Exception as e:
            print(f"任务提交失败: {e}")
            # 如果提交失败，需要清理状态
            self._cleanup_failed_task()
            return False
        finally:
            # 无论成功失败，都要释放提交锁
            self._submitting_task = False
    
    def _start_task_processing(self, task: Task):
        """启动任务处理"""
        try:
            # 启动数字人合成线程
            self.digital_human_thread = DigitalHumanSynthesisThread(task, self.video_model)
            self.digital_human_thread.start()
            
            # 启动音频播放线程
            self.audio_player_thread = AudioPlayerThread(task)
            self.audio_player_thread.start()
            
            # 启动帧处理定时器
            self._start_frame_timer(task)
            
            # 启动队列检查定时器
            self._start_queue_check_timer()
            
            print(f"任务 {task.task_id} 开始处理")
            
        except Exception as e:
            error_msg = f"启动任务处理失败: {str(e)}"
            print(error_msg)
            self.callback.on_error(task, error_msg)
    
    def _start_frame_timer(self, task: Task):
        """启动帧处理定时器 - 使用高精度定时器确保音视频同步"""
        self.frame_timer = QTimer()
        # 设置为高精度定时器，这对音视频同步至关重要
        self.frame_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.frame_timer.timeout.connect(lambda: self._process_frame(task))
        frame_interval = 1000 // self.config.video_fps  # 转换为毫秒
        self.frame_timer.start(frame_interval)
        print(f"启动高精度帧定时器，间隔: {frame_interval}ms ({self.config.video_fps}fps)")
    
    def _process_frame(self, task: Task):
        """处理视频帧"""
        try:
            # 尝试从队列获取图像
            img = task.llm_virtual_image_queue.get(timeout=0.01)
            if img is not None:
                # 如果这是第一帧，停止IDLE模式
                if self.is_idle:
                    self.stop_idle_mode()
                
                # 创建帧数据
                frame_data = FrameData(
                    image=img,
                    frame_index=getattr(self, '_frame_counter', 0),
                    is_idle=False
                )
                
                # 发出帧就绪信号
                self.frame_ready.emit(task, frame_data)
                
                # 更新帧计数器
                self._frame_counter = getattr(self, '_frame_counter', 0) + 1
                
        except Exception:
            # 队列为空或其他异常，继续等待
            pass
    
    def start_idle_mode(self):
        """启动IDLE模式"""
        if self.idle_timer and self.idle_timer.isActive():
            self.idle_timer.stop()
        
        self.is_idle = True
        self.idle_frame_index = 0
        
        # 创建IDLE定时器 - 使用高精度定时器
        self.idle_timer = QTimer()
        self.idle_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.idle_timer.timeout.connect(self._process_idle_frame)
        frame_interval = 1000 // self.config.video_fps
        self.idle_timer.start(frame_interval)
        
        print("进入IDLE模式")
    
    def stop_idle_mode(self):
        """停止IDLE模式"""
        if self.idle_timer and self.idle_timer.isActive():
            self.idle_timer.stop()
        
        self.is_idle = False
        print("停止IDLE模式")
    
    def _process_idle_frame(self):
        """处理IDLE帧"""
        try:
            # 构建图片路径
            img_dir = os.path.join(self.config.dataset_path, "full_body_img")
            image_path = os.path.join(img_dir, f"{self.idle_frame_index}.jpg")
            
            if os.path.exists(image_path):
                idle_image = cv2.imread(image_path)
                if idle_image is not None:
                    frame_data = FrameData(
                        image=idle_image,
                        frame_index=self.idle_frame_index,
                        is_idle=True
                    )
                    
                    # 发出IDLE帧就绪信号
                    self.idle_frame_ready.emit(frame_data)
            
            # 循环索引
            self.idle_frame_index = (self.idle_frame_index + 1) % self.config.idle_image_count
            
        except Exception as e:
            print(f"处理IDLE帧时出错: {e}")
    
    def _start_queue_check_timer(self):
        """启动队列检查定时器"""
        self.queue_check_timer = QTimer()
        self.queue_check_timer.timeout.connect(self._check_task_completion)
        self.queue_check_timer.start(500)  # 每500ms检查一次
    
    def _check_task_completion(self):
        """检查任务完成状态"""
        if not self.current_task or self.current_task.status != TaskStatus.RUNNING:
            return
        
        # 检查线程是否完成
        digital_finished = not self.digital_human_thread or not self.digital_human_thread.is_alive()
        audio_finished = not self.audio_player_thread or not self.audio_player_thread.is_alive()
        
        if digital_finished and audio_finished:
            print("数字人合成和音频播放线程已完成，等待视频帧播放完成...")
            # 采用与原版app_main.py相同的逻辑：等待1秒后直接完成任务
            # 这1秒足够让剩余的帧播放完成
            QTimer.singleShot(1000, self._complete_current_task)
    
    def _cleanup_failed_task(self):
        """清理失败的任务状态"""
        # 停止可能已启动的定时器
        if self.frame_timer and self.frame_timer.isActive():
            self.frame_timer.stop()
        if self.queue_check_timer and self.queue_check_timer.isActive():
            self.queue_check_timer.stop()
        
        # 停止可能已启动的线程
        if self.digital_human_thread and self.digital_human_thread.is_alive():
            self.digital_human_thread.stop()
        if self.audio_player_thread and self.audio_player_thread.is_alive():
            self.audio_player_thread.stop()
        
        # 重置状态
        self._frame_counter = 0
        
        # 如果不在IDLE模式，重新进入IDLE模式
        if not self.is_idle:
            self.start_idle_mode()
    
    def _complete_current_task(self):
        """完成当前任务"""
        if not self.current_task:
            return
        
        # 停止相关定时器
        if self.frame_timer:
            self.frame_timer.stop()
        if self.queue_check_timer:
            self.queue_check_timer.stop()
        
        # 更新任务状态
        old_status = self.current_task.status
        self.current_task.end_task(success=True)
        
        # 创建任务结果
        result = TaskResult(
            task_id=self.current_task.task_id,
            success=True,
            total_frames=self._frame_counter  # 直接使用，因为已经在submit_question中初始化
        )
        
        # 发出完成信号
        self.callback.on_task_completed(result)
        
        # 发出状态变更信号
        self.task_status_changed.emit(self.current_task, old_status, TaskStatus.FINISHED)
        
        # 重新进入IDLE模式
        self.current_task.set_idle()
        self.start_idle_mode()
        
        print(f"任务 {result.task_id} 完成")
    
    def _on_frame_ready(self, task: Task, frame_data: FrameData):
        """帧就绪回调"""
        self.callback.on_frame_ready(task, frame_data)
    
    def _on_idle_frame_ready(self, frame_data: FrameData):
        """IDLE帧就绪回调"""
        self.callback.on_idle_frame_ready(frame_data)
    
    def _on_task_status_changed(self, task: Task, old_status: TaskStatus, new_status: TaskStatus):
        """任务状态变更回调"""
        self.callback.on_task_status_changed(task, old_status, new_status)
    
    def shutdown(self):
        """关闭引擎"""
        # 停止所有定时器
        if self.frame_timer:
            self.frame_timer.stop()
        if self.idle_timer:
            self.idle_timer.stop()
        if self.queue_check_timer:
            self.queue_check_timer.stop()
        
        # 停止所有线程
        if self.digital_human_thread and self.digital_human_thread.is_alive():
            self.digital_human_thread.stop()
        if self.audio_player_thread and self.audio_player_thread.is_alive():
            self.audio_player_thread.stop()
        
        print("数字人引擎已关闭")