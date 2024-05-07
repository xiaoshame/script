import json
import brotli
import base64
from haralyzer import HarParser


with open("D:\\workspace\\xiaohongshu\\1.har", encoding='utf-8') as f:
    har_parser = HarParser(json.loads(f.read()))


data = har_parser.har_data
entries = data['entries']
for entry in entries:
    text = entry['response']['content']['text']
    content = brotli.decompress(base64.b64decode(text)).decode()
    info = json.loads(content)
    print(info)
