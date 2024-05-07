import requests
import json
import configparser
import os
# URL地址
url = 'https://japanwest.tts.speech.microsoft.com/cognitiveservices/voices/list'

# 定义headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
    'Ocp-Apim-Subscription-Key':os.environ.get('SPEECH_KEY'),
    # 其他您需要的headers
}

# 发送GET请求，包含headers
response = requests.get(url, headers=headers)

# 检查请求是否成功
if response.status_code == 200:
    config = configparser.ConfigParser()
    config.read('config.ini')
    config['voice']={}
    # 输出返回的数据
    data = json.loads(response.text)
    for voice in data:
        if voice['Locale'] == 'zh-CN' or voice['Locale'] == 'zh-TW':
            config['voice'][voice['DisplayName']] =voice['ShortName']
    with open('config.ini', 'w',encoding='utf-8') as configfile:
        config.write(configfile)
else:
    # 输出错误信息
    print('Error:', response.status_code)