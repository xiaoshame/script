import re

text = '''http://chat.dz11.com/chat?session=inbox&topic=tpc_I6XXTMbjzMx3'''

pattern = re.compile(r'^(?:http[s]?://)?([^:/\s]+)')
matches = pattern.findall(text)

for match in matches:
    print("匹配结果：", match)