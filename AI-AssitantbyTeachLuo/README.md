<!--
 * @Author: kraken8081 202024@cumtb.edu.cn
 * @Date: 2024-08-05 14:37:59
 * @LastEditors: kraken8081 202024@cumtb.edu.cn
 * @LastEditTime: 2024-08-06 19:54:40
 * @FilePath: /Model/AI-AssitantbyTeachLuo/README.md
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
-->
# 端到端语音交互AI法律助手
- ## 环境安装

    python版本：Python 3.8.19
    ```shell
    conda create -n cosyvoice python=3.8 -y
    conda activate cosyvoice
    pip install  pynini==2.1.5
    pip install dashscope
    apt update
    apt-get install sox libsox-dev
    pip install funasr
    pip install dashscope
    apt install ffmpeg

    # 配置SenseVoice语音识别
    git clone https://github.com/FunAudioLLM/SenseVoice.git
    cd SenseVoice
    pip install -r requirements.txt 

    # 配置CosyVoice语音合成
    git clone https://github.com/FunAudioLLM/SenseVoice.git
    cd 配置CosyVoice
    pip install -r requirements.txt 

    # 启动服务
    cd CosyVoice
    export PYTHONPATH=third_party/Matcha-TTS
    python AI-assitantbyTeachLuo.py
    ```

- ## 交互对话
<div align="center"><img src="./image/img1.png" width="px"></div>
