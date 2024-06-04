import re

text = '''var DATA = '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';
$(function()'''

pattern = re.compile(r"var DATA = '(.*?)';")
matches = pattern.findall(text)

for match in matches:
    print("匹配结果：", match)