# Digital Human SDK

一个强大的实时数字人合成SDK，支持语音合成、唇形同步和视频生成。

## 🎯 特性

- **实时处理**: 支持实时语音合成和视频生成
- **IDLE模式**: 智能待机状态，循环播放预设图片
- **UI分离**: 核心功能与UI完全分离，支持多种前端
- **插件化**: 基于回调机制，易于集成和扩展
- **多平台**: 支持桌面应用、Web API、控制台等多种使用方式
- **高性能**: 多线程处理，GPU加速推理，高精度定时器确保音视频同步
- **统一配置**: 使用 `DigitalHumanConfig` 统一管理所有配置参数
- **完整示例**: 提供PyQt5、Web API、控制台等多种使用示例

## 🚀 快速开始

### 安装

#### 从源码安装

```bash
# 1. 克隆项目
git clone <repository-url>
cd digital_human_sdk

# 2. 安装
pip install -r requirements.txt
```

#### 运行示例

```bash
# 运行完整SDK示例（推荐）
python examples/sdk_example.py

```

> 注意：当前版本为开发版本，暂未发布到PyPI。请直接从源码安装使用。

### 基本使用

```python
from digital_human_sdk import DigitalHumanEngine, DigitalHumanConfig, DigitalHumanCallback
from digital_human_sdk.models import Task, TaskStatus, FrameData, TaskResult

# 1. 创建配置
config = DigitalHumanConfig(
    checkpoint_path="./assets/weight/trained.pth",
    dataset_path="./assets/data",
    llm_server_url="http://127.0.0.1:8080/v1/chat/completions"
)

# 2. 实现回调接口
class MyCallback(DigitalHumanCallback):
    def on_frame_ready(self, task: Task, frame_data: FrameData):
        # 处理新的视频帧
        print(f"收到帧: {frame_data.frame_index}")
    
    def on_idle_frame_ready(self, frame_data: FrameData):
        # 处理IDLE模式帧
        print(f"IDLE帧: {frame_data.frame_index}")
    
    def on_task_status_changed(self, task: Task, old_status: TaskStatus, new_status: TaskStatus):
        # 处理状态变更
        print(f"任务状态: {old_status} -> {new_status}")
    
    # ... 实现其他回调方法

# 3. 创建引擎并使用
callback = MyCallback()
engine = DigitalHumanEngine(config, callback)

# 提交问题
success = engine.submit_question("你好，请介绍一下自己")
```

## 🏗️ 架构设计

### 项目结构

```
digital_human_sdk/
├── digital_human_sdk/       # 核心SDK包
│   ├── __init__.py         # SDK入口，导出主要类
│   ├── core.py             # 核心引擎 DigitalHumanEngine
│   ├── models.py           # 数据模型 Task, TaskStatus, FrameData
│   ├── callbacks.py        # 回调接口 DigitalHumanCallback
│   ├── exceptions.py       # 自定义异常类
│   ├── CONFIG_GUIDE.md     # 配置指南文档
│   ├── config/             # 配置管理
│   │   ├── __init__.py
│   │   └── config.py       # DigitalHumanConfig 统一配置类
│   ├── llm/                # LLM模块
│   │   ├── __init__.py
│   │   ├── llm_chat_client.py  # LLM客户端
│   │   └── llm_client.py
│   ├── tts/                # TTS模块
│   │   ├── __init__.py
│   │   ├── cosyvoice_client.py     # CosyVoice客户端
│   │   ├── cosyvoice_pb2.py        # gRPC协议文件
│   │   ├── cosyvoice_pb2_grpc.py   # gRPC服务文件
│   │   ├── cosyvoice.proto         # Protocol Buffer定义
│   │   └── utils.py
│   ├── video/              # 视频生成模块
│   │   ├── __init__.py
│   │   ├── unet.py         # UNet神经网络模型
│   │   └── video_model.py  # 视频模型封装
│   ├── threads/            # 多线程处理
│   │   ├── __init__.py
│   │   ├── digital_human_synthesis_thread.py  # 数字人合成线程
│   │   ├── audio_player_thread.py             # 音频播放线程
│   │   └── synthesis_thread.py
│   ├── utils/              # 工具模块
│   │   ├── __init__.py
│   │   └── file_utils.py
│   ├── assets/             # 资源文件
│   │   ├── data/           # 数据集（图片、landmarks）
│   │   └── weight/         # 模型权重文件
│   └── examples/           # SDK内置示例
│       └── sdk_example.py
└── examples/               # 外部使用示例
    ├── sdk_example.py      # 完整SDK示例
    ├── pyqt5_example.py    # PyQt5桌面应用示例
    ├── simple_console_example.py  # 简单控制台示例
    └── web_api_example.py  # Web API服务示例
```

