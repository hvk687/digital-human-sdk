"""
Digital Human SDK - Digital Human Synthesis Thread
"""
import threading
import numpy as np
from typing import Optional

from ..models import Task
from ..tts import CosyVoiceClient
from ..video import VideoModel


class DigitalHumanSynthesisThread(threading.Thread):
    """数字人合成线程"""
    
    def __init__(self, task: Task, video_model: VideoModel, 
                 tts_host: str = 'localhost', tts_port: int = 8998, tts_mode: str = 'sft'):
        super().__init__()
        self.task = task
        self.video_model = video_model
        self.stop_event = threading.Event()
        
        # 初始化TTS客户端
        self.cosyvoice_client = CosyVoiceClient(
            host=tts_host,
            port=tts_port,
            mode=tts_mode
        )
        
        print(f"数字人合成线程初始化完成，任务ID: {task.task_id}")

    def run(self):
        """线程主循环"""
        try:
            print(f"数字人合成线程开始处理任务 {self.task.task_id}")
            
            while not self.stop_event.is_set():
                try:
                    # 从LLM响应队列获取文本
                    data = self.task.llm_response_queue.get(timeout=1.0)
                    
                    if data == "DONE":
                        print("LLM响应完成，数字人合成线程结束")
                        break
                        
                    if data.startswith("ERROR:"):
                        print(f"LLM响应错误: {data[7:]}")
                        continue

                    print(f"开始处理文本: {data}")
                    
                    # 执行TTS合成
                    audio, features = self._do_tts(data)
                    if audio is None or features is None:
                        continue
                    
                    # 设置音频特征到视频模型
                    self.video_model.set_audio_features(features)

                    # 处理音频和生成视频帧
                    self._process_audio_and_generate_frames(audio)
                    
                except Exception as e:
                    if not self.stop_event.is_set():
                        print(f"处理过程中出现异常: {e}")
                    break

            # 发送结束标记
            self.task.llm_response_audio_chunk_queue.put(None)
            self.task.llm_virtual_image_queue.put(None)
            print(f"数字人合成线程完成，任务ID: {self.task.task_id}")
            
        except Exception as e:
            print(f"数字人合成线程异常: {e}")
            # 发送错误标记
            self.task.llm_response_audio_chunk_queue.put(None)
            self.task.llm_virtual_image_queue.put(None)

    def _do_tts(self, text: str) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """执行TTS合成"""
        try:
            # 调用TTS服务
            audio_data, raw_features = self.cosyvoice_client.inference("100", tts_text=text)
            
            # 转换音频数据
            audio_array = np.frombuffer(audio_data, dtype=np.float32)
            
            # 转换特征数据
            features = np.frombuffer(raw_features, dtype=np.float32).reshape(-1, 2, 1024)
            
            print(f"TTS合成完成，音频长度: {len(audio_array)}, 特征形状: {features.shape}")
            return audio_array, features
            
        except Exception as e:
            print(f"TTS合成失败: {e}")
            return None, None

    def _process_audio_and_generate_frames(self, audio: np.ndarray):
        """处理音频并生成视频帧"""
        try:
            # 确保音频长度为偶数（如果需要）
            if len(audio) % 2 == 1:
                audio = audio[:-1]
            
            # 分块处理音频
            total_frames = len(audio)
            chunk_size = 640  # 音频块大小
            num_chunks = total_frames // chunk_size

            for i in range(num_chunks):
                if self.stop_event.is_set():
                    break

                # 提取音频块
                start = i * chunk_size
                end = start + chunk_size
                chunk = audio[start:end]
                
                # 将音频块放入队列
                self.task.llm_response_audio_chunk_queue.put(chunk)

                try:
                    # 生成对应的视频帧
                    img_idx = i % self.video_model.len_img
                    img = self.video_model.process_frame(img_idx, i)
                    
                    if img is not None:
                        self.task.llm_virtual_image_queue.put(img)
                        
                except Exception as e:
                    print(f"视频帧生成异常: {e}")

            # 处理剩余的音频数据
            if total_frames % chunk_size > 0:
                remaining_chunk = audio[num_chunks * chunk_size:]
                if remaining_chunk.size > 0:
                    self.task.llm_response_audio_chunk_queue.put(remaining_chunk)
                    
        except Exception as e:
            print(f"音频处理和帧生成异常: {e}")

    def stop(self):
        """停止线程"""
        self.stop_event.set()
        print(f"数字人合成线程停止信号已发送，任务ID: {self.task.task_id}")

    def __del__(self):
        """析构函数"""
        if hasattr(self, 'cosyvoice_client'):
            self.cosyvoice_client.close()