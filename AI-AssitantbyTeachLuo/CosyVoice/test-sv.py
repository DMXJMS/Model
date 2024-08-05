
from funasr.utils.postprocess_utils import rich_transcription_postprocess
import sys
# from model import SenseVoiceSmall


sys.path.append("/root/autodl-fs/CosyVoice-main") 
sys.path.append("/root/autodl-fs/SenseVoice-main") 

from model import SenseVoiceSmall
model_dir = "/root/autodl-fs/pretrained_models/SenseVoiceSmall"
m_recogize, param_recogize = SenseVoiceSmall.from_pretrained(model=model_dir)



def process_audio(audio):
    global m_recogize, param_recogize
    print('Processing audio:', audio)
    res = m_recogize.inference(
            data_in=audio,
            language="zh", # "zn", "en", "yue", "ja", "ko", "nospeech"
            use_itn=False,**param_recogize)
    result = res[0][0]['text']
    text = rich_transcription_postprocess(result)
        
#     pattern = r'[\u4e00-\u9fff]+'
#     chinese_characters = re.findall(pattern, text)

#     # 将提取到的汉字连接成一个字符串
#     result = ''.join(chinese_characters)

    print("识别结果:",result)
    print("识别tewxt：",text)
    return result

process_audio("zero_shot_prompt.wav")
