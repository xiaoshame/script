import json
import xml.etree.ElementTree as ET

### follow网站拷贝https://api.follow.is/entries 接口返回的json 文件
### 批量替换rss 地址并合成opml文件，方便订阅

# 解析JSON并构建OPML的函数
def build_opml(json_file_path, opml_body):
    with open(json_file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
    rss_feeds = data['data'][0]['feeds']
    
    for rss_feed in rss_feeds:
        url = rss_feed['url']
        if 'rsshub://' in url:
            replaced_url = url.replace("rsshub://", "https://rsshub.app/")

            outline_attribs = {
                "type": "rss",
                "text": rss_feed['title'],
                "description": rss_feed['description'],
                "xmlUrl": replaced_url
            }
            ET.SubElement(opml_body, "outline", attrib=outline_attribs)

# OPML的根元素和子元素
opml_root = ET.Element("opml", version="2.0")
head = ET.SubElement(opml_root, "head")
ET.SubElement(head, "title").text = "My RSS Feeds"
body = ET.SubElement(opml_root, "body")

# JSON文件路径
json_file_path1 = r'D:\\workspace\\\script\rss\\follow\\1.json'
json_file_path2 = r'D:\\workspace\\script\\rss\\follow\\2.json'
json_file_path3 = r'D:\\workspace\\script\\rss\\follow\\3.json'

# 构建OPML，传入JSON文件路径和OPML的body元素
build_opml(json_file_path1, body)
# build_opml(json_file_path2, body)
# build_opml(json_file_path3, body)

# 将OPML结构转换为字符串并保存到文件
opml_str = ET.tostring(opml_root, encoding='utf-8', method='xml').decode()
with open(r'D:\\workspace\\script\\rss\\follow\\output.opml', 'w', encoding='utf-8') as f:
    f.write(opml_str)