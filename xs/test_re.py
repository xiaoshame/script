import re

text = '''url:'https://play.4kvm.pro/m3/3e6a3b91715951131/53Q2hyb21lJGh0dHBzOi8vd3d3LjRrdm0ubmV0L3dwLWNvbnRlbnQvdXBsb2Fkcy8yMDIxLzA2LzBlMTg1NjZmNzljNjI5Lm0zdTgkMTcxNTkwNzkzMQ6646ad5b5d6f4.m3u8','''

pattern = re.compile(r"url:'([^']+\.(?:m3u8|mp4))'")
matches = pattern.findall(text)

for match in matches:
    print("匹配结果：", match)