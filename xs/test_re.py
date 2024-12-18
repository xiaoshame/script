import re
import json

text = '''提起澳门，你想到的声音是什么？是耳熟能详的旋律，或是丰富多样的语言，跟随短片感受声音里的多彩澳门。<br><video width="1920" height="1080" src="https://video.twimg.com/ext_tw_video/1868924061570809857/pu/vid/avc1/1280x720/sX-bOJbfBxd6I2iO.mp4?tag=12" controls="controls" poster="https://pbs.twimg.com/ext_tw_video_thumb/1868924061570809857/pu/img/CdELNp32H0EVv9Hi.jpg"></video>'''
pattern = re.compile(r'<video[^>]*\s+src="([^"]*)"')
matches = pattern.findall(text)
data_json = '''{
    "video": [
        {
            "title": "高清",
            "url": "https://video.twimg.com/ext_tw_video/1868988596784709634/pu/vid/avc1/720x960/fEM10FSN8DnkJBnz.mp4?tag=12"
        },
        {
            "title": "高清1",
            "url": "https://video.twimg.com/ext_tw_video/1868988596784709634/pu/vid/avc1/720x960/fEM10FSN8DnkJBnz.mp4?tag=12"
        }
    ]
}'''

for data in data_json:
    print(data['video'][0])
    
for match in matches:
    print("匹配结果：", match)