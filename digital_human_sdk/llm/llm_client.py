"""
Digital Human SDK - LLM Client
"""
import requests
import json
import time
import queue
import threading
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict, Any

from ..models import Task, TaskStatus


class LLMChatClient:
    """LLM聊天客户端"""
    
    def __init__(self, server_url: str = "http://127.0.0.1:8080/v1/chat/completions", 
                 headers: Optional[Dict[str, str]] = None, 
                 timeout: float = 60.0, 
                 retries: int = 3, 
                 chunk_size: int = 10,
                 model_name: str = "qwen2.5-7b"):
        self.server_url = server_url
        self.headers = headers or {}
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.model_name = model_name
        self.current_task: Optional[Task] = None
        
        # 标点符号集合，用于分割响应
        self.punctuation_set = {
            '，', '。', '！', '？', '；', ',', '.', '!', '?', ';', ':', '：', '"', ''', '"', "'"
        }

        # 初始化HTTP会话
        self.session = requests.Session()
        retry_strategy = Retry(
            total=retries,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
        self.session.mount('http://', HTTPAdapter(max_retries=retry_strategy))
        self.session.mount('https://', HTTPAdapter(max_retries=retry_strategy))
        
        # 调试：验证 TaskStatus 枚举
        print(f"[LLM客户端初始化] TaskStatus 枚举值: {[status.name for status in TaskStatus]}")
        print(f"[LLM客户端初始化] IDLE 状态值: {TaskStatus.IDLE}")
        print(f"[LLM客户端初始化] IDLE 状态名: {TaskStatus.IDLE.name}")

    def receive_task(self, task: Task) -> bool:
        """接收新任务"""
        print(f"[LLM客户端] 尝试接收任务 {task.task_id}")
        
        if self.current_task:
            print(f"[LLM客户端] 当前任务 {self.current_task.task_id} 状态: {self.current_task.status}")
        else:
            print(f"[LLM客户端] 当前没有任务")
            
        # 详细调试：检查状态比较
        allowed_statuses = (TaskStatus.FINISHED, TaskStatus.FAILED, TaskStatus.IDLE)
        print(f"[LLM客户端] 允许的状态: {[s.name for s in allowed_statuses]}")
        print(f"[LLM客户端] 当前状态: {self.current_task.status.name if self.current_task else 'None'}")
        print(f"[LLM客户端] 状态检查: {self.current_task.status in allowed_statuses if self.current_task else 'N/A'}")
        
        if self.current_task and self.current_task.status not in allowed_statuses:
            print(f"[LLM客户端] 拒绝任务 {task.task_id}，当前任务状态不允许: {self.current_task.status}")
            return False
            
        print(f"[LLM客户端] 接受任务 {task.task_id}")
        self.current_task = task
        self.current_task.start_task()
        self._send_request()
        return True

    def _send_request(self):
        """发送LLM请求"""
        headers = {"Content-Type": "application/json", **self.headers}
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "你是一个知识助手。"},
                {"role": "user", "content": self.current_task.question}
            ],
            "temperature": 0.7,
            "max_tokens": 512,
            "stream": True
        }

        # 在单独线程中处理流式响应
        receive_thread = threading.Thread(
            target=self._receive_stream,
            args=(headers, payload),
            daemon=True
        )
        receive_thread.start()

    def _receive_stream(self, headers: Dict[str, str], payload: Dict[str, Any]):
        """接收流式响应"""
        buffer = ""
        try:
            with self.session.post(self.server_url, headers=headers, json=payload,
                                   stream=True, timeout=self.timeout) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:].strip()
                            if data == '[DONE]':
                                if buffer:
                                    self.current_task.llm_response_queue.put(buffer)
                                break

                            try:
                                chunk = json.loads(data)
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    buffer += content
                                    last_punct_idx = -1
                                    for i, char in enumerate(reversed(buffer)):
                                        if char in self.punctuation_set:
                                            last_punct_idx = len(buffer) - i - 1
                                            break

                                    if last_punct_idx >= 0 and len(buffer[:last_punct_idx + 1]) > self.chunk_size:
                                        text_to_queue = buffer[:last_punct_idx + 1]
                                        buffer = buffer[last_punct_idx + 1:]
                                        print(f"put data {text_to_queue} to queue")
                                        self.current_task.llm_response_queue.put(text_to_queue)
                                        
                            except json.JSONDecodeError as e:
                                error_msg = f"ERROR: JSON 解析错误 - {str(e)}"
                                self.current_task.llm_response_queue.put(error_msg)
                                
        except Exception as e:
            error_msg = f"ERROR: 请求异常 - {str(e)}"
            self.current_task.llm_response_queue.put(error_msg)
            if self.current_task:
                self.current_task.end_task(success=False)
        finally:
            if self.current_task:
                self.current_task.llm_response_queue.put("DONE")

    def shutdown(self):
        """关闭客户端"""
        if self.session:
            self.session.close()
        print("LLM客户端已关闭")