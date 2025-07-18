# Digital Human SDK - 配置指南

## 🎯 统一配置类

SDK现在使用统一的 `DigitalHumanConfig` 配置类，简化了配置管理。

## 📋 配置参数

### 基本使用

```python
from digital_human_sdk import DigitalHumanConfig

# 使用默认配置
config = DigitalHumanConfig()

# 自定义配置
config = DigitalHumanConfig(
    # 模型路径
    checkpoint_path="./assets/weight/trained.pth",
    dataset_path="./assets/data",
    
    # LLM配置
    llm_server_url="http://127.0.0.1:8080/v1/chat/completions",
    llm_response_chunk_size=15,
    
    # TTS配置
    tts_server_host="localhost",
    tts_server_port=8998,
    tts_mode="zero_shot",
    
    # 视频配置
    video_fps=25,
    idle_image_count=10
)
```

### 完整参数列表

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `checkpoint_path` | str | "./assets/weight/trained.pth" | 模型权重文件路径 |
| `dataset_path` | str | "./assets/data" | 数据集路径 |
| `asr_type` | str | "hubert" | 音频特征提取类型 |
| `speaker_id` | str | "100" | 说话人ID |
| `hubert_sampling_rate` | int | 16000 | 音频采样率 |
| `llm_server_url` | str | "http://127.0.0.1:8080/v1/chat/completions" | LLM服务地址 |
| `llm_response_chunk_size` | int | 15 | LLM响应块大小 |
| `llm_model_name` | str | "qwen2.5-7b" | LLM模型名称 |
| `tts_server_host` | str | "localhost" | TTS服务主机 |
| `tts_server_port` | int | 8998 | TTS服务端口 |
| `tts_mode` | str | "zero_shot" | TTS模式 |
| `video_fps` | int | 25 | 视频帧率 |
| `idle_image_count` | int | 10 | IDLE模式图片数量 |

## 🔄 向后兼容

为了保持向后兼容，SDK提供了以下兼容属性：

```python
config = DigitalHumanConfig()

# 这些属性仍然可以使用（向后兼容）
print(config.checkpoint)  # 等同于 Path(config.checkpoint_path)
print(config.dataset)     # 等同于 Path(config.dataset_path)
print(config.asr)         # 等同于 config.asr_type
print(config.llm_server)  # 等同于 config.llm_server_url
```

## ✅ 配置验证

```python
config = DigitalHumanConfig()

# 验证配置是否有效
if config.validate():
    print("配置验证通过")
else:
    print("配置验证失败")
```

## 🎨 使用示例

### 1. 基本使用

```python
from digital_human_sdk import DigitalHumanEngine, DigitalHumanConfig

# 创建配置
config = DigitalHumanConfig()

# 创建引擎
engine = DigitalHumanEngine(config, callback)
```

### 2. 自定义TTS配置

```python
config = DigitalHumanConfig(
    tts_server_host="your-tts-server.com",
    tts_server_port=8998,
    tts_mode="sft"  # 或 "zero_shot", "cross_lingual", "instruct"
)
```

### 3. 性能优化配置

```python
config = DigitalHumanConfig(
    video_fps=30,  # 提高帧率
    idle_image_count=20,  # 增加IDLE图片数量
    llm_response_chunk_size=20  # 调整响应块大小
)
```

## 🔧 迁移指南

### 从旧版Config迁移

如果你之前使用的是旧版的 `Config` 类：

```python
# 旧版本
from config import Config
old_config = Config()

# 新版本 - 直接替换即可
from digital_human_sdk import DigitalHumanConfig
new_config = DigitalHumanConfig()

# 或者继续使用Config（现在是DigitalHumanConfig的别名）
from digital_human_sdk import Config
config = Config()
```

### 属性映射

| 旧属性 | 新属性 | 说明 |
|--------|--------|------|
| `config.checkpoint` | `config.checkpoint_path` | 现在返回字符串路径 |
| `config.dataset` | `config.dataset_path` | 现在返回字符串路径 |
| `config.asr` | `config.asr_type` | 名称更清晰 |
| `config.llm_server` | `config.llm_server_url` | 名称更清晰 |
| `config.llm_response_chunck_size` | `config.llm_response_chunk_size` | 修正拼写错误 |

## 🎯 最佳实践

1. **使用配置验证**：总是调用 `config.validate()` 来确保配置正确
2. **环境特定配置**：为不同环境创建不同的配置
3. **配置文件**：考虑从JSON或YAML文件加载配置
4. **错误处理**：妥善处理配置验证失败的情况

```python
# 最佳实践示例
config = DigitalHumanConfig(
    checkpoint_path="./models/my_model.pth",
    tts_server_host="production-tts.example.com"
)

if not config.validate():
    print("配置验证失败，使用默认配置")
    config = DigitalHumanConfig()

engine = DigitalHumanEngine(config, callback)
```