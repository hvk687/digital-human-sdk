"""
Digital Human SDK - Unified Configuration
"""
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class DigitalHumanConfig:
    """统一的数字人SDK配置类"""
    # 模型路径配置
    checkpoint_path: str = "./digital_human_sdk/assets/weight/trained.pth"
    dataset_path: str = "./digital_human_sdk/assets/data"
    
    # 音频配置
    asr_type: str = "hubert"  # hubert 或 wenet
    speaker_id: str = "100"
    hubert_sampling_rate: int = 16000
    
    # LLM配置
    llm_server_url: str = "http://127.0.0.1:8080/v1/chat/completions"
    llm_response_chunk_size: int = 15
    llm_model_name: str = "qwen2.5-7b"
    
    # TTS配置
    tts_server_host: str = "localhost"
    tts_server_port: int = 8998
    tts_mode: str = "zero_shot"  # sft, zero_shot, cross_lingual, instruct
    
    # 视频配置
    video_fps: int = 25
    idle_image_count: int = 10  # IDLE模式循环的图片数量
    
    # 兼容属性 - 为了向后兼容
    @property
    def checkpoint(self):
        """兼容原有的checkpoint属性"""
        return Path(self.checkpoint_path)
    
    @property
    def dataset(self):
        """兼容原有的dataset属性"""
        return Path(self.dataset_path)
    
    @property
    def asr(self):
        """兼容原有的asr属性"""
        return self.asr_type
    
    @property
    def llm_server(self):
        """兼容原有的llm_server属性"""
        return self.llm_server_url
    
    @property
    def llm_response_chunck_size(self):
        """兼容原有的拼写错误属性"""
        return self.llm_response_chunk_size
    
    @property
    def base_dir(self):
        """兼容原有的base_dir属性"""
        return Path("./digital_human_sdk/assets")
    
    def validate(self) -> bool:
        """验证配置是否有效"""
        try:
            # 检查必要的路径
            if not Path(self.checkpoint_path).exists():
                print(f"警告: 模型文件不存在: {self.checkpoint_path}")
                return False
                
            if not Path(self.dataset_path).exists():
                print(f"警告: 数据集路径不存在: {self.dataset_path}")
                return False
            
            # 检查数值范围
            if self.video_fps <= 0 or self.video_fps > 60:
                print(f"错误: 视频帧率无效: {self.video_fps}")
                return False
                
            if self.hubert_sampling_rate <= 0:
                print(f"错误: 采样率无效: {self.hubert_sampling_rate}")
                return False
                
            return True
            
        except Exception as e:
            print(f"配置验证失败: {e}")
            return False


# 为了完全向后兼容，保留Config类作为DigitalHumanConfig的别名
Config = DigitalHumanConfig