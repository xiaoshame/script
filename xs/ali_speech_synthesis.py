
import os
import configparser
import ali_token
import time
import requests
import json

#以下代码会根据上述TEXT文本反复进行语音合成
class AliTTs:
    def __init__(self):
        self.token = self.get_token()

    def get_token(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        token = self.config['ali']['token']
        expire_time = self.config['ali']['expire_time']
        if float(expire_time) < time.time():
            token = ali_token.get_token()
        return token

    def speak(self,voice_id,text):
        path = 'D:\\workspace\\script\\xs\\output.wav'
        appkey = os.environ.get('ALIYUN_APPKEY')
        url = f"https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/tts?appkey={appkey}&token={self.token}&text={text}&format=wav&voice={voice_id}&sample_rate=16000"

        # 发起GET请求
        response = requests.get(url)

        # 检查响应状态码
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
            return path
        else:
            return None

if __name__ == "__main__":
    text_to_tts = AliTTs()
    text_to_tts.speak("zhimiao_emo","2019/03/02上午有1/2的概率下暴雨所以有600人選擇3:30p.m.再出門,支付$500或￥600可以獲得代金券")