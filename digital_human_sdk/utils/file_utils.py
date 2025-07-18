"""
Digital Human SDK - File Utilities
"""
import json
import torchaudio
import logging
from pathlib import Path


def load_wav(wav_path, target_sr):
    """加载音频文件并重采样到目标采样率"""
    speech, sample_rate = torchaudio.load(wav_path, backend='soundfile')
    speech = speech.mean(dim=0, keepdim=True)
    if sample_rate != target_sr:
        assert sample_rate > target_sr, f'wav sample rate {sample_rate} must be greater than {target_sr}'
        speech = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=target_sr)(speech)
    return speech


def read_lists(list_file):
    """读取列表文件"""
    lists = []
    with open(list_file, 'r', encoding='utf8') as fin:
        for line in fin:
            lists.append(line.strip())
    return lists


def read_json_lists(list_file):
    """读取JSON列表文件"""
    lists = read_lists(list_file)
    results = {}
    for fn in lists:
        with open(fn, 'r', encoding='utf8') as fin:
            results.update(json.load(fin))
    return results


def ensure_dir(path):
    """确保目录存在"""
    Path(path).mkdir(parents=True, exist_ok=True)


def validate_file_exists(file_path):
    """验证文件是否存在"""
    return Path(file_path).exists()