import os
import numpy as np
import torch
import cv2
from .unet import Model
from ..config.config import Config

class VideoModel:
    def __init__(self, config :Config):
        self.config = config
        self.checkpoint = str(config.checkpoint)
        self.dataset_dir = str(config.dataset)
        self.mode = config.asr

        # 加载模型
        self.net = Model(6, self.mode).cuda()
        self.net.load_state_dict(torch.load(self.checkpoint))
        self.net.eval()

        # 需要处理的音频特征
        self.audio_feats = None
        # 设置视频路径和参数
        self.img_dir = os.path.join(self.dataset_dir, "full_body_img/")
        self.lms_dir = os.path.join(self.dataset_dir, "landmarks/")
        self.len_img = len(os.listdir(self.img_dir)) - 1
        print(f"data: {self.img_dir}, {self.lms_dir}")
        # 获取示例图像尺寸
        exm_img = self.load_image(os.path.join(self.img_dir, "0.jpg"))
        self.h, self.w = exm_img.shape[:2]

        # 计算总帧数和估计的视频时长（秒）
        self.total_frames = 0
        self.fps = 25.0 if self.mode == "hubert" else 20.0
        self.frame_interval = 1.0 / self.fps  # 每帧间隔（秒）
        self.video_duration = 0
    
    def set_audio_features(self, audio_features):
        self.audio_feats = audio_features

    def load_image(self, path):
        """加载图像"""
        return cv2.imread(path)

    def get_audio_features(self, index):
        """获取音频特征"""
        left = index - 8
        right = index + 8
        pad_left = 0
        pad_right = 0
        if left < 0:
            pad_left = -left
            left = 0
        if right > self.audio_feats.shape[0]:
            pad_right = right - self.audio_feats.shape[0]
            right = self.audio_feats.shape[0]
        auds = torch.from_numpy(self.audio_feats[left:right])
        if pad_left > 0:
            auds = torch.cat([torch.zeros_like(auds[:pad_left]), auds], dim=0)
        if pad_right > 0:
            auds = torch.cat([auds, torch.zeros_like(auds[:pad_right])], dim=0)
        return auds

    def process_frame(self, img_idx, current_frame):
        """处理视频帧"""
        img_path = os.path.join(self.img_dir, f"{img_idx}.jpg")
        lms_path = os.path.join(self.lms_dir, f"{img_idx}.lms")

        img = self.load_image(img_path)
        lms_list = []
        with open(lms_path, "r") as f:
            lines = f.read().splitlines()
            for line in lines:
                arr = line.split(" ")
                arr = np.array(arr, dtype=np.float32)
                lms_list.append(arr)
        lms = np.array(lms_list, dtype=np.int32)
        xmin = lms[1][0]
        ymin = lms[52][1]

        xmax = lms[31][0]
        width = xmax - xmin
        ymax = ymin + width
        crop_img = img[ymin:ymax, xmin:xmax]
        h, w = crop_img.shape[:2]
        crop_img = cv2.resize(crop_img, (168, 168), cv2.INTER_AREA)
        crop_img_ori = crop_img.copy()
        img_real_ex = crop_img[4:164, 4:164].copy()
        img_real_ex_ori = img_real_ex.copy()
        img_masked = cv2.rectangle(img_real_ex_ori, (5, 5, 150, 145), (0, 0, 0), -1)

        img_masked = img_masked.transpose(2, 0, 1).astype(np.float32)
        img_real_ex = img_real_ex.transpose(2, 0, 1).astype(np.float32)

        img_real_ex_T = torch.from_numpy(img_real_ex / 255.0)
        img_masked_T = torch.from_numpy(img_masked / 255.0)
        img_concat_T = torch.cat([img_real_ex_T, img_masked_T], axis=0)[None]
        audio_feat = self.get_audio_features(current_frame)
        if self.mode == "hubert":
            audio_feat = audio_feat.reshape(32, 32, 32)
        if self.mode == "wenet":
            audio_feat = audio_feat.reshape(256, 16, 32)
        audio_feat = audio_feat[None]
        audio_feat = audio_feat.cuda()
        img_concat_T = img_concat_T.cuda()

        with torch.no_grad():
            pred = self.net(img_concat_T, audio_feat)[0]

        pred = pred.cpu().numpy().transpose(1, 2, 0) * 255
        pred = np.array(pred, dtype=np.uint8)
        crop_img_ori[4:164, 4:164] = pred
        crop_img_ori = cv2.resize(crop_img_ori, (w, h))
        img[ymin:ymax, xmin:xmax] = crop_img_ori

        return img
