#语音生成
from cosyvoice.cli.cosyvoice import CosyVoice
from cosyvoice.utils.file_utils import load_wav
import torchaudio
import sys

sys.path.append("/root/autodl-fs/CosyVoice") 
sys.path.append("/root/autodl-fs/SenseVoice-main") 

cosyvoice = CosyVoice('/root/autodl-fs/pretrained_models/CosyVoice-300M')
prompt_speech_16k = load_wav('luoxianghigh.wav', 16000)
ori_text="对立开来，但其实你可以想一想，在开车的过程中，是在交通规则的保护下驾驶更自由，还是随心所欲无视规则开车更自由呢？因此我们会发"

#语音识别
from model import SenseVoiceSmall
from funasr.utils.postprocess_utils import rich_transcription_postprocess
model_dir = "/root/autodl-fs/pretrained_models/SenseVoiceSmall"
m_recogize, param_recogize = SenseVoiceSmall.from_pretrained(model=model_dir)

# 环境变量
host_avatar = 'user.png'
user_avatar = 'luoxiang.png'
session_id = ""
app_id = "8f3d0e435fab4cd4820ca0bb87b7f2fc"
api_key = "sk-d97b0582520741d8866586df0c2b63b2"

init_response = """你好！我是罗翔，你的法律咨询助理。如果你有任何法律相关的问题，无论是关于合同纠纷、公司合规、民事权利还是其他法律困惑，
都可以告诉我。我会运用我的专业知识和技能，为你提供准确的法律信息和实用的建议。请问今天有什么我可以帮助你的吗？"""

import gradio as gr
from http import HTTPStatus
from dashscope import Application

def call_with_session(session_id,prompt,app_id,api_key):
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
def tts_chat_api(response):
    global cosyvoice,prompt_speech_16k,ori_text

    path = "zero_shot_luoxiang.wav"
    output = cosyvoice.inference_zero_shot(response, ori_text, prompt_speech_16k)
    torchaudio.save(path, output['tts_speech'], 22050)
    return path
    

with gr.Blocks(theme=gr.themes.ThemeClass) as demo:
    state = gr.State({'messages': []})
    with gr.Row():
        with gr.Column(scale=1):
            user_chatbot = gr.Chatbot(
                value=[[None, init_response]],
                elem_classes="app-chatbot",
                avatar_images=[host_avatar, user_avatar],
                label="交互区",
                show_label=True,
                bubble_full_width=False,
                height=800)
        with gr.Column(scale=1):
            audio_user = gr.Audio(label="User Input", sources=['microphone'], type='filepath')
            user_text = gr.Textbox(label="语音识别内容")
            user_submit = gr.Button("提交", variant="primary")
            audio_bot = gr.Audio(label="Bot Output", autoplay=True, type='filepath')
            clear_history = gr.Button("清除历史对话", variant="primary")

    def process_audio(audio):
        global m_recogize, param_recogize
        print('Processing audio:', audio)
        res = m_recogize.inference(
                data_in=audio,
                language="zh", # "zn", "en", "yue", "ja", "ko", "nospeech"
                use_itn=False,**param_recogize)
        result = res[0][0]['text']
        text = rich_transcription_postprocess(result)

        print("识别结果:",text)
        return text
    def clear_history_handler(user_text, state, chatbot):
        global session_id,init_response
        session_id = ""
        chatbot = []
        yield (chatbot, None)
        chatbot.append((None, init_response))
        yield (chatbot,"text")

    def user_submit_handler(user_text, state, chatbot):
        global session_id,app_id,api_key
        print("user_text==",user_text)
        chatbot.append((user_text, None))
        yield (chatbot, None)
        messages = state['messages']
        if len(session_id) == 0:
            session,response = call_with_session(session_id,user_text,app_id,api_key)
            session_id = session
        else:
            session,response = call_with_session(session_id,user_text,app_id,api_key)
        chatbot.append((None, response))
        messages.append({"role": "assistant", "content": response})
        state['messages'] = messages
        audio = tts_chat_api(response)
        yield (chatbot,audio)

    audio_user.stop_recording(process_audio, inputs=audio_user, outputs=user_text)
    user_submit.click(user_submit_handler, inputs=[user_text, state, user_chatbot], outputs=[user_chatbot, audio_bot])
    clear_history.click(clear_history_handler,inputs=[user_text, state, user_chatbot],outputs=[user_chatbot, audio_bot])

demo.launch(server_name='0.0.0.0',server_port=7873)

