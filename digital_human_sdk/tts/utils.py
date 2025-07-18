"""
Digital Human SDK - TTS Utilities
"""
import torchaudio
import torch
from typing import Tuple


def load_wav(wav_path: str, target_sr: int) -> torch.Tensor:
    """加载音频文件并重采样"""
    try:
        speech, sample_rate = torchaudio.load(wav_path, backend='soundfile')
        speech = speech.mean(dim=0, keepdim=True)
        
        if sample_rate != target_sr:
            if sample_rate <= target_sr:
                raise ValueError(f'音频采样率 {sample_rate} 必须大于目标采样率 {target_sr}')
            speech = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=target_sr)(speech)
        
        return speech
        
    except Exception as e:
        print(f"加载音频文件失败 {wav_path}: {e}")
        raise


def validate_audio_format(audio_data: bytes) -> bool:
    """验证音频数据格式"""
    try:
        # 基本的音频数据验证
        if not audio_data or len(audio_data) == 0:
            return False
        
        # 检查是否是合理的音频数据长度
        if len(audio_data) < 1024:  # 至少1KB
            return False
            
        return True
        
    except Exception:
        return False


def audio_bytes_to_numpy(audio_bytes: bytes, dtype=None) -> torch.Tensor:
    """将音频字节数据转换为numpy数组"""
    import numpy as np
    
    if dtype is None:
        dtype = np.float32
    
    try:
        audio_array = np.frombuffer(audio_bytes, dtype=dtype)
        return torch.from_numpy(audio_array)
    except Exception as e:
        print(f"音频数据转换失败: {e}")
        raise