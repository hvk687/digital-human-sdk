"""
Digital Human SDK - Audio Player Thread
"""
import threading
import pyaudio


class AudioPlayerThread(threading.Thread):
    """音频播放线程"""
    
    def __init__(self, task, sampling_rate=16000):
        super().__init__()
        self.task = task
        self.sampling_rate = sampling_rate
        self.stop_event = threading.Event()
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.sampling_rate,
            output=True
        )

    def run(self):
        """运行音频播放"""
        try:
            while True:
                if self.stop_event.is_set():
                    break
                chunk = self.task.llm_response_audio_chunk_queue.get()
                if chunk is None:
                    break
                self.stream.write(chunk.tobytes())
        except Exception as e:
            print(f"音频播放异常: {e}")
        finally:
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()

    def stop(self):
        """停止音频播放"""
        self.stop_event.set()