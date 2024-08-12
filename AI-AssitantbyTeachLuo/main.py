import gradio as gr
from http import HTTPStatus
from dashscope import Application
import sys
sys.path.append('./third_party/SenseVoice')
sys.path.append('./third_party/CosyVoice/')
sys.path.append('./third_party/CosyVoice/third_party/Matcha-TTS/')

from cosyvoice.cli.cosyvoice import CosyVoice
from cosyvoice.utils.file_utils import load_wav
import torchaudio
from funasr.utils.postprocess_utils import rich_transcription_postprocess

from model import SenseVoiceSmall
import requests
import json


init_response = """你好！我是罗翔，你的法律咨询助理。如果你有任何法律相关的问题，无论是关于合同纠纷、公司合规、民事权利还是其他法律困惑，
都可以告诉我。我会运用我的专业知识和技能，为你提供准确的法律信息和实用的建议。请问今天有什么我可以帮助你的吗？"""
host_avatar = './asset/user.png'
user_avatar = './asset/luoxiang.png'

# SenseVoice Model
SenseVoice_model_dir = 'pretrained_models/SenseVoiceSmall'
m_recognize, param_recogize = SenseVoiceSmall.from_pretrained(SenseVoice_model_dir)

# CosyVoice Model
zero_shot_audio_path = 'asset/zero_shot_lx_prompt.wav'
cosyvoice = CosyVoice('pretrained_models/CosyVoice-300M-Instruct')
prompt_speech_16k = load_wav(zero_shot_audio_path, 16000)
zero_shot_audio_text = "对立开来，但其实你可以想一想，在开车的过程中，是在交通规则的保护下驾驶更自由，还是随心所欲无视规则开车更自由呢？因此我们会发"

# LLM Service
session_id = ""
app_id = "your_app_id" #你的应用ID
api_key = "sk-xxx" #你的API Key
ollama_url = "" #你的ollama服务地址


def process_audio(audio):
    global m_recognize, param_recogize
    print("Processing Audio:", audio)
    res = m_recognize.inference(
        data_in=audio,
        language="zh", # 'zh', 'en', 'yue', 'ja', 'ko', 'nospeech'
        use_itn=False,
        **param_recogize
    )
    # result = res[0][0]['text']
    result = rich_transcription_postprocess(res[0][0]['text'])
    return result


def tts_api(response):
    path = 'asset/tts_output.wav'
    output = cosyvoice.inference_zero_shot(response, zero_shot_audio_text, prompt_speech_16k)
    #! 待修改，不需要保存音频文件，直接进行输出    
    torchaudio.save(path, output['tts_speech'], 22050)    
    return path        


# 使用在线LLM API服务
def call_with_session(session_id,prompt,app_id,api_key):
    print("sessionid 4 ",session_id)
    response_fail = "在法庭上给张三辩护中,稍等"
    if session_id=="":
        response = Application.call(app_id=app_id,
                                prompt=prompt,
                                api_key=api_key
                                )

    else:
        response = Application.call(app_id=app_id,
                                prompt=prompt,
                                session_id=session_id,
                                api_key=api_key)
        
    if response.status_code != HTTPStatus.OK:
        print('request_id=%s, code=%s, message=%s\n' % (response.request_id, response.status_code, response.message))
        return session_id,response_fail
    else:
        print('request_id=%s, output=%s, usage=%s\n' % (response.request_id, response.output, response.usage))
        session_id = response.output["session_id"]
        response_success = response.output["text"]
        return session_id,response_success


def call_ollama_service(message, port=11434):
    url = f"http://localhost:{port}/api/chat"
    payload = {
        "model": "qwen:0.5b",
        "messages": [{"role": "user", "content": message}]
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        response_content = ""
        for line in response.iter_lines():
            if line:
                response_content += json.loads(line)["message"]["content"]
        return response_content
    else:
        return f"Error: {response.status_code} - {response.text}"


def user_submit_handler(user_text, state, chatbot):
    global session_id, app_id, api_key
    print("User Text:", user_text)
    chatbot.append((user_text, None))
    yield (chatbot, None)
     
    messages = state['message']
    print("messages:", messages)
    
    # 调用ollama服务
    try:
        response = call_ollama_service(user_text)    
    except:
        if  len(session_id) == 0:
            session, response = call_with_session(session_id, user_text, app_id, api_key)
            session_id = session
        else:
            session, respone = call_with_session(session_id, user_text, app_id, api_key)
    
    chatbot.append((None, response))
    messages.append({"role": "assistant", "content": response})
    state['message'] = messages
    audio = tts_api(response)
    yield(chatbot, audio)
    

def clear_history_handler(user_text, state, chatbot):
    session_id = ""
    chatbot = []
    yield (chatbot, None)
    chatbot.append((None, init_response))
    yield (chatbot, "text")
    
    
with gr.Blocks() as demo:
    state = gr.State({'message': []})
    
    with gr.Row():
        with gr.Column(scale=1):            
            user_chatbot = gr.Chatbot(value=[[None, init_response]],
                                    elem_classes="app-chatbot",
                                    avatar_images=[host_avatar, user_avatar],
                                    label="交互区",
                                    show_label=True,
                                    bubble_full_width=False,
                                    height=800)
            
        with gr.Column(scale=1):
            audio_input = gr.Audio(label="User Input", sources=['microphone'], type='filepath')
            #* 通过上传音频的形式进行对话
            # audio_user = gr.Audio(label="User Input", autoplay=True, type='filepath')
            # audio_submit = gr.Button("提交录音", variant="primary")
            user_text = gr.Textbox(label="语音识别内容或直接输入对话内容")
            user_submit = gr.Button("发起对话", variant="primary")
            audio_bot = gr.Audio(label="Bot Output", autoplay=True, type='filepath')
            clear_history = gr.Button("清除历史对话", variant="primary")
    
    audio_input.stop_recording(process_audio, inputs=audio_input, outputs=user_text)
    # audio_submit.click(process_audio, inputs=audio_user, outputs=user_text)
    user_submit.click(user_submit_handler, inputs=[user_text, state, user_chatbot], outputs=[user_chatbot, audio_bot])
                        
        
demo.launch(server_name='0.0.0.0', server_port=8888)