"""
Digital Human SDK - Digital Human Synthesis Thread
"""
import threading
import numpy as np
from ..tts.cosyvoice_client import CosyVoiceClient


class DigitalHumanSynthesisThread(threading.Thread):
    """数字人合成线程"""
    
    def __init__(self, task, model, tts_config=None):
        super().__init__()
        self.task = task
        self.model = model
        self.stop_event = threading.Event()
        
        # 初始化TTS客户端 - 使用工作的默认配置
        if tts_config:
            self.cosyvoice_grpc_client = CosyVoiceClient(
                host=tts_config.get('host', 'localhost'),
                port=tts_config.get('port', 8998),
                mode=tts_config.get('mode', 'zero_shot')  # 使用原来工作的默认模式
            )
        else:
            # 使用原来工作的默认配置
            self.cosyvoice_grpc_client = CosyVoiceClient()

    def run(self):
        """运行数字人合成"""
        try:
            while True:
                if self.stop_event.is_set():
                    break
                    
                data = self.task.llm_response_queue.get()
                print(f"begin to process : {data} and call hubert")
                if data == "DONE":
                    break
                if data.startswith("ERROR:"):
                    print(f"\n{data[7:]}")
                    continue

                audio, features = self.do_tts(data)
                self.model.set_audio_features(features)

                total_frames = len(audio)
                num_chunks = total_frames // 640

                for i in range(num_chunks):
                    if self.stop_event.is_set():
                        break

                    start = i * 640
                    end = start + 640
                    chunk = audio[start:end]
                    self.task.llm_response_audio_chunk_queue.put(chunk)

                    try:
                        img = self.model.process_frame(i % self.model.len_img, i)
                        if img is not None:
                            self.task.llm_virtual_image_queue.put(img)
                    except Exception as e:
                        print("模型异常:", e)

                if total_frames % 640 > 0:
                    chunk = audio[num_chunks * 640:]
                    if chunk.size > 0:
                        self.task.llm_response_audio_chunk_queue.put(chunk)

            # 合成完成后，向队列添加结束标记
            self.task.llm_response_audio_chunk_queue.put(None)
            self.task.llm_virtual_image_queue.put(None)
            print("数字人合成线程完成")
        except Exception as e:
            print(f"数字人合成线程异常: {e}")
            # 向队列添加错误标记
            self.task.llm_response_audio_chunk_queue.put(None)
            self.task.llm_virtual_image_queue.put(None)

    def do_tts(self, text, max_retries=3):
        """执行TTS合成，带重试机制"""
        for attempt in range(max_retries):
            try:
                print(f"TTS合成尝试 {attempt + 1}/{max_retries}: {text[:50]}...")
                
                audio_data, raw_features = self.cosyvoice_grpc_client.inference("100", tts_text=text)
                
                if not audio_data or not raw_features:
                    raise Exception("TTS返回空数据")
                
                audio_array = np.frombuffer(audio_data, dtype=np.float32)
                features = np.frombuffer(raw_features, dtype=np.float32).reshape(-1, 2, 1024)
                
                print(f"TTS合成成功: 音频长度={len(audio_array)}, 特征形状={features.shape}")
                return audio_array, features
                
            except Exception as e:
                print(f"TTS合成失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                
                if attempt == max_retries - 1:
                    # 最后一次尝试失败，抛出异常
                    raise Exception(f"TTS合成失败，已重试{max_retries}次: {str(e)}")
                
                # 等待一段时间后重试
                import time
                time.sleep(1.0 * (attempt + 1))  # 递增等待时间
                
        return None, None

    def stop(self):
        """停止合成线程"""
        self.stop_event.set()