### 数据流

```
用户输入 → LLM处理 → 文本块 → TTS合成 → 音频+特征
                                              ↓
UI显示 ← 视频帧 ← UNet模型 ← 音频特征 + 基础图片
    ↓
IDLE模式 ← 任务完成 ← 帧处理完成 ← 音频播放完成
```

## ⚙️ 配置选项

### DigitalHumanConfig

| 参数                      | 类型 | 默认值                                          | 说明                                           |
| ------------------------- | ---- | ----------------------------------------------- | ---------------------------------------------- |
| `checkpoint_path`         | str  | "./digital_human_sdk/assets/weight/trained.pth" | 模型权重文件路径                               |
| `dataset_path`            | str  | "./digital_human_sdk/assets/data"               | 数据集路径                                     |
| `asr_type`                | str  | "hubert"                                        | 音频特征提取类型 (hubert/wenet)                |
| `speaker_id`              | str  | "100"                                           | 说话人ID                                       |
| `hubert_sampling_rate`    | int  | 16000                                           | 音频采样率                                     |
| `llm_server_url`          | str  | "http://127.0.0.1:8080/v1/chat/completions"     | LLM服务地址                                    |
| `llm_response_chunk_size` | int  | 15                                              | LLM响应块大小                                  |
| `llm_model_name`          | str  | "qwen2.5-7b"                                    | LLM模型名称                                    |
| `tts_server_host`         | str  | "localhost"                                     | TTS服务主机                                    |
| `tts_server_port`         | int  | 8998                                            | TTS服务端口                                    |
| `tts_mode`                | str  | "zero_shot"                                     | TTS模式 (sft/zero_shot/cross_lingual/instruct) |
| `video_fps`               | int  | 25                                              | 视频帧率                                       |
| `idle_image_count`        | int  | 10                                              | IDLE模式图片数量                               |

### 配置验证

```python
config = DigitalHumanConfig()
if config.validate():
    print("配置验证通过")
else:
    print("配置验证失败，请检查路径和参数")
```

> 详细配置说明请参考 [CONFIG_GUIDE.md](CONFIG_GUIDE.md)

## 🔌 回调接口

### DigitalHumanCallback

必须实现的回调方法：

```python
def on_task_status_changed(self, task: Task, old_status: TaskStatus, new_status: TaskStatus):
    """任务状态改变时调用"""
    pass

def on_frame_ready(self, task: Task, frame_data: FrameData):
    """新的视频帧准备就绪时调用"""
    pass

def on_idle_frame_ready(self, frame_data: FrameData):
    """IDLE模式帧准备就绪时调用"""
    pass

def on_task_completed(self, result: TaskResult):
    """任务完成时调用"""
    pass

def on_error(self, task: Optional[Task], error_message: str):
    """发生错误时调用"""
    pass

def on_llm_response_chunk(self, task: Task, text_chunk: str):
    """LLM响应文本块时调用（可选）"""
    pass
```

## 📋 系统要求

### 基础要求

- Python 3.10+
- CUDA支持的GPU（推荐）
- 8GB+ RAM

### 依赖包

主要依赖包括：
- **PyTorch** (CUDA版本) - 深度学习框架，GPU加速推理
- **PyQt5** - GUI框架，用于桌面应用界面
- **OpenCV** - 图像处理和计算机视觉
- **gRPC & Protobuf** - TTS服务通信协议
- **PyAudio** - 音频处理和播放
- **Requests** - HTTP客户端，用于LLM服务通信
- **qt-material** - UI主题美化（可选）

完整依赖列表请参考 `requirements.txt`

### 外部服务

