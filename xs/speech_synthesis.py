import azure.cognitiveservices.speech as speechsdk
import os
import configparser

class tts():
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        
    def speak(self, voice_id,text):
        path = 'D:\\workspace\\script\\xs\\output.wav'
        speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region="japanwest")  
        file_config = speechsdk.audio.AudioOutputConfig(filename=path)
        speech_config.speech_synthesis_voice_name= self.config['voices'][voice_id]
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=file_config)  
        speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()
        return path,speech_synthesis_result

if __name__ == "__main__":
    text_to_tts = tts()
    text_to_tts.speak("yunxia","2019/03/02上午有1/2的概率下暴雨所以有600人選擇3:30p.m.再出門,支付$500或￥600可以獲得代金券")