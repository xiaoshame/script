# encoding=utf-8
import hashlib
import os
import re
import time

# tts
voiceMap = {
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",
    "xiaoyi": "zh-CN-XiaoyiNeural",
    "yunjian": "zh-CN-YunjianNeural",
    "yunxi": "zh-CN-YunxiNeural",
    "yunxia": "zh-CN-YunxiaNeural",
    "yunyang": "zh-CN-YunyangNeural",
    "xiaobei": "zh-CN-liaoning-XiaobeiNeural",
    "xiaoni": "zh-CN-shaanxi-XiaoniNeural",
    "hiugaai": "zh-HK-HiuGaaiNeural",
    "hiumaan": "zh-HK-HiuMaanNeural",
    "wanlung": "zh-HK-WanLungNeural",
    "hsiaochen": "zh-TW-HsiaoChenNeural",
    "hsioayu": "zh-TW-HsiaoYuNeural",
    "yunjhe": "zh-TW-YunJheNeural",
}
def getVoiceById(voiceId):
    return voiceMap.get(voiceId)

class EdgeTTS():
    def __init__(self):
        return

    def createAudio(self,text, voiceId, rate):
        voice = getVoiceById(voiceId)
        rate = f"+{rate}%"
        if not voice:
            return "error params"
        data_md5 = hashlib.md5((text+voiceId+rate).encode('utf-8')).hexdigest()
        file_name = f'{data_md5}.wav'
        if os.path.exists(file_name):
            pwdPath = os.getcwd()
            filePath = pwdPath + "/" + file_name
            return filePath
        pwdPath = os.getcwd()
        filePath = pwdPath + "/" + file_name
        dirPath = os.path.dirname(filePath)
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        if not os.path.exists(filePath):
            # 用open创建文件 兼容mac
            open(filePath, 'a').close()
        script = 'edge-tts --rate=' + rate + ' --voice ' + voice + ' --text "' + text + '" --write-media ' + filePath
        os.system(script)
        return filePath


    def clear_tmp_file(self,sec=120):
        zip_file_list = os.listdir(os.getcwd())
        for file in zip_file_list:
            if file.endswith('.zip') or file.endswith('.wav') or file.endswith('jpg'):
                zip_file_time = os.path.getmtime(file)
                if (time.time() - zip_file_time) > sec:
                    os.remove(file)

    def speak(self, voice, text, rate):
        self.clear_tmp_file()
        filePath = self.createAudio(text, voice, rate)
        return filePath

if __name__ == "__main__":
    text_to_tts = EdgeTTS()
    text_to_tts.speak("yunyang","2019/03/02上午有1/2的概率下暴雨所以有600人選擇3:30p.m.再出門,支付$500或￥600可以獲得代金券",20)