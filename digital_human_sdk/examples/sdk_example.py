"""
Digital Human SDK 使用示例 - 统一配置版本
"""
import sys
from pathlib import Path

# 添加SDK路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLineEdit, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
import qt_material
import cv2

from digital_human_sdk import (
    DigitalHumanEngine, 
    DigitalHumanConfig,  # 使用统一的配置类
    DigitalHumanCallback,
    Task, 
    TaskStatus, 
    FrameData, 
    TaskResult
)


class SDKDigitalHumanCallback(DigitalHumanCallback):
    """SDK版本的回调实现"""
    
    def __init__(self, ui_app):
        self.ui_app = ui_app
    
    def on_task_status_changed(self, task: Task, old_status: TaskStatus, new_status: TaskStatus):
        """任务状态改变"""
        status_text = {
            TaskStatus.CREATED: "已创建",
            TaskStatus.RUNNING: "运行中",
            TaskStatus.FINISHED: "已完成",
            TaskStatus.FAILED: "已失败",
            TaskStatus.IDLE: "待机中"
        }.get(new_status, "未知状态")
        
        self.ui_app.status_label.setText(f"任务状态: {status_text}")
        print(f"任务 {task.task_id} 状态变更: {old_status} -> {new_status}")
    
    def on_frame_ready(self, task: Task, frame_data: FrameData):
        """新帧准备就绪"""
        self.ui_app.display_frame(frame_data.image)
    
    def on_idle_frame_ready(self, frame_data: FrameData):
        """IDLE帧准备就绪"""
        self.ui_app.display_frame(frame_data.image)
    
    def on_task_completed(self, result: TaskResult):
        """任务完成"""
        print(f"任务 {result.task_id} 完成，总帧数: {result.total_frames}")
    
    def on_error(self, task, error_message: str):
        """错误处理"""
        print(f"错误: {error_message}")
        self.ui_app.status_label.setText(f"错误: {error_message}")
    
    def on_llm_response_chunk(self, task: Task, text_chunk: str):
        """LLM响应文本块"""
        print(f"LLM响应: {text_chunk}")


class SDKDigitalHumanApp(QMainWindow):
    """使用统一配置的数字人SDK应用"""
    
    def __init__(self):
        super().__init__()
        
        # 创建统一的SDK配置
        self.config = DigitalHumanConfig(
            # 模型路径配置
            #checkpoint_path="./assets/weight/trained.pth",
            #dataset_path="./assets/data",
            
            # LLM配置
            llm_server_url="http://10.1.10.253:8000/v1/chat/completions",
            llm_response_chunk_size=15,
            llm_model_name="qwen2.5-7b",
            
            # TTS配置
            tts_server_host="localhost",
            tts_server_port=8998,
            tts_mode="zero_shot",  # 使用工作的模式
            
            # 视频配置
            video_fps=25,
            idle_image_count=10,
            
            # 音频配置
            asr_type="hubert",
            speaker_id="100",
            hubert_sampling_rate=16000
        )
        
        # 验证配置
        if not self.config.validate():
            print("警告: 配置验证失败，某些功能可能无法正常工作")
        
        # 创建回调
        self.callback = SDKDigitalHumanCallback(self)
        
        # 初始化UI
        self.init_ui()
        
        # 创建数字人引擎
        self.engine = DigitalHumanEngine(self.config, self.callback)
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('数字人SDK示例 - 统一配置版本')
        self.resize(800, 800)
        self.center()

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        # 视频显示区域
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setText("数字人SDK加载中...")
        self.video_label.setMinimumHeight(600)

        # 输入区域
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("请输入问题...")
        self.text_input.returnPressed.connect(self.on_submit_question)

        # 提交按钮
        self.submit_button = QPushButton("提交问题")
        self.submit_button.clicked.connect(self.on_submit_question)
        
        # 状态显示
        self.status_label = QLabel("状态: 初始化中")
        self.status_label.setAlignment(Qt.AlignCenter)

        # 配置信息显示
        config_info = QLabel(f"配置: {self.config.tts_mode}模式, {self.config.video_fps}fps, 说话人{self.config.speaker_id}")
        config_info.setAlignment(Qt.AlignCenter)
        config_info.setStyleSheet("color: gray; font-size: 10px;")

        # 布局
        layout.addWidget(self.video_label, stretch=1)
        layout.addWidget(self.text_input)
        layout.addWidget(self.submit_button)
        layout.addWidget(self.status_label)
        layout.addWidget(config_info)

        self.setCentralWidget(central_widget)
    
    def center(self):
        """窗口居中"""
        frameGeometry = self.frameGeometry()
        centerPoint = QApplication.primaryScreen().availableGeometry().center()
        frameGeometry.moveCenter(centerPoint)
        self.move(frameGeometry.topLeft())
    
    def on_submit_question(self):
        """提交问题"""
        question = self.text_input.text().strip()
        if not question:
            return
        
        # 使用SDK提交问题
        if self.engine.submit_question(question):
            self.text_input.clear()
            print(f"问题已提交: {question}")
        else:
            print("问题提交失败，可能有其他任务正在处理")
    
    def display_frame(self, image):
        """显示图像帧"""
        if image is None:
            return
        
        try:
            # 转换OpenCV图像为Qt格式
            height, width, channel = image.shape
            bytes_per_line = 3 * width
            q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            
            # 创建QPixmap并缩放
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(
                self.video_label.width(),
                self.video_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # 显示图像
            self.video_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"显示图像时出错: {e}")
    
    def closeEvent(self, event):
        """关闭事件"""
        if hasattr(self, 'engine'):
            self.engine.shutdown()
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 应用主题
    qt_material.apply_stylesheet(app, theme='dark_teal.xml')
    
    # 创建并显示应用
    digital_human_app = SDKDigitalHumanApp()
    digital_human_app.show()
    
    print("=== 数字人SDK示例启动 ===")
    print("使用统一的DigitalHumanConfig配置类")
    print("支持完整的数字人功能：LLM对话、TTS合成、视频生成、IDLE模式")
    print("输入问题开始体验数字人对话!")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()