# Copyright (c) 2024 Alibaba Inc (authors: Xiang Lyu)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
import logging
import argparse
import torchaudio
import cosyvoice_pb2
import cosyvoice_pb2_grpc
import grpc
import torch
import numpy as np
from utils import load_wav
import time, io


class CosyVoiceClient:
    def __init__(self, host='localhost', port=8998, mode='zero_shot', prompt_text="", prompt_wav="",
                 instruct_text='你好'):
        self.host = host
        self.port = port
        self.mode = mode
        self.prompt_text = prompt_text
        self.prompt_wav = prompt_wav
        self.instruct_text = instruct_text
        self.prompt_sr, self.target_sr = 16000, 22050
        # 初始化时打开 gRPC 通道并创建 stub
        self.channel = grpc.insecure_channel("{}:{}".format(self.host, self.port))
        self.stub = cosyvoice_pb2_grpc.CosyVoiceStub(self.channel)

    def inference(self, spk_id, tts_text):
    
        start = time.time()
        request = cosyvoice_pb2.Request()
        if self.mode == 'sft':
            logging.info('send sft request')
            sft_request = cosyvoice_pb2.sftRequest()
            sft_request.spk_id = spk_id
            sft_request.tts_text = tts_text
            request.sft_request.CopyFrom(sft_request)
        elif self.mode == 'zero_shot':
            logging.info('send zero_shot request')
            zero_shot_request = cosyvoice_pb2.zeroshotRequest()
            zero_shot_request.tts_text = tts_text
            zero_shot_request.prompt_text = self.prompt_text
            zero_shot_request.spk_id = spk_id
            if self.prompt_wav != "":
                prompt_speech = load_wav(self.prompt_wav, self.prompt_sr)
                zero_shot_request.prompt_audio = (prompt_speech.numpy() * (2 ** 15)).astype(np.int16).tobytes()

            request.zero_shot_request.CopyFrom(zero_shot_request)
        elif self.mode == 'cross_lingual':
            logging.info('send cross_lingual request')
            cross_lingual_request = cosyvoice_pb2.crosslingualRequest()
            cross_lingual_request.tts_text = tts_text
            prompt_speech = load_wav(self.prompt_wav, self.prompt_sr)
            cross_lingual_request.prompt_audio = (prompt_speech.numpy() * (2 ** 15)).astype(np.int16).tobytes()
            request.cross_lingual_request.CopyFrom(cross_lingual_request)
        else:
            logging.info('send instruct request')
            instruct_request = cosyvoice_pb2.instructRequest()
            instruct_request.tts_text = tts_text
            instruct_request.spk_id = spk_id
            instruct_request.instruct_text = self.instruct_text
            request.instruct_request.CopyFrom(instruct_request)

        response = self.stub.Inference(request)

        # concat response bytes
        tts_audio = b''
        tts_feature = b''
        for r in response:
            tts_audio += r.tts_audio
            tts_feature += r.tts_feature

        return tts_audio, tts_feature

    def __del__(self):
        # 析构时关闭 gRPC 通道
        if hasattr(self, 'channel'):
            self.channel.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--host',
                        type=str,
                        default='localhost')
    parser.add_argument('--port',
                        type=int,
                        default=8998)
    parser.add_argument('--mode',
                        default='zero_shot',
                        choices=['sft', 'zero_shot', 'cross_lingual', 'instruct'],
                        help='request mode')
    parser.add_argument('--tts_text',
                        type=str,
                        default='你好，我是通义千问语音合成大模型，请问有什么可以帮您的吗？')
    parser.add_argument('--spk_id',
                        type=str,
                        default='100')
    parser.add_argument('--prompt_text',
                        type=str,
                        default="")
    parser.add_argument('--prompt_wav',
                        type=str,
                        default="")
    parser.add_argument('--instruct_text',
                        type=str,
                        default='Theo \'Crimson\', is a fiery, passionate rebel leader. \
                                 Fights with fervor for justice, but struggles with impulsiveness.')
    parser.add_argument('--tts_wav',
                        type=str,
                        default='demo.wav')
    args = parser.parse_args()

    client = CosyVoiceClient(host=args.host, port=args.port, mode=args.mode, prompt_text=args.prompt_text,
                             prompt_wav=args.prompt_wav, instruct_text=args.instruct_text)
    tts_audio = client.inference(spk_id=args.spk_id, tts_text=args.tts_text)