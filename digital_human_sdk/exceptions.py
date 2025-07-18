"""
Digital Human SDK - Custom Exceptions
"""


class DigitalHumanSDKError(Exception):
    """SDK基础异常类"""
    pass


class ConfigurationError(DigitalHumanSDKError):
    """配置错误"""
    pass


class ModelLoadError(DigitalHumanSDKError):
    """模型加载错误"""
    pass


class TaskSubmissionError(DigitalHumanSDKError):
    """任务提交错误"""
    pass


class ServiceConnectionError(DigitalHumanSDKError):
    """服务连接错误"""
    pass


class ResourceNotFoundError(DigitalHumanSDKError):
    """资源未找到错误"""
    pass