1. **LLM服务**: 需要运行兼容OpenAI API的语言模型服务
   - 支持流式响应
   - 推荐使用Qwen2.5-7B或类似模型
2. **TTS服务**: 需要运行CosyVoice gRPC服务
   - 支持多种TTS模式
   - 端口默认8998
3. **模型文件**: 需要预训练的数字人模型权重

### 目录结构要求

```
project/
├── assets/
│   ├── weight/
│   │   └── trained.pth      # 训练好的模型
│   └── data/
│       ├── full_body_img/   # 图片序列 0.jpg-9.jpg
│       └── landmarks/       # 对应的landmark文件
└── your_app.py             # 你的应用代码
```

## 🎨 使用示例

项目提供了多种完整的使用示例，位于 `examples/` 目录：

### 1. 完整SDK示例 (`examples/sdk_example.py`)

这是最完整的示例，包含统一配置、完整UI和所有功能：

```python
from digital_human_sdk import DigitalHumanEngine, DigitalHumanConfig, DigitalHumanCallback

# 创建统一配置
config = DigitalHumanConfig(
    llm_server_url="http://127.0.0.1:8080/v1/chat/completions",
    tts_server_host="localhost",
    tts_server_port=8998,
    video_fps=25
)

# 实现回调接口
class MyCallback(DigitalHumanCallback):
    def on_frame_ready(self, task, frame_data):
        # 处理视频帧
        self.display_frame(frame_data.image)
    
    # ... 实现其他回调方法

# 运行示例
python examples/sdk_example.py
```

# 交互循环
while True:
    question = input("请输入问题 (输入 'quit' 退出): ")
    if question.lower() == 'quit':
        break
    engine.submit_question(question)

# 运行示例
python examples/simple_console_example.py
```

## 📚 API参考

### 核心类

#### DigitalHumanEngine
主要的数字人引擎类，负责协调所有组件。

```python
class DigitalHumanEngine:
    def __init__(self, config: DigitalHumanConfig, callback: DigitalHumanCallback)
    def submit_question(self, question: str) -> bool
    def shutdown(self)
```

#### DigitalHumanConfig
统一的配置管理类。

```python
class DigitalHumanConfig:
    def validate(self) -> bool  # 验证配置是否有效
```

#### DigitalHumanCallback
回调接口，需要用户实现。

```python
class DigitalHumanCallback(ABC):
    @abstractmethod
    def on_task_status_changed(self, task, old_status, new_status)
    @abstractmethod
    def on_frame_ready(self, task, frame_data)
    @abstractmethod
    def on_idle_frame_ready(self, frame_data)
    @abstractmethod
    def on_task_completed(self, result)
    @abstractmethod
    def on_error(self, task, error_message)
    @abstractmethod
    def on_llm_response_chunk(self, task, text_chunk)
```

### 数据模型

#### Task
任务对象，包含任务信息和状态。

```python
class Task:
    task_id: int
    question: str
    status: TaskStatus
    # 内部队列用于数据传递
```

#### TaskStatus
任务状态枚举。

```python
class TaskStatus(Enum):
    CREATED = 0
    RUNNING = 1
    FINISHED = 2
    FAILED = 3
    IDLE = 4
```

#### FrameData
帧数据对象。

```python
@dataclass
class FrameData:
    image: Optional[object]  # numpy array
    audio_chunk: Optional[object]  # numpy array
    frame_index: int = 0
    is_idle: bool = False
```

## 🔧 高级功能

### 1. 自定义TTS配置

```python
config = DigitalHumanConfig(
    tts_server_host="your-tts-server.com",
    tts_server_port=8998,
    tts_mode="zero_shot",  # sft, zero_shot, cross_lingual, instruct
)
```

### 2. 性能优化

```python
config = DigitalHumanConfig(
    video_fps=30,  # 提高帧率
    idle_image_count=20,  # 增加IDLE图片数量
    llm_response_chunk_size=20,  # 调整响应块大小
)
```

### 3. 错误处理

```python
class MyCallback(DigitalHumanCallback):
    def on_error(self, task, error_message):
        logging.error(f"数字人处理错误: {error_message}")
        # 实现错误恢复逻辑
        
    def on_task_status_changed(self, task, old_status, new_status):
        if new_status == TaskStatus.FAILED:
            # 处理任务失败情况
            self.handle_task_failure(task)
```

### 4. 多线程安全

SDK内部使用多线程处理，所有回调都在Qt主线程中执行，确保UI操作安全。

### 5. 资源管理

```python
# 正确的资源管理
try:
    engine = DigitalHumanEngine(config, callback)
    # 使用引擎...
finally:
    engine.shutdown()  # 确保资源正确释放
```

## 🚀 快速开始指南

### 1. 环境准备

```bash
# 1. 克隆项目
git clone <repository-url>
cd digital_human_sdk

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt
```

### 2. 准备资源文件

确保以下目录结构存在：

```
digital_human_sdk/assets/
├── weight/
│   └── trained.pth          # 数字人模型权重文件
└── data/
    ├── full_body_img/       # 图片序列 0.jpg ~ 9.jpg
    └── landmarks/           # 对应的landmark文件
```

> **重要**: 模型权重文件和数据集是SDK正常运行的必要条件，请确保这些文件存在且路径正确。

### 3. 启动外部服务

SDK依赖以下外部服务，请确保它们正常运行：

```bash
# 1. 启动LLM服务（兼容OpenAI API）
# 示例：使用Ollama、vLLM或其他LLM服务
# 默认地址: http://127.0.0.1:8080/v1/chat/completions

# 2. 启动TTS服务（CosyVoice gRPC服务）
# 默认端口: 8998
# 确保服务支持zero_shot模式
```

### 4. 验证安装

```bash
# 运行配置验证
python -c "
from digital_human_sdk import DigitalHumanConfig
config = DigitalHumanConfig()
if config.validate():
    print('✅ 配置验证通过')
else:
    print('❌ 配置验证失败，请检查资源文件')
"
```

### 5. 运行示例

```bash
# 运行完整示例（推荐）
python examples/sdk_example.py

# 或运行简单控制台示例
python examples/simple_console_example.py
```

## 🔄 版本历史

### v1.0.0 (当前版本)
- ✅ 统一配置系统 `DigitalHumanConfig`
- ✅ 完整的回调接口 `DigitalHumanCallback`
- ✅ 多种使用示例（PyQt5、Web API、控制台）
- ✅ 高精度音视频同步
- ✅ IDLE模式支持
- ✅ 多线程处理架构
- ✅ 完整的错误处理和异常系统

## 🐛 故障排除

### 常见问题

1. **模型加载失败**
   ```
   错误: 模型文件不存在: ./digital_human_sdk/assets/weight/trained.pth
   ```
   - 检查模型文件路径和权限
   - 确认CUDA环境配置正确
   - 使用 `config.validate()` 验证配置

2. **服务连接失败**
   ```
   错误: LLM服务连接失败
   ```
   - 检查LLM和TTS服务是否正常运行
   - 验证网络连接和端口配置
   - 确认服务URL格式正确

3. **图片显示异常**
   ```
   错误: 处理IDLE帧时出错
   ```
   - 确认图片文件存在且格式正确
   - 检查图片路径配置
   - 验证图片序列完整性（0.jpg ~ 9.jpg）

4. **Qt应用相关问题**
   ```
   错误: QApplication instance already exists
   ```
   - 确保只创建一个QApplication实例
   - 在Web API模式下正确管理Qt事件循环

### 调试模式

启用详细日志输出：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 或在配置中启用调试
config = DigitalHumanConfig()
if not config.validate():
    print("配置验证失败，请检查以下项目：")
    print("1. 模型文件路径")
    print("2. 数据集路径") 
    print("3. 服务连接配置")
```

### 性能优化建议

1. **GPU加速**
   - 确保CUDA环境正确安装
   - 使用GPU版本的PyTorch

2. **内存优化**
   - 适当调整 `idle_image_count`
   - 监控内存使用情况

3. **网络优化**
   - LLM和TTS服务尽量部署在本地网络
   - 调整 `llm_response_chunk_size` 优化响应速度

## 📄 许可证

本SDK遵循Apache 2.0许可证。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个SDK。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- GitHub Issues
- Email: team@digitalhuman